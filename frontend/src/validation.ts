const MAX_USER_IDS = 100

type ParsedUserIds = { userIds: number[] } | { validationError: string }

export function parseUserIds(input: string): ParsedUserIds {
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
