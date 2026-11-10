# Relatório Final do Projeto

> Campos marcados com **[preencher]** dependem de dados seus (nome, turma, URL publicada). Complete-os antes de entregar.

## 1. Identificação

| Campo | Informação |
|---|---|
| Nome do projeto | Sistema de Controle de Produtos |
| Aluno | **[preencher]** |
| Turma | **[preencher]** |
| Unidade curricular | UC14 — Projeto Integrador (Encontro 09: Publicação e Validação Final) |
| Data | **[preencher — data da entrega]** |

## 2. Descrição da aplicação

**Objetivo do sistema:** centralizar o cadastro de produtos de uma loja (nome, categoria, preço e quantidade em estoque) em uma aplicação Web simples, com acesso por login, substituindo controles feitos em papel ou em planilhas soltas.

**Público-alvo:** donos e funcionários de pequenas lojas de informática e eletrônicos (categorias Periféricos, Monitores, Acessórios, Hardware e Outros) que precisam consultar e atualizar preços e estoque com rapidez.

**Principais funcionalidades:**

- Cadastro de usuário, login e logout (senhas guardadas como hash).
- Painel com o total de produtos, de unidades em estoque e de usuários.
- Cadastro, listagem, pesquisa (por nome ou categoria), detalhes, edição e exclusão de produtos.
- Produtos agrupados por categoria, com etiqueta de preço e aviso de "últimas unidades" (estoque ≤ 5) ou "esgotado".
- Lista de usuários com a quantidade de produtos cadastrados por cada um.
- Validação dos formulários no navegador (HTML5) e no servidor (Python).

Requisitos, regras de negócio, modelagem do banco e rotas estão detalhados em [`docs/documentacao.md`](docs/documentacao.md).

## 3. Tecnologias utilizadas

| Camada | Tecnologia |
|---|---|
| Frontend | HTML5, CSS3 (layout responsivo), templates Jinja2 |
| Backend | Python 3.12 + Flask 3.1.3 |
| Banco de dados | SQLite (módulo `sqlite3` do Python) |
| Hospedagem | Vercel (função Python serverless + CDN para CSS e fontes) |
| Versionamento | Git e GitHub |
| Testes automatizados | pytest |

## 4. Publicação

| Campo | Informação |
|---|---|
| Plataforma utilizada | Vercel |
| Repositório | **[preencher — https://github.com/seu-usuario/seu-repositorio]** |
| URL da aplicação | **[preencher — https://seu-projeto.vercel.app]** |
| Data da publicação | **[preencher]** |
| Variáveis de ambiente | `SECRET_KEY` (chave que assina o cookie de login) |

### 4.1 Ajustes feitos para hospedar no Vercel

| Arquivo | O que mudou | Por quê |
|---|---|---|
| `requirements.txt` (novo) | Lista `Flask==3.1.3` | O Vercel instala as dependências a partir deste arquivo. Sem ele, o Flask não é instalado. |
| `.python-version` (novo) | `3.12` | Fixa a versão do Python usada pelo Vercel. |
| `static/` → `public/static/` | Pasta movida; `app.py` aponta `static_folder` para ela | O Vercel ignora a pasta `static` do Flask e só publica arquivos estáticos que estão em `public/`. Os endereços continuam sendo `/static/...`, então os templates não mudaram. |
| `banco.py` | Banco em `/tmp/sistema.db` quando roda no Vercel | No Vercel, a pasta do projeto é somente leitura; `/tmp` é a única pasta com permissão de escrita. |
| `app.py` | Lê `SECRET_KEY` da variável de ambiente e avisa se ela faltar | Senhas e chaves não devem ficar no código nem no GitHub. |
| `.gitignore` (novo) | Ignora `.venv/`, `sistema.db`, `__pycache__/`, `.env`, `.vercel` | Evita enviar ambiente virtual, banco local e segredos para o GitHub. |
| `.vercelignore` (novo) | Não envia `tests/`, `.venv` e `sistema.db` | Deixa o pacote publicado menor. |

O Vercel detecta o Flask automaticamente (procura um objeto `app` no arquivo `app.py`), então não foi preciso criar `vercel.json`.

### 4.2 Checklist do ambiente

- [x] O projeto está em um repositório Git, pronto para o GitHub.
- [x] As dependências estão listadas em `requirements.txt`.
- [x] O comando de inicialização é dispensado: o Vercel encontra `app` em `app.py`.
- [x] Arquivos estáticos (CSS e fontes) estão em `public/static/`.
- [x] O banco de dados está preparado para o ambiente (pasta `/tmp`).
- [ ] Variável de ambiente `SECRET_KEY` configurada no painel do Vercel. **[marcar após configurar]**
- [ ] Aplicação acessada pela URL pública. **[marcar após publicar]**

### 4.3 Limitação conhecida: dados temporários no Vercel

O Vercel executa a aplicação como uma função serverless. O arquivo `/tmp/sistema.db` existe apenas enquanto a instância da função está ativa: quando ela fica um tempo sem uso, é reiniciada ou é feito um novo deploy, **o banco volta vazio** (usuários e produtos cadastrados somem). Se o Vercel abrir mais de uma instância ao mesmo tempo, cada uma tem o seu próprio banco.

Para a demonstração isso não atrapalha: basta criar a conta e cadastrar os produtos na hora. O sistema também foi ajustado para não quebrar quando isso acontece: se o cookie de login apontar para um usuário que não existe mais, a sessão é encerrada com a mensagem "Sua sessão expirou. Entre novamente." (falha F07, seção 6). Para guardar os dados de forma permanente, o próximo passo seria trocar o SQLite local por um banco hospedado (veja a seção 7).

## 5. Testes realizados

Os testes foram executados em **09/11/2026** em três ambientes:

1. **Local**, com o cliente de testes do Flask (pytest).
2. **Simulação do Vercel**: servidor rodando com `VERCEL=1`, pasta do projeto somente leitura e um usuário sem permissão de escrita, acessado por requisições HTTP reais.
3. **Build oficial do Vercel** (`vercel build`, Vercel CLI 65.14.0): confirma que o Vercel detecta o Flask, instala as dependências e publica `public/static` na CDN.

Depois da publicação, repita a seção 5.4 diretamente na URL do Vercel.

### 5.1 Testes funcionais

| Nº | Funcionalidade | Ação | Resultado esperado | Resultado obtido | Status |
|---|---|---|---|---|---|
| TF01 | Página inicial | Acessar `/` sem login | Redireciona para a tela de login | Tela "Entrar" exibida | ✅ Aprovado |
| TF02 | Cadastro de usuário | Criar conta com nome, e-mail e senha válidos | Mensagem de sucesso e ida ao login | "Cadastro realizado! Faça login para continuar." | ✅ Aprovado |
| TF03 | Login | Entrar com e-mail e senha corretos | Acesso ao painel | Painel com "Olá, Ana" | ✅ Aprovado |
| TF04 | Login inválido | Entrar com senha errada | Acesso negado com aviso | "Usuário ou senha inválidos." | ✅ Aprovado |
| TF05 | Cadastro de produto | Cadastrar "Teclado mecânico", Periféricos, R$ 299,90, 10 un. | Produto salvo e listado | Produto listado com código PER-0001 | ✅ Aprovado |
| TF06 | Listagem | Abrir a lista com 2 produtos de categorias diferentes | Produtos agrupados por categoria | "2 produtos", faixas Periféricos e Monitores | ✅ Aprovado |
| TF07 | Pesquisa | Pesquisar "mouse" e depois "Monitores" | Só os produtos correspondentes | Filtro por nome e por categoria corretos | ✅ Aprovado |
| TF08 | Consulta (detalhes) | Abrir um produto com R$ 100,00 e 3 un. | Dados completos do produto | Valor em estoque R$ 300,00, "Últimas 3 un.", cadastrado por Ana | ✅ Aprovado |
| TF09 | Edição | Alterar nome, preço e estoque | Dados atualizados | "Produto atualizado com sucesso!" e novo nome exibido | ✅ Aprovado |
| TF10 | Exclusão | Excluir o produto | Produto removido | "Produto excluído." e lista vazia | ✅ Aprovado |
| TF11 | Painel | Abrir o painel com 2 produtos (10 + 5 un.) | Totais corretos | 2 produtos, 15 unidades, 1 usuário | ✅ Aprovado |
| TF12 | Lista de usuários | Abrir "Usuários" | E-mail e contagem de produtos | ana@teste.com com 1 produto | ✅ Aprovado |
| TF13 | Logout | Clicar em "Sair" e tentar abrir o painel | Sessão encerrada | "Você saiu do sistema." e painel bloqueado | ✅ Aprovado |
| TF14 | Layout (CSS e fontes) | Abrir `/static/style.css` e as fontes | Arquivos carregados | HTTP 200 local; publicados na CDN pelo `vercel build` | ✅ Aprovado |

### 5.2 Testes exploratórios

| Nº | O que foi tentado | Resultado esperado | Resultado obtido | Status |
|---|---|---|---|---|
| TE01 | Cadastro com campos vazios, e-mail sem domínio e senha de 3 caracteres | Mensagens de erro, nada salvo | Mensagens exibidas para os 3 casos | ✅ Aprovado |
| TE02 | Cadastrar o mesmo e-mail duas vezes | Bloquear duplicidade | "Este e-mail já está cadastrado." | ✅ Aprovado |
| TE03 | Abrir `/painel`, `/produtos`, `/produtos/novo`, `/usuarios` e `/produtos/1` direto pela URL sem login | Redirecionar ao login | Todas redirecionam para `/login` | ✅ Aprovado |
| TE04 | Produto com nome vazio, nome com 2 letras, categoria fora da lista, preço negativo, preço "abc", estoque negativo, estoque 2,5 | Mensagem de erro em cada caso | Mensagens corretas, nada salvo | ✅ Aprovado |
| TE05 | Preço digitado como `nan`, `inf`, `1e400`, `1e5`, `12,345` e `2000000` (enviado sem passar pelo navegador) | Recusar com mensagem | 1ª rodada: erro 500 e lista quebrada (F04, F05). Após correção: recusados | ✅ Aprovado no reteste |
| TE06 | Estoque com 30 dígitos | Recusar com mensagem | 1ª rodada: erro 500 (F06). Após correção: recusado | ✅ Aprovado no reteste |
| TE07 | Abrir e editar um produto que não existe (`/produtos/999`) | Aviso amigável | "Produto não encontrado." | ✅ Aprovado |
| TE08 | Banco zerado com o usuário ainda logado (o que acontece no Vercel) e tentar cadastrar produto | Pedir novo login | 1ª rodada: erro 500 (F07). Após correção: "Sua sessão expirou. Entre novamente." | ✅ Aprovado no reteste |
| TE09 | Errar um campo do produto | Manter o que já foi digitado | Campos preenchidos continuam no formulário | ✅ Aprovado |
| TE10 | Rodar o app com a pasta do projeto somente leitura (como no Vercel) | App inicia normalmente | 1ª rodada: "unable to open database file" (F01). Após correção: app sobe e grava em `/tmp` | ✅ Aprovado no reteste |

### 5.3 Testes automatizados

Arquivo `tests/test_app.py` com **43 testes em pytest** (14 funcionais, 26 casos exploratórios e 3 de unidade). Para rodar:

```bash
pip install -r requirements-dev.txt
pytest -v
```

| Rodada | Código | Resultado |
|---|---|---|
| 1ª (código original) | antes das correções | 35 aprovados, **8 reprovados** (TE05 ×6, TE06, TE08) |
| 2ª (reteste) | após as correções | **43 aprovados, 0 reprovados** |

Os testes de unidade conferem que a senha é salva como hash (nunca em texto), que os filtros de moeda e código (`R$ 1.234,50`, `MON-0005`) estão corretos e que o preço aceita vírgula decimal.

### 5.4 Roteiro de verificação na URL publicada

Execute no navegador, pela URL do Vercel, e marque o resultado:

| Nº | Verificação | Status |
|---|---|---|
| P01 | A página inicial abre e mostra a tela de login | **[ ]** |
| P02 | O layout (cores, fontes, etiquetas de preço) aparece corretamente | **[ ]** |
| P03 | Criar uma conta e entrar | **[ ]** |
| P04 | Cadastrar 3 produtos de categorias diferentes | **[ ]** |
| P05 | Pesquisar por nome e por categoria | **[ ]** |
| P06 | Abrir os detalhes, editar e excluir um produto | **[ ]** |
| P07 | O painel mostra os totais certos | **[ ]** |
| P08 | Sair e tentar abrir `/painel` pela URL (deve pedir login) | **[ ]** |
| P09 | Abrir no celular (ou no modo responsivo do navegador, F12) | **[ ]** |
| P10 | Abrir em outro navegador | **[ ]** |

## 6. Resultados

| Indicador | Quantidade |
|---|---|
| Testes funcionais | 14 (14 aprovados) |
| Testes exploratórios | 10 (10 aprovados após correções) |
| Testes automatizados | 43 (43 aprovados no reteste) |
| Falhas encontradas | 8 |
| Falhas corrigidas | 8 |

### 6.1 Falhas encontradas e correções realizadas

| Nº | Falha | Tipo | Causa | Correção | Reteste |
|---|---|---|---|---|---|
| F01 | App não inicia no Vercel: `sqlite3.OperationalError: unable to open database file` | Configuração da hospedagem / caminho de arquivo | O banco era criado na pasta do projeto, que é somente leitura no Vercel | `banco.py` usa `/tmp/sistema.db` quando a variável `VERCEL` existe | TE10 ✅ |
| F02 | Dependências não seriam instaladas no Vercel | Dependência não instalada | Faltava `requirements.txt` | Criado `requirements.txt` com `Flask==3.1.3` | `vercel build` instalou o Flask ✅ |
| F03 | Página sem CSS e sem fontes no Vercel | Caminho de arquivos | O Vercel ignora a pasta `static` do Flask | Pasta movida para `public/static/` e `static_folder` ajustado | TF14 e `vercel build` ✅ |
| F04 | Preço `nan` causava erro 500 | Validação de formulário | `float("nan")` passava na validação e o banco recusava o valor | Preço validado com o mesmo padrão do formulário (números com até 2 casas decimais) | TE05 ✅ |
| F05 | Preço `inf` ou `1e400` era salvo e **quebrava a lista de produtos para todos** | Validação de formulário | Valor infinito não pode ser formatado como R$ | Mesmo padrão de F04 + preço máximo de R$ 1.000.000,00 | TE05 ✅ |
| F06 | Estoque com muitos dígitos causava erro 500 (`OverflowError`) | Validação de formulário | Número maior do que o SQLite suporta | Estoque máximo de 1.000.000 unidades (servidor e campo `max` no HTML) | TE06 ✅ |
| F07 | Erro 500 ao cadastrar produto depois que o banco é zerado | Erro no código Python | O cookie de login apontava para um usuário que não existia mais (chave estrangeira) | `login_obrigatorio` confere se o usuário ainda existe; se não, encerra a sessão | TE08 ✅ |
| F08 | Depois de um erro, gravações seguintes falhavam com "database is locked" | Conexão com o banco | Quando ocorria um erro, a conexão ficava aberta e travava o arquivo | As conexões passaram a ser fechadas automaticamente no fim de cada requisição (`teardown_appcontext`) | TE05 ✅ |

Após cada correção, **todos** os testes foram executados de novo (não só o da falha), para garantir que nada mais foi afetado.

## 7. Considerações finais

**Dificuldades encontradas**

- Entender que o Vercel não é um servidor comum: a aplicação roda como função serverless, sem pasta com permissão de escrita (exceto `/tmp`) e sem servir a pasta `static` do Flask.
- O SQLite guarda os dados em arquivo, e no Vercel esse arquivo é temporário.
- Os testes exploratórios mostraram que a validação no navegador não basta: enviando os dados sem passar pelo formulário, valores como `nan` e `inf` derrubavam o sistema.

**Soluções aplicadas**

- Ajustes de hospedagem (`requirements.txt`, `public/static`, banco em `/tmp`, `SECRET_KEY` como variável de ambiente), validados com o `vercel build` oficial.
- Validação no servidor igual à do navegador, com limites de preço e estoque.
- Tratamento da sessão quando o usuário não existe mais e fechamento automático das conexões.
- 43 testes automatizados para repetir todas as verificações a cada mudança.

**Melhorias futuras**

- Trocar o SQLite local por um banco hospedado (por exemplo, Postgres pelo Marketplace do Vercel, ou Turso, que é compatível com SQLite) para os dados não se perderem.
- Recuperação de senha e perfis de acesso (administrador e usuário), que ficaram fora do escopo.
- Rodar os testes automaticamente a cada push (GitHub Actions).

**Conclusão**

A aplicação foi revisada, adaptada e preparada para publicação no Vercel, testada com 14 testes funcionais, 10 exploratórios e 43 automatizados, e as 8 falhas encontradas foram corrigidas e retestadas. O sistema atende às funcionalidades propostas. A limitação de dados temporários do SQLite no Vercel está registrada, junto com o caminho para resolvê-la.

---

## Apêndice: roteiro da apresentação técnica

1. **Nome e objetivo:** Sistema de Controle de Produtos, cadastro de preços e estoque de uma loja.
2. **Problema:** controle de preços e estoque espalhado em papel e planilhas.
3. **Tecnologias:** Python, Flask, Jinja2, HTML, CSS, SQLite, Vercel, GitHub e pytest.
4. **Aplicação publicada:** abrir a URL do Vercel no navegador.
5. **Funcionalidades:** criar conta, entrar, cadastrar 2 ou 3 produtos, pesquisar, ver detalhes, editar, excluir, painel e usuários.
6. **Testes:** mostrar as tabelas da seção 5 e rodar `pytest -v` no terminal (43 aprovados).
7. **Falhas e soluções:** destacar F01 (o app nem iniciava no Vercel), F05 (`inf` quebrava a lista) e F07 (sessão após o banco zerar).
8. **Considerações finais:** limitação do SQLite no Vercel e melhorias futuras.
