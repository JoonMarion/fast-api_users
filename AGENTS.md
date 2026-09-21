# AGENTS.md

Instruções para agentes de IA (Codex, Cursor) neste repositório.
Leia este arquivo inteiro antes de qualquer tarefa.

## 1. Contexto

Aplicação pequena: backend em **Python/FastAPI** e frontend em **React + TypeScript**
que consulta usuários por ID em uma API HTTP externa, de forma assíncrona e resiliente.

O que está sendo prioridade é **julgamento técnico**, não volume de código.
Prefira sempre a solução **menor, mais simples e mais legível** que atenda ao requisito.

## 2. Stack

- Backend: Python 3.11+, FastAPI, Pydantic v2, httpx (AsyncClient), uvicorn
- Testes: pytest, pytest-asyncio (ou anyio), FastAPI TestClient / httpx.AsyncClient
- Lint/format: ruff
- Frontend: React + TypeScript + Vite, HTML e CSS simples
- Provider externo padrão: JSONPlaceholder (`https://jsonplaceholder.typicode.com/users/{id}`)

As dependências listadas nesta stack estão previamente aprovadas para o setup inicial.
Não adicione outras dependências sem justificar e pedir confirmação.

## 3. Estrutura do projeto

```
/backend
  app/
    main.py                  # criação do app, lifespan, CORS
    config.py                # timeout, concorrência, base_url, max ids
    schemas.py               # Pydantic: request/response
    api/routes.py            # POST /api/users/fetch
    services/user_service.py # regra de negócio (orquestração)
    providers/base.py        # Protocol UserProvider + exceções de domínio
    providers/jsonplaceholder.py
  tests/
  pyproject.toml
/frontend
  src/ (App.tsx, api.ts, types.ts, styles.css)
README.md
AGENTS.md
```

Só crie novas camadas ou pastas quando houver benefício concreto para separação de
responsabilidades, testabilidade ou troca do provider.

## 4. Contrato da API

`POST /api/users/fetch`

Request:

```json
{ "user_ids": [1, 2, 3, 4] }
```

Response (200):

```json
{
  "users": [
    { "id": 1, "name": "Leanne Graham" },
    { "id": 2, "name": "Ervin Howell" }
  ],
  "failed": [3, 4],
  "errors": [
    { "id": 3, "reason": "not_found" },
    { "id": 4, "reason": "provider_error" }
  ]
}
```

- `reason` é um dos valores: `not_found`, `timeout`, `provider_error`.
- O modelo público `User` contém apenas `id: int` e `name: str`; dados adicionais do
  provider não devem vazar para o contrato da API.
- `users`, `failed` e `errors` devem preservar a ordem dos IDs deduplicados recebidos.
- `failed` deve conter exatamente os mesmos IDs, na mesma ordem, de `errors`.
- Entrada inválida retorna **422** (validação padrão do FastAPI/Pydantic).
- Falhas individuais de usuário **nunca** viram 5xx: a resposta é 200 com o ID em `failed`.

## 5. Regras do backend

**Validação (Pydantic)**
- `user_ids`: lista não vazia, inteiros positivos, máximo 100 itens por request.
- O limite de 100 considera a lista recebida antes da deduplicação.
- Depois da validação, deduplicar IDs preservando a primeira ocorrência e a ordem.

**Provider**
- Definir `UserProvider` como `Protocol` com `async def get_user(self, user_id: int) -> User`.
- Exceções de domínio em `providers/base.py`: `UserNotFound`, `ProviderTimeout`, `ProviderError`.
- Traduzir erros do `httpx` (404, timeout, erros HTTP, erros de rede) para essas exceções
  **dentro do provider**. O service não pode importar `httpx`.
- Mapear `404` para `UserNotFound`, timeout para `ProviderTimeout` e demais status HTTP,
  erros de rede ou payload inválido para `ProviderError`.
- Usar um único `httpx.AsyncClient` compartilhado, criado e fechado no `lifespan` do FastAPI,
  com timeout explícito vindo de `config.py`. Nunca criar um client por request.
- Trocar de provider deve exigir apenas uma nova classe que implemente o Protocol
  e a troca na injeção de dependência.

**Service**
- Depende apenas de `UserProvider` (injetado), nunca de uma implementação concreta.
- Executar consultas com `asyncio.gather`, com wrapper por tarefa que captura as exceções
  de domínio e retorna sucesso ou falha. Uma falha nunca interrompe as demais.
- Limitar a concorrência de cada chamada ao service com `asyncio.Semaphore`
  (valor em `config.py`, padrão 10).
- Manter a ordem original dos IDs deduplicados na resposta.
- Não engolir exceções inesperadas em silêncio: registrar em log e tratar como `provider_error`.

**Config**
- Manter o limite de 100 IDs como constante do contrato.
- `PROVIDER_TIMEOUT_SECONDS` (padrão 5), `MAX_CONCURRENCY` (padrão 10),
  `PROVIDER_BASE_URL` e `FRONTEND_ORIGIN` devem ser sobrescrevíveis por variável de ambiente.
- Preferir a biblioteca padrão para ler o ambiente; não adicionar uma dependência apenas
  para configuração deste projeto pequeno.

**CORS**
- Liberar apenas `FRONTEND_ORIGIN` (padrão `http://localhost:5173`).

## 6. Regras do frontend

- Um componente principal (`App.tsx`) com estados `loading`, `error` e `result` é suficiente.
- Entrada de IDs separados por vírgula ou espaço. Validar no cliente:
  ignorar vazios, avisar sobre valores não numéricos ou não positivos.
- Desabilitar o botão durante o loading.
- Exibir: loading, usuários encontrados, IDs que falharam (com o motivo, se disponível)
  e erro do backend (rede fora do ar ou resposta não-2xx) com mensagem legível.
- `types.ts` espelha o response do backend. Sem `any`.
- Sem biblioteca de UI. CSS simples.
- Chamada ao backend isolada em `api.ts`, com URL base configurável (`VITE_API_URL` ou proxy do Vite).

## 7. Testes

- **Nunca** chamar a rede real nos testes. Usar fake provider injetado (preferido) ou `respx`.
- Preferir o fake provider; não adicionar `respx` somente para os testes obrigatórios.
- Obrigatórios:
  1. Consulta com sucesso (todos os IDs retornam em `users`, `failed` vazio).
  2. Falha de um usuário sem interromper os demais (ex.: fake lança erro para o ID 3;
     os outros ficam em `users` e o 3 aparece em `failed`).
- Desejáveis (baratos): timeout, usuário não encontrado, IDs duplicados, validação 422.
- Cada teste deve exercitar comportamento real. Não mockar o que deveria ser testado.

## 8. Fora de escopo (NÃO fazer)

Kubernetes, Kafka, Celery/filas, CQRS, Event Sourcing, microsserviços, Terraform, autenticação,
deploy, cloud, ORMs ou banco de dados, cache no código, bibliotecas de UI, gerenciadores
de estado (Redux etc.) e qualquer coisa "production-ready" além do pedido.
PostgreSQL, cache e filas devem aparecer **apenas como sugestão de evolução no README**.

## 9. Próxima etapa: aplicar os diferenciais

O núcleo da aplicação já está funcionando, testado e commitado. Embora estes itens
continuem opcionais no enunciado original, eles passam a compor o escopo ativo de
evolução deste repositório.

Implementar em etapas pequenas, seguindo esta ordem de prioridade:

1. [x] Controle explícito de concorrência com `asyncio.Semaphore`.
2. [x] Docker Compose para iniciar backend e frontend com um comando, validado com build
   e execução local dos dois serviços.
3. [x] Retry com backoff + jitter e tratamento de `429`/`Retry-After`, exclusivamente
   dentro do provider.
4. [x] Logging estruturado, mantendo a solução simples e sem adicionar plataforma de
   observabilidade externa.
5. [x] CI simples executando Ruff, pytest e o build do frontend.

Cada diferencial deve ser implementado e verificado isoladamente antes do próximo.
Continuam fora de escopo implementações de PostgreSQL, cache, filas ou infraestrutura
cloud; esses itens permanecem apenas como sugestões de evolução no README.

## 10. Padrões de código

- Type hints em todo o backend. `async/await` corretos, sem `requests` ou I/O bloqueante em função async.
- Nomes claros em inglês no código; comentários só quando explicam o "porquê".
- Funções pequenas, sem código morto, sem `print` de debug, sem `except Exception: pass`.
- Sem segredos no repositório. Fornecer `.env.example` se houver variáveis.
- Rodar `ruff check` e `ruff format` antes de finalizar uma tarefa.

## 11. Como trabalhar (fluxo do agente)

- Trabalhe em **etapas pequenas** e pare para revisão ao fim de cada uma:
  0. setup mínimo: estrutura, `__init__.py`, `pyproject.toml`, Ruff, pytest,
     Vite React + TypeScript, `.gitignore` e `.env.example`
  1. config + schemas + provider
  2. service
  3. rota + lifespan + CORS
  4. testes
  5. frontend
  6. README
- Antes de codar uma etapa, resuma em poucas linhas o que vai fazer.
- Não altere arquivos fora do escopo da etapa atual.
- Ao fim de cada etapa, execute as verificações aplicáveis naquele momento.
- Depois de criar os testes, execute `ruff check`, `ruff format --check` e `pytest` a cada
  alteração relevante no backend. Para o frontend, execute `npm run build`.
- Não declare "pronto" sem executar todas as verificações aplicáveis e informar o resultado.
- Se algo estiver ambíguo, escolha a opção mais simples, registre a decisão e siga.

## 12. README (entregável)

Deve ser curto e honesto, cobrindo:
1. Como executar o projeto (backend, frontend, testes).
2. Principais decisões técnicas.
3. O que melhoraria com mais tempo.
4. Uso de IA: quais ferramentas (Codex, Cursor) e para quê, indicando o que foi revisado manualmente.
5. Resposta à pergunta: "Se esta aplicação precisasse consultar milhares de usuários, o que você mudaria?"
   Pontos: processar em lotes e limitar concorrência; usar endpoint batch do provider, se existir;
   cache (Redis) e persistência (PostgreSQL); retry com backoff + jitter, respeitando `429`/`Retry-After`,
   e circuit breaker; processamento em background (fila + worker) com `job_id` e consulta de status
   ou SSE/webhook; paginação/streaming da resposta; métricas e logs estruturados.

## 13. Definição de pronto do núcleo

Esta checklist valida a entrega obrigatória original. Para considerar concluída a etapa
de evolução atual, também é necessário concluir os itens pendentes da seção 9.

- [x] Endpoint validando entrada e retornando `users` e `failed` separados
- [x] Falha, not found, erro HTTP e timeout de um usuário não afetam os demais
- [x] Provider isolado atrás de interface, trocável sem mexer no service
- [x] Testes passando (mínimo os dois obrigatórios), sem rede real
- [x] Frontend com loading, sucesso, falhados e erro do backend
- [x] `ruff` limpo
- [x] README completo e coerente com o código
- [x] Nada fora do escopo foi adicionado
