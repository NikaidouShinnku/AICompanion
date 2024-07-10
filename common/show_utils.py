from consoles import print_markdown


def show_response(res, *, no_pretty:bool = False, title:str):
    acc = []
    if isinstance(res, str):
        if no_pretty:
            print(res)
        else:
            print_markdown(res, title=title)
        return res

    print("[AI]:", end="")
    for chunk in res:
        print(chunk, end='')
        acc.append(chunk)
    print()
    return "".join(acc)