from consoles import print_markdown
from rich.text import Text
from itertools import cycle

def show_response(
        res,
        *,
        no_pretty:bool = False,
        title:str,
        title_align: str = "center",
        width: int = 120,
):
    if isinstance(res, str):
        if no_pretty:
            print(res)
        else:
            print_markdown(res, title=title, title_align=title_align, width=width)
        return res


def to_progress_bar(
        *,
        n_done: int,
        n_total: int,
        bar_len: int = 20
):
    done_ratio = int(n_done) / int(n_total)
    done_bar_count = round(done_ratio * bar_len)
    return "󰹞" * done_bar_count + "󰹟" * (bar_len - done_bar_count)
