"""Configuração dos testes: cada teste usa um banco SQLite novo e vazio."""
import os
import sys
import tempfile

import pytest

# Garante que "import app" funcione rodando `pytest` na pasta do projeto
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Antes de importar o app: aponta o banco para um arquivo temporário,
# para os testes nunca mexerem no sistema.db de verdade.
os.environ["DATABASE_PATH"] = os.path.join(tempfile.mkdtemp(), "inicial.db")

import app as aplicacao  # noqa: E402
import banco  # noqa: E402


@pytest.fixture
def cliente(tmp_path, monkeypatch):
    """Cliente de teste do Flask com um banco novo para cada teste."""
    monkeypatch.setattr(banco, "CAMINHO_BANCO", str(tmp_path / "teste.db"))
    banco.criar_tabelas()
    aplicacao.app.config.update(TESTING=True)
    with aplicacao.app.test_client() as cliente:
        yield cliente


@pytest.fixture
def logado(cliente):
    """Cliente já cadastrado e com login feito (usuária Ana)."""
    cliente.post("/cadastro", data={"nome": "Ana", "email": "ana@teste.com", "senha": "123456"})
    cliente.post("/login", data={"email": "ana@teste.com", "senha": "123456"})
    return cliente
