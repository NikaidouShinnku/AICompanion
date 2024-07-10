
import pathlib
prompt_directory = pathlib.Path(__file__).parent.absolute()

def read_prompt(name:str):
    path = prompt_directory /f"{name}.template"

    if not path.exists():
        raise FileNotFoundError(f"{path} does not exist")

    return path.read_text(encoding="utf-8")