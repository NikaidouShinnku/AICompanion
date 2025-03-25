import json
from datetime import datetime

from chat_history import ChatHistory
from common.show_utils import show_response
from dataset import dataset_directory
from interviewee import interviewee_directory
from llms import chat
from prompts import read_prompt
from common.tool_utils import extract_reply

class GeneralAI:

    def __init__(
            self,
            chat_history:
            ChatHistory,
            model: str,
    ):
        self.chat_history = chat_history
        self.begin = datetime.now()
        self.final_prompt_template = read_prompt("generalAI_prompt")
        self.model = model

        example_prompt_template = read_prompt("single_research")
        with open(f"{dataset_directory()}/research_examples.json", "r", encoding="utf-8") as f:
            example_dataset = json.loads(f.read())

        examples = []
        num = 1
        for example in example_dataset:
            examples.append(
                example_prompt_template.format(
                    description=example["description"],
                    chat_history=self.format_chat_history(example['chat_history']),
                    thought=example["thought"],
                    reply=example["reply"],
                    case=example["case"],
                    search_result=example["search_result"],
                    quote=example["quote"],
                    num=num
                )
            )
            num += 1
        self.examples = "\n\n".join(examples)
        # show_response(self.examples, title="examples")

    def get_prompt(self, current_user_input:str, search_result):
        messages = self.chat_history.get_message()
        if len(messages) > 0:
            chat_history = messages
        else:
            current_user_input = ""
            chat_history = []

        return self.final_prompt_template.format(
            examples=self.examples,
            chat_history=self.format_chat_history(chat_history),
            current_user_input=current_user_input,
            search_result=search_result,
            date=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )

    def generate_response(self, current_user_input: str):
        search_result = "No Search Result Yet"
        search_fail_count = 0  # Initialize the search failure counter

        while True:
            prompt = self.get_prompt(current_user_input, search_result)
            res = chat(prompt=prompt, model=self.model, temperature=0.7)

            if extract_reply(res=res, token="reply").startswith("[SEARCH]"):
                search_query = extract_reply(res=res, token="reply").replace("[search]", "").strip()
                search_result = search_keywords_and_return_results(search_query)

                # Check if the search result is still unavailable
                if search_result == "No search results returned.":
                    search_fail_count += 1
                    if search_fail_count >= 3:  # After 3 failed attempts, stop searching
                        search_result = "The search is not available, stop searching and give a reply"
                        continue
                else:
                    search_fail_count = 0  # Reset counter if search succeeds
                continue
            else:
                break

        return res

    def format_chat_history(self, messages):
        formatted = ""
        for message in messages:
            formatted += message['role'] + ": " + message['content'].replace("\n", "") + "\n\n"

        return formatted


import requests


# 示例：提取关键词的简单函数，你可以根据需求改进
def extract_keywords(user_input):
    keywords = user_input.split()
    return keywords


# 使用Bing Search API进行搜索
def search_web(query):
    api_key = "399edd5fde974e3dbb1072ad0a1f10e8"
    search_url = "https://api.bing.microsoft.com/v7.0/search"

    headers = {"Ocp-Apim-Subscription-Key": api_key}
    params = {"q": query, "textDecorations": True, "textFormat": "HTML"}

    try:
        response = requests.get(search_url, headers=headers, params=params)
        response.raise_for_status()
        search_results = response.json()
        return search_results
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        return None


# 格式化并返回搜索结果
def format_search_results(search_results, num_results=3):
    top_results = []

    if "webPages" in search_results:
        for i in range(min(num_results, len(search_results['webPages']['value']))):
            result = search_results['webPages']['value'][i]
            top_results.append({
                'title': result['name'],
                'url': result['url'],
                'snippet': result['snippet']
            })
    else:
        print("No web pages found in search results.")

    return top_results


# 综合实现
def search_keywords_and_return_results(user_input):
    # Step 1: 提取关键词
    keywords = extract_keywords(user_input)
    query = " ".join(keywords)

    search_results = search_web(query)

    if search_results:
        formatted_results = format_search_results(search_results, num_results=3)

        results_str = ""
        for result in formatted_results:
            results_str += f"Title: {result['title']}\n"
            results_str += f"URL: {result['url']}\n"
            results_str += f"Snippet: {result['snippet']}\n\n"

        return results_str.strip()  # 返回结果字符串，去掉最后的多余空行
    else:
        return "No search results returned."
