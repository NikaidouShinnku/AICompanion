import json

from common.show_utils import show_response
from chat_history import ChatHistory
from dataset import dataset_directory
from interviewee import interviewee_directory
from llms import chat
from prompts import read_prompt
from knowledge_graph.model import KnowledgeGraph


class CritiqueAgent:
    def __init__(self, name: str, distilled_tree: KnowledgeGraph, chat_history: ChatHistory, interviewee: str, model: str):
        self.current_response = None
        self.chat_history = chat_history
        self.name = name
        self.distilled_tree = distilled_tree
        self.interviewee = interviewee
        self.model = model

        self.final_prompt_template = read_prompt("distill")

        example_prompt_template = read_prompt("single_example")
        with open(f"{dataset_directory()}/distill_examples.json", "r", encoding="utf-8") as f:
            example_dataset = json.loads(f.read())

        examples = []
        num = 1
        for example in example_dataset:
            examples.append(
                example_prompt_template.format(
                    description=example["description"],
                    distilled_tree=example["knowledge_graph"],
                    chat_history=example["chat_history"],
                    current_response=example["current_response"],
                    actions=example["actions"],
                    num=num
                )
            )
            num += 1
        self.examples = "\n\n".join(examples)

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
            examples=self.examples,
            distilled_tree=self.distilled_tree.get_tree(),
            chat_history=chat_history,
            current_response=self.current_response
        )

    def update_tree(self, turn: int):
        for i in range(3):
            try:
                return self.do_update_tree(turn=turn)
            except:
                if i == 2:
                    raise ValueError("Fail to update tree")


    def do_update_tree(self, turn:int):
        prompt = self.get_prompt()
        # import pyperclip
        # pyperclip.copy(prompt)
        res = chat(prompt=prompt, model=self.model)

        start_pos = res.find("[")
        if start_pos != -1:
            res = res[start_pos:]
        end_pos = res.rfind("]")
        if end_pos != -1:
            res = res[:end_pos + 1]

        # show_response(res, title="Distill")
        try:
            res = json.loads(res)
        except:
            res = json.loads(res.replace("'", '"').replace("None", "null"))

        for action in res:
            if action["action"] == "update_existing_knowledge_node":
                knowledge_id = action["arguments"]["knowledge_id"]
                knowledge_type = action["arguments"]["knowledge_type"]
                knowledge_detail = action["arguments"]["knowledge_detail"]
                self.distilled_tree.renew_knowledge(self.current_response, knowledge_detail, knowledge_id, knowledge_type, turn)
            elif action["action"] == "add_new_knowledge_node":
                objective_id = action["arguments"]["objective_id"]
                knowledge_detail = action["arguments"]["knowledge_detail"]
                self.distilled_tree.add_knowledge(self.current_response, objective_id, knowledge_detail, turn)

        self.distilled_tree.dump("task_result/current_distilled_tree")
