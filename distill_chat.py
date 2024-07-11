# -*- coding: utf-8 -*-
import time

from asr import record_and_asr
from chat_history import ChatHistory
from common.multiline_input_util import multi_input
from common.show_utils import show_response
from knowledge_graph.model import KnowledgeGraph
import argparse
from consoles import print_markdown, print_code
from plan import plan_directory
from agent.distill import DistillAgent
from agent.generate import GenerationAgent
from tts import tts

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--model', default="llama3-70b-8192", type=str, help='model name')
    parser.add_argument('--stream', action='store_true', help='Run in stream mode')
    parser.add_argument('--task',  type=str, help='Choose the task', default="education-distill-plan")
    parser.add_argument('--interviewee', type=str, help='Name of the interviewee', default="maria")
    parser.add_argument('--tts', type=bool, help='enable tts', default=False)
    args = parser.parse_args()

    chat_history = ChatHistory()
    distilled_tree = KnowledgeGraph.restore(f"{plan_directory()}/{args.task}")

    distill_agent = DistillAgent(name=args.task+"-distill-agent", distilled_tree=distilled_tree, chat_history=chat_history, interviewee=args.interviewee)
    generate_agent = GenerationAgent(name=args.task+"-generate-agent", distilled_tree=distilled_tree, chat_history=chat_history, interviewee=args.interviewee)
    # other agents

    begin = time.time()
    turn = 1

    while True:
        generation_res = generate_agent.generate_question(model=args.model)

        import re
        pattern = r"<question>(.*?)</question>"
        match = re.search(pattern, generation_res, re.DOTALL)
        if match:
            question = match.group(1).strip()
        else:
            question = generation_res

        chat_history.append(role="assistant", content=question)  # Replace with generated question
        print_code(distilled_tree.format_to_tree(), language="json", title="DistilledTree")
        show_response(res=question, title="Question")
        if args.tts:
            tts(question, output="question.mp3", play=True)
        user_input = multi_input('user:')
        if user_input == '/asr':
            user_input = record_and_asr()
            show_response(res=user_input, title="ASR Result")
        chat_history.append(role="user", content=user_input)
        distill_agent.update_tree(model=args.model, turn=turn)
        turn += 1

        if time.time() - begin > 30 * 60:
            break
