import json
from datetime import datetime, timedelta

from chat_history import ChatHistory
from common.show_utils import show_response
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
        self.begin = datetime.now()
        self.final_prompt_template = read_prompt("generate")
        self.suggestion = None

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

    def get_prompt(self):
        messages = self.chat_history.get_message()
        if len(messages) > 0:
            current_response = messages[-1]['content']
            chat_history = messages[:-1]
        else:
            current_response = ""
            chat_history = []

        suggestion_prompt_template = read_prompt("single_suggestion")
        self.suggestion = suggestion_prompt_template.format(
            supervise_efficiency=self.supervise_efficiency(),
            supervise_objective=self.supervise_objective(),
            supervise_generation_style=self.supervise_generation_style()
        )

        return self.final_prompt_template.format(
            interviewee=self.interviewee_name,
            user_background=self.background_info,
            domain=self.distilled_tree.domain,
            examples=self.example,
            distilled_tree=self.distilled_tree.get_tree(),
            chat_history=chat_history,
            current_response=current_response,
            suggestions=self.suggestion
        )

    def supervise_efficiency(self):
        current_time = datetime.now()
        elapsed_time = current_time - self.begin
        total_time = timedelta(seconds=1800)  # 30 minutes
        elapsed_ratio = elapsed_time / total_time  # 已过时间比例
        objective_completion = sum(1 for obj in self.distilled_tree.objectives if obj.obj_complete)
        total_objectives = len(self.distilled_tree.objectives)
        completion_ratio = objective_completion / total_objectives  # 目标完成比例

        # 如果时间未过三分之一，不给出提示
        if elapsed_ratio > 1 / 3:

            # 计算时间比例与目标完成比例的比值
            if elapsed_ratio > 0:
                ratio = completion_ratio / elapsed_ratio
            else:
                ratio = 0

            # 根据比值给出建议
            if ratio >= 1.5:
                return "进度较快，可以多深入询问问题，在有意思的知识点上进行追问。"

            elif ratio <= 0.67:
                return "进度较慢，优先完成Objectives，不要追问过深。"
            else:
                return "进度正常，继续保持。"
        else:
            return None

    def supervise_objective(self):
        incomplete_objectives = [obj.obj_description for obj in self.distilled_tree.objectives if not obj.obj_complete]
        return incomplete_objectives

    def supervise_generation_style(self):
        prompt = read_prompt("style_identifier")
        messages = self.chat_history.get_message()
        if len(messages) > 0:
            current_response = messages[-1]['content']
            chat_history = messages[:-1]
        else:
            current_response = ""
            chat_history = []
        prompt = prompt.format(
            chat_history=chat_history,
            current_response=current_response
        )
        return chat(prompt=prompt, model="deepseek-chat")

    def generate_question(self, model: str):
        prompt = self.get_prompt()
        # import pyperclip
        # pyperclip.copy(prompt)
        return chat(prompt=prompt, model=model)



