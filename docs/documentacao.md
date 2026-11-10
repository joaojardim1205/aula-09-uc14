## 1. Planejamento

**Proposta:** aplicação Web simples para cadastrar e gerenciar produtos.
**Escopo:** cadastro de usuários, login/logout, CRUD de produtos com pesquisa e validações.
**Fora do escopo:** recuperação de senha, envio de e-mail, upload de imagens, APIs externas, pagamentos, dashboard avançado, permissões complexas.
**Tecnologias:** Python, Flask, Jinja2, HTML5, CSS3 e SQLite.

## 2. Requisitos

### Funcionais
| Código | Requisito |
|---|---|
| RF01 | Cadastrar usuário (nome, e-mail, senha) |
| RF02 | Realizar login e logout |
| RF03 | Cadastrar produto (nome, categoria, preço, estoque) |
| RF04 | Listar produtos |
| RF05 | Pesquisar produtos por nome ou categoria |
| RF06 | Visualizar os detalhes de um produto |
| RF07 | Editar produto |
| RF08 | Excluir produto (com confirmação) |
| RF09 | Exibir painel com totais de produtos, estoque e usuários |
| RF10 | Listar usuários cadastrados com a quantidade de produtos de cada um |

### Não funcionais
| Código | Requisito |
|---|---|
| RNF01 | Dados armazenados em SQLite (`sistema.db`; em `/tmp` no Vercel) |
| RNF02 | Senhas armazenadas como hash (nunca em texto puro) |
| RNF03 | Páginas internas acessíveis apenas com login |
| RNF04 | Validação no cliente (HTML5) e no servidor (Python) |
| RNF05 | Interface responsiva (funciona em telas pequenas) |
| RNF06 | Publicada no Vercel, com a chave secreta em variável de ambiente (`SECRET_KEY`) |

## 3. Regras de negócio

| Código | Regra |
|---|---|
| RN01 | Todos os campos obrigatórios devem ser preenchidos |
| RN02 | O e-mail deve ter formato válido e ser único no sistema |
| RN03 | A senha deve ter no mínimo 6 caracteres |
| RN04 | O nome do produto deve ter no mínimo 3 caracteres |
| RN05 | O preço deve ser numérico (até 2 casas decimais), não negativo e de no máximo R$ 1.000.000,00 |
| RN06 | O estoque deve ser um número inteiro, não negativo e de no máximo 1.000.000 |
| RN07 | A categoria deve ser uma das opções da lista |
| RN08 | Cada produto guarda o usuário que o cadastrou (`usuario_id`) |
| RN09 | Todo usuário logado pode consultar, editar e excluir produtos |

## 4. Modelagem do banco

Relacionamento **1:N** — um usuário cadastra vários produtos.

```sql
CREATE TABLE usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    senha_hash TEXT NOT NULL,
    perfil TEXT NOT NULL DEFAULT 'usuario'
);

CREATE TABLE produtos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id INTEGER NOT NULL,
    nome TEXT NOT NULL,
    categoria TEXT NOT NULL,
    preco REAL NOT NULL CHECK (preco >= 0),
    estoque INTEGER NOT NULL CHECK (estoque >= 0),
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
);
```

## 5. Estrutura do projeto

```
projeto_integrador/
├── app.py                # rotas, regras de negócio e validações
├── banco.py              # conexão e criação das tabelas
├── requirements.txt      # dependências (instaladas pelo Vercel)
├── requirements-dev.txt  # dependências de desenvolvimento (pytest)
├── .python-version       # versão do Python usada no Vercel
├── .gitignore / .vercelignore
├── RELATORIO_FINAL.md    # relatório de publicação, testes e falhas
├── README.md             # como rodar e publicar
├── templates/
│   ├── base.html            # layout com menu
│   ├── _mensagens.html      # mensagens de sucesso/erro
│   ├── _macros.html         # etiqueta de preço e situação do estoque
│   ├── login.html
│   ├── cadastro.html
│   ├── painel.html
│   ├── usuarios.html        # lista de usuários
│   ├── produtos.html        # lista + pesquisa
│   ├── produto_form.html    # cadastro e edição
│   └── produto_detalhe.html # visualização dos dados
├── public/static/        # CSS e fontes (servidos pela CDN no Vercel)
│   ├── style.css
│   └── fonts/
├── tests/
│   ├── conftest.py
│   └── test_app.py       # 43 testes automatizados (pytest)
└── docs/documentacao.md
```

O banco `sistema.db` é criado automaticamente: na pasta do projeto ao rodar no computador, e em `/tmp` no Vercel.

## 6. Rotas

| Rota | Método | Descrição | Login |
|---|---|---|---|
| `/cadastro` | GET/POST | Cadastro de usuário | Não |
| `/login` | GET/POST | Login | Não |
| `/logout` | GET | Sair | — |
| `/painel` | GET | Painel inicial | Sim |
| `/usuarios` | GET | Lista de usuários | Sim |
| `/produtos?busca=` | GET | Lista e pesquisa | Sim |
| `/produtos/novo` | GET/POST | Novo produto | Sim |
| `/produtos/<id>` | GET | Detalhes | Sim |
| `/produtos/<id>/editar` | GET/POST | Editar | Sim |
| `/produtos/<id>/excluir` | POST | Excluir | Sim |