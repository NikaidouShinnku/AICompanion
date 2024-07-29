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
        # rid = relationship["id"]
        # if int(rid) == 1:
        #     rid = ' 󰬺 󰎤 󰲠 󰼏 󰎦 '
        mermaid_code += f'{relationship["source"]} --> |"[{relationship["id"]}]"| {relationship["target"]}\n'
        mermaid_code += f'    linkStyle {index} stroke-dasharray: 5 {10-relationship["strength"]},font-family:\'MesloLGLDZ Nerd Font Propo\',stroke:#FFFFFF,stroke-width:2px,font-size:25px,padding:2px;\n'

    mermaid_code += "    classDef default font-family: 'MesloLGLDZ Nerd Font Propo',fill:none,stroke:#E6E6E6,color:#EAEDED,font-size:25px,stroke-width:1px,rx:4,ry:4;\n"
    mermaid_code += "    classDef labelStyle font-size:30px,fill:#FF00FF,color:#1E8449,font-weight:bold;\n"
    mermaid_code += "    classDef edgeLabel font-family: 'MesloLGLDZ Nerd Font Propo', monospace,fill:black,stroke:black,rx:4,ry:4,font-weight:bold,font-size: 16px, color: white,padding:4px;\n"

    return mermaid_code

