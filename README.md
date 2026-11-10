# Sistema de Controle de Produtos

Aplicação Web em Flask para cadastrar e gerenciar os produtos de uma loja: preço, categoria e estoque, com login de usuários.

- Documentação técnica: [`docs/documentacao.md`](docs/documentacao.md)
- Relatório de publicação e testes: [`RELATORIO_FINAL.md`](RELATORIO_FINAL.md)

## Rodar no computador

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
python app.py                    # abre em http://127.0.0.1:5000
```

## Rodar os testes

```bash
pytest -v
```

## Publicar no Vercel

1. Envie o projeto para um repositório no GitHub.
2. Em [vercel.com](https://vercel.com), clique em **Add New → Project** e importe o repositório. O Vercel detecta o Flask sozinho.
3. Em **Environment Variables**, crie `SECRET_KEY` com um valor aleatório:
   `python -c "import secrets; print(secrets.token_hex(32))"`
4. Clique em **Deploy**.

> No Vercel, o banco SQLite fica em `/tmp` e é **temporário**: os dados são apagados quando a função reinicia. Veja a seção 4.3 do relatório.
