import type { UserFetchRequest, UserFetchResponse } from "./types"

const apiBaseUrl = (import.meta.env.VITE_API_URL ?? "").replace(/\/+$/, "")

export async function fetchUsers(userIds: number[]): Promise<UserFetchResponse> {
  const requestBody: UserFetchRequest = { user_ids: userIds }
  let response: Response

  try {
    response = await fetch(`${apiBaseUrl}/api/users/fetch`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(requestBody),
    })
  } catch {
    throw new Error(
      "Não foi possível conectar ao servidor. Verifique se o backend está em execução.",
    )
  }

  if (!response.ok) {
    throw new Error(
      `O servidor retornou o erro ${response.status}. Tente novamente em instantes.`,
    )
  }

  return response.json() as Promise<UserFetchResponse>
}
