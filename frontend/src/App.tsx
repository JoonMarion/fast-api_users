import { type FormEvent, useState } from "react"

import { fetchUsers } from "./api"
import type { FailureReason, UserFetchResponse } from "./types"

const MAX_USER_IDS = 100

const failureReasonLabels: Record<FailureReason, string> = {
  not_found: "usuário não encontrado",
  timeout: "tempo de resposta esgotado",
  provider_error: "erro no serviço externo",
}

type ParsedUserIds = { userIds: number[] } | { validationError: string }

function parseUserIds(input: string): ParsedUserIds {
  const tokens = input.split(/[\s,]+/).filter(Boolean)

  if (tokens.length === 0) {
    return { validationError: "Informe pelo menos um ID." }
  }

  if (tokens.length > MAX_USER_IDS) {
    return {
      validationError: `Informe no máximo ${MAX_USER_IDS} IDs por consulta.`,
    }
  }

  const invalidTokens = tokens.filter((token) => {
    const value = Number(token)
    return !Number.isInteger(value) || value <= 0
  })

  if (invalidTokens.length > 0) {
    return {
      validationError: `Use apenas números inteiros positivos. Valores inválidos: ${invalidTokens.join(
        ", ",
      )}.`,
    }
  }

  return { userIds: tokens.map(Number) }
}

function App() {
  const [input, setInput] = useState("")
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<UserFetchResponse | null>(null)

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError(null)
    setResult(null)

    const parsed = parseUserIds(input)
    if ("validationError" in parsed) {
      setError(parsed.validationError)
      return
    }

    setLoading(true)

    try {
      setResult(await fetchUsers(parsed.userIds))
    } catch (caughtError: unknown) {
      setError(
        caughtError instanceof Error
          ? caughtError.message
          : "Não foi possível concluir a consulta.",
      )
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="page">
      <section className="panel" aria-labelledby="page-title">
        <header>
          <p className="eyebrow">Consulta de usuários</p>
          <h1 id="page-title">Buscar usuários por ID</h1>
          <p className="intro">
            Digite até 100 IDs separados por vírgula ou espaço.
          </p>
        </header>

        <form onSubmit={handleSubmit}>
          <label htmlFor="user-ids">IDs dos usuários</label>
          <div className="form-row">
            <input
              id="user-ids"
              name="user-ids"
              type="text"
              inputMode="numeric"
              placeholder="Ex.: 1, 2, 3"
              value={input}
              onChange={(event) => setInput(event.target.value)}
              disabled={loading}
              aria-describedby="input-help"
            />
            <button type="submit" disabled={loading}>
              {loading ? "Consultando..." : "Buscar"}
            </button>
          </div>
          <small id="input-help">Somente números inteiros positivos.</small>
        </form>

        {loading && (
          <p className="status" role="status">
            Consultando usuários...
          </p>
        )}

        {error && (
          <p className="message error" role="alert">
            {error}
          </p>
        )}

        {result && (
          <section className="results" aria-live="polite">
            <div>
              <h2>Usuários encontrados</h2>
              {result.users.length > 0 ? (
                <ul>
                  {result.users.map((user) => (
                    <li key={user.id}>
                      <span>{user.name}</span>
                      <small>ID {user.id}</small>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="empty">Nenhum usuário encontrado.</p>
              )}
            </div>

            {result.errors.length > 0 && (
              <div className="failures">
                <h2>IDs que falharam</h2>
                <ul>
                  {result.errors.map((item) => (
                    <li key={item.id}>
                      <span>ID {item.id}</span>
                      <small>{failureReasonLabels[item.reason]}</small>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </section>
        )}
      </section>
    </main>
  )
}

export default App
