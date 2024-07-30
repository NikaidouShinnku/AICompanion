import contextlib
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
    sub_knowledge: List["Knowledge"] = []
    other: Union[List[str], None] = None
    raw_user_response: Dict[int, str] = None
    is_generalized_node: bool = False


class Objective(BaseModel):
    id: str = str(uuid.uuid4())
    obj_description: Union[str, None] = None
    knowledge: List[Knowledge] = []
    progress: float = 0
    obj_complete: bool = False
    # def to_xml(self):
    #     ...


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
        def clean_knowledge(knowledge_item: Dict, drop_attrs: List) -> Dict:
            for attr in drop_attrs:
                if attr in knowledge_item:
                    del knowledge_item[attr]
            for sub in knowledge_item.get('sub_knowledge', []):
                clean_knowledge(sub, drop_attrs)
            return knowledge_item

        tree = self.model_dump()
        # Attrs drop
        if "id" in tree:
            del tree["id"]
        for obj in tree['objectives']:
            for obj_attr in drop_objective_attrs:
                if obj_attr in obj:
                    del obj[obj_attr]
            for knowledge in obj.get("knowledge", []):
                clean_knowledge(knowledge, drop_knowledge_attrs)

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

    @contextlib.contextmanager
    def with_xml_context(self, tag: str, context:list):
        context.append(f"<{tag}")
        yield
        context.append(f"</{tag}>")
    def to_xml(self):
        """
        Get the JSON representation of the knowledge tree.
        Returns:
            str: JSON string representing the knowledge tree.
        """
        formats = []
        with self.with_xml_context(tag="knowledge_graph", context=formats):
            with self.with_xml_context(tag="id", context=formats):
                pass

        formats.append("<knowledge_graph id=1234>")

        formats.append("</knowledge_graph>")

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

    def find_knowledge_by_id(self, knowledge_id: str) -> Union[Knowledge, None]:
        """
        Find and return the knowledge node with the specified ID.
        Args:
            knowledge_id (str): The ID of the knowledge node to be found.
        Returns:
            Union[Knowledge, None]: The knowledge node if found, otherwise None.
        """
        for objective in self.objectives:
            for knowledge in objective.knowledge:
                if knowledge.id == knowledge_id:
                    return knowledge
                for sub_knowledge in knowledge.sub_knowledge:
                    if sub_knowledge.id == knowledge_id:
                        return sub_knowledge
        return None

    def add_knowledge_node(
            self,
            raw_res: str,
            knowledge_details: Dict[str, str],
            turn: int,
            parent_id: str
    ):
        """
        Add a new Knowledge node as a sub-knowledge node to an existing Knowledge node or Objective node.
        Args:
            raw_res (str): The raw user response to be stored.
            knowledge_details (Dict[str, str]): A dictionary where keys are knowledge types and values are the corresponding details.
            turn (int): The turn number of the current conversation.
            parent_id (str): The ID of the parent node (Objective or Knowledge) to which the new sub-Knowledge node will be added.
        Raises:
            ValueError: If the specified parent node does not exist.
        """
        if 'concept' not in knowledge_details:
            raise ValueError("Knowledge details must include 'concept'.")

        new_knowledge = Knowledge(id=str(uuid.uuid4()))  # Ensure a new unique UUID is generated
        for knowledge_type, knowledge_detail in knowledge_details.items():
            if knowledge_type in ['concept', 'why_important', 'knowledge_description', 'example', 'other']:
                setattr(new_knowledge, knowledge_type, knowledge_detail)
            else:
                raise ValueError(f"Invalid type {knowledge_type}.")
        new_knowledge.raw_user_response = {turn: raw_res}

        def find_and_add(parent):
            if parent.id == parent_id:
                parent.sub_knowledge.append(new_knowledge)
                return True
            for sub in parent.sub_knowledge:
                if find_and_add(sub):
                    return True
            return False

        parent_found = False
        for objective in self.objectives:
            if objective.id == parent_id:
                objective.knowledge.append(new_knowledge)
                parent_found = True
                self.manage_progress(objective.id)
                break
            for knowledge in objective.knowledge:
                if find_and_add(knowledge):
                    parent_found = True
                    self.update_objective_progress_by_knowledge_id(parent_id)
                    break

        if not parent_found:
            raise ValueError(f"Parent node with id {parent_id} not found.")

    def generalize_knowledge(
            self,
            raw_res: str,
            knowledge_details: Dict[str, str],
            sub_knowledge_ids: List[str],
            turn: int,
            parent_id: str
    ):
        """
        Add a new Knowledge node with a list of sub-knowledge nodes by their IDs.
        Args:
            raw_res (str): The raw user response to be stored.
            knowledge_details (Dict[str, str]): A dictionary where keys are knowledge types and values are the corresponding details.
            sub_knowledge_ids (List[str]): A list of IDs of sub-knowledge nodes to be added.
            turn (int): The turn number of the current conversation.
            parent_id (str): The ID of the parent node (Objective or Knowledge) to which the new Knowledge node will be added.
        Raises:
            ValueError: If the specified parent node or sub-knowledge nodes do not exist.
        """
        if 'concept' not in knowledge_details:
            raise ValueError("Knowledge details must include 'concept'.")

        new_knowledge = Knowledge(id=str(uuid.uuid4()), is_new_node=True)  # Ensure a new unique UUID is generated
        for knowledge_type, knowledge_detail in knowledge_details.items():
            if knowledge_type in ['concept', 'why_important', 'knowledge_description', 'example', 'other']:
                setattr(new_knowledge, knowledge_type, knowledge_detail)
            else:
                raise ValueError(f"Invalid type {knowledge_type}.")
        new_knowledge.raw_user_response = {turn: raw_res}

        # Function to find and remove sub-knowledge by IDs
        def find_and_remove_knowledge(knowledge_list: List[Knowledge], ids: List[str]) -> List[Knowledge]:
            found_knowledge = []
            for knowledge in knowledge_list[:]:
                if knowledge.id in ids:
                    found_knowledge.append(knowledge)
                    knowledge_list.remove(knowledge)
                else:
                    found_knowledge.extend(find_and_remove_knowledge(knowledge.sub_knowledge, ids))
            return found_knowledge

        sub_knowledge_list = []
        for objective in self.objectives:
            sub_knowledge_list.extend(find_and_remove_knowledge(objective.knowledge, sub_knowledge_ids))
            self.update_objective_progress_by_knowledge_id(objective.id)

        if not sub_knowledge_list:
            raise ValueError(f"No sub-knowledge nodes with the given IDs {sub_knowledge_ids} found.")

        new_knowledge.sub_knowledge.extend(sub_knowledge_list)  # Add the found sub-knowledge nodes

        def find_and_add(parent):
            if parent.id == parent_id:
                parent.sub_knowledge.append(new_knowledge)
                return True
            for sub in parent.sub_knowledge:
                if find_and_add(sub):
                    return True
            return False

        parent_found = False
        for objective in self.objectives:
            if objective.id == parent_id:
                objective.knowledge.append(new_knowledge)
                parent_found = True
                self.manage_progress(objective.id)
                break
            for knowledge in objective.knowledge:
                if find_and_add(knowledge):
                    parent_found = True
                    self.update_objective_progress_by_knowledge_id(parent_id)
                    break

        if not parent_found:
            raise ValueError(f"Parent node with id {parent_id} not found.")

    def renew_knowledge(self, raw_res: str, knowledge_detail: str, knowledge_type: str, turn: int, knowledge_id: str):
        """
        Renew the knowledge in the knowledge tree. If the knowledge doesn't exist, create it as a sub-knowledge node.
        Args:
            raw_res (str): The raw user response to be stored.
            knowledge_detail (str): The new data to be inserted into the knowledge node.
            knowledge_type (str): The type of knowledge to be updated (concept, why_important, knowledge_description, example, or other).
            turn (int): The turn number of the current conversation.
            knowledge_id (str): The ID of the knowledge node to be updated.
        Raises:
            ValueError: If the specified type is not valid.
        """
        if knowledge_type not in ['concept', 'why_important', 'knowledge_description', 'example', 'other']:
            raise ValueError(f"Invalid type {knowledge_type}.")

        def update_knowledge_node(knowledge: Knowledge):
            setattr(knowledge, knowledge_type, knowledge_detail)
            if knowledge.raw_user_response is None:
                knowledge.raw_user_response = {}
            knowledge.raw_user_response[turn] = raw_res

        def find_and_update_knowledge(knowledge_list: List[Knowledge], knowledge_id: str) -> bool:
            for knowledge in knowledge_list:
                if knowledge.id == knowledge_id:
                    update_knowledge_node(knowledge)
                    return True
                if find_and_update_knowledge(knowledge.sub_knowledge, knowledge_id):
                    return True
            return False

        found = False
        for objective in self.objectives:
            if find_and_update_knowledge(objective.knowledge, knowledge_id):
                self.update_objective_progress_by_knowledge_id(knowledge_id)
                found = True
                break

        if not found:
            raise ValueError(f"Knowledge with id {knowledge_id} not found. Unable to renew knowledge.")

    def delete_knowledge(self, knowledge_id: str):
        """
        Delete the knowledge node with the specified ID.
        Args:
            knowledge_id (str): The ID of the knowledge node to be deleted.
        Raises:
            ValueError: If the specified knowledge node does not exist.
        """

        def delete_node(knowledge_list: List[Knowledge], knowledge_id: str) -> bool:
            for i, knowledge in enumerate(knowledge_list):
                if knowledge.id == knowledge_id:
                    del knowledge_list[i]
                    return True
                if delete_node(knowledge.sub_knowledge, knowledge_id):
                    return True
            return False

        found = False
        for objective in self.objectives:
            if delete_node(objective.knowledge, knowledge_id):
                self.manage_progress(objective.id)
                found = True
                break

        if not found:
            raise ValueError(f"Knowledge with id {knowledge_id} not found. Unable to delete knowledge.")

    def move_knowledge(self, src_id: str, des_id: str):
        """
        Move a Knowledge node to a new parent Knowledge node or Objective node.
        Args:
            src_id (str): The ID of the Knowledge node to be moved.
            des_id (str): The ID of the destination Knowledge node or Objective node.
        Raises:
            ValueError: If the source or destination node does not exist.
        """

        def find_and_remove_knowledge(knowledge_list: List[Knowledge], knowledge_id: str) -> Union[Knowledge, None]:
            for i, knowledge in enumerate(knowledge_list):
                if knowledge.id == knowledge_id:
                    return knowledge_list.pop(i)
                found = find_and_remove_knowledge(knowledge.sub_knowledge, knowledge_id)
                if found:
                    return found
            return None

        # Step 1: Find and remove the source knowledge node
        src_knowledge = None
        for objective in self.objectives:
            src_knowledge = find_and_remove_knowledge(objective.knowledge, src_id)
            if src_knowledge:
                self.update_objective_progress_by_knowledge_id(objective.id)
                break

        if not src_knowledge:
            raise ValueError(f"Source node with id {src_id} not found.")

        # Step 2: Find the destination node and add the source knowledge node as its sub-knowledge
        def find_and_add_knowledge(knowledge_list: List[Knowledge], knowledge_id: str,
                                   knowledge_to_add: Knowledge) -> bool:
            for knowledge in knowledge_list:
                if knowledge.id == knowledge_id:
                    knowledge.sub_knowledge.append(knowledge_to_add)
                    return True
                if find_and_add_knowledge(knowledge.sub_knowledge, knowledge_id, knowledge_to_add):
                    return True
            return False

        dest_found = False
        for objective in self.objectives:
            if objective.id == des_id:
                objective.knowledge.append(src_knowledge)
                dest_found = True
                self.update_objective_progress_by_knowledge_id(objective.id)
                break
            if find_and_add_knowledge(objective.knowledge, des_id, src_knowledge):
                dest_found = True
                self.update_objective_progress_by_knowledge_id(objective.id)
                break

        if not dest_found:
            raise ValueError(f"Destination node with id {des_id} not found.")

    def update_objective_progress_by_knowledge_id(self, knowledge_id: str):
        """
        Update the progress of the objective containing the specified knowledge ID.
        Args:
            knowledge_id (str): The ID of the knowledge node.
        """
        for objective in self.objectives:
            if any(knowledge.id == knowledge_id or any(sub_knowledge.id == knowledge_id for sub_knowledge in knowledge.sub_knowledge) for knowledge in objective.knowledge):
                self.manage_progress(objective.id)
                break

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

        def count_sub_knowledge_fields(knowledge: Knowledge) -> int:
            count = sum(
                getattr(knowledge, field) is not None for field in ['concept', 'why_important', 'knowledge_description', 'example']
            )
            for sub_knowledge in knowledge.sub_knowledge:
                count += count_sub_knowledge_fields(sub_knowledge)
            return count

        sub_knowledge_count = sum(
            count_sub_knowledge_fields(knowledge)
            for knowledge in objective.knowledge
            if not getattr(knowledge, 'is_generalized_node', False)
        )

        objective.progress = min(sub_knowledge_count * 0.05, 1.0)

        objective.obj_complete = objective.progress >= 0.95

        self.task_complete = all(obj.obj_complete for obj in self.objectives)
