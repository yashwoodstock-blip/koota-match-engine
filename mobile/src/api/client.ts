import Constants from 'expo-constants';

const extra = Constants.expoConfig?.extra || {};
export const API_BASE_URL =
  extra.apiBaseUrl ||
  process.env.EXPO_PUBLIC_API_BASE_URL ||
  'https://koota-match-engine.onrender.com';

interface RequestOptions extends RequestInit {
  token?: string | null;
  timeoutMs?: number;
  retryOnColdStart?: boolean;
}

const DEFAULT_TIMEOUT_MS = 30000; // 30s to comfortably tolerate Render free-tier cold starts

/**
 * Fetch with automatic AbortController timeout and optional 1-time retry for cold starts.
 */
async function fetchWithTimeout(
  url: string,
  options: RequestInit,
  timeoutMs: number = DEFAULT_TIMEOUT_MS
): Promise<Response> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const response = await fetch(url, {
      ...options,
      signal: controller.signal,
    });
    return response;
  } finally {
    clearTimeout(timer);
  }
}

export async function apiClient<T>(
  endpoint: string,
  options: RequestOptions = {}
): Promise<T> {
  const {
    token,
    headers = {},
    timeoutMs = DEFAULT_TIMEOUT_MS,
    retryOnColdStart = true,
    ...rest
  } = options;

  const reqHeaders: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(headers as Record<string, string>),
  };

  if (token) {
    reqHeaders['Authorization'] = `Bearer ${token}`;
  }

  const url = endpoint.startsWith('http') ? endpoint : `${API_BASE_URL}${endpoint}`;

  let response: Response;

  try {
    response = await fetchWithTimeout(url, { ...rest, headers: reqHeaders }, timeoutMs);
  } catch (err: any) {
    // If timed out or network error on cold backend, attempt 1 immediate retry
    if (retryOnColdStart) {
      try {
        response = await fetchWithTimeout(url, { ...rest, headers: reqHeaders }, timeoutMs);
      } catch (retryErr: any) {
        if (retryErr?.name === 'AbortError') {
          throw new Error(
            'Server wake-up timed out. The server is spinning up from inactivity — please try again in a few seconds.'
          );
        }
        throw new Error(
          retryErr?.message || 'Network request failed. Please check your internet connection.'
        );
      }
    } else {
      if (err?.name === 'AbortError') {
        throw new Error('Request timed out. Please try again.');
      }
      throw new Error(
        err?.message || 'Network request failed. Please check your internet connection.'
      );
    }
  }

  // Handle server 502/503/504 gateway spin-up codes with 1 retry
  if (retryOnColdStart && (response.status === 502 || response.status === 503 || response.status === 504)) {
    try {
      response = await fetchWithTimeout(url, { ...rest, headers: reqHeaders }, timeoutMs);
    } catch {
      // Retain original response if retry fails
    }
  }

  const data = await response.json().catch(() => null);

  if (!response.ok) {
    const errorMsg =
      data?.detail?.message ||
      data?.detail ||
      data?.message ||
      `Request failed with status ${response.status}`;
    const errorObj: any = new Error(typeof errorMsg === 'string' ? errorMsg : JSON.stringify(errorMsg));
    errorObj.status = response.status;
    errorObj.detail = data?.detail || data;
    throw errorObj;
  }

  return data as T;
}
