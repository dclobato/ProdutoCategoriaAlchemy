from rich.console import Console
from rich.prompt import IntPrompt, Prompt, Confirm
from rich.table import Table
from sqlalchemy import select, func, exc
from sqlalchemy.orm import Session
from models import Categoria


def lista_categorias(engine: Session, console: Console):
    tabela = Table(title="Lista de categorias cadastradas")
    tabela.add_column("Nome", justify="left", no_wrap=True)
    tabela.add_column("Cadastro", justify="left", no_wrap=True)
    tabela.add_column("Atualizado", justify="left", no_wrap=True)
    tabela.add_column("# produtos", justify="right", no_wrap=True)

    with Session(engine) as sessao:
        categorias = sessao.scalars(select(Categoria).order_by(Categoria.nome))
        for categoria in categorias.yield_per(100):
            tabela.add_row(categoria.nome, f"{categoria.dta_cadastro.strftime('%Y-%m-%d')}",
                           f"{categoria.dta_atualizacao.strftime('%Y-%m-%d %H:%M')}",
                           f"{len(categoria.lista_de_produtos):4d}")
    console.print(tabela)


def adiciona_categoria(engine: Session, console: Console):
    nome = Prompt.ask("Digite o nome da nova categoria")
    with Session(engine) as sessao:
        query = select(func.count()).where(func.lower(Categoria.nome).like(f"%{nome}%"))
        count = sessao.execute(query).scalar()
        if count > 0:
            query = select(Categoria).where(func.lower(Categoria.nome).like(f"%{nome}%")).order_by(Categoria.nome)
            categorias = sessao.scalars(query)
            tabela = Table(title="Lista de categorias similares já cadastradas")
            tabela.add_column("Nome", justify="left", no_wrap=True)
            tabela.add_column("Cadastro", justify="left", no_wrap=True)
            tabela.add_column("Atualizado", justify="left", no_wrap=True)
            tabela.add_column("# produtos", justify="right", no_wrap=True)
            for categoria in categorias.yield_per(100):
                tabela.add_row(categoria.nome, f"{categoria.dta_cadastro.strftime('%Y-%m-%d')}",
                               f"{categoria.dta_atualizacao.strftime('%Y-%m-%d %H:%M')}",
                               f"{len(categoria.lista_de_produtos):4d}")
            console.print(tabela)

    if Confirm.ask(f"Confirma o cadastramento da categoria '{nome}'"):
        with Session(engine) as sessao:
            cat = Categoria(nome=nome)
            sessao.add(cat)
            sessao.commit()


def altera_categoria(engine: Session, console: Console):
    pass


def remove_categoria(engine: Session, console: Console):
    cat_id = seleciona_categoria_id(engine, console, titulo="Selecione a categoria a ser removida",
                                 msg_cancelar="Interromper a remoção",
                                 msg_prompt="Qual o Id da categoria que vai ser removida?")
    if cat_id is None:
        return

    with Session(engine) as sessao:
        try:
            categoria = sessao.get_one(Categoria, cat_id)
        except exc.NoResultFound:
            print("Categoria inexistente")
        else:
            mensagem = f"Confirma a remoção da categoria {categoria.nome}"
            if len(categoria.lista_de_produtos) > 0:
                tabela = Table(title="Produtos que serão removidos junto com a categoria")
                tabela.add_column("Nome", justify="left", no_wrap=True)
                tabela.add_column("Preço", justify="right", no_wrap=True)
                tabela.add_column("Estoque", justify="right", no_wrap=True)
                tabela.add_column("Cadastro", justify="left", no_wrap=True)
                tabela.add_column("Atualizado", justify="left", no_wrap=True)
                for produto in categoria.lista_de_produtos:
                    tabela.add_row(produto.nome, f"R$ {produto.preco:.2f}", f"{produto.estoque:4d}",
                                   f"{produto.dta_cadastro.strftime('%Y-%m-%d')}",
                                   f"{produto.dta_atualizacao.strftime('%Y-%m-%d %H:%M')}")
                console.print(tabela)
                mensagem = mensagem + f" e todos os {len(categoria.lista_de_produtos)} produtos relacionados?"
            else:
                mensagem = mensagem + "?"
            if Confirm.ask(mensagem):
                sessao.delete(categoria)
                sessao.commit()
                print("Feito!")
            else:
                print("Remoção interrompida")


def seleciona_categoria_id(engine: Session, console: Console, titulo: str = "Selecione uma categorias",
                           msg_cancelar: str = "Interromper a seleção", msg_prompt: str = "Selecione uma categoria"):

    caption = []
    nomeparcial = Prompt.ask("Digite o nome parcial da categoria (enter para todas)", default="", show_default=True)
    if nomeparcial != "":
        caption.append(f"Apenas categorias contendo '{nomeparcial}'")

    if len(caption) == 0:
        tabela = Table(title=titulo)
    else:
        tabela = Table(title=titulo, caption=". ".join(caption))

    tabela.add_column("Id", justify="right", no_wrap=True)
    tabela.add_column("Nome", justify="left", no_wrap=True)
    tabela.add_column("Cadastro", justify="left", no_wrap=True)
    tabela.add_column("Atualizado", justify="left", no_wrap=True)
    tabela.add_column("# produtos", justify="right", no_wrap=True)

    item = 1
    with Session(engine) as sessao:
        id_uuid = dict()
        categorias = sessao.scalars(select(Categoria).where(func.lower(Categoria.nome).like(f"%{nomeparcial}%")).order_by(Categoria.nome))
        for categoria in categorias.yield_per(100):
            id_uuid[str(item)] = categoria.id
            tabela.add_row(str(item), categoria.nome, f"{categoria.dta_cadastro.strftime('%Y-%m-%d')}",
                           f"{categoria.dta_atualizacao.strftime('%Y-%m-%d %H:%M')}",
                           f"{len(categoria.lista_de_produtos):4d}")
            item = item + 1
    item = item - 1
    tabela.add_row(str(0), msg_cancelar, "", "", "")
    console.print(tabela)
    escolha = IntPrompt.ask(msg_prompt, default=0, show_default=True)
    if escolha > item:
        console.print(f"[bold red]{escolha} não é uma opção válida")
        return None
    if escolha == 0:
        return None
    return id_uuid[str(escolha)]
