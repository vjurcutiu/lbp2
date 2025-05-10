// src/services/apiVaultService.js

import apiClient from './apiClient'

const VAULT_ROUTE = '/api-vault'     // adjust if you mount the blueprint at a different path

/**
 * Add or update a secret in the API vault.
 * @param {string} name   The vault entry name (e.g. 'PINECONE_API_KEY')
 * @param {string} value  The secret value
 */
async function upsertSecret(name, value) {
  if (!name || !value) {
    throw new Error('Both name and value are required to upsert a vault secret.');
  }
  // The Flask route expects form data (entry_name, secret_value)
  const payload = new FormData()
  payload.append('entry_name', name)
  payload.append('secret_value', value)

  await apiClient.post(`${VAULT_ROUTE}/`, payload, {
    headers: {
      // let axios set the correct multipart/form-data boundary:
      'Content-Type': 'multipart/form-data',
    }
  })
}

/**
 * Update the PINECONE_API_KEY in the vault.
 * @param {string} key
 */
export async function updatePineconeKey(key) {
  return upsertSecret('PINECONE_API_KEY', key)
}

/**
 * Update the OPENAI_API_KEY in the vault.
 * @param {string} key
 */
export async function updateOpenAIKey(key) {
  return upsertSecret('OPENAI_API_KEY', key)
}

/**
 * (Optional) Fetch the list of vault entries.
 * Useful if you want to display currently stored keys.
 */
export async function listVaultEntries() {
  const response = await apiClient.get(`${VAULT_ROUTE}/`)
  // response.entries is whatever your Flask endpoint renders; adapt as needed
  return response.entries
}
