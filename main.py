# -*- coding: utf-8 -*-
import asyncio
import threading
import argparse
import os
import re
import shlex
import subprocess
import time
import atexit
from prompt_toolkit import PromptSession, HTML, prompt
from prompt_toolkit.history import FileHistory
from agent.knowledge_test import KnowledgeTest
from agent.article_summarize import ArticleSummarize
from agent.general import GeneralAI
from agent.shinku_roleplay import ShinkuAI
from agent.research import Researcher
from asr import record_and_asr
from chat_history import ChatHistory
from common.show_utils import show_response
from consoles import print_code
from welcome import hello
from tts.ai_tts import tts_with_ai_segmented as tts
from tts.ai_tts import stop_audio_playback, is_audio_playing
from common.tool_utils import check_file_exists, check_url_valid, read_file_content, fetch_url_content, extract_reply, read_pdf_content

history_file = 'history.txt'
process = None
# 启动 TTS 子进程
def start_tts_process():
    show_response(res="正在启动TTS系统，请稍等...", title=None)
    process = subprocess.Popen(
        ['cmd.exe', '/c', 'api.bat'],
        cwd=r'C:\Users\25899\Desktop\GPT-SoVITS-beta0706',
        stdout=subprocess.DEVNULL,
        #stdout=None,
        stderr=subprocess.DEVNULL,
        #stderr=None
    )
    time.sleep(5)
    # show_response(res="TTS系统启动完毕", title=None)
    return process

def kill_process(process):
    subprocess.call(
        ['taskkill', '/F', '/T', '/PID', str(process.pid)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

def play_tts_in_thread(reply):
    tts_thread = threading.Thread(target=tts, args=(reply,))
    tts_thread.start()

def clean_file(path: str):
    folder_path = path
    if os.path.exists(folder_path):
        for filename in os.listdir(folder_path):
            file_path = os.path.join(folder_path, filename)
            if os.path.isfile(file_path):
                os.remove(file_path)

def cleanup():
    global process
    if process:
        kill_process(process)
    clean_file('temp_tts_output')
# Clean Up Whenever the Main Process Exits
atexit.register(cleanup)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--model', default="gemini-1.5-flash", type=str, help='Model name')
    parser.add_argument('--tts', action='store_true', help='Enable tts')
    parser.add_argument('--asr', action='store_true', help='Enable asr')
    args = parser.parse_args()

    hello()

    process = None
    if args.tts:
        process = start_tts_process()
        time.sleep(2)

    valid_mode = ['文章总结讨论', '学习新概念', '日程安排', '知识小测验', '通用', '角色扮演：二阶堂真红']
    mode = None
    chat_history = ChatHistory()

    inputs = []

    # 1. 选择要使用的Agent（不同学习模式）
    while not mode:
        mode_input_index = prompt(HTML("选择AI助手模式:"
                                       "\n<ansired>1.文章总结讨论</ansired>"
                                       "\n<ansiyellow>2.学习新概念</ansiyellow>"
                                       "\n<ansiblue>3.日程安排</ansiblue>"
                                       "\n<ansigreen>4.知识小测验</ansigreen>"
                                       "\n<ansicyan>5.通用</ansicyan>"
                                       "\n<ansiyellow>6.角色扮演：二阶堂真红</ansiyellow>"
                                       "\n>"))

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
                    if args.asr:
                        time.sleep(3)
                        user_input = record_and_asr()
                        show_response(res=user_input, title="ASR Result", title_align="left", width=40)
                        chat_history.append(role="user", content=user_input)
                        break
                    else:
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
                play_tts_in_thread(reply)
                while is_audio_playing():
                    time.sleep(0.1)

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
                    if args.asr:
                        time.sleep(3)
                        user_input = record_and_asr()
                        show_response(res=user_input, title="ASR Result", title_align="left", width=40)
                        chat_history.append(role="user", content=user_input)
                        break
                    else:
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
                play_tts_in_thread(reply)
                while is_audio_playing():
                    time.sleep(0.1)

# ==============================================================================#

    elif mode == '日程安排':
        pass

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
                    if args.asr:
                        time.sleep(3)
                        user_input = record_and_asr()
                        show_response(res=user_input, title="ASR Result", title_align="left", width=40)
                        chat_history.append(role="user", content=user_input)
                        break
                    else:
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
                play_tts_in_thread(reply)
                while is_audio_playing():
                    time.sleep(0.1)

#==============================================================================#

    elif mode == '通用':
        general_agent = GeneralAI(
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
                    if args.asr:
                        time.sleep(3)
                        user_input = record_and_asr()
                        show_response(res=user_input, title="ASR Result", title_align="left", width=40)
                        chat_history.append(role="user", content=user_input)
                        break
                    else:
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

            res = general_agent.generate_response(current_user_input=user_input)
            reply = extract_reply(res=res, token="reply")

            chat_history.append(role="assistant", content=reply.strip())

            show_response(reply, title="AI助手回复")

            if args.tts:
                play_tts_in_thread(reply)
                while is_audio_playing():
                    time.sleep(0.1)

        # ==============================================================================#

    elif mode == '角色扮演：二阶堂真红':
        shinku_agent = ShinkuAI(
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
                    if args.asr:
                        time.sleep(3)
                        user_input = record_and_asr()
                        show_response(res=user_input, title="ASR Result", title_align="left", width=40)
                        chat_history.append(role="user", content=user_input)
                        break
                    else:
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

            res = shinku_agent.generate_response(current_user_input=user_input)
            reply = extract_reply(res=res, token="reply")

            chat_history.append(role="assistant", content=reply.strip())

            show_response(reply, title="AI助手回复")

            if args.tts:
                play_tts_in_thread(reply)
                while is_audio_playing():
                    time.sleep(0.1)

#==============================================================================#

    # 程序结束时终止子程序并清理临时文件夹
    if process:
        kill_process(process)

    clean_file('temp_tts_output')
