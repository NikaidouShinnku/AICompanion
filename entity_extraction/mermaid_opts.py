import base64
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Dict, List, Tuple

from icecream import ic
from common.show_utils import show_response


#
# from utils.consoles import display_image_in_terminal, print_code
# from utils.io import suppress_output

# def parse_entities_and_triples(json_data):
#     id_pattern = r"(\[\d+\])"
#     entities = {}
#     relationships = []
#     for item in json_data["entities_and_triples"]:
#         matches = re.findall(id_pattern, item)
#         if len(matches) == 1:
#             # Handle entities
#             id, label = item.split(", ", 1)  # Split only on the first comma
#             entities[id] = label
#         elif len(matches) == 2:
#             segments = re.split(id_pattern, item)
#             segments = [segment.strip() for segment in segments if segment.strip()]
#             source, relation, target = segments
#             relationships.append((source, relation, target))
#         else:
#             print("Fail to parse item:", item)
#     return entities, relationships
# 

def merge_entities_and_relationships(
    *,
    entities1,
    relationships1,
    entities2,
    relationships2,
) -> Tuple[Dict[str, str], List[Tuple[str, str, str]]]:
    new_entities = entities1.copy()
    new_relationships = relationships1.copy()

    id_mapping = {}
    max_id = max([int(re.findall(r"\d+", key)[0]) for key in new_entities.keys()] + [0])

    for old_id, label in entities2.items():
        # Check if an entity with the same label already exists in new_entities
        existing_id = None
        for new_id, new_label in new_entities.items():
            if new_label == label:
                existing_id = new_id
                break

        if existing_id:
            id_mapping[old_id] = existing_id
        else:
            if old_id in new_entities:
                new_id = f"[{max_id + 1}]"
                max_id += 1
                id_mapping[old_id] = new_id
                new_entities[new_id] = label
            else:
                new_entities[old_id] = label

    for relationship in relationships2:
        source, relation, target = relationship
        new_source = id_mapping.get(source, source)
        new_target = id_mapping.get(target, target)
        new_relationships.append((new_source, relation, new_target))

    return new_entities, new_relationships

def clean_id(id: str):
    return id

def mermaid_code_of(entities, relationships):

    code = "graph LR\n"

    for id, label in entities.items():
        code += f"    {id}[{label}]\n"

    for source, relation, target in relationships:
        code += f"    {(source)} -->| {relation} | {(target)}\n"

    # 添加样式设置
    code += "\n"
    for id in entities.keys():
        code += f"    style {(id)} fill:none,stroke:#ffffff,color:#ffffff\n"

    code += "    linkStyle default font-family:'Terminess Nerd Font Propo',stroke:#EAEDED,stroke-width:2px,font-size:20px,padding:2px;\n"
    code += "    classDef default font-family: 'Terminess Nerd Font Propo',fill:none,stroke:#BFC9CA,color:#EAEDED,font-size:20px,stroke-width:1px,rx:4,ry:4;\n"
    code += "    classDef labelStyle font-size:20px,fill:#ABEBC6,color:#1E8449,font-weight:bold;\n"
    code += "    classDef edgeLabel font-family: 'Terminess Nerd Font Propo', monospace,stroke:#F4F6F7,color:#F4F6F7,rx:4,ry:4,font-weight:bold,font-size: 16px, color: black,padding:4px;\n"
    # mermaid_code += "    classDef customFont font-family:Fira Code,font-size:14px,fill:#f9f,stroke:#333,stroke-width:4px;\n"

    return code

from PIL import Image

def get_image_size(image_path):
    with Image.open(image_path) as img:
        width, height = img.size
    return width, height

from screeninfo import get_monitors

def get_screen_resolution():
    monitors = get_monitors()
    for monitor in monitors:
        print(f"Monitor: {monitor.name}, Width: {monitor.width}, Height: {monitor.height}")

    return monitors[0].width, monitors[0].height

def display_image_in_terminal(path):
    """
    Displays an image centered in the terminal with optional resizing.
    Args:
        path (str): The path to the image file.
        width (int, optional): The desired width of the image. If not provided, the original width will be used.
        height (int, optional): The desired height of the image. If not provided, the original height will be used.
    Returns:
        None
    """
    print("\n" * 10)
    img_x, img_y = get_image_size(path)
    term_col, term_row = shutil.get_terminal_size()
    scr_x, scr_y = get_screen_resolution()

    pixels_per_col = scr_x / term_col
    pixels_per_row = scr_y / term_row

    ic(img_x, img_y, term_col, term_row, pixels_per_col, pixels_per_row)

    x = int((scr_x - img_x) / 2 / pixels_per_col)
    y = int(scr_y / pixels_per_row)

    ic(x,y)

    if x < 0:
        x = 0
    if y < 0:
        y = 0

    subprocess.run(
        [
            "wezterm",
            "imgcat",
            path,
            # "--resize",
            # "1000x800",
            "--position",
            f'{x},{y}'
        ]
    )
    print()  # Add a newline after the image


def display_relationship_descriptions(relationships):
    if not relationships:
        return

    note = "\n".join([
        f'{relationship["id"]}. {relationship["description"]}'
        for relationship in relationships
    ])

    show_response(note, title="关系备注", title_align="center")



def create_mermaid_png_and_display(mermaid_code, relationships, display_in_term=True):
    # Create a temporary file for the Mermaid code
    with tempfile.NamedTemporaryFile(mode="w", suffix=".mmd", delete=False) as mmd_file:
        mmd_file_path = mmd_file.name
        Path(mmd_file_path).write_text(mermaid_code, encoding="utf-8")

    # Create a temporary file for the PNG output
    png_file_path = tempfile.mktemp(suffix=".png")

    # Convert Mermaid to PNG using mmdc (Mermaid CLI)
    command = [
        r"C:\Users\25899\Downloads\node-v20.15.1-win-x64\mmdc.cmd",
        "-i", mmd_file_path,
        "-t", "dark",
        "--width", "1200",
        "--height", "2000",
        "-b", "transparent",
        "-o", png_file_path,
    ]

    try:
        if display_in_term:
            print(mermaid_code)
            result = subprocess.run(command, check=True, capture_output=True)

        # Display the PNG in iTerm2
        if os.path.exists(png_file_path):
            display_image_in_terminal(png_file_path)
            display_relationship_descriptions(relationships)
        else:
            raise FileNotFoundError(f"File {png_file_path} does not exist")

    finally:
        # Clean up temporary files
        if os.path.exists(mmd_file_path):
            try:
                os.unlink(mmd_file_path)
            except OSError as e:
                print(f"Error deleting file {mmd_file_path}: {e}")

        if os.path.exists(png_file_path):
            try:
                os.unlink(png_file_path)
            except OSError as e:
                print(f"Error deleting file {png_file_path}: {e}")

