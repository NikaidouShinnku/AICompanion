from consoles import print_code

_hello = r"""
                                        ___    ____   __________  __  _______  ___    _   __________  _   __
                                       /   |  /  _/  / ____/ __ \/  |/  / __ \/   |  / | / /  _/ __ \/ | / /
                                      / /| |  / /   / /   / / / / /|_/ / /_/ / /| | /  |/ // // / / /  |/ /
                                     / ___ |_/ /   / /___/ /_/ / /  / / ____/ ___ |/ /|  // // /_/ / /|  /
                                    /_/  |_/___/   \____/\____/_/  /_/_/   /_/  |_/_/ |_/___/\____/_/ |_/                                                                         
"""

def hello():
    from rich.text import Text
    from rich.console import Console
    print("\n"*12)
    console = Console()
    text = Text(_hello, style="green")
    console.print(text)
    print("\n"*12)
