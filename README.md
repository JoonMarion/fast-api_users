# Fast API Users

Aplicação pequena com backend FastAPI e frontend React para consultar usuários por ID
no JSONPlaceholder. As consultas são assíncronas, têm concorrência limitada e isolam a
falha de cada usuário.

## Requisitos

- Python 3.11 ou superior
- Node.js 20.19+ ou 22.12+
- npm
- Acesso ao PyPI e ao registro npm para baixar as dependências
- Acesso ao provider configurado (por padrão, JSONPlaceholder)

## Instalação e execução

### Setup automatizado

Na raiz do projeto, execute:

```bash
python scripts/setup.py
```

No Linux ou macOS, use `python3` em todos os comandos desta seção caso `python` não esteja
disponível. O script valida as versões do Python e do Node.js, a presença do npm e o
acesso ao provider antes de alterar o projeto. Em seguida, ele cria `backend/.venv`,
preserva arquivos de ambiente existentes, instala as dependências do backend e executa
`npm ci` no frontend.

Para apenas validar os requisitos, sem criar ou instalar nada:

```bash
python scripts/setup.py --check-only
```

Em ambientes temporariamente sem acesso ao provider, a verificação de conectividade pode
ser ignorada explicitamente com `--skip-provider-check`.

Depois do setup, inicie backend e frontend juntos, a partir da raiz do projeto:

```bash
python scripts/run.py
```

O setup apenas prepara o ambiente e encerra mostrando um resumo; ele não inicia serviços
automaticamente. Execute o comando acima em outro terminal para manter instalação e
execução como etapas explícitas.

O backend ficará disponível em `http://localhost:8000` e o frontend em
`http://localhost:5173`. Os dois processos permanecem no mesmo terminal e são encerrados
com `Ctrl+C`.

As etapas abaixo descrevem o processo manual equivalente.

### Backend

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

### Frontend

Em outro terminal:

```bash
cd frontend
npm ci
cp .env.example .env.local
npm run dev
```

No PowerShell, use `Copy-Item .env.example .env.local` no lugar de `cp`.

O Vite usa `http://localhost:5173` por padrão. Para validar a compilação de produção,
execute `npm run build`.

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
cache, retry, circuit breaker, processamento em background ou observabilidade avançada.
Também não inclui configuração de deploy ou containers.

### Se precisasse consultar milhares de usuários

Esta seria uma evolução de arquitetura, não uma ampliação direta do limite atual:

1. Processaria IDs em lotes, mantendo controle explícito de concorrência e limites
   globais para proteger a aplicação e o provider.
2. Preferiria um endpoint batch do provider, caso disponível, reduzindo conexões e
   overhead por usuário.
3. Usaria Redis para cache temporário e PostgreSQL quando fosse necessária persistência
   e rastreabilidade dos resultados.
4. Adicionaria retry com backoff exponencial e jitter, respeitando `429` e
   `Retry-After`, além de circuit breaker para falhas persistentes.
5. Para trabalhos longos, usaria fila e workers: a API retornaria um `job_id`, com
   consulta de status e, se necessário, atualização por SSE ou webhook.
6. Entregaria resultados por paginação ou streaming para evitar respostas muito grandes.
7. Adicionaria métricas de latência, erro, fila e cache, além de logs estruturados com
   correlação por request e job.
