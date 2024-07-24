# -*- coding: utf-8 -*-
import json
import time

import pyperclip

from agent.critique import CritiqueAgent
from agent.simulation import SimulationAgent
from agent.summary import SummaryAgent
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
from agent.generation import GenerationAgent
from progress import Progress
from tts import tts
from snapshot import snapshot_directory
import readline

history_file = 'history.txt'
                                                                                                                      
def save_history(history_file):
  readline.write_history_file(history_file)

def load_history(history_file):
  try:
      readline.read_history_file(history_file)
  except FileNotFoundError:
      pass

# Load history from the history file
load_history(history_file)


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

def dump_snapshot(
        file: str,
        knowledge_graph,
        chat_history,
        interviewee,
        model,
        task,
        tone
):
    data = {
        'knowledge_graph': knowledge_graph,
        'chat_history': chat_history,
        'interviewee': interviewee,
        'model': model,
        'task': task,
        'tone': tone
    }
    with open(file + ".json", 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def load_restore_data(file: str):
    with open("snapshot/" + file + ".json", 'r', encoding='utf-8') as f:
        data = json.load(f)
        task = data["task"]
        interviewee = data["interviewee"]
        model = data["model"]
        distilled_tree = KnowledgeGraph(**data["knowledge_graph"])
        chat_history = ChatHistory(**data["chat_history"])
        tone = data["tone"]
    return distilled_tree, chat_history, task, interviewee, model, tone


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--model', default="llama3-70b-8192", type=str, help='Model name')
    parser.add_argument('--stream', action='store_true', help='Run in stream mode')
    parser.add_argument('--task',  type=str, help='Choose the task', default="organism-classification-distill-plan")
    parser.add_argument('--interviewee', type=str, help='Name of the interviewee', default="maria")
    parser.add_argument('--auto', action='store_true', help='Do a simulation')
    parser.add_argument('--tts', action='store_true', help='Enable tts')
    parser.add_argument('--restore', type=str, help='restore the task', default="")
    args = parser.parse_args()

    valid_tones = ['严肃的', '幽默的', '海盗式的', '随意的', '莎士比亚式的', '无建议']
    tone = None
    chat_history = ChatHistory()
    distilled_tree = KnowledgeGraph.restore(f"{plan_directory()}/{args.task}")
    progress = Progress(total_minutes=distilled_tree.estimated_minute, objectives_count=len(distilled_tree.objectives))

    if args.restore:
        distilled_tree, chat_history, args.task, args.interviewee, args.model, tone = load_restore_data(args.restore)

    while not tone:
        tone_input = input("你希望萃取专家的语气风格是（严肃的/幽默的/海盗式的/随意的/莎士比亚式的/无建议）：")

        if tone_input in valid_tones:
            tone = tone_input
        else:
            print("无效的选项，请重新输入。")

    distill_agent = DistillAgent(
        name=args.task+"-distill-agent",
        distilled_tree=distilled_tree,
        chat_history=chat_history,
        interviewee=args.interviewee,
        model=args.model
    )
    generate_agent = GenerationAgent(
        name=args.task+"-generate-agent",
        distilled_tree=distilled_tree,
        chat_history=chat_history,
        interviewee=args.interviewee,
        model=args.model,
        progress=progress,
        tone=tone
    )
    simulate_agent = SimulationAgent(
        name=args.task+"-simulate-agent",
        distilled_tree=distilled_tree,
        chat_history=chat_history,
        interviewee=args.interviewee,
        model=args.model
    )
    critique_agent = CritiqueAgent(
        name=args.task+"-critique-agent",
        distilled_tree=distilled_tree,
        chat_history=chat_history,
        interviewee=args.interviewee,
        model=args.model
    )
    summary_agent = SummaryAgent(
        name=args.task + "-summary-agent",
        distilled_tree=distilled_tree,
        chat_history=chat_history,
        model=args.model
    )
    # other agents

    begin = time.time()

    while True:
        question = generate_agent.generate_question()

        chat_history.append(role="萃取专家", content=question)
        show_response(res=question, title=f'萃取专家 / {args.model} / Roleplay')
        if args.tts:
            tts(question, output="question.mp3", play=True)
        if args.auto:
            user_input = simulate_agent.simulate_response()
            show_response(user_input, title="auto-reply")
        else:
            try:
                while True:
                    user_input = input(args.interviewee + ": ")
                    if user_input == "/dump":
                        chat_history_chopped_last = ChatHistory()
                        chat_history_chopped_last.chat_history = chat_history.chat_history[:-1]
                        dump_snapshot(
                            file="snapshot/test-snapshot2",
                            knowledge_graph=distilled_tree.model_dump(),
                            chat_history=chat_history_chopped_last.model_dump(),
                            interviewee=args.interviewee,
                            model=args.model,
                            task=args.task,
                            tone=tone
                        )
                    elif user_input == "/auto":
                        args.auto = not args.auto
                    elif user_input == "/tree":
                        print_code(distilled_tree.format_to_tree(), language="json", title="DistilledTree")
                    elif user_input == "/generation-prompt":
                        show_response(generate_agent.get_prompt(), title="Generation / Prompt")
                    elif user_input == "/distill-prompt":
                        show_response(distill_agent.get_prompt(), title="Distill / Prompt")
                    elif user_input == "/summary-prompt":
                        show_response(summary_agent.get_prompt(), title="Summary / Prompt")
                    elif user_input:
                        break
            finally:
                # Save history to the history file
                save_history(history_file)
        if user_input == '/asr':
            user_input = record_and_asr()
        if user_input == '/clipboard':
            user_input = pyperclip.paste()

        if user_input is None:
            user_input = ""
        chat_history.append(role=args.interviewee, content=user_input)
        distill_agent.update_tree(turn=progress.get_round())
        summary_agent.restructure(turn=progress.get_round())
        # critique_agent.rate_response()
        progress.on_interviewee_replied(
            objectives_completed=distilled_tree.get_completed_objective_num()
        )

        if time.time() - begin > distilled_tree.estimated_minute:
            show_response(generate_agent.end_chat(), title="萃取专家")
            break


