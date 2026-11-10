"""Criação e conexão com o banco de dados SQLite (sistema.db)."""
import os
import sqlite3

from flask import g, has_app_context


def _caminho_banco():
    """Decide onde o arquivo do banco fica.

    - DATABASE_PATH definida: usa o caminho informado (útil para testes).
    - Rodando no Vercel (variável VERCEL=1): usa /tmp, a única pasta com
      permissão de escrita no Vercel. Os dados são TEMPORÁRIOS lá: somem
      quando a função é reiniciada (veja o RELATORIO_FINAL.md).
    - Rodando no computador: sistema.db na mesma pasta deste arquivo.
    """
    if os.environ.get("DATABASE_PATH"):
        return os.environ["DATABASE_PATH"]
    if os.environ.get("VERCEL"):
        return "/tmp/sistema.db"
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "sistema.db")


CAMINHO_BANCO = _caminho_banco()


def conectar():
    """Abre uma conexão com o banco. As linhas podem ser lidas como dicionário.

    Durante uma requisição, a conexão também é registrada em `g` para ser
    fechada automaticamente no fim (mesmo se acontecer um erro no meio).
    """
    conexao = sqlite3.connect(CAMINHO_BANCO)
    conexao.row_factory = sqlite3.Row
    conexao.execute("PRAGMA foreign_keys = ON")
    if has_app_context():
        g.setdefault("conexoes", []).append(conexao)
    return conexao


def fechar_conexoes(erro=None):
    """Fecha as conexões abertas na requisição (chamada pelo Flask no final)."""
    for conexao in g.pop("conexoes", []):
        conexao.close()


def criar_tabelas():
    """Cria as tabelas usuarios e produtos, caso ainda não existam."""
    conexao = conectar()
    conexao.executescript(
        """
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            senha_hash TEXT NOT NULL,
            perfil TEXT NOT NULL DEFAULT 'usuario'
        );

        CREATE TABLE IF NOT EXISTS produtos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER NOT NULL,
            nome TEXT NOT NULL,
            categoria TEXT NOT NULL,
            preco REAL NOT NULL CHECK (preco >= 0),
            estoque INTEGER NOT NULL CHECK (estoque >= 0),
            FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
        );
        """
    )
    conexao.commit()
    conexao.close()
