# -*- coding: utf-8 -*-
import json
import shutil
import time

import pyperclip
from prompt_toolkit import PromptSession, HTML,prompt
from prompt_toolkit.history import FileHistory

from agent.critique import CritiqueAgent
from agent.generation_review import ReviewGenerationAgent
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
from llms.statistics import get_usage
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
from welcome import hello

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
        review_history,
        interviewee,
        model,
        task,
        tone,
        progress
):
    data = {
        'knowledge_graph': knowledge_graph,
        'chat_history': chat_history,
        'review_history': review_history,
        'interviewee': interviewee,
        'model': model,
        'task': task,
        'tone': tone,
        'progress': progress
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
        review_history = ChatHistory(**data["review_history"])
        tone = data["tone"]
        progress = Progress(total_minutes=0,objectives_count=0)
        progress.load_from_dict(data["progress"])
    return distilled_tree, chat_history, review_history, task, interviewee, model, tone, progress

def show_progress():
    progress_template = read_prompt("show_progress")
    p = progress.get_progress()
    usage = get_usage()

    objective_progress = to_progress_bar(
        n_done=int(p["progress_completed"] * 100),
        n_total=p["objectives_total"] * 100
    )
    time_elapsed = p["time_total"] - p["time_remaining"]
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
        rounds_remaining=p["rounds_remaining"] if p["rounds_remaining"] != 'Unknown' else '',
        prompt_tokens = usage['prompt_tokens'],
        completion_tokens = usage['completion_tokens'],
        total_tokens = usage['total_tokens'],
        price=usage['price']
    )
    show_response(progress_stats, title="访谈进度概览", width=80)

def show_tree():
    from knowledge_graph.style import build_rich_tree
    from rich.console import Console
    tree = tree_manager.get_current_tree()
    if not tree:
        return
    styled_tree = build_rich_tree(tree)
    console = Console()
    console.print(styled_tree)
    # print_code(json_str_to_yaml_str(tree_manager.get_current_tree().format_to_tree()),
    #            language="yaml",
    #            title="DistilledTree"
    #            )

def show_graph():
    mermaid_code = generate_mermaid(entity_relationship_triple.get_entities(),
                                    entity_relationship_triple.get_relationships()
                                    )
    create_mermaid_png_and_display(mermaid_code=mermaid_code,
                                   relationships=entity_relationship_triple.get_relationships()
                                   )

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--model', default="llama3-70b-8192", type=str, help='Model name')
    parser.add_argument('--stream', action='store_true', help='Run in stream mode')
    parser.add_argument('--task',  type=str, help='Choose the task', default="organism-classification-distill-plan")
    parser.add_argument('--interviewee', type=str, help='Name of the interviewee', default="maria")
    parser.add_argument('--auto', action='store_true', help='Do a simulation')
    parser.add_argument('--tts', action='store_true', help='Enable tts')
    parser.add_argument('--restore', type=str, help='restore the task', default="")
    parser.add_argument('--generation-mode', type=str, choices=["conversation", "solo"],help='restore the task', default="conversation")
    args = parser.parse_args()

    hello()

    valid_tones = ['严肃', '幽默', '海盗式', '甄嬛传风格', '莎士比亚式', "鲁迅风格", '无建议']
    tone = None
    entity_relationship_triple = EntityRelationTriple()
    tree_manager = KnowledgeTreeManager()
    chat_history = ChatHistory()
    review_history = ChatHistory()
    distilled_tree = KnowledgeGraph.restore(f"{plan_directory()}/{args.task}")
    progress = Progress(total_minutes=distilled_tree.estimated_minute, objectives_count=len(distilled_tree.objectives))

    if args.restore:
        (distilled_tree,
         chat_history,
         review_history,
         args.task,
         args.interviewee,
         args.model,
         tone,
         progress) = load_restore_data(args.restore)

    while not tone:
        tone_input_index = prompt(HTML("你希望萃取专家的语气风格是:\n<ansired>1.严肃</ansired>\n<ansiyellow>2.幽默</ansiyellow>\n<ansiblue>3.海盗式</ansiblue>\n<ansigreen>4.甄嬛传风格</ansigreen>\n<ansicyan>5.莎士比亚式</ansicyan>\n<ansiyellow>6.鲁迅风格</ansiyellow>\n7.默认 \n>> "))

        try:
            index = int(tone_input_index or len(valid_tones))
            if 0 < index <= len(valid_tones):
                tone = valid_tones[index-1]
        except:
            pass

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
        review_history=review_history
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
    review_generation_agent = ReviewGenerationAgent(
        name=args.task+"-review-generate-agent",
        distilled_tree=distilled_tree,
        model=args.model,
        progress=progress,
        review_history=review_history
    )
    # other agents

    begin = time.time()
    turn = 0
    term_col, _ = shutil.get_terminal_size()
    while True:

        question = None
        if args.generation_mode == "conversation":
            for i in range(5):
                question = generate_agent.generate_question()
                review_history.append(role="Asker", content=question)
                show_response(question, title="问题发起者（小组讨论）", offset=term_col//2,width=60, title_align="right", border_color="cyan")
                verification, answer = review_generation_agent.generate_review()
                if verification == "No":
                    review_history.append(role="Reviewer", content=answer)
                    show_response("🙅 \n"+answer, title="问题审核员（小组讨论）", offset=term_col//2, width=60, title_align="left", border_color="cyan")
                if verification == "Yes":
                    review_history.append(role="Reviewer", content="该问题被审核通过")
                    show_response(" ", title="问题审核员（小组讨论）", offset=term_col // 2, width=60, title_align="left", border_color="cyan")
                    break
        else:
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
                            review_history=review_history.model_dump(),
                            interviewee=args.interviewee,
                            model=args.model,
                            task=args.task,
                            tone=tone,
                            progress=progress.mapping(),
                        )
                    elif user_input == "/auto":
                        args.auto = True
                        user_input = simulate_agent.simulate_response()
                        show_response(user_input, title="auto-reply  ", title_align='left')
                        turn += 1
                        break
                    elif user_input == "/tree":
                        show_tree()
                    elif user_input == "/graph":
                        show_graph()
                    elif user_input == "/generation-prompt":
                        show_response(generate_agent.get_prompt(), title="Generation / Prompt")
                    elif user_input == "/distill-prompt":
                        show_response(distill_agent.get_prompt(), title="Distill / Prompt")
                    elif user_input == "/review-generation-prompt":
                        show_response(review_generation_agent.get_prompt(), title="Generation-Review / Prompt")
                    elif user_input == "/summary-prompt":
                        show_response(summary_agent.get_prompt(), title="Summary / Prompt")
                    elif user_input == "/refine":
                        summary_agent.restructure(turn=progress.get_round())
                        tree_manager.push_back(distilled_tree.clone())
                    elif user_input == "/undo":
                        tree_manager.pop()
                    elif user_input == "/progress":
                        show_progress()
                    elif user_input == '/asr':
                        user_input = record_and_asr()
                        show_response(res=user_input, title="ASR Result", title_align="left", width=40)
                        break
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
            objectives_completed=distilled_tree.get_completed_objective_num(),
            total_objective_progress=distilled_tree.get_total_objective_progress()
        )

        if time.time() - begin > distilled_tree.estimated_minute * 60:
            show_tree()
            show_graph()
            show_progress()
            show_response(res=generate_agent.end_chat(), title=f'  萃取专家', title_align="right")
            break
        if args.auto:
            if turn % 3 == 0:
                verified = input("continue?(Y/N)")
                if verified in ('Y', ''):
                    continue
                else:
                    args.auto = False


