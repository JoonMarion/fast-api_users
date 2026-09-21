# Fast API Users

Aplicação pequena com backend FastAPI e frontend React para consultar usuários por ID
no JSONPlaceholder. As consultas são assíncronas, têm concorrência limitada e isolam a
falha de cada usuário.

## Executar com Docker (recomendado)

### Requisitos

- Docker Engine com o plugin Docker Compose;
- acesso ao Docker Hub, PyPI e registro npm para construir as imagens;
- acesso ao provider configurado.

O provider é a API externa consultada pelo backend. Por padrão, é o JSONPlaceholder e
não exige conta ou token; os containers precisam apenas conseguir acessar
`https://jsonplaceholder.typicode.com`.

<details>
<summary><strong>Instalar e validar o Docker</strong></summary>

O Docker Engine executa os containers. O plugin Compose fornece o comando
`docker compose`, responsável por iniciar backend e frontend juntos.

**Windows**

1. Instale o [Docker Desktop para Windows](https://docs.docker.com/desktop/setup/install/windows-install/).
2. Durante a instalação, mantenha a opção de WSL 2 recomendada pelo instalador.
3. Inicie o Docker Desktop e aguarde até o serviço ficar disponível.

**macOS**

1. Instale o [Docker Desktop para macOS](https://docs.docker.com/desktop/setup/install/mac-install/)
   correspondente ao processador Intel ou Apple Silicon.
2. Inicie o Docker pela pasta Applications.

**Linux**

1. Instale o [Docker Engine](https://docs.docker.com/engine/install/) seguindo as
   instruções da sua distribuição.
2. Instale o [plugin Docker Compose](https://docs.docker.com/compose/install/linux/).

Confirme a instalação:

```bash
docker --version
docker compose version
docker run --rm hello-world
```

O Docker Desktop já inclui Docker Engine, Docker CLI e Docker Compose. No Linux, esses
componentes podem ser instalados separadamente.

</details>

### Iniciar a aplicação

Na raiz do projeto, execute:

```bash
docker compose up --build
```

O backend ficará disponível em `http://localhost:8000` e o frontend em
`http://localhost:5173`. Para encerrar e remover os containers:

```bash
docker compose down
```

As configurações do backend e `VITE_API_URL` podem ser sobrescritas por variáveis do
ambiente antes de executar o Compose; caso não sejam informadas, os valores padrão da
aplicação serão utilizados.

## Executar sem Docker (alternativa)

### Requisitos

- Python 3.11 ou superior;
- Node.js 20.19+ ou 22.12+;
- npm;
- acesso ao PyPI, registro npm e provider configurado.

<details>
<summary><strong>Instalar e validar os requisitos locais</strong></summary>

1. Instale o [Python](https://www.python.org/downloads/) 3.11 ou superior.
2. Instale uma versão compatível do [Node.js](https://nodejs.org/en/download); o npm é
   incluído na instalação do Node.js.
3. Confirme as versões:

```bash
python --version
node --version
npm --version
```

No Linux ou macOS, o comando do Python pode ser `python3`.

</details>

### Setup automatizado

Na raiz do projeto, execute:

```bash
python scripts/setup.py
```

No Linux ou macOS, use `python3` caso `python` não esteja disponível. O script valida os
requisitos, cria `backend/.venv`, preserva arquivos de ambiente existentes e instala as
dependências do backend e do frontend.

Depois do setup, em outro terminal, execute:

```bash
python scripts/run.py
```

O backend ficará disponível em `http://localhost:8000` e o frontend em
`http://localhost:5173`. Os dois processos são encerrados com `Ctrl+C`.

Para apenas validar os requisitos, sem instalar nada:

```bash
python scripts/setup.py --check-only
```

Se o provider estiver temporariamente indisponível, use `--skip-provider-check` para
ignorar somente essa verificação.

<details>
<summary><strong>Instalação e execução manual</strong></summary>

#### Backend

```bash
cd backend
python -m venv .venv
```

Ative o ambiente virtual:

```powershell
# Windows PowerShell
.venv\Scripts\Activate.ps1
```

```bash
# Linux/macOS
source .venv/bin/activate
```

Instale as dependências e inicie a API:

```bash
python -m pip install -e ".[dev]"
cp .env.example .env
uvicorn app.main:app --reload --port 8000
```

No PowerShell, use `Copy-Item .env.example .env` no lugar de `cp`.
A documentação interativa ficará em `http://localhost:8000/docs`.

#### Frontend

Em outro terminal:

```bash
cd frontend
npm ci
cp .env.example .env.local
npm run dev
```

No PowerShell, use `Copy-Item .env.example .env.local` no lugar de `cp`.
Para validar a compilação de produção, execute `npm run build`.

</details>

## Variáveis de ambiente

Cada projeto mantém sua própria configuração:

- `backend/.env`: configuração local do FastAPI;
- `frontend/.env.local`: configuração local carregada pelo Vite;
- os respectivos `.env.example` documentam os valores esperados e podem ser versionados.

Os arquivos locais são ignorados pelo Git. Variáveis definidas no ambiente do processo
têm prioridade sobre os valores de `backend/.env`.

### Backend

| Variável | Padrão | Finalidade |
| --- | --- | --- |
| `PROVIDER_TIMEOUT_SECONDS` | `5` | Timeout das chamadas ao provider |
| `MAX_CONCURRENCY` | `10` | Máximo de consultas simultâneas por request |
| `PROVIDER_BASE_URL` | `https://jsonplaceholder.typicode.com` | URL base do provider |
| `FRONTEND_ORIGIN` | `http://localhost:5173` | Única origem liberada pelo CORS |

### Frontend

| Variável | Padrão | Finalidade |
| --- | --- | --- |
| `VITE_API_URL` | URL relativa | URL do backend usada pelo frontend |

Configuração local recomendada em `frontend/.env.local`:

```env
VITE_API_URL=http://localhost:8000
```

## API

`POST /api/users/fetch`

Request:

```json
{
  "user_ids": [1, 2, 999]
}
```

Response `200`:

```json
{
  "users": [
    { "id": 1, "name": "Leanne Graham" },
    { "id": 2, "name": "Ervin Howell" }
  ],
  "failed": [999],
  "errors": [
    { "id": 999, "reason": "not_found" }
  ]
}
```

A entrada aceita de 1 a 100 IDs inteiros positivos. IDs repetidos são removidos após a
validação, preservando a primeira ocorrência. Entrada inválida retorna `422`; falhas
individuais retornam `200` com motivo `not_found`, `timeout` ou `provider_error`.

## Qualidade e testes

Dentro de `backend`, com o ambiente virtual ativo:

```bash
ruff format .
ruff check .
ruff format --check .
pytest
```

Os testes usam provider fake e `httpx.MockTransport`; não acessam a rede real.

## Decisões técnicas

- O provider implementa um `Protocol`, mantendo o service independente de HTTPX e da
  implementação JSONPlaceholder.
- Um único `httpx.AsyncClient` é criado e fechado pelo lifespan do FastAPI.
- O provider repete até duas vezes falhas transitórias, usando backoff exponencial com
  jitter e respeitando `Retry-After` em respostas `429`.
- Os eventos da aplicação são escritos como JSON pela biblioteca padrão, incluindo
  contexto de retries, resultado das consultas e exceções inesperadas.
- O service usa `asyncio.gather` e um semáforo por request; uma falha não cancela as
  demais consultas e a ordem de entrada é preservada.
- Pydantic concentra validação, deduplicação e o contrato público mínimo de usuário.
- A dependência do service pode ser substituída nos testes da rota.
- O frontend usa um único componente, tipos explícitos e CSS simples, sem biblioteca de
  estado ou componentes visuais.

## Uso de IA

Utilizei apenas o Codex, com o modelo GPT-5.6 Sol, para apoiar a revisão do código, a
análise dos resultados de lint, testes e build e a verificação de aderência aos
requisitos do desafio. As análises, recomendações e conclusões foram revisadas
manualmente antes de serem incorporadas ao projeto.

## Limitações e melhorias futuras

A aplicação depende da disponibilidade do provider, espera todas as consultas antes de
responder e limita cada request a 100 posições. Não possui autenticação, persistência,
cache, circuit breaker ou processamento em background. Também não possui métricas,
tracing ou centralização dos logs estruturados. O retry é limitado a duas novas
tentativas por consulta e não substitui um circuit breaker.
O Docker Compose fornecido é voltado apenas à execução local; não há configuração de
deploy.

### Se precisasse consultar milhares de usuários

Esta seria uma evolução de arquitetura, não uma ampliação direta do limite atual:

1. Processaria IDs em lotes, mantendo controle explícito de concorrência e limites
   globais para proteger a aplicação e o provider.
2. Preferiria um endpoint batch do provider, caso disponível, reduzindo conexões e
   overhead por usuário.
3. Usaria Redis para cache temporário e PostgreSQL quando fosse necessária persistência
   e rastreabilidade dos resultados.
4. Ajustaria os limites do retry existente conforme métricas do provider e adicionaria
   circuit breaker para falhas persistentes.
5. Para trabalhos longos, usaria fila e workers: a API retornaria um `job_id`, com
   consulta de status e, se necessário, atualização por SSE ou webhook.
6. Entregaria resultados por paginação ou streaming para evitar respostas muito grandes.
7. Adicionaria métricas de latência, erro, fila e cache e centralizaria os logs
   estruturados, com correlação por request e job.
