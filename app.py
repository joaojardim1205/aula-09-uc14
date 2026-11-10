"""Sistema de Controle de Produtos - aplicação principal Flask.

Aqui ficam as rotas, as regras de negócio (validações) e a integração
com o banco de dados (banco.py) e os templates (pasta templates/).
"""
import math
import os
import re
import sqlite3
from functools import wraps

from flask import Flask, flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

import banco

# Os arquivos estáticos (CSS e fontes) ficam em public/static/:
# - no computador, o próprio Flask os serve em /static/...
# - no Vercel, a pasta public/ é servida direto pela CDN (o Vercel ignora a
#   pasta static do Flask), e o endereço continua sendo /static/...
app = Flask(__name__, static_folder="public/static", static_url_path="/static")

# Em produção, defina a variável de ambiente SECRET_KEY (no Vercel:
# Settings > Environment Variables). Ela assina o cookie de login.
app.secret_key = os.environ.get("SECRET_KEY", "troque-esta-chave-em-producao")
if os.environ.get("VERCEL") and not os.environ.get("SECRET_KEY"):
    print("AVISO: SECRET_KEY não definida no Vercel. Defina-a nas variáveis de ambiente.")

# Fecha as conexões com o banco ao fim de cada requisição, mesmo com erro
app.teardown_appcontext(banco.fechar_conexoes)

CATEGORIAS = ["Periféricos", "Monitores", "Acessórios", "Hardware", "Outros"]
EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
# Produtos com esta quantidade (ou menos) aparecem como "estoque baixo"
ESTOQUE_BAIXO = 5
# Limites para evitar valores absurdos (ex.: "1e400", "nan" ou números gigantes)
PRECO_MAXIMO = 1_000_000
ESTOQUE_MAXIMO = 1_000_000
# Mesmo formato aceito pelo formulário: números com até 2 casas decimais
PRECO_REGEX = re.compile(r"^\d+(\.\d{1,2})?$")
ESTOQUE_REGEX = re.compile(r"^\d+$")


# ---------------------------------------------------------------------------
# Funções auxiliares
# ---------------------------------------------------------------------------

@app.context_processor
def variaveis_globais():
    """Disponibiliza o limite de estoque baixo para todos os templates."""
    return {"ESTOQUE_BAIXO": ESTOQUE_BAIXO}

def login_obrigatorio(funcao):
    """Decorador: só deixa acessar a rota se o usuário estiver logado."""
    @wraps(funcao)
    def verificar(*args, **kwargs):
        if "usuario_id" not in session:
            flash("Faça login para acessar esta página.", "erro")
            return redirect(url_for("login"))

        # O cookie de login pode apontar para um usuário que não existe mais
        # no banco (no Vercel o banco em /tmp é zerado quando a função
        # reinicia). Nesse caso, encerra a sessão em vez de dar erro 500.
        conexao = banco.conectar()
        usuario = conexao.execute(
            "SELECT id FROM usuarios WHERE id = ?", (session["usuario_id"],)
        ).fetchone()
        conexao.close()
        if usuario is None:
            session.clear()
            flash("Sua sessão expirou. Entre novamente.", "erro")
            return redirect(url_for("login"))

        return funcao(*args, **kwargs)
    return verificar


@app.template_filter("moeda")
def formatar_moeda(valor):
    """Formata um número no padrão brasileiro: 1234.5 -> R$ 1.234,50"""
    texto = f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {texto}"


@app.template_filter("preco_varejo")
def preco_varejo(valor):
    """Separa o preço como nas etiquetas de loja: 1299.9 -> ("1.299", "90")"""
    reais, centavos = formatar_moeda(valor)[3:].split(",")
    return reais, centavos


@app.template_filter("codigo")
def codigo_produto(produto):
    """Código de peça: 3 letras da categoria + id. Ex.: Monitores, 5 -> MON-0005"""
    prefixo = produto["categoria"][:3].upper()
    return f"{prefixo}-{produto['id']:04d}"


def validar_usuario(nome, email, senha):
    """Regras de negócio do cadastro de usuário. Retorna lista de erros."""
    erros = []
    if not nome or not email or not senha:
        erros.append("Preencha todos os campos.")
    if email and not EMAIL_REGEX.match(email):
        erros.append("Informe um e-mail válido.")
    if senha and len(senha) < 6:
        erros.append("A senha deve ter pelo menos 6 caracteres.")
    return erros


def validar_produto(formulario):
    """Regras de negócio do produto. Retorna (dados, erros)."""
    nome = formulario.get("nome", "").strip()
    categoria = formulario.get("categoria", "").strip()
    preco_texto = formulario.get("preco", "").strip().replace(",", ".")
    estoque_texto = formulario.get("estoque", "").strip()

    dados = {"nome": nome, "categoria": categoria,
             "preco": preco_texto, "estoque": estoque_texto}
    erros = []

    if not nome or not categoria or not preco_texto or not estoque_texto:
        erros.append("Preencha todos os campos obrigatórios.")
    if nome and len(nome) < 3:
        erros.append("O nome do produto deve ter pelo menos 3 caracteres.")
    if categoria and categoria not in CATEGORIAS:
        erros.append("Selecione uma categoria válida.")

    if preco_texto:
        if preco_texto.startswith("-"):
            erros.append("O preço não pode ser negativo.")
        elif not PRECO_REGEX.match(preco_texto):
            # Recusa textos como "nan", "inf", "1e5" ou "12,345"
            erros.append("O preço deve ser um número válido, com até 2 casas decimais.")
        else:
            dados["preco"] = float(preco_texto)
            if not math.isfinite(dados["preco"]) or dados["preco"] > PRECO_MAXIMO:
                erros.append("O preço deve ser de no máximo R$ 1.000.000,00.")

    if estoque_texto:
        if estoque_texto.startswith("-"):
            erros.append("O estoque não pode ser negativo.")
        elif not ESTOQUE_REGEX.match(estoque_texto):
            erros.append("O estoque deve ser um número inteiro.")
        else:
            dados["estoque"] = int(estoque_texto)
            if dados["estoque"] > ESTOQUE_MAXIMO:
                erros.append("O estoque deve ser de no máximo 1.000.000 unidades.")

    return dados, erros


def buscar_produto(produto_id):
    """Busca um produto pelo id (com o nome de quem cadastrou)."""
    conexao = banco.conectar()
    produto = conexao.execute(
        """SELECT p.*, u.nome AS cadastrado_por
           FROM produtos p JOIN usuarios u ON u.id = p.usuario_id
           WHERE p.id = ?""",
        (produto_id,),
    ).fetchone()
    conexao.close()
    return produto


# ---------------------------------------------------------------------------
# Usuários: cadastro, login e logout
# ---------------------------------------------------------------------------

@app.route("/")
def inicio():
    if "usuario_id" in session:
        return redirect(url_for("painel"))
    return redirect(url_for("login"))


@app.route("/cadastro", methods=["GET", "POST"])
def cadastro():
    if request.method == "POST":
        nome = request.form.get("nome", "").strip()
        email = request.form.get("email", "").strip().lower()
        senha = request.form.get("senha", "")

        erros = validar_usuario(nome, email, senha)
        if not erros:
            try:
                conexao = banco.conectar()
                conexao.execute(
                    "INSERT INTO usuarios (nome, email, senha_hash) VALUES (?, ?, ?)",
                    (nome, email, generate_password_hash(senha)),
                )
                conexao.commit()
                conexao.close()
                flash("Cadastro realizado! Faça login para continuar.", "sucesso")
                return redirect(url_for("login"))
            except sqlite3.IntegrityError:
                # A coluna email é UNIQUE: o banco impede e-mails repetidos
                erros.append("Este e-mail já está cadastrado.")

        for erro in erros:
            flash(erro, "erro")
        return render_template("cadastro.html", nome=nome, email=email)

    return render_template("cadastro.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        senha = request.form.get("senha", "")

        conexao = banco.conectar()
        usuario = conexao.execute(
            "SELECT * FROM usuarios WHERE email = ?", (email,)
        ).fetchone()
        conexao.close()

        if usuario and check_password_hash(usuario["senha_hash"], senha):
            session.clear()
            session["usuario_id"] = usuario["id"]
            session["usuario_nome"] = usuario["nome"]
            return redirect(url_for("painel"))

        flash("Usuário ou senha inválidos.", "erro")
        return render_template("login.html", email=email)

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("Você saiu do sistema.", "sucesso")
    return redirect(url_for("login"))


# ---------------------------------------------------------------------------
# Painel
# ---------------------------------------------------------------------------

@app.route("/painel")
@login_obrigatorio
def painel():
    conexao = banco.conectar()
    total_produtos = conexao.execute("SELECT COUNT(*) FROM produtos").fetchone()[0]
    total_usuarios = conexao.execute("SELECT COUNT(*) FROM usuarios").fetchone()[0]
    total_estoque = conexao.execute(
        "SELECT COALESCE(SUM(estoque), 0) FROM produtos"
    ).fetchone()[0]
    conexao.close()
    return render_template(
        "painel.html",
        total_produtos=total_produtos,
        total_usuarios=total_usuarios,
        total_estoque=total_estoque,
    )


# ---------------------------------------------------------------------------
# Usuários: listagem
# ---------------------------------------------------------------------------

@app.route("/usuarios")
@login_obrigatorio
def usuarios():
    conexao = banco.conectar()
    # LEFT JOIN para contar os produtos de cada usuário (inclusive quem tem 0)
    lista = conexao.execute(
        """SELECT u.id, u.nome, u.email, u.perfil, COUNT(p.id) AS total_produtos
           FROM usuarios u LEFT JOIN produtos p ON p.usuario_id = u.id
           GROUP BY u.id
           ORDER BY u.nome"""
    ).fetchall()
    conexao.close()
    return render_template("usuarios.html", usuarios=lista)


# ---------------------------------------------------------------------------
# Produtos: listagem, pesquisa, cadastro, detalhes, edição e exclusão
# ---------------------------------------------------------------------------

@app.route("/produtos")
@login_obrigatorio
def produtos():
    busca = request.args.get("busca", "").strip()
    conexao = banco.conectar()
    if busca:
        termo = f"%{busca}%"
        lista = conexao.execute(
            """SELECT * FROM produtos
               WHERE nome LIKE ? OR categoria LIKE ?
               ORDER BY nome""",
            (termo, termo),
        ).fetchall()
    else:
        lista = conexao.execute("SELECT * FROM produtos ORDER BY nome").fetchall()
    conexao.close()
    return render_template("produtos.html", produtos=lista, busca=busca)


@app.route("/produtos/novo", methods=["GET", "POST"])
@login_obrigatorio
def produto_novo():
    if request.method == "POST":
        dados, erros = validar_produto(request.form)
        if not erros:
            conexao = banco.conectar()
            conexao.execute(
                """INSERT INTO produtos (usuario_id, nome, categoria, preco, estoque)
                   VALUES (?, ?, ?, ?, ?)""",
                (session["usuario_id"], dados["nome"], dados["categoria"],
                 dados["preco"], dados["estoque"]),
            )
            conexao.commit()
            conexao.close()
            flash("Produto cadastrado com sucesso!", "sucesso")
            return redirect(url_for("produtos"))

        for erro in erros:
            flash(erro, "erro")
        return render_template("produto_form.html", produto=dados, categorias=CATEGORIAS)

    return render_template("produto_form.html", produto=None, categorias=CATEGORIAS)


@app.route("/produtos/<int:produto_id>")
@login_obrigatorio
def produto_detalhe(produto_id):
    produto = buscar_produto(produto_id)
    if produto is None:
        flash("Produto não encontrado.", "erro")
        return redirect(url_for("produtos"))
    return render_template("produto_detalhe.html", produto=produto)


@app.route("/produtos/<int:produto_id>/editar", methods=["GET", "POST"])
@login_obrigatorio
def produto_editar(produto_id):
    produto = buscar_produto(produto_id)
    if produto is None:
        flash("Produto não encontrado.", "erro")
        return redirect(url_for("produtos"))

    if request.method == "POST":
        dados, erros = validar_produto(request.form)
        if not erros:
            conexao = banco.conectar()
            conexao.execute(
                """UPDATE produtos SET nome = ?, categoria = ?, preco = ?, estoque = ?
                   WHERE id = ?""",
                (dados["nome"], dados["categoria"], dados["preco"],
                 dados["estoque"], produto_id),
            )
            conexao.commit()
            conexao.close()
            flash("Produto atualizado com sucesso!", "sucesso")
            return redirect(url_for("produtos"))

        for erro in erros:
            flash(erro, "erro")
        dados["id"] = produto_id
        return render_template("produto_form.html", produto=dados, categorias=CATEGORIAS)

    return render_template("produto_form.html", produto=produto, categorias=CATEGORIAS)


@app.route("/produtos/<int:produto_id>/excluir", methods=["POST"])
@login_obrigatorio
def produto_excluir(produto_id):
    conexao = banco.conectar()
    conexao.execute("DELETE FROM produtos WHERE id = ?", (produto_id,))
    conexao.commit()
    conexao.close()
    flash("Produto excluído.", "sucesso")
    return redirect(url_for("produtos"))


# Cria as tabelas ao iniciar a aplicação
banco.criar_tabelas()

if __name__ == "__main__":
    app.run(debug=True)
