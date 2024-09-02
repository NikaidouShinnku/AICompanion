import json
from datetime import datetime

from chat_history import ChatHistory
from common.show_utils import show_response
from dataset import dataset_directory
from interviewee import interviewee_directory
from llms import chat
from prompts import read_prompt

class KnowledgeTest:

    def __init__(
            self,
            chat_history:
            ChatHistory,
            model: str,
    ):
        self.chat_history = chat_history
        self.begin = datetime.now()
        self.final_prompt_template = read_prompt("knowledgetest_prompt")
        self.model = model

        example_prompt_template = read_prompt("single_test")
        with open(f"{dataset_directory()}/knowledgetest_examples.json", "r", encoding="utf-8") as f:
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
                    num=num
                )
            )
            num += 1
        self.examples = "\n\n".join(examples)

    def get_prompt(self, current_user_input:str):
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
            date=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )

    def generate_response(self, current_user_input:str):
        prompt = self.get_prompt(current_user_input)
        show_response(prompt, title="Prompt")
        res = chat(prompt=prompt, model=self.model, temperature=0.7)

        return res

    def format_chat_history(self, messages):
        formatted = ""
        for message in messages:
            formatted += message['role'] + ": " + message['content'].replace("\n", "") + "\n\n"

        return formatted
