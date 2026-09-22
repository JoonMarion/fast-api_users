# Fast API Users

Aplicação full stack para consultar usuários por ID no
[JSONPlaceholder](https://jsonplaceholder.typicode.com/). O backend processa as
consultas de forma assíncrona, limita a concorrência e isola falhas individuais; o
frontend apresenta sucessos e erros parciais em uma interface simples.

**Stack:** Python 3.11, FastAPI, Pydantic, HTTPX, Redis, React, TypeScript e Vite.

```text
React → FastAPI → UserService → CachedUserProvider → Redis / JSONPlaceholder
```

## Executar

Ainda não tem o Docker? Siga o [guia oficial de instalação](https://docs.docker.com/get-started/get-docker/)
para seu sistema operacional.

Com Docker e o plugin Compose instalados, execute na raiz do projeto:

```bash
docker compose up --build
```

Esse comando inicia todo o ambiente: backend, frontend e Redis.

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

O Redis fica acessível apenas na rede interna do Compose e não persiste dados em disco.

Para encerrar:

```bash
docker compose down
```

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
- Redis usa cache-aside por usuário com TTL; indisponibilidade do cache degrada para o
  provider externo sem alterar o contrato da API.
- Logs estruturados em JSON registram consultas, retries e falhas inesperadas.
- O frontend mantém estado local, cliente HTTP e tipos separados, sem dependências de
  UI ou gerenciamento global de estado.

## Qualidade

Os testes usam providers e clientes Redis falsos, além de `httpx.MockTransport`;
nenhuma suíte depende da rede real. A CI executa Ruff, pytest e o build do frontend em
cada `push` e `pull request`.
Para executar as mesmas verificações antes do push:

```bash
python scripts/check.py
```

Não é necessário ativar ou preparar a virtualenv. O próprio script valida os requisitos
e executa o setup na primeira utilização ou quando os arquivos de dependências mudarem.

<details>
<summary><strong>O que o script verifica?</strong></summary>

1. Setup e sincronização das dependências.
2. Lint com `ruff check`.
3. Formatação com `ruff format --check`.
4. Testes do backend com `pytest`.
5. Build do frontend com `npm run build`.

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
| `REDIS_URL` | `redis://localhost:6379/0` |
| `CACHE_TTL_SECONDS` | `300` |
| `CACHE_TIMEOUT_SECONDS` | `0.5` |
| `VITE_API_URL` | URL relativa |

Os exemplos estão em `backend/.env.example` e `frontend/.env.example`.

</details>

## Se precisasse consultar milhares de usuários

A evolução seria incremental: processar IDs em lotes com limites globais de
concorrência, priorizar um endpoint batch do provider e dimensionar o cache Redis já
existente. PostgreSQL seria considerado apenas se surgisse necessidade de persistência
ou rastreabilidade. Trabalhos longos iriam para uma fila com workers, retornando
`job_id` e status por polling, SSE ou webhook. Também seriam considerados circuit
breaker, paginação ou streaming, métricas e centralização dos logs estruturados.

## Limitações atuais

O limite de concorrência é por request e o Compose é voltado ao desenvolvimento local.
O cache não possui persistência, autenticação, prevenção de stampede ou invalidação além
do TTL. Não há banco persistente, circuit breaker, processamento em background,
métricas ou tracing.

## Uso de IA

O Codex, com o modelo GPT-5.6 Sol, foi usado para apoiar revisão de código, análise dos
resultados de lint, testes e build e verificação dos requisitos. As decisões e mudanças
incorporadas ao projeto foram revisadas manualmente.
