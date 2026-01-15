/**
 * Beta Signup API Route
 *
 * Handles beta program signup requests from the frontend.
 * Relays the request to the backend API.
 */

export default defineEventHandler(async (event) => {
  const config = useRuntimeConfig()
  const backendUrl = config.public.apiBaseUrl

  try {
    // Read request body
    const body = await readBody(event)

    // Forward to backend API
    const response = await $fetch(`${backendUrl}/api/beta/signup`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body
    })

    return response
  } catch (error: any) {
    // Handle ofetch/FetchError
    if (error.statusCode) {
      throw createError({
        statusCode: error.statusCode,
        statusMessage: error.data?.detail || error.statusMessage || 'Erreur backend'
      })
    }

    // Handle network errors
    throw createError({
      statusCode: 500,
      statusMessage: 'Erreur de connexion au serveur'
    })
  }
})
