# Fast API Users

Aplicação full stack para consultar usuários por ID no
[JSONPlaceholder](https://jsonplaceholder.typicode.com/). O backend processa as
consultas de forma assíncrona, limita a concorrência e isola falhas individuais; o
frontend apresenta sucessos e erros parciais em uma interface simples.

**Stack:** Python 3.11, FastAPI, Pydantic, HTTPX, React, TypeScript e Vite.

```text
React → FastAPI → UserService → UserProvider → JSONPlaceholder
```

## Executar

Ainda não tem o Docker? Siga o [guia oficial de instalação](https://docs.docker.com/get-started/get-docker/)
para seu sistema operacional.

Com Docker e o plugin Compose instalados, execute na raiz do projeto:

```bash
docker compose up --build
```

Use `--build` na primeira execução e depois de alterar código, dependências ou algum
`Dockerfile`. Para apenas iniciar novamente sem mudanças, basta:

```bash
docker compose up
```

O `--build` reconstrói as mesmas imagens e reaproveita o cache; ele não cria uma nova
imagem nomeada a cada execução.

- Frontend: http://localhost:5173
- API: http://localhost:8000
- Swagger: http://localhost:8000/docs

Para encerrar:

```bash
docker compose down
```

<details>
<summary><strong>Executar localmente sem Docker</strong></summary>

### Requisitos

- Python 3.11+
- Node.js 20.19+ ou 22.12+
- npm

### Setup automático

Na raiz do projeto:

```bash
python scripts/setup.py
python scripts/run.py
```

O setup valida os requisitos, cria `backend/.venv`, configura os arquivos de ambiente
e instala as dependências. Use `python3` no lugar de `python` quando necessário.

### Setup manual

Backend:

```bash
cd backend
python -m venv .venv
```

Ative o ambiente virtual com `.venv\Scripts\Activate.ps1` no PowerShell ou
`source .venv/bin/activate` no Linux/macOS. Depois:

```bash
python -m pip install -e ".[dev]"
uvicorn app.main:app --reload --port 8000
```

Frontend, em outro terminal:

```bash
cd frontend
npm ci
npm run dev
```

</details>

## API

`POST /api/users/fetch`

```json
{
  "user_ids": [1, 2, 999]
}
```

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

A API aceita de 1 a 100 IDs inteiros positivos. IDs repetidos são removidos sem
alterar a ordem. Entrada inválida retorna `422`; falhas individuais retornam `200` com
motivo `not_found`, `timeout` ou `provider_error`.

## Decisões técnicas

- `UserProvider` isola a integração externa e mantém o service independente de HTTPX.
- Um único `httpx.AsyncClient` é compartilhado durante o ciclo de vida da aplicação.
- `asyncio.gather` e `asyncio.Semaphore` permitem concorrência controlada sem perder a
  ordem dos resultados.
- Retry seletivo usa backoff exponencial com jitter e respeita `Retry-After` em `429`.
- Logs estruturados em JSON registram consultas, retries e falhas inesperadas.
- O frontend mantém estado local, cliente HTTP e tipos separados, sem dependências de
  UI ou gerenciamento global de estado.

## Qualidade

Os testes usam providers falsos e `httpx.MockTransport`; nenhuma suíte depende da rede
real. A CI executa Ruff, pytest e o build do frontend em cada `push` e `pull request`.
Para executar as mesmas verificações antes do push:

```bash
python scripts/check.py
```

Não é necessário ativar a virtualenv: o script usa automaticamente o Python de
`backend/.venv`. Antes da primeira execução, rode `python scripts/setup.py` para criar
o ambiente e instalar as dependências do backend e do frontend.

<details>
<summary><strong>O que o script verifica?</strong></summary>

1. Lint com `ruff check`.
2. Formatação com `ruff format --check`.
3. Testes do backend com `pytest`.
4. Build do frontend com `npm run build`.

As etapas são executadas em sequência e o script interrompe no primeiro erro.

</details>

<details>
<summary><strong>Configuração</strong></summary>

| Variável | Padrão |
| --- | --- |
| `PROVIDER_TIMEOUT_SECONDS` | `5` |
| `MAX_CONCURRENCY` | `10` |
| `PROVIDER_BASE_URL` | `https://jsonplaceholder.typicode.com` |
| `FRONTEND_ORIGIN` | `http://localhost:5173` |
| `VITE_API_URL` | URL relativa |

Os exemplos estão em `backend/.env.example` e `frontend/.env.example`.

</details>

## Se precisasse consultar milhares de usuários

A evolução seria incremental: processar IDs em lotes com limites globais de
concorrência, priorizar um endpoint batch do provider e usar Redis ou PostgreSQL apenas
quando cache, persistência ou rastreabilidade fossem necessários. Trabalhos longos
iriam para uma fila com workers, retornando `job_id` e status por polling, SSE ou
webhook. Também seriam considerados circuit breaker, paginação ou streaming, métricas
e centralização dos logs estruturados.

## Limitações atuais

O limite de concorrência é por request, o Compose é voltado ao desenvolvimento local e
não há autenticação, cache, persistência, circuit breaker, processamento em background,
métricas ou tracing.

## Uso de IA

O Codex, com o modelo GPT-5.6 Sol, foi usado para apoiar revisão de código, análise dos
resultados de lint, testes e build e verificação dos requisitos. As decisões e mudanças
incorporadas ao projeto foram revisadas manualmente.
