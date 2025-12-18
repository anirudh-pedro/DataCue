/**
 * Centralized API client with Firebase authentication support.
 * All API calls should use this module to ensure proper auth headers.
 */

import { auth } from '../firebase';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

/**
 * Get the current user's Firebase ID token.
 * Returns null if user is not authenticated.
 */
async function getAuthToken() {
  const user = auth.currentUser;
  if (!user) {
    return null;
  }
  try {
    return await user.getIdToken();
  } catch (error) {
    console.error('Failed to get auth token:', error);
    return null;
  }
}

/**
 * Build headers object with optional authentication.
 * @param {Object} customHeaders - Additional headers to include
 * @param {boolean} includeAuth - Whether to include auth token (default: true)
 * @returns {Promise<Object>} Headers object
 */
async function buildHeaders(customHeaders = {}, includeAuth = true) {
  const headers = {
    'Content-Type': 'application/json',
    ...customHeaders,
  };

  if (includeAuth) {
    const token = await getAuthToken();
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
  }

  return headers;
}

/**
 * Make an authenticated API request.
 * @param {string} endpoint - API endpoint (with or without leading slash)
 * @param {Object} options - Fetch options
 * @param {boolean} options.auth - Whether to include auth (default: true)
 * @returns {Promise<Response>} Fetch response
 */
export async function apiRequest(endpoint, options = {}) {
  const { auth: includeAuth = true, headers: customHeaders, ...fetchOptions } = options;
  
  // Normalize endpoint
  const normalizedEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
  const url = `${API_BASE_URL.replace(/\/+$/, '')}${normalizedEndpoint}`;
  
  // Build headers
  const headers = await buildHeaders(customHeaders, includeAuth);
  
  // If body is FormData, remove Content-Type to let browser set it
  if (fetchOptions.body instanceof FormData) {
    delete headers['Content-Type'];
  }
  
  return fetch(url, {
    ...fetchOptions,
    headers,
  });
}

/**
 * Make a GET request.
 */
export async function apiGet(endpoint, options = {}) {
  return apiRequest(endpoint, { ...options, method: 'GET' });
}

/**
 * Make a POST request with JSON body.
 */
export async function apiPost(endpoint, data, options = {}) {
  return apiRequest(endpoint, {
    ...options,
    method: 'POST',
    body: JSON.stringify(data),
  });
}

/**
 * Make a POST request with FormData body (for file uploads).
 */
export async function apiPostForm(endpoint, formData, options = {}) {
  return apiRequest(endpoint, {
    ...options,
    method: 'POST',
    body: formData,
  });
}

/**
 * Make a PATCH request with JSON body.
 */
export async function apiPatch(endpoint, data, options = {}) {
  return apiRequest(endpoint, {
    ...options,
    method: 'PATCH',
    body: JSON.stringify(data),
  });
}

/**
 * Make a DELETE request.
 */
export async function apiDelete(endpoint, options = {}) {
  return apiRequest(endpoint, { ...options, method: 'DELETE' });
}

// Export the base URL for components that need it
export { API_BASE_URL };

// Export auth token getter for special cases
export { getAuthToken };
