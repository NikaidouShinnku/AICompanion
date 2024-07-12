import json

from common.show_utils import show_response
from chat_history import ChatHistory
from dataset import dataset_directory
from interviewee import interviewee_directory
from knowledge_graph.model import KnowledgeGraph
from llms import chat
from prompts import read_prompt


class SimulationAgent:

    def __init__(self, name: str, distilled_tree: KnowledgeGraph, chat_history: ChatHistory, interviewee:str):
        self.chat_history = chat_history
        self.name = name
        self.distilled_tree = distilled_tree
        self.interviewee = interviewee
        self.final_prompt_template = read_prompt("auto_simulation")

    def get_prompt(self):

        messages = self.chat_history.get_message()
        new_question = messages[-1]['content']
        chat_history = messages[:-1]

        with open(f"{interviewee_directory()}/{self.interviewee}.json", "r", encoding="utf-8") as f:
            background_dataset = json.loads(f.read())

        return self.final_prompt_template.format(
            domain=self.distilled_tree.domain,
            distilled_tree=self.distilled_tree.get_tree(),
            chat_history=chat_history,
            user_name=background_dataset["name"],
            user_age=background_dataset["age"],
            user_sex=background_dataset["sex"],
            user_edu=background_dataset["education_level"],
            user_prof=background_dataset["profession"],
            user_other=background_dataset["other"],
            question=new_question
        )

    def simulate_response(self, model:str):
        prompt = self.get_prompt()
        # show_response(prompt,title="AUTO PROMPT")
        return chat(prompt=prompt, model=model)
