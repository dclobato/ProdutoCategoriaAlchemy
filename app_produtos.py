from decimal import Decimal

from rich.console import Console
from rich.prompt import Prompt, IntPrompt, FloatPrompt, Confirm
from rich.table import Table
from sqlalchemy import select, func, exc, update
from sqlalchemy.orm import Session

import app_categorias
from models import Produto, Categoria


def lista_produtos(engine: Session, console: Console, msg_titulo: str = "Lista de produtos cadastrados"):
    tabela = Table(title=msg_titulo, caption="(*) Produtos com estoque negativo")
    tabela.add_column("Nome", justify="left")
    tabela.add_column("Ativo?", justify="center")
    tabela.add_column("Preço", justify="right")
    tabela.add_column("Estoque", justify="right")
    tabela.add_column("Cadastro", justify="left")
    tabela.add_column("Atualizado", justify="left")
    tabela.add_column("Categoria", justify="left")

    with Session(engine) as sessao:
        produtos = sessao.scalars(select(Produto).order_by(Produto.nome))
        for produto in produtos.yield_per(100):
            nome = produto.nome
            if produto.estoque < 0:
                nome = nome + " (*)"
            tabela.add_row(nome, "S" if produto.ativo else "N", f"R$ {produto.preco:.2f}", f"{produto.estoque:4d}",
                           f"{produto.dta_cadastro.strftime('%Y-%m-%d')}",
                           f"{produto.dta_atualizacao.strftime('%Y-%m-%d %H:%M')}", f"{produto.categoria.nome}")
    console.print(tabela)


def lista_produtos_sem_estoque(engine: Session, console: Console):
    tabela = Table(title="Lista de produtos ativos sem estoque", caption="(*) Produtos com estoque negativo")
    tabela.add_column("Nome", justify="left")
    tabela.add_column("Preço", justify="right")
    tabela.add_column("Cadastro", justify="right")
    tabela.add_column("Atualizado", justify="right")
    tabela.add_column("Categoria", justify="left")

    with Session(engine) as sessao:
        produtos = sessao.scalars(
            select(Produto).where(Produto.estoque <= 0).where(Produto.ativo).order_by(Produto.nome))
        for produto in produtos.yield_per(100):
            nome = produto.nome
            if produto.estoque < 0:
                nome = nome + " (*)"
            tabela.add_row(nome, f"R$ {produto.preco:.2f}", f"{produto.dta_cadastro.strftime('%Y-%m-%d')}",
                           f"{produto.dta_atualizacao.strftime('%Y-%m-%d %H:%M')}", f"{produto.categoria.nome}")
    console.print(tabela)


def adiciona_produto(engine: Session, console: Console):
    cat_id = app_categorias.seleciona_categoria_id(engine, console, titulo="Selecione uma categoria",
                                                   msg_cancelar="Cancelar a adição",
                                                   msg_prompt="Em qual categoria o produto será adicionado?")
    if cat_id is None:
        return
    produto = Produto()
    produto.nome = Prompt.ask("Qual o nome do produto?")
    produto.estoque = IntPrompt.ask("Qual o estoque inicial do produto?", default=0, show_default=True)
    produto.preco = Decimal(FloatPrompt.ask("Qual o preço inicial do produto?", default=0.00, show_default=True))
    if Confirm.ask(f"Confirma o cadastramento do produto '{produto.nome}'?"):
        with Session(engine) as sessao:
            categoria = sessao.get(Categoria, cat_id)
            sessao.add(produto)
            categoria.lista_de_produtos.append(produto)
            sessao.commit()


def altera_produto(engine: Session, console: Console):
    id_produto = selecionar_produto_id(engine, console, titulo="Escolha um produto para ser alterado",
                                       apenas_ativos=True)

    # Escolhe o produto
    # Passa pelos atributos alterando, dando como default o valor atual
    pass


def remove_produto(engine: Session, console: Console):
    id_produto = selecionar_produto_id(engine, console, titulo="Escolha um produto para ser alterado",
                                       apenas_ativos=False)

    with Session(engine) as sessao:
        sessao.expire_on_commit = False
        try:
            produto = sessao.get_one(Produto, id_produto)
        except exc.NoResultFound:
            print("Produto inexistente")
        else:
            if Confirm.ask(f"Confirma a remoção do produto {produto.nome}?"):
                sessao.delete(produto)
                sessao.commit()
                print("Feito!")
            else:
                print("Remoção interrompida")


def compra_produto(engine: Session, console: Console):
    id_produto = selecionar_produto_id(engine, console, titulo="Escolha um produto para comprar", apenas_ativos=True)

    with Session(engine) as sessao:
        produto = sessao.get_one(Produto, id_produto)
        nome = produto.nome
        qtd_atual = produto.estoque

    adicionar = IntPrompt.ask(f"Adicionar quantas unidades às {qtd_atual} já existentes?")
    if adicionar < 0:
        print("Compra cancelada")
        return
    qtd_nova = qtd_atual + adicionar
    with Session(engine) as sessao:
        produto = sessao.get_one(Produto, id_produto)
        produto.estoque = qtd_nova
        sessao.commit()
        print(f"{nome} agora com {qtd_nova} unidades")


def vende_produto(engine: Session, console: Console):
    id_produto = selecionar_produto_id(engine, console, titulo="Escolha um produto para vender", apenas_ativos=True)

    with Session(engine) as sessao:
        produto = sessao.get_one(Produto, id_produto)
        nome = produto.nome
        qtd_atual = produto.estoque

    reduzir = IntPrompt.ask(f"Vender quantas unidades das {qtd_atual} existentes?")
    if reduzir < 0:
        print("Venda interrompida")
        return
    qtd_nova = qtd_atual - reduzir
    if qtd_nova < 0 and not Confirm.ask(f"Produto ficará com estoque negativo de {qtd_nova * -1} unidades. Confirma?"):
        print("Venda interrompida")
        return
    with Session(engine) as sessao:
        produto = sessao.get_one(Produto, id_produto)
        produto.estoque = qtd_nova
        sessao.commit()
        print(f"{nome} agora com {qtd_nova} unidades")


def mudar_estado_produto(engine: Session, console: Console):
    id_produto = selecionar_produto_id(engine, console, titulo="Escolha um produto para alterar", apenas_ativos=False)

    with Session(engine) as sessao:
        produto = sessao.get_one(Produto, id_produto)
        nome = produto.nome
        ativo = produto.ativo

    atual = "ativo" if ativo else "inativo"
    novo = "inativo" if ativo else "ativo"

    if Confirm.ask(f"Alterar o estado do produto '{nome}' de {atual} para {novo}?", default=False, show_default=True):
        with Session(engine) as sessao:
            produto = sessao.get_one(Produto, id_produto)
            produto.ativo = not produto.ativo
            sessao.commit()
            print(f"O produto '{nome}' agora está {novo}")


def selecionar_produto_id(engine: Session, console: Console, titulo: str = "Selecione um produto",
                          msg_cancelar: str = "Interromper a seleção", msg_prompt: str = "Selecione um produto",
                          apenas_ativos: bool = False):
    caption = []
    nomeparcial = Prompt.ask("Digite o nome parcial do produto (enter para todos)", default="", show_default=True)
    if nomeparcial != "":
        caption.append(f"Apenas produtos contendo '{nomeparcial}'")
    if apenas_ativos:
        caption.append("Apenas produtos ativos")

    if len(caption) == 0:
        tabela = Table(title=titulo)
    else:
        tabela = Table(title=titulo, caption=". ".join(caption))

    tabela.add_column("Id", justify="right")
    tabela.add_column("Nome", justify="left")
    if not apenas_ativos:
        tabela.add_column("Ativo?", justify="center")
    tabela.add_column("Preço", justify="right")
    tabela.add_column("Estoque", justify="right")
    tabela.add_column("Cadastro", justify="left")
    tabela.add_column("Atualizado", justify="left")
    tabela.add_column("Categoria", justify="left")

    item = 1
    with Session(engine) as sessao:
        id_uuid = dict()
        query = select(Produto).where(func.lower(Produto.nome).like(f"%{nomeparcial}%"))
        if apenas_ativos:
            query = query.where(Produto.ativo)
        query = query.order_by(Produto.nome)
        produtos = sessao.scalars(query)
        for produto in produtos.yield_per(100):
            id_uuid[str(item)] = produto.id
            nome = produto.nome
            if produto.estoque < 0:
                nome = nome + " (*)"
            if not apenas_ativos:
                tabela.add_row(str(item), nome, "S" if produto.ativo else "N", f"R$ {produto.preco:.2f}",
                               f"{produto.estoque:4d}", f"{produto.dta_cadastro.strftime('%Y-%m-%d')}",
                               f"{produto.dta_atualizacao.strftime('%Y-%m-%d %H:%M')}", f"{produto.categoria.nome}")
            else:
                tabela.add_row(str(item), nome, f"R$ {produto.preco:.2f}", f"{produto.estoque:4d}",
                               f"{produto.dta_cadastro.strftime('%Y-%m-%d')}",
                               f"{produto.dta_atualizacao.strftime('%Y-%m-%d %H:%M')}", f"{produto.categoria.nome}")

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


def alterar_preco_produto(engine: Session, console: Console):
    id_produto = selecionar_produto_id(engine, console, titulo="Escolha um produto para corrigir o preço",
                                       apenas_ativos=True)

    with Session(engine) as sessao:
        produto = sessao.get_one(Produto, id_produto)
        nome = produto.nome
        preco = produto.preco

    novo_preco = Decimal(FloatPrompt.ask(f"Qual o novo preço de '{nome}'?", default=float(preco), show_default=True))
    if novo_preco <= 0:
        print("Preço não pode ser zero nem negativo")
        return
    with Session(engine) as sessao:
        produto = sessao.get_one(Produto, id_produto)
        produto.preco = Decimal(novo_preco)
        sessao.commit()
        print(f"{nome} agora custa R$ {novo_preco:.2f}")


def alterar_preco_todos_produto(engine: Session, console: Console):
    percentual = FloatPrompt.ask("Qual vai ser o percentual de reajuste (0.00 a 100.00%)?", default=0.00,
                                 show_default=True)
    if percentual < 0 or percentual > 100:
        print("Percentual inválido")
        return

    taxa = Decimal(1.0 + percentual / 100.0)
    with Session(engine) as sessao:
        sessao.execute(update(Produto).values(preco=Produto.preco * taxa).where(Produto.ativo))
        sessao.commit()
        print(f"Precos corrigidos em {percentual:.2f}%!")
