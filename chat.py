# -*- coding: utf-8 -*-
import agent.distill
from llms import chat
import argparse
import requests
from bs4 import BeautifulSoup
from consoles import print_markdown

chat_history = []

def show_response(res, no_pretty:bool = False):
    acc = []
    if isinstance(res, str):
        if no_pretty:
            print(res)
        else:
            print_markdown(res, title="From AI")
        return res

    print("[AI]:", end="")
    for chunk in res:
        print(chunk, end='')
        acc.append(chunk)
    print()
    return "".join(acc)

def fetch_url_content(url):
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for HTTP errors
        soup = BeautifulSoup(response.text, 'html.parser')
        return soup.get_text()  # Extract text from the HTML
    except requests.exceptions.RequestException as e:
        print(f"Error fetching URL: {e}")
        return None


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--file', nargs='+', action="extend", default=[], type=str, help='add file')
    parser.add_argument('--model', default="llama3-70b-8192", type=str, help='model name')
    parser.add_argument('--prompt', required=True, type=str, help='user prompt')
    parser.add_argument('--history', action='store_true', help='Enter conversation mode')
    parser.add_argument('--stream', action='store_true', help='Run in stream mode')
    parser.add_argument('--no-pretty', action='store_true', help='print in plaintext mode')
    parser.add_argument('--url', type=str, help='URL to fetch content from')

    args = parser.parse_args()

    combined_content = ""

    if args.file:
        for file in args.file:
            with open(file, 'r', encoding='utf-8') as f:
                combined_content += "file-info: " + f.read() + "\n"

    if args.url:
        url_content = fetch_url_content(args.url)
        if url_content:
            combined_content += "web-info: " + url_content + "\n"

    prompt = args.prompt

    if combined_content:
        prompt = f"""
            {combined_content}

        阅读上面的内容，然后回答用户的问题："{args.prompt}"
        """

    if not args.history:
        res = chat(prompt=prompt, model=args.model, stream=args.stream)
        response = show_response(res,args.no_pretty)

    else:
        chat_history.append(
            {"role": "user", "content": prompt}
        )
        res = chat(messages=chat_history, model=args.model, stream=args.stream)
        response = show_response(res)
        chat_history += [
            {"role": "assistant", "content": response}
        ]
        while True:
            q = input("[User]: ")
            chat_history.append(
                {"role": "user", "content": q}
            )
            res = chat(messages=chat_history, model=args.model, stream=args.stream)
            response = show_response(res)
            chat_history += [
                {"role": "assistant", "content": response}
            ]
            if len(chat_history) > 100:
                chat_history = chat_history[-100:]
