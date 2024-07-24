import uuid
from typing import List, Union
from datetime import datetime
import copy

from knowledge_graph.model import KnowledgeGraph


class KnowledgeTreeManager:
    def __init__(self):
        self.knowledge_tree_stack: List[KnowledgeGraph] = []

    def push_back(self, knowledge_tree: KnowledgeGraph):
        self.knowledge_tree_stack.append(copy.deepcopy(knowledge_tree))

    def pop(self) -> Union[KnowledgeGraph, None]:
        if self.knowledge_tree_stack:
            return self.knowledge_tree_stack.pop()
        return None

    def get_current_tree(self) -> Union[KnowledgeGraph, None]:
        if self.knowledge_tree_stack:
            return self.knowledge_tree_stack[-1]
        return None

    def list_all_trees(self):
        return [tree.id for tree in self.knowledge_tree_stack]