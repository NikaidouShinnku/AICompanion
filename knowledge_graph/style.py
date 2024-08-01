from rich.tree import Tree
from rich.panel import Panel
from rich.text import Text
from common.show_utils import to_progress_bar

from knowledge_graph.model import KnowledgeGraph, Knowledge


def build_knowledge_tree(knowledge: Knowledge, parent_branch):
    detail = Text()
    if knowledge.concept:
        detail.append("Concept: ", style="cyan")
        detail.append(knowledge.concept, style="white")
    if knowledge.why_important:
        detail.append("\nSignificance: ", style="cyan")
        detail.append(knowledge.why_important, style="white")
    if knowledge.knowledge_description:
        detail.append("\nDescription: ", style="cyan")
        detail.append(knowledge.knowledge_description, style="white")
    if knowledge.example:
        detail.append("\nExample: ", style="cyan")
        detail.append(knowledge.example, style="white")

    knowledge_info = Panel(detail, title="Knowledge", width=100)
    knowledge_branch = parent_branch.add(knowledge_info)

    for sub_knowledge in knowledge.sub_knowledge:
        build_knowledge_tree(sub_knowledge, knowledge_branch)

def build_rich_tree(kg: KnowledgeGraph):
    tree = Tree('.')
    for obj in kg.objectives:
        detail = Text()
        detail.append("Objective: ", style="red")
        detail.append(obj.obj_description, style="green")
        detail.append("\nProgress: ", style="red")
        detail.append(to_progress_bar(n_done=int(obj.progress * 100), n_total=100), style="green")
        detail.append("\nKnowledge Node Count: ", style="red")
        detail.append(str(obj.n_nodes()), style="green")

        obj_info = Panel(detail, title="Objective", width=80)
        obj_branch = tree.add(obj_info)

        for knowledge in obj.knowledge:
            build_knowledge_tree(knowledge, obj_branch)

    return tree