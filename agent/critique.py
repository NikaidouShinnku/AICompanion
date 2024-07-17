import json

from common.show_utils import show_response
from chat_history import ChatHistory
from dataset import dataset_directory
from interviewee import interviewee_directory
from llms import chat
from prompts import read_prompt
from knowledge_graph.model import KnowledgeGraph


class CritiqueAgent:
    def __init__(self,
                 name: str,
                 distilled_tree: KnowledgeGraph,
                 chat_history: ChatHistory,
                 interviewee: str,
                 model: str
                 ):
        self.current_response = None
        self.chat_history = chat_history
        self.name = name
        self.distilled_tree = distilled_tree
        self.interviewee = interviewee
        self.model = model

        self.final_prompt_template = read_prompt("critique")

        example_prompt_template = read_prompt("single_critique")
        with open(f"{dataset_directory()}/critiques_tier_example.json", "r", encoding="utf-8") as f:
            example_dataset = json.loads(f.read())

        num = 1
        self.example = example_prompt_template.format(
            relevance_tier=example_dataset["relevance_tier"],
            professional_tier=example_dataset["professional_tier"],
            num=num
        )
        num += 1

        background_prompt_template = read_prompt("single_background")
        with open(f"{interviewee_directory()}/{interviewee}.json", "r", encoding="utf-8") as f:
            background_dataset = json.loads(f.read())
            self.interviewee_name = background_dataset["name"]

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
        self.current_response = messages[-1]['content']
        chat_history = messages[:-1]
        return self.final_prompt_template.format(
            interviewee=self.interviewee_name,
            user_background=self.background_info,
            domain=self.distilled_tree.domain,
            examples=self.example,
            distilled_tree=self.distilled_tree.get_tree(),
            chat_history=chat_history,
            current_response=self.current_response
        )

    def rate_response(self):
        prompt = self.get_prompt()

        res = chat(prompt=prompt, model=self.model)

        show_response(res, title="评分 / 评语")
        return res
