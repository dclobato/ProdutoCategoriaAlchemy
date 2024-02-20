from rich.console import Console
from rich.prompt import IntPrompt

import app_categorias  # type: ignore
import app_produtos  # type: ignore


def menu(opcoes, engine):
    console = Console(width=100)
    while True:
        console.rule("[bold red]Escolha uma opção")
        total_opcoes = len(opcoes)
        for opcao in enumerate(opcoes):
            print(f"{opcao[0] + 1}: {opcao[1]['texto']}")
        print(f"0: Sair")

        escolha = IntPrompt.ask("Escolha uma opção", default=0, show_default=True)
        if escolha > total_opcoes:
            console.print(f"[bold red]{escolha} não é uma opção válida")
            continue
        if escolha == 0:
            break
        opcoes[escolha - 1]["acao"](engine, console)
    return
