import json

from chat_history import ChatHistory
from dataset import dataset_directory
from interviewee import interviewee_directory
from llms import chat
from prompts import read_prompt
from knowledge_graph.model import KnowledgeGraph


class GenerationAgent:

    def __init__(self, name: str, distilled_tree: KnowledgeGraph, chat_history: ChatHistory, interviewee:str):
        self.chat_history = chat_history
        self.name = name
        self.distilled_tree = distilled_tree
        self.interviewee = interviewee

        self.final_prompt_template = read_prompt("generate")

        example_prompt_template = read_prompt("single_question")
        with open(f"{dataset_directory()}/generation_examples.json", "r", encoding="utf-8") as f:
            example_dataset = json.loads(f.read())
            self.example = example_prompt_template.format(
                description=example_dataset["description"],
                distilled_tree=example_dataset["knowledge_graph"],
                chat_history=example_dataset["chat_history"],
                current_response=example_dataset["current_response"],
                question=example_dataset["question"],
                objective=example_dataset["target_objective"],
                reasons=example_dataset["reason"],
            )

        background_prompt_template = read_prompt("single_background")
        with open(f"{interviewee_directory()}/{interviewee}.json", "r", encoding="utf-8") as f:
            background_dataset = json.loads(f.read())
            self.background_info = background_prompt_template.format(
                user_name=background_dataset["name"],
                user_age=background_dataset["age"],
                user_sex=background_dataset["sex"],
                user_edu=background_dataset["education_level"],
                user_prof=background_dataset["profession"],
                user_other=background_dataset["other"]
            )

    def get_prompt(self):
        messages = self.chat_history.get_message()
        if len(messages) > 0:
            current_response = messages[-1]['content']
            chat_history = messages[:-1]
        else:
            current_response = ""
            chat_history = []
        return self.final_prompt_template.format(
            user_background=self.background_info,
            domain=self.distilled_tree.domain,
            examples=self.example,
            distilled_tree=self.distilled_tree.get_tree(),
            chat_history=chat_history,
            current_response=current_response
        )

    def generate_question(self, model: str):
        prompt = self.get_prompt()
        return chat(prompt=prompt, model=model)
