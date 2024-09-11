# -*- coding: utf-8 -*-
import argparse

import shlex
from prompt_toolkit import PromptSession, HTML, prompt
from prompt_toolkit.history import FileHistory
import subprocess

from agent.knowledge_test import KnowledgeTest
from agent.article_summarize import ArticleSummarize
from agent.research import Researcher
from asr import record_and_asr
from chat_history import ChatHistory
from common.show_utils import show_response
from welcome import hello
from tts.ai_tts import tts_with_ai_segmented as tts
from tts.ai_tts import stop_audio_playback
from common.tool_utils import check_file_exists, check_url_valid, read_file_content, fetch_url_content, extract_reply, read_pdf_content

history_file = 'history.txt'

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--model', default="gemini-1.5-flash", type=str, help='Model name')
    parser.add_argument('--tts', action='store_true', help='Enable tts')
    args = parser.parse_args()

    hello()
    if args.tts:
        process = subprocess.Popen(['cmd.exe', '/c', 'api.bat'], cwd=r'C:\Users\25899\Desktop\GPT-SoVITS-beta0706',
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL)


    valid_mode = ['文章总结讨论', '学习新概念', '管理作业/日程', '知识小测验', '通用']
    mode = None
    chat_history = ChatHistory()

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
    end_chat = False

# ==============================================================================#

    if mode == '文章总结讨论':
        summary_agent = ArticleSummarize(
            chat_history=chat_history,
            model=args.model
        )
        while True:
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
                        file_path = shlex.split(user_input[5:].strip())[0]  # 解析带空格的路径
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
                    elif user_input == '/end':
                        end_chat = True
                        break
                    elif user_input == '/stop-audio':
                        stop_audio_playback()
                    elif user_input:
                        chat_history.append(role="user", content=user_input)
                        break
            finally:
                pass

            if end_chat:
                break

            context = ""

            for input_type, value in inputs:
                if input_type == 'file':
                    file_content = read_file_content(value)
                    if file_content:
                        context += "file-info: " + file_content + "\n End of this file \n"
                elif input_type == 'url':
                    url_content = fetch_url_content(value)
                    if url_content:
                        context += "web-info: " + url_content + "\n End of this web-info \n"

            res = summary_agent.generate_response(current_user_input=user_input, context=context)
            reply = extract_reply(res=res, token="reply")
            quote = extract_reply(res=res, token="quote")

            chat_history.append(role="assistant", content=f"{reply}, quote:{quote}".strip())

            show_response(reply, title="AI助手回复")
            show_response(quote, title="引用")

            if args.tts:
                tts(reply)

#==============================================================================#

    elif mode == '学习新概念':
        research_agent = Researcher(
            chat_history=chat_history,
            model=args.model
        )
        while True:
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
                    elif user_input == '/end':
                        end_chat = True
                        break
                    elif user_input:
                        chat_history.append(role="user", content=user_input)
                        break
            finally:
                pass

            if end_chat:
                break

            res = research_agent.generate_response(current_user_input=user_input)
            reply = extract_reply(res=res, token="reply")
            quote = extract_reply(res=res, token="quote")

            chat_history.append(role="assistant", content=f"{reply}, quote:{quote}".strip())

            show_response(reply, title="AI助手回复")
            show_response(quote, title="引用")

            if args.tts:
                tts(reply)


# ==============================================================================#

    elif mode == '知识小测验':
        test_agent = KnowledgeTest(
            chat_history=chat_history,
            model=args.model
        )
        while True:
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
                    elif user_input == '/end':
                        end_chat = True
                        break
                    elif user_input:
                        chat_history.append(role="user", content=user_input)
                        break
            finally:
                pass

            if end_chat:
                break

            res = test_agent.generate_response(current_user_input=user_input)
            reply = extract_reply(res=res, token="reply")

            chat_history.append(role="assistant", content=reply.strip())

            show_response(reply, title="AI助手回复")

            if args.tts:
                tts(reply)

#==============================================================================#

