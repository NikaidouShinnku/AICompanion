import json

from common.show_utils import show_response
from chat_history import ChatHistory
from dataset import dataset_directory
from interviewee import interviewee_directory
from llms import chat
from prompts import read_prompt
from knowledge_graph.model import KnowledgeGraph


class SummaryAgent:
    def __init__(self,
                 name: str,
                 distilled_tree: KnowledgeGraph,
                 chat_history: ChatHistory,
                 model: str
                 ):
        self.chat_history = chat_history
        self.name = name
        self.distilled_tree = distilled_tree
        self.model = model

        self.final_prompt_template = read_prompt("summary")

        example_prompt_template = read_prompt("single_summary_example")
        with open(f"{dataset_directory()}/summary_examples.json", "r", encoding="utf-8") as f:
            example_dataset = json.loads(f.read())

        examples = []
        num = 1
        for example in example_dataset:
            examples.append(
                example_prompt_template.format(
                    description=example["description"],
                    distilled_tree=example["knowledge_graph"],
                    chat_history=example["chat_history"],
                    thought=example["thought"],
                    actions=example["actions"],
                    num=num
                )
            )
            num += 1
        self.examples = "\n\n".join(examples)


    def get_prompt(self):
        chat_history = self.chat_history.get_message()
        return self.final_prompt_template.format(
            domain=self.distilled_tree.domain,
            examples=self.examples,
            distilled_tree=self.distilled_tree.get_tree(),
            chat_history=chat_history,
        )

    def restructure(self, turn: int):
        prompt = self.get_prompt()

        res = chat(prompt=prompt, model=self.model)

        show_response(res, title="重新结构化知识树")

        start_pos = res.find("[")
        if start_pos != -1:
            res = res[start_pos:]
        end_pos = res.rfind("]")
        if end_pos != -1:
            res = res[:end_pos + 1]

        try:
            res = json.loads(res)
        except:
            res = json.loads(res.replace("'", '"').replace("None", "null"))

        messages = self.chat_history.get_message()
        current_response = messages[-1]['content']

        for action in res:
            if action["action"] == "update_existing_knowledge_node":
                knowledge_id = action["arguments"]["knowledge_id"]
                knowledge_type = action["arguments"]["knowledge_type"]
                knowledge_detail = action["arguments"]["knowledge_detail"]
                self.distilled_tree.renew_knowledge(
                    current_response, knowledge_detail, knowledge_type, turn, knowledge_id
                )
            elif action["action"] == "add_new_knowledge_node":
                parent_id = action["arguments"]["parent_id"]
                knowledge_detail = action["arguments"]["knowledge_detail"]
                self.distilled_tree.add_knowledge(
                    current_response, knowledge_detail, turn, parent_id
                )
            elif action["action"] == "delete_knowledge_node":
                knowledge_id = action["arguments"]["knowledge_id"]
                self.distilled_tree.delete_knowledge(knowledge_id)
            elif action["action"] == "move_knowledge_node":
                src_knowledge_id = action["arguments"]["source_knowledge_id"]
                des_knowledge_id = action["arguments"]["destination_knowledge_id"]
                self.distilled_tree.move_knowledge(src_knowledge_id, des_knowledge_id)
