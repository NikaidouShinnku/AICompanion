from datetime import datetime
from pydantic import BaseModel
from typing import List, Union, Dict
from pydantic.json import pydantic_encoder
import uuid
import json
import copy
import decimal


class Knowledge(BaseModel):
    id: str = str(uuid.uuid4())
    concept: Union[str, None] = None
    why_important: Union[str, None] = None
    knowledge_description: Union[str, None] = None
    example: Union[str, None] = None
    # sub_knowledge: List["Knowledge"] = []
    other: Union[List[str], None] = None
    raw_user_response: Dict[int, str] = None


class Objective(BaseModel):
    id: str = str(uuid.uuid4())
    obj_description: Union[str, None] = None
    knowledge: List[Knowledge] = []
    progress: float = 0
    obj_complete: bool = False


class KnowledgeGraph(BaseModel):
    id: str = str(uuid.uuid4())
    domain: Union[str, None] = None
    name: Union[str, None] = None
    task_description: Union[str, None] = None
    objectives: List[Objective]
    task_complete: bool = False
    start_date: str = datetime.now().strftime("%Y-%m-%d")
    end_date: str = datetime.now().strftime("%Y-%m-%d")
    estimated_minute: Union[int, None] = None

    def get_completed_objective_num(self):
        return sum(obj.obj_complete for obj in self.objectives)

    def clone(self):
        return copy.deepcopy(self)

    def to_readable_tree(self, drop_objective_attrs: List = [], drop_knowledge_attrs: List = []) -> Dict:
        tree = self.model_dump()
        # Attrs drop
        if "id" in tree:
            del tree["id"]
        for obj in tree['objectives']:
            for obj_attr in drop_objective_attrs:
                if obj_attr in obj:
                    del obj[obj_attr]
            for knowledge in obj.get("knowledge", []):
                for knowledge_attr in drop_knowledge_attrs:
                    if knowledge_attr in knowledge:
                        del knowledge[knowledge_attr]

        # Name change
        new_objectives = []
        for obj in tree['objectives']:
            readable_obj = {}
            for obj_key, obj_value in obj.items():
                if obj_key == "progress":
                    readable_obj["目标进度"] = obj_value
                elif obj_key == "obj_complete":
                    if obj['progress'] == 0:
                        readable_obj["完成度"] = "未开始"
                    elif obj['progress'] < 0.5:
                        readable_obj["完成度"] = "未完成，进度未过半"
                    elif obj['progress'] < 1:
                        readable_obj["完成度"] = "未完成，进度过半"
                    else:
                        readable_obj["完成度"] = "目标完成，可以不再和对方讨论该Objective"
                else:
                    readable_obj[obj_key] = obj_value
            new_objectives.append(readable_obj)

        tree['objectives'] = new_objectives

        return tree

    def get_tree(self):
        """
        Get the JSON representation of the knowledge tree.
        Returns:
            str: JSON string representing the knowledge tree.
        """
        return self.json(exclude_none=True)

    def format_to_tree(self):
        """
        Get the JSON representation of the knowledge tree.
        Returns:
            str: JSON string representing the knowledge tree.
        """
        return json.dumps(self.dict(), indent=2, ensure_ascii=False)

    @classmethod
    def restore(cls, file: str):
        """
        Load the knowledge tree from a JSON file.
        Args:
            file (str): The path to the JSON file containing the knowledge tree.
        Returns:
            KnowledgeGraph: An instance of KnowledgeGraph initialized with the data from the file.
        """
        with open(file + ".json", 'r') as f:
            data = json.load(f)
        return KnowledgeGraph(**data)  # Initialize the instance with the data from the file


    def dump(self, file: str):
        """
        Write the knowledge tree to a JSON file.
        Args:
            file (str): The path to the JSON file where the knowledge tree will be saved.
        """
        self.end_date = datetime.now().strftime("%Y-%m-%d")
        with open(file + ".json", 'w') as f:
            f.write(self.json())

    def add_objective(self):
        """
        Add a new Objective node to the KnowledgeGraph with a unique UUID.
        """
        new_objective = Objective()
        self.objectives.append(new_objective)

    def add_knowledge(self, raw_res: str, objective_id: str, knowledge_details: Dict[str, str], turn: int):
        """
        Add a new Knowledge node to a specified Objective node with a unique UUID and initial details.
        Args:
            raw_res (str): The raw user response to be stored.
            objective_id (str): The ID of the Objective node to which the new Knowledge node will be added.
            knowledge_details (Dict[str, str]): A dictionary where keys are knowledge types and values are the corresponding details.
            turn (int): The turn number of the current conversation.
        Raises:
            ValueError: If the specified Objective node does not exist in the KnowledgeGraph.
            ValueError: If 'knowledge_description' is not provided.
        """
        if 'knowledge_description' not in knowledge_details:
            raise ValueError("'knowledge_description' is required.")

        objective = next((o for o in self.objectives if o.id == objective_id), None)
        if objective:
            new_knowledge = Knowledge()
            for knowledge_type, knowledge_detail in knowledge_details.items():
                if knowledge_type in ['concept', 'why_important', 'knowledge_description', 'example', 'other']:
                    setattr(new_knowledge, knowledge_type, knowledge_detail)
                else:
                    raise ValueError(f"Invalid type {knowledge_type}.")
            new_knowledge.raw_user_response = {turn: raw_res}
            objective.knowledge.append(new_knowledge)
        else:
            raise ValueError(f"Objective with id {objective_id} not found.")
        self.manage_progress(objective_id)

    def renew_knowledge(self, raw_res: str, knowledge_detail: str, knowledge_id: str, knowledge_type: str, turn: int,
                        objective_id: str = None):
        """
        Renew the knowledge in the knowledge tree. If the knowledge doesn't exist, create it.
        Args:
            raw_res (str): The raw user response to be stored.
            knowledge_detail (str): The new data to be inserted into the knowledge node.
            knowledge_id (str): The ID of the knowledge node to be updated.
            knowledge_type (str): The type of knowledge to be updated (concept, why_important, knowledge_description, example, or other).
            turn (int): The turn number of the current conversation.
            objective_id (str): The ID of the objective node where the knowledge should be added if it doesn't exist.
        Raises:
            ValueError: If the specified type is not valid.
        """
        found = False
        for objective in self.objectives:
            for knowledge in objective.knowledge:
                if knowledge.id == knowledge_id:
                    if knowledge_type in ['concept', 'why_important', 'knowledge_description', 'example', 'other']:
                        setattr(knowledge, knowledge_type, knowledge_detail)
                        if knowledge.raw_user_response is None:
                            knowledge.raw_user_response = {}
                        knowledge.raw_user_response[turn] = raw_res
                        objective_id = objective.id
                        self.manage_progress(objective_id)
                        found = True
                        break

        if not found and objective_id:
            self.add_knowledge(raw_res, objective_id, {knowledge_type: knowledge_detail,
                                                       'knowledge_description': 'Automatically created knowledge node'},
                               turn)
            self.manage_progress(objective_id)

    def manage_progress(self, objective_id: str):
        """
        Updates the progress of a specific objective in the knowledge graph.
        Each sub-knowledge field ('example', 'why_important', 'knowledge_description', 'concept') contributes 5 points.
        If the progress reaches or exceeds 90%, mark complete as True.
        Additionally, if all objectives are complete, mark the KnowledgeGraph as complete.
        Args:
            objective_id (str): The ID of the objective to update.
        """
        objective = next((o for o in self.objectives if o.id == objective_id), None)
        if objective is None:
            raise ValueError(f"Objective with ID {objective_id} not found.")

        sub_knowledge_count = 0
        for knowledge in objective.knowledge:
            # Count each sub-knowledge field that is not None
            sub_knowledge_count += sum(
                1 for field in ['concept', 'why_important', 'knowledge_description', 'example'] if
                knowledge.dict().get(field) is not None)

        # Calculate progress based on sub-knowledge fields
        objective.progress = (sub_knowledge_count * 0.05)

        # Mark complete if progress is 90% or more
        if objective.progress >= 0.9:
            objective.obj_complete = True
        else:
            objective.obj_complete = False

        # Check if all objectives are complete and update KnowledgeGraph's task_complete
        if all(obj.obj_complete for obj in self.objectives):
            self.task_complete = True
        else:
            self.task_complete = False
