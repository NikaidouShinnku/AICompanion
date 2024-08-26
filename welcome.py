from consoles import print_code

_hello = r"""
                                                       _____ _           ____  _____________________    __
                                                      / ___/(_)____     / __ \/  _/ ___/_  __/  _/ /   / /
                                                      \__ \/ / ___/    / / / // / \__ \ / /  / // /   / /
                                                     ___/ / / /  _    / /_/ // / ___/ // / _/ // /___/ /___
                                                    /____/_/_/  (_)  /_____/___//____//_/ /___/_____/_____/                                                                          
"""

def hello():
    from rich.text import Text
    from rich.console import Console
    print("\n"*12)
    console = Console()
    text = Text(_hello, style="green")
    console.print(text)
    print("\n"*12)
