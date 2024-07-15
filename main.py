# -*- coding: utf-8 -*-
import json
import time

from agent.simulation import SimulationAgent
from asr import record_and_asr
from chat_history import ChatHistory
from common.multiline_input_util import multi_input
from common.show_utils import show_response
from knowledge_graph.model import KnowledgeGraph
import argparse
from consoles import print_markdown, print_code
from llms import chat
from plan import plan_directory
from agent.distill import DistillAgent
from agent.generate import GenerationAgent
from tts import tts

def dump(file: str, description: str, knowledge_graph, chat_history, current_response: str):
    """
    Write the chat history, current response and knowledge tree to a JSON file.
    Args:
        file (str): The path to the JSON file where the data will be saved.
        description (str): Description of the knowledge tree.
        knowledge_graph: The knowledge graph data.
        chat_history: The chat history data.
        current_response (str): The current response data.
    """

    data = {
        "description": description,
        "knowledge_graph": knowledge_graph,
        "chat_history": chat_history,
        "current_response": current_response,
        "reason": "",
        "target_objective": "",
        "question": ""
    }

    # Write data to the JSON file
    with open(file + ".template", 'a') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
        f.write("\n")

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--model', default="llama3-70b-8192", type=str, help='Model name')
    parser.add_argument('--stream', action='store_true', help='Run in stream mode')
    parser.add_argument('--task',  type=str, help='Choose the task', default="marooned-distill-plan")
    parser.add_argument('--interviewee', type=str, help='Name of the interviewee', default="maria")
    parser.add_argument('--auto', action='store_true', help='Do a simulation')
    parser.add_argument('--tts', action='store_true', help='Enable tts')
    args = parser.parse_args()

    chat_history = ChatHistory()
    distilled_tree = KnowledgeGraph.restore(f"{plan_directory()}/{args.task}")

    distill_agent = DistillAgent(name=args.task+"-distill-agent", distilled_tree=distilled_tree, chat_history=chat_history, interviewee=args.interviewee, model="qwen-max-longcontext")
    generate_agent = GenerationAgent(name=args.task+"-generate-agent", distilled_tree=distilled_tree, chat_history=chat_history, interviewee=args.interviewee, model=args.model)
    simulate_agent = SimulationAgent(name=args.task+"-simulate-agent", distilled_tree=distilled_tree, chat_history=chat_history, interviewee=args.interviewee, model=args.model)
    # other agents

    begin = time.time()
    turn = 1

    while True:
        question = generate_agent.generate_question()

        chat_history.append(role="assistant", content=question)
        show_response(res=question, title="Question")
        if args.tts:
            tts(question, output="question.mp3", play=True)
        if args.auto:
            user_input = simulate_agent.simulate_response()
            show_response(user_input, title="auto-reply")
        else:
            user_input = multi_input(args.interviewee + ": ")
        if user_input == '/asr':
            user_input = record_and_asr()
        chat_history.append(role=args.interviewee, content=user_input)
        distill_agent.update_tree(turn=turn)
        turn += 1

        if time.time() - begin > 30 * 60:
            break

        while True:
            command = input("Command:")
            if command == "/dump":
                description = input("What should the description be:")
                current_response = chat_history.get_message()[-1]['content']
                dump_chat_history = chat_history.get_message()[:-1]
                dump(description=description, current_response=current_response, chat_history=dump_chat_history,
                     knowledge_graph=distilled_tree.get_tree(), file="dataset/collected_examples")
            elif command == "/auto":
                args.auto = not args.auto
            elif command == "/tree":
                print_code(distilled_tree.format_to_tree(), language="json", title="DistilledTree")
            elif command == "/continue" or command == "":
                break
            else:
                print("Unknown Command, Please Try Again")
