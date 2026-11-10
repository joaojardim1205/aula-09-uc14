"""Testes automatizados (pytest) do Sistema de Controle de Produtos.

Rodar na pasta do projeto:
    pip install -r requirements-dev.txt
    pytest -v

Os códigos (TF = teste funcional, TE = teste exploratório) são os mesmos
usados no RELATORIO_FINAL.md.
"""
import pytest

import app as aplicacao
import banco


def novo_produto(cliente, **campos):
    dados = {"nome": "Teclado mecânico", "categoria": "Periféricos", "preco": "299,90", "estoque": "10"}
    dados.update(campos)
    return cliente.post("/produtos/novo", data=dados, follow_redirects=True)


def texto(resposta):
    return resposta.get_data(as_text=True)


# ---------------------------------------------------------------------------
# Testes funcionais
# ---------------------------------------------------------------------------

def test_tf01_pagina_inicial_leva_ao_login(cliente):
    resposta = cliente.get("/", follow_redirects=True)
    assert resposta.status_code == 200
    assert "Entrar" in texto(resposta)


def test_tf02_cadastro_de_usuario(cliente):
    resposta = cliente.post(
        "/cadastro",
        data={"nome": "Ana", "email": "ana@teste.com", "senha": "123456"},
        follow_redirects=True,
    )
    assert "Cadastro realizado" in texto(resposta)


def test_tf03_login_com_credenciais_validas(cliente):
    cliente.post("/cadastro", data={"nome": "Ana", "email": "ana@teste.com", "senha": "123456"})
    resposta = cliente.post(
        "/login", data={"email": "ana@teste.com", "senha": "123456"}, follow_redirects=True
    )
    assert "Painel" in texto(resposta)
    assert "Olá, Ana" in texto(resposta)


def test_tf04_login_com_senha_errada(cliente):
    cliente.post("/cadastro", data={"nome": "Ana", "email": "ana@teste.com", "senha": "123456"})
    resposta = cliente.post("/login", data={"email": "ana@teste.com", "senha": "errada"})
    assert "Usuário ou senha inválidos" in texto(resposta)


def test_tf05_cadastrar_produto(logado):
    resposta = novo_produto(logado)
    assert "Produto cadastrado com sucesso" in texto(resposta)
    assert "Teclado mecânico" in texto(resposta)
    assert "PER-0001" in texto(resposta)  # código gerado pela categoria + id


def test_tf06_listar_produtos_por_categoria(logado):
    novo_produto(logado, nome="Mouse sem fio")
    novo_produto(logado, nome="Monitor 24", categoria="Monitores", preco="899")
    pagina = texto(logado.get("/produtos"))
    assert "2 produtos" in pagina
    assert "Periféricos" in pagina and "Monitores" in pagina


def test_tf07_pesquisar_por_nome_e_categoria(logado):
    novo_produto(logado, nome="Mouse sem fio")
    novo_produto(logado, nome="Monitor 24", categoria="Monitores", preco="899")
    por_nome = texto(logado.get("/produtos?busca=mouse"))
    assert "Mouse sem fio" in por_nome and "Monitor 24" not in por_nome
    por_categoria = texto(logado.get("/produtos?busca=Monitores"))
    assert "Monitor 24" in por_categoria and "Mouse sem fio" not in por_categoria


def test_tf08_ver_detalhes_do_produto(logado):
    novo_produto(logado, preco="100", estoque="3")
    pagina = texto(logado.get("/produtos/1"))
    assert "Cadastrado por" in pagina and "Ana" in pagina
    assert "R$ 300,00" in pagina  # valor em estoque = 100 x 3
    assert "Últimas 3 un." in pagina  # estoque baixo (até 5)


def test_tf09_editar_produto(logado):
    novo_produto(logado)
    resposta = logado.post(
        "/produtos/1/editar",
        data={"nome": "Teclado sem fio", "categoria": "Periféricos", "preco": "199,90", "estoque": "4"},
        follow_redirects=True,
    )
    assert "Produto atualizado com sucesso" in texto(resposta)
    assert "Teclado sem fio" in texto(logado.get("/produtos/1"))


def test_tf10_excluir_produto(logado):
    novo_produto(logado)
    resposta = logado.post("/produtos/1/excluir", follow_redirects=True)
    assert "Produto excluído" in texto(resposta)
    assert "Nenhum produto cadastrado" in texto(resposta)


def test_tf11_painel_mostra_totais(logado):
    novo_produto(logado, estoque="10")
    novo_produto(logado, nome="Mouse sem fio", estoque="5")
    pagina = texto(logado.get("/painel"))
    assert "Produtos cadastrados <strong>2</strong>" in pagina
    assert "Unidades em estoque <strong>15</strong>" in pagina
    assert "Usuário <strong>1</strong>" in pagina


def test_tf12_lista_de_usuarios_com_contagem(logado):
    novo_produto(logado)
    pagina = texto(logado.get("/usuarios"))
    assert "ana@teste.com" in pagina
    assert '<span class="contagem">1</span>' in pagina


def test_tf13_logout_encerra_a_sessao(logado):
    resposta = logado.get("/logout", follow_redirects=True)
    assert "Você saiu do sistema" in texto(resposta)
    depois = logado.get("/painel", follow_redirects=True)
    assert "Faça login para acessar esta página" in texto(depois)


def test_tf14_arquivos_estaticos_carregam(cliente):
    css = cliente.get("/static/style.css")
    fonte = cliente.get("/static/fonts/anton-latin.woff2")
    assert css.status_code == 200 and fonte.status_code == 200
    css.close()
    fonte.close()


# ---------------------------------------------------------------------------
# Testes exploratórios (dados inválidos, acessos diretos pela URL etc.)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "dados, mensagem",
    [
        ({"nome": "", "email": "", "senha": ""}, "Preencha todos os campos"),
        ({"nome": "Ana", "email": "ana@", "senha": "123456"}, "Informe um e-mail válido"),
        ({"nome": "Ana", "email": "ana@teste.com", "senha": "123"}, "pelo menos 6 caracteres"),
    ],
)
def test_te01_cadastro_com_dados_invalidos(cliente, dados, mensagem):
    assert mensagem in texto(cliente.post("/cadastro", data=dados))


def test_te02_email_duplicado(cliente):
    dados = {"nome": "Ana", "email": "ana@teste.com", "senha": "123456"}
    cliente.post("/cadastro", data=dados)
    assert "Este e-mail já está cadastrado" in texto(cliente.post("/cadastro", data=dados))


@pytest.mark.parametrize("rota", ["/painel", "/produtos", "/produtos/novo", "/usuarios", "/produtos/1"])
def test_te03_paginas_internas_exigem_login(cliente, rota):
    resposta = cliente.get(rota)
    assert resposta.status_code == 302
    assert resposta.headers["Location"].endswith("/login")


@pytest.mark.parametrize(
    "campos, mensagem",
    [
        ({"nome": ""}, "Preencha todos os campos obrigatórios"),
        ({"nome": "TV"}, "pelo menos 3 caracteres"),
        ({"categoria": "Brinquedos"}, "Selecione uma categoria válida"),
        ({"preco": "-10"}, "O preço não pode ser negativo"),
        ({"preco": "abc"}, "O preço deve ser um número válido"),
        ({"estoque": "-1"}, "O estoque não pode ser negativo"),
        ({"estoque": "2.5"}, "O estoque deve ser um número inteiro"),
    ],
)
def test_te04_produto_com_dados_invalidos(logado, campos, mensagem):
    resposta = novo_produto(logado, **campos)
    assert mensagem in texto(resposta)
    assert "Nenhum produto cadastrado" in texto(logado.get("/produtos"))


@pytest.mark.parametrize("preco", ["nan", "inf", "1e400", "1e5", "12,345", "2000000"])
def test_te05_preco_fora_do_padrao_e_recusado(logado, preco):
    """Falha F04/F05: antes, 'nan' dava erro 500 e 'inf' quebrava a lista de produtos."""
    resposta = novo_produto(logado, preco=preco)
    assert resposta.status_code == 200
    assert "O preço deve" in texto(resposta)
    assert logado.get("/produtos").status_code == 200


def test_te06_estoque_gigante_e_recusado(logado):
    """Falha F06: antes, um estoque com 30 dígitos dava erro 500 (OverflowError)."""
    resposta = novo_produto(logado, estoque="9" * 30)
    assert resposta.status_code == 200
    assert "no máximo 1.000.000 unidades" in texto(resposta)


def test_te07_produto_inexistente(logado):
    for rota in ["/produtos/999", "/produtos/999/editar"]:
        resposta = logado.get(rota, follow_redirects=True)
        assert "Produto não encontrado" in texto(resposta)


def test_te08_sessao_de_usuario_que_nao_existe_mais(logado):
    """Falha F07: no Vercel o banco em /tmp é zerado ao reiniciar a função.
    O cookie de login continuava válido e cadastrar produto dava erro 500."""
    conexao = banco.conectar()
    conexao.execute("DELETE FROM usuarios")
    conexao.commit()
    conexao.close()
    resposta = novo_produto(logado)
    assert "Sua sessão expirou" in texto(resposta)


def test_te09_campos_preenchidos_sao_mantidos_apos_erro(logado):
    resposta = novo_produto(logado, nome="Webcam HD", preco="-5")
    assert 'value="Webcam HD"' in texto(resposta)


# ---------------------------------------------------------------------------
# Testes de unidade (regras de negócio e segurança)
# ---------------------------------------------------------------------------

def test_tu01_senha_salva_como_hash(cliente):
    cliente.post("/cadastro", data={"nome": "Ana", "email": "ana@teste.com", "senha": "123456"})
    conexao = banco.conectar()
    senha_hash = conexao.execute("SELECT senha_hash FROM usuarios").fetchone()[0]
    conexao.close()
    assert senha_hash != "123456"
    assert senha_hash.startswith(("scrypt:", "pbkdf2:"))


def test_tu02_filtros_de_formatacao():
    assert aplicacao.formatar_moeda(1234.5) == "R$ 1.234,50"
    assert aplicacao.preco_varejo(1299.9) == ("1.299", "90")
    assert aplicacao.codigo_produto({"categoria": "Monitores", "id": 5}) == "MON-0005"


def test_tu03_validar_produto_aceita_virgula_decimal():
    dados, erros = aplicacao.validar_produto(
        {"nome": "Mouse", "categoria": "Periféricos", "preco": "49,90", "estoque": "7"}
    )
    assert erros == []
    assert dados["preco"] == 49.9 and dados["estoque"] == 7
