export type FailureReason = "not_found" | "timeout" | "provider_error"

export interface User {
  id: number
  name: string
}

export interface UserFetchError {
  id: number
  reason: FailureReason
}

export interface UserFetchRequest {
  user_ids: number[]
}

export interface UserFetchResponse {
  users: User[]
  failed: number[]
  errors: UserFetchError[]
}
