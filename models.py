import uuid

from sqlalchemy import Column, Integer, ForeignKey, String, Boolean, func, DateTime, DECIMAL, Uuid
from sqlalchemy.orm import DeclarativeBase, relationship


# Modulo com as classes POPO do projeto
# Plain Old Python Object

class Base(DeclarativeBase):
    pass


class Categoria(Base):
    __tablename__ = "categorias"

    id = (Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4))
    nome = (Column(String, nullable=False))
    dta_cadastro = (Column(DateTime, server_default=func.now(), nullable=False))
    dta_atualizacao = (Column(DateTime, onupdate=func.now(), default=func.now(), nullable=False))

    # https://docs.sqlalchemy.org/en/20/orm/queryguide/relationships.html
    lista_de_produtos = relationship("Produto", back_populates="categoria", lazy="selectin",
                                     cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return (f"Categoria(id={self.id!r}, "
                f"Nome={self.nome})")


class Produto(Base):
    __tablename__ = "produtos"

    id = (Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4))
    nome = Column(String, nullable=False)
    preco = Column(DECIMAL(10, 2), default=0.00)
    estoque = Column(Integer, default=0)
    ativo = Column(Boolean, default=True)
    dta_cadastro = Column(DateTime, server_default=func.now())
    dta_atualizacao = Column(DateTime, onupdate=func.now(), default=func.now(), nullable=False)
    categoria_id = Column(Uuid(as_uuid=True), ForeignKey("categorias.id"))

    # https://docs.sqlalchemy.org/en/20/orm/queryguide/relationships.html
    categoria = relationship("Categoria", back_populates="lista_de_produtos")

    def __repr__(self) -> str:
        return (f"Produto(id={self.id!r}, "
                f"Nome={self.nome!r}, "
                f"Preco=R$ {self.preco:.2f}, "
                f"Ativo={self.ativo}, "
                f"Estoque={self.estoque}, "
                f"Categoria={self.categoria_id})")


class Pessoa(Base):
    __tablename__ = "pessoas"

    id = (Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4))
    nome = (Column(String, nullable=False))
