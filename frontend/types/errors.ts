/**
 * Standardized error type for the application
 */
export interface AppError {
  message: string
  code?: string
  status?: number
  details?: Record<string, unknown>
}

/**
 * Type guard to check if an error is an AppError
 */
export function isAppError(error: unknown): error is AppError {
  return typeof error === 'object' && error !== null && 'message' in error
}

/**
 * Convert any error to an AppError
 */
export function toAppError(error: unknown): AppError {
  if (isAppError(error)) return error
  if (error instanceof Error) return { message: error.message }
  return { message: String(error) }
}

/**
 * Get error message from any error type safely
 */
export function getErrorMessage(error: unknown): string {
  if (isAppError(error)) return error.message
  if (error instanceof Error) return error.message
  if (typeof error === 'string') return error
  return 'An unknown error occurred'
}
