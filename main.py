# -*- coding: utf-8 -*-
import json
import time

import pyperclip
from prompt_toolkit import PromptSession, HTML
from prompt_toolkit.history import FileHistory

from agent.critique import CritiqueAgent
from agent.simulation import SimulationAgent
from agent.summary import SummaryAgent
from agent.entity_extraction_distill import EntityExtractionAgent
from knowledge_graph.entity_relation_triple import EntityRelationTriple
from asr import record_and_asr
from chat_history import ChatHistory
from common.show_utils import show_response, to_progress_bar
from knowledge_graph.model import KnowledgeGraph
from knowledge_graph.model_manager import KnowledgeTreeManager
import argparse
from consoles import print_code
from plan import plan_directory
from agent.distill import DistillAgent
from agent.generation import GenerationAgent
from progress.progress import Progress
from prompts import read_prompt
from tts import tts
# import readline
from common.convert import json_str_to_yaml_str
from entity_extraction.mermaid_opts import create_mermaid_png_and_display
from common.mermaid_code import generate_mermaid

history_file = 'history.txt'
                                                                                                                      
# def save_history(history_file):
#   readline.write_history_file(history_file)
#
# def load_history(history_file):
#   try:
#       readline.read_history_file(history_file)
#   except FileNotFoundError:
#       pass

# Load history from the history file
# load_history(history_file)


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

    valid_tones = ['严肃的', '幽默的', '海盗式的', '随意的', '莎士比亚式的', '无建议', '']
    tone = None
    entity_relationship_triple = EntityRelationTriple()
    tree_manager = KnowledgeTreeManager()
    chat_history = ChatHistory()
    distilled_tree = KnowledgeGraph.restore(f"{plan_directory()}/{args.task}")
    progress = Progress(total_minutes=distilled_tree.estimated_minute, objectives_count=len(distilled_tree.objectives))

    if args.restore:
        distilled_tree, chat_history, args.task, args.interviewee, args.model, tone = load_restore_data(args.restore)

    while not tone:
        tone_input = input("你希望萃取专家的语气风格是（严肃的/幽默的/海盗式的/随意的/莎士比亚式的/无建议）：")

        if tone_input in valid_tones:
            tone = tone_input
            if tone == '':
                tone = '无建议'
        else:
            print("无效的选项，请重新输入。")

    distill_agent = DistillAgent(
        name=args.task+"-distill-agent",
        distilled_tree=distilled_tree,
        chat_history=chat_history,
        interviewee=args.interviewee,
        model=args.model
    )
    entity_extraction_agent = EntityExtractionAgent(
        name=args.task+"-distill-agent",
        distilled_tree=distilled_tree,
        chat_history=chat_history,
        model=args.model,
        entity_types=["ANIMAL", "SUBSTANCE", "DATE", "EVENT", "TRAITS", "ACTION", "OTHER"],
        entity_relationship_triple=entity_relationship_triple
    )
    generate_agent = GenerationAgent(
        name=args.task+"-generate-agent",
        distilled_tree=distilled_tree,
        chat_history=chat_history,
        interviewee=args.interviewee,
        model=args.model,
        progress=progress,
        tone=tone,
        prompt="roleplay_generate"
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

    turn = 0
    while True:
        question = generate_agent.generate_question()

        chat_history.append(role="萃取专家", content=question)
        show_response(res=question, title=f'  萃取专家', title_align="right")
        if args.tts:
            tts(question, output="question.mp3", play=True)
        if args.auto:
            user_input = simulate_agent.simulate_response()
            show_response(user_input, title="auto-reply  ", title_align='left')
            turn += 1
        else:
            try:
                session = PromptSession(
                    HTML(f'<ansicyan><b> {args.interviewee}  >> </b></ansicyan>'),
                    history=FileHistory('history.txt')
                )
                while True:
                    user_input = session.prompt()
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
                        print_code(json_str_to_yaml_str(tree_manager.get_current_tree().format_to_tree()),
                                   language="yaml",
                                   title="DistilledTree"
                                   )
                    elif user_input == "/graph":
                        mermaid_code = generate_mermaid(entity_relationship_triple.get_entities(),
                                        entity_relationship_triple.get_relationships()
                                        )
                        create_mermaid_png_and_display(mermaid_code=mermaid_code,
                                                       relationships=entity_relationship_triple.get_relationships()
                                                       )
                    elif user_input == "/generation-prompt":
                        show_response(generate_agent.get_prompt(), title="Generation / Prompt")
                    elif user_input == "/distill-prompt":
                        show_response(distill_agent.get_prompt(), title="Distill / Prompt")
                    elif user_input == "/summary-prompt":
                        show_response(summary_agent.get_prompt(), title="Summary / Prompt")
                    elif user_input == "/refine":
                        summary_agent.restructure(turn=progress.get_round())
                        tree_manager.push_back(distilled_tree.clone())
                    elif user_input == "/undo":
                        tree_manager.pop()
                    elif user_input == "/progress":
                        progress_template = read_prompt("show_progress")
                        p = progress.get_progress()

                        objective_progress = to_progress_bar(
                            n_done=p["objectives_completed_count"],
                            n_total=p["objectives_total"]
                        )
                        time_elapsed = p["time_total"]-p["time_remaining"]
                        time_progress = to_progress_bar(
                            n_done=time_elapsed,
                            n_total=p["time_total"]
                        )
                        progress_stats = progress_template.format(
                            time_progress=time_progress,
                            time_elapsed=time_elapsed,
                            time_total=p["time_total"],
                            obj_progress=objective_progress,
                            obj_completed=p["objectives_completed_count"],
                            obj_total=p["objectives_total"],
                            rounds_completed=p["round_total"],
                            rounds_remaining=p["rounds_remaining"] if p["rounds_remaining"] != 'Unknown' else ''
                        )
                        show_response(progress_stats, title="访谈进度概览", width=80)
                    elif user_input == '/asr':
                        user_input = record_and_asr()
                    elif user_input == '/clipboard':
                        user_input = pyperclip.paste()

                    elif user_input[:1] == "/":
                        print("Unknown Command")
                        continue
                    elif user_input:
                        break
            finally:
                    pass
                # Save history to the history file
                # save_history(history_file)

        chat_history.append(role=args.interviewee, content=user_input)
        mermaid_code, relation = entity_extraction_agent.extract_triplet(turn=progress.get_round())
        create_mermaid_png_and_display(mermaid_code=mermaid_code,
                                       relationships=relation
                                       )

        distill_agent.update_tree(turn=progress.get_round())
        tree_manager.push_back(distilled_tree)
        # critique_agent.rate_response()
        progress.on_interviewee_replied(
            objectives_completed=distilled_tree.get_completed_objective_num()
        )

        if time.time() - begin > distilled_tree.estimated_minute * 60:
            show_response(generate_agent.end_chat(), title="萃取专家")
            break

        if turn % 5 == 0:
            verified = input("continue?(Y/N)")
            if verified in ('Y', ''):
                continue
            else:
                args.auto = False


