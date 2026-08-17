import * as SecureStore from 'expo-secure-store';
import { LargeSecureStore } from '../src/lib/supabase';

// In-memory mock for SecureStore
const store: Record<string, string> = {};

jest.mock('expo-secure-store', () => ({
  getItemAsync: jest.fn(async (key: string) => store[key] || null),
  setItemAsync: jest.fn(async (key: string, val: string) => {
    store[key] = val;
  }),
  deleteItemAsync: jest.fn(async (key: string) => {
    delete store[key];
  }),
}));

describe('LargeSecureStore test suite', () => {
  beforeEach(() => {
    for (const key of Object.keys(store)) {
      delete store[key];
    }
    jest.clearAllMocks();
  });

  test('stores and retrieves small value directly', async () => {
    await LargeSecureStore.setItem('test_key', 'short_jwt_token');
    const val = await LargeSecureStore.getItem('test_key');
    expect(val).toBe('short_jwt_token');
  });

  test('chunks and reassembles value exceeding 1800 characters', async () => {
    const largePayload = 'A'.repeat(3000) + 'B'.repeat(1500);
    await LargeSecureStore.setItem('large_token', largePayload);

    expect(SecureStore.setItemAsync).toHaveBeenCalledWith('large_token_chunked', 'true');
    expect(SecureStore.setItemAsync).toHaveBeenCalledWith('large_token_count', '3');

    const retrieved = await LargeSecureStore.getItem('large_token');
    expect(retrieved).toBe(largePayload);
    expect(retrieved?.length).toBe(4500);
  });

  test('removes all chunked keys upon deletion', async () => {
    const largePayload = 'X'.repeat(4000);
    await LargeSecureStore.setItem('key_to_delete', largePayload);
    await LargeSecureStore.removeItem('key_to_delete');

    const retrieved = await LargeSecureStore.getItem('key_to_delete');
    expect(retrieved).toBeNull();
  });
});
