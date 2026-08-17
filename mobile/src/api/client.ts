import Constants from 'expo-constants';
import * as SecureStore from 'expo-secure-store';

const extra = Constants.expoConfig?.extra || {};
export const API_BASE_URL = extra.apiBaseUrl || 'https://koota-match-engine.onrender.com';

interface RequestOptions extends RequestInit {
  token?: string | null;
}

export async function apiClient<T>(endpoint: string, options: RequestOptions = {}): Promise<T> {
  const { token, headers = {}, ...rest } = options;

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
    response = await fetch(url, {
      ...rest,
      headers: reqHeaders,
    });
  } catch (err: any) {
    throw new Error(err?.message || 'Network request failed. Please check your internet connection.');
  }

  const data = await response.json().catch(() => null);

  if (!response.ok) {
    const errorMsg = data?.detail || data?.message || `Request failed with status ${response.status}`;
    throw new Error(errorMsg);
  }

  return data as T;
}
