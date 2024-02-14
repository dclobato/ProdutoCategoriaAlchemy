from sqlalchemy import create_engine

import app_categorias
import app_produtos
from menu import menu

if __name__ == "__main__":
    engine = create_engine("sqlite+pysqlite:///test.sqlite3", echo=False)

    opcoes = [{"texto": "Listar os produtos cadastrados", "acao": app_produtos.lista_produtos},
              {"texto": "Listar os produtos sem estoque", "acao": app_produtos.lista_produtos_sem_estoque},
              {"texto": "Listar as categorias cadastradas", "acao": app_categorias.lista_categorias},
              {"texto": "Adiciona nova categoria", "acao": app_categorias.adiciona_categoria},
              {"texto": "Adicionar novo produto", "acao": app_produtos.adiciona_produto},
              {"texto": "Alterar um produto", "acao": app_produtos.altera_produto},
              {"texto": "Vende um produto", "acao": app_produtos.vende_produto},
              {"texto": "Compra um produto", "acao": app_produtos.compra_produto},
              {"texto": "Alterar o preço de um produto", "acao": app_produtos.alterar_preco_produto},
              {"texto": "Corrigir todos os preços por um percental", "acao": app_produtos.alterar_preco_todos_produto},
              {"texto": "Alterar o estado de um produto", "acao": app_produtos.mudar_estado_produto},
              {"texto": "Remover uma categoria e produtos relacionados", "acao": app_categorias.remove_categoria}, ]
    menu(opcoes, engine)
