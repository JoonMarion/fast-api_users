# CONTEXT.md

## Como usar este documento

Este arquivo é **contexto de referência** para agentes de IA (Codex, Cursor, Claude etc.) e para o refinamento de prompts neste repositório. Ele reúne, **sem alterações no texto original**, dois materiais do processo seletivo:

1. **A descrição da vaga**: explica quem é o profissional buscado, quais competências são valorizadas e como o contratante avalia o perfil.
2. **O desafio técnico prático (segunda fase)**: é o enunciado oficial do que deve ser entregue: requisitos, entregáveis, diferenciais opcionais e limites de escopo.

**Papel deste documento em relação ao `AGENTS.md`:**

- Este arquivo é a **fonte da verdade dos requisitos** (o "o quê" e o "porquê").
- O `AGENTS.md` define **como implementar** (stack, estrutura, regras de código, fluxo de trabalho).
- Se houver conflito sobre *o que entregar*, prevalece este documento. Se houver conflito sobre *como implementar*, prevalece o `AGENTS.md`, desde que os requisitos do enunciado continuem atendidos.

**Como usar ao escrever ou refinar prompts:**

- Use a Parte 1 para calibrar o nível de senioridade, o tom e as prioridades (qualidade de código, autonomia, julgamento técnico, uso de IA).
- Use a Parte 2 para checar se cada prompt e cada entrega cobrem os requisitos obrigatórios e respeitam os limites do desafio.
- Ao propor algo novo, verifique se não cai na lista "Limites do desafio" (o que **não** é exigido).

---

# PARTE 1: Descrição da vaga

> **O que esta parte descreve:** o anúncio da vaga para a qual o desafio foi proposto. Serve para entender o perfil-alvo (Desenvolvedor Fullstack Pleno Python), as tecnologias esperadas, o modelo de contratação e o que o contratante valoriza. Não é uma lista de tarefas de implementação; é o contexto do "quem está avaliando e o que procura".

Procuramos Desenvolvedor Fullstack Pleno Python para atuar em projeto de grande cliente.

Procuramos um profissional com boa base técnica, autonomia no dia a dia e capacidade de participar ativamente da construção de soluções de software escaláveis e bem estruturadas.

## Responsabilidades

> *Descreve o que a pessoa contratada faria no dia a dia.*

- Desenvolver, manter e evoluir aplicações e ferramentas de software;
- Atuar tanto no back-end quanto no front-end dos projetos;
- Desenvolver APIs, integrações e funcionalidades utilizando Python;
- Participar da definição e implementação de soluções técnicas;
- Garantir código limpo, organizado e de fácil manutenção;
- Trabalhar em conjunto com time técnico, liderança e demais áreas envolvidas no projeto.

## Requisitos obrigatórios

> *Descreve as competências mínimas exigidas. O desafio técnico é uma forma de demonstrar várias delas na prática.*

- Experiência como Desenvolvedor(a) Full Stack Pleno;
- Experiência sólida com Python;
- Experiência com desenvolvimento de aplicações de software;
- Conhecimento de APIs e integrações;
- Experiência com bancos de dados relacionais;
- Conhecimento de front-end moderno, preferencialmente React e TypeScript;
- Vivência com automações, LLMs ou soluções utilizando Inteligência Artificial;
- Boa organização, autonomia e senso de responsabilidade;
- Capacidade de trabalhar em equipe e se comunicar bem no contexto técnico.

## Diferenciais

> *Descreve competências desejáveis, mas não obrigatórias. Podem inspirar sugestões de evolução no README, mas não devem inflar o escopo do desafio.*

- Experiência com FastAPI, Flask ou frameworks similares;
- Conhecimento de PostgreSQL;
- Experiência com integrações de APIs de terceiros;
- Conhecimento com automações utilizando n8n, Make, Zapier ou ferramentas similares;
- Vivência com APIs de LLMs (OpenAI, Anthropic ou Google Gemini), LangChain/LangGraph, RAG, embeddings e bancos vetoriais como pgvector, Pinecone, Weaviate ou Chroma;
- Conhecimento em boas práticas de performance, segurança e escalabilidade.

## O que esperamos desse profissional

> *Descreve o perfil comportamental e os critérios de avaliação implícitos: proatividade, qualidade de código, atenção à experiência do usuário e capacidade de traduzir regra de negócio em solução técnica.*

- Perfil proativo e comprometido com entregas;
- Facilidade para entender regras de negócio e transformá-las em solução técnica;
- Atenção à qualidade do código e à experiência do usuário;
- Interesse em evoluir tecnicamente e contribuir com o time;
- Disponibilidade full time, 8h por dia, e feedbacks ágeis nas ferramentas de comunicação online da empresa.

## Condições da contratação

> *Descreve o modelo de contratação e trabalho. Informativo; não afeta a implementação.*

Modelo de contratação: PJ
Modelo de trabalho: Home Office (remoto)
Dedicação: Full time, 8h por dia

Se você tem experiência com Python e desenvolvimento Full Stack e quer atuar em projetos desafiadores de software, essa oportunidade pode ser para você.

## Sobre a vaga

> *Descreve o contexto do projeto e a duração do contrato.*

- Contrato inicial de 3 meses com possibilidade de renovação;
- Atuação no desenvolvimento e manutenção de aplicações e ferramentas de software para cliente de grande porte;
- Projetos envolvendo integrações, automações e soluções modernas de tecnologia;
- Contrato PJ, Full Time, 8h por dia, Home Office.

Interessados devem candidatar-se pelo LinkedIn respondendo às perguntas de seleção.

## Requisitos adicionados pelo anunciante da vaga

> *Descreve os filtros de triagem do LinkedIn (tempo mínimo de experiência por tecnologia). Informativo; não afeta a implementação.*

- Mais de 3 anos de experiência profissional com Python (Programming Language)
- Mais de 2 anos de experiência profissional com PostgreSQL
- Mais de 2 anos de experiência profissional com React.js

---

# PARTE 2: Desafio técnico prático (segunda fase)

> **O que esta parte descreve:** o enunciado oficial do desafio técnico. É a especificação do que deve ser construído e entregue. Toda implementação, teste e trecho de README deve ser coerente com ela.

## 01. Consulta de usuários

> *Descreve o objetivo geral: uma pequena aplicação Full Stack com backend Python e frontend React.*

Desenvolva uma pequena aplicação Full Stack com backend em Python e frontend em React.

### Backend

> *Descreve os requisitos do backend: framework preferencial, contrato do endpoint e comportamentos obrigatórios (validação, assincronia, resiliência a falhas parciais e tratamento de erros).*

Utilize Python. FastAPI é preferencial, mas Flask ou framework equivalente também são aceitos.
Crie o endpoint:

`POST /api/users/fetch`

Entrada:

```json
{
  "user_ids": [1, 2, 3, 4]
}
```

A implementação deve:

- Validar os dados de entrada.
- Consultar usuários por uma API HTTP externa.
- Executar as consultas de forma assíncrona.
- Impedir que a falha de um usuário interrompa o processamento dos demais.
- Tratar usuário não encontrado, erros HTTP e timeout.
- Retornar separadamente usuários obtidos e IDs que falharam.

Formato conceitual:

```json
{
  "users": [{ "id": 1, "name": "..." }],
  "failed": [3, 4]
}
```

Pequenas variações de estrutura são aceitáveis.

### Provider externo

> *Descreve a exigência de desacoplamento: a fonte dos dados (API pública ou simulada) deve poder ser trocada sem reescrever a regra de negócio.*

Você pode utilizar uma API pública simples ou simular o provider. Separe a lógica principal da integração externa o suficiente para permitir a troca do provider sem reescrever toda a regra de negócio.

### Frontend

> *Descreve os requisitos da interface: entrada de lista de IDs, execução da consulta e exibição dos quatro estados (loading, encontrados, falhados, erro do backend).*

Utilize React, preferencialmente com TypeScript. A interface deve permitir informar uma lista de IDs, executar a consulta e exibir loading, usuários encontrados, IDs que falharam e erro do backend.
HTML e CSS simples são suficientes. Não é necessário utilizar biblioteca de UI.

### Testes

> *Descreve o mínimo de testes automatizados exigido.*

Inclua pelo menos dois testes automatizados:

- Consulta com sucesso.
- Falha de um usuário sem interromper o processamento dos demais.

### README

> *Descreve o entregável de documentação: o que o README deve conter, incluindo a declaração de uso de IA e uma pergunta de escalabilidade que precisa ser respondida.*

Inclua um README curto com:

- Como executar o projeto.
- Principais decisões técnicas.
- O que melhoraria caso tivesse mais tempo.
- Se utilizou IA, qual ferramenta e para quê.
- Resposta à pergunta: "Se esta aplicação precisasse consultar milhares de usuários, o que você mudaria?"

## Diferenciais opcionais

> *Descreve itens extras que podem ser feitos, mas que **não são requisitos** e cuja ausência **não será penalizada**. Só considerar depois que o núcleo estiver funcionando e testado.*

Estes itens não são requisitos e sua ausência não será penalizada:

- Controle explícito de concorrência
- Retry com backoff e tratamento de 429
- Logging estruturado e observabilidade
- Docker e CI
- PostgreSQL e cache
- Organização arquitetural adicional

## Limites do desafio

> *Descreve explicitamente o que **não** deve ser feito ou não é exigido. Serve como trava contra excesso de engenharia (over-engineering).*

Não exigimos Kubernetes, Kafka, CQRS, Event Sourcing, microsserviços, Terraform, arquitetura distribuída avançada, infraestrutura cloud complexa, autenticação, deploy ou uma aplicação production-ready completa.