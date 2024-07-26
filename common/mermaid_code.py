from icecream import ic


def parse_entity_relation(output):
    index = output.find("<|COMPLETE|>")
    if index != -1:
        output = output[:index]

    entities = []
    relationships = []
    lines = output.split("##")

    for line in lines:
        if line:

            line = line.strip('\n ()')
            elements = line.split("<|>")
            if elements[0] == '"entity"':
                entity = {
                    "name": elements[1].strip('"'),
                    "type": elements[2].strip('"'),
                    "description": elements[3].strip('"')
                }
                entities.append(entity)
            elif elements[0] == '"relationship"':
                relationship = {
                    "source": elements[1].strip('"'),
                    "target": elements[2].strip('"'),
                    "description": elements[3].strip('"'),
                    "strength": int(elements[4].strip('()" '))
                }
                relationships.append(relationship)

    return entities, relationships


def generate_mermaid(entities, relationships):
    mermaid_code = "graph TD\n"

    for entity in entities:
        mermaid_code += f'{entity["name"]}["{entity["type"]}:{entity["name"]}"]\n'

    for index, relationship in enumerate(relationships):
        mermaid_code += f'{relationship["source"]} --> |"{relationship["description"]}"| {relationship["target"]}\n'
        mermaid_code += f'    linkStyle {index} font-family:\'Terminess Nerd Font Propo\',stroke:#FF0000,stroke-width:{relationship["strength"]}px,font-size:40px,padding:2px;\n'

    return mermaid_code
