from typing import List, Dict, Tuple
import re

class EntityRelationTriple:
    def __init__(self):
        self.entities: List[Dict[str, str]] = []
        self.relationships: List[Dict[str, str]] = []
        self.current_entity_id = 1
        self.current_relationship_id = 1

    def get_entities(self) -> List[Dict[str, str]]:
        return self.entities

    def get_relationships(self) -> List[Dict[str, str]]:
        return self.relationships

    def generate_entity_id(self) -> int:
        entity_id = self.current_entity_id
        self.current_entity_id += 1
        return entity_id

    def generate_relationship_id(self) -> int:
        relationship_id = self.current_relationship_id
        self.current_relationship_id += 1
        return relationship_id

    def merge_entities_and_relationships(
            self,
            other_entities: List[Dict[str, str]],
            other_relationships: List[Dict[str, str]]
    ):
        # 将现有的实体名称和关系（source, target）存储到集合中以便快速查找
        existing_entity_names = {entity['name'] for entity in self.entities}
        existing_relationships = {(rel['source'], rel['target']): rel for rel in self.relationships}

        # 处理传入的实体列表
        for entity in other_entities:
            if entity['name'] not in existing_entity_names:
                entity['id'] = str(self.generate_entity_id())  # 添加ID
                self.entities.append(entity)
                existing_entity_names.add(entity['name'])

        # 处理传入的关系列表
        for relationship in other_relationships:
            key = (relationship['source'], relationship['target'])
            if key in existing_relationships:
                existing_relationship = existing_relationships[key]
                if existing_relationship['description'] != relationship['description']:
                    existing_relationship['description'] += f"| {relationship['description']}"
                relationship['id'] = str(existing_relationship['id'])
            else:
                relationship['id'] = str(self.generate_relationship_id())  # 添加ID
                self.relationships.append(relationship)
                existing_relationships[key] = relationship

