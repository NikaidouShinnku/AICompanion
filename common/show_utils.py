from consoles import print_markdown
from rich.text import Text
from itertools import cycle

def show_response(
        res,
        *,
        no_pretty:bool = False,
        title:str,
        title_align: str = "center"
):
    acc = []
    if isinstance(res, str):
        if no_pretty:
            print(res)
        else:
            print_markdown(res, title=title, title_align=title_align)
        return res

    print("[AI]:", end="")
    for chunk in res:
        print(chunk, end='')
        acc.append(chunk)
    print()
    return "".join(acc)