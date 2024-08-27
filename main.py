# -*- coding: utf-8 -*-
import json
import shutil
import time
import re

import pyperclip
from prompt_toolkit import PromptSession, HTML,prompt
from prompt_toolkit.history import FileHistory

from agent.critique import CritiqueAgent
from agent.generation_review import ReviewGenerationAgent
from agent.simulation import SimulationAgent
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
from agent.article_summarize import ArticleSummarize
from progress.progress import Progress
from prompts import read_prompt
from tts import tts
from common.convert import json_str_to_yaml_str
from entity_extraction.mermaid_opts import create_mermaid_png_and_display
from common.mermaid_code import generate_mermaid
from welcome import hello
from llms import chat

history_file = 'history.txt'

def extract_reply(res: str, token: str) -> str:
    pattern = fr"<{token}>(.*?)</{token}>"
    match = re.search(pattern, res, re.DOTALL)
    if match:
        return match.group(1).strip()
    return res

def fetch_url_content(url):
    import requests
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.text
        else:
            print(f"Failed to fetch URL: {url}. Status code: {response.status_code}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        return None

def read_file_content(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        print(f"File not found: {file_path}")
        return None
    except IOError as e:
        print(f"Error reading file {file_path}: {e}")
        return None

def check_file_exists(file_path):
    return os.path.exists(file_path)

def check_url_valid(url):
    import requests
    try:
        response = requests.head(url)
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--model', default="llama3-70b-8192", type=str, help='Model name')
    parser.add_argument('--tts', action='store_true', help='Enable tts')
    args = parser.parse_args()

    hello()

    valid_mode = ['文章总结讨论', '学习新概念', '管理作业/日程', '知识小测验', '通用']
    mode = None
    chat_history = ChatHistory()

    summary_agent = ArticleSummarize(
        chat_history=chat_history,
        model=args.model
    )

    inputs = []

    # 1. 选择要使用的Agent（不同学习模式）
    while not mode:
        mode_input_index = prompt(HTML("选择AI助手模式:\n<ansired>1.文章总结讨论</ansired>\n<ansiyellow>2.学习新概念</ansiyellow>\n<ansiblue>3.管理作业/日程</ansiblue>\n<ansigreen>4.知识小测验</ansigreen>\n<ansicyan>5.通用</ansicyan>\n>> "))

        try:
            index = int(mode_input_index or len(valid_mode))
            if 0 < index <= len(valid_mode):
                mode = valid_mode[index-1]
        except:
            pass

    # 2. 与不同Agent进行互动
    if mode == '文章总结讨论':
        try:
            session = PromptSession(
                HTML(f'<ansicyan><b> 用户  >> </b></ansicyan>'),
                history=FileHistory('history.txt')
            )
            while True:
                user_input = session.prompt()

                if user_input == '/asr':
                    user_input = record_and_asr()
                    show_response(res=user_input, title="ASR Result", title_align="left", width=40)
                    break
                elif user_input.startswith('file:'):
                    file_path = user_input[5:].strip()
                    if check_file_exists(file_path):
                        inputs.append(('file', file_path))
                    else:
                        print(f"File not found: {file_path}")
                elif user_input.startswith('url:'):
                    url_input = user_input[4:].strip()
                    if check_url_valid(url_input):
                        inputs.append(('url', url_input))
                    else:
                        print(f"Invalid or inaccessible URL: {url_input}")
                elif user_input:
                    break

        finally:
            pass

        context = ""

        for input_type, value in inputs:
            if input_type == 'file':
                file_content = read_file_content(value)
                if file_content:
                    context += "file-info: " + file_content + "\n"
            elif input_type == 'url':
                url_content = fetch_url_content(value)
                if url_content:
                    context += "web-info: " + url_content + "\n"

        res = summary_agent.generate_response(current_user_input=user_input, context=context)

        show_response(extract_reply(res=res, token="reply"), title="AI助手回复")
        show_response(extract_reply(res=res, token="quote"), title="引用")

        if args.tts:
            tts(extract_reply(res=res, token="reply"), output="tts_result.mp3", play=True)

    elif mode == '学习新概念':
        pass