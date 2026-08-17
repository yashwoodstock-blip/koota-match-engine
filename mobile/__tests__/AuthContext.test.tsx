import React from 'react';
import { renderHook, act } from '@testing-library/react-hooks';
import { AuthProvider, useAuth } from '../src/context/AuthContext';
import * as authApi from '../src/api/authApi';
import { supabase } from '../src/lib/supabase';
import * as SecureStore from 'expo-secure-store';

jest.mock('../src/lib/supabase', () => ({
  supabase: {
    auth: {
      getSession: jest.fn(),
      signInWithOAuth: jest.fn(),
      setSession: jest.fn(),
      signOut: jest.fn(),
    },
  },
}));

jest.mock('expo-secure-store', () => ({
  getItemAsync: jest.fn(),
  setItemAsync: jest.fn(),
  deleteItemAsync: jest.fn(),
}));

jest.mock('expo-web-browser', () => ({
  openAuthSessionAsync: jest.fn(),
  maybeCompleteAuthSession: jest.fn(),
}));

describe('AuthContext Hook', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (supabase.auth.getSession as jest.Mock).mockResolvedValue({
      data: { session: null },
      error: null,
    });
  });

  test('initializes with unauthenticated default state', async () => {
    const wrapper = ({ children }: { children: React.ReactNode }) => (
      <AuthProvider>{children}</AuthProvider>
    );
    const { result, waitForNextUpdate } = renderHook(() => useAuth(), { wrapper });

    await waitForNextUpdate();

    expect(result.current.isAuthenticated).toBe(false);
    expect(result.current.session).toBeNull();
    expect(result.current.profile).toBeNull();
    expect(result.current.isLoading).toBe(false);
  });

  test('redeemInvite stores invite token and updates state on success', async () => {
    jest.spyOn(authApi, 'redeemInviteCode').mockResolvedValueOnce({
      status: 'valid',
      message: 'Invite verified',
      invite_code: 'A9K2M4P7',
      invite_token: 'token_abc',
    });

    const wrapper = ({ children }: { children: React.ReactNode }) => (
      <AuthProvider>{children}</AuthProvider>
    );
    const { result, waitForNextUpdate } = renderHook(() => useAuth(), { wrapper });
    await waitForNextUpdate();

    let success = false;
    await act(async () => {
      success = await result.current.redeemInvite('A9K2M4P7');
    });

    expect(success).toBe(true);
    expect(result.current.inviteCode).toBe('A9K2M4P7');
    expect(result.current.inviteToken).toBe('token_abc');
    expect(SecureStore.setItemAsync).toHaveBeenCalledWith('koota_invite_token', 'token_abc');
  });

  test('logout purges state and clears SecureStore items', async () => {
    (supabase.auth.signOut as jest.Mock).mockResolvedValueOnce({ error: null });

    const wrapper = ({ children }: { children: React.ReactNode }) => (
      <AuthProvider>{children}</AuthProvider>
    );
    const { result, waitForNextUpdate } = renderHook(() => useAuth(), { wrapper });
    await waitForNextUpdate();

    await act(async () => {
      await result.current.logout();
    });

    expect(result.current.isAuthenticated).toBe(false);
    expect(result.current.session).toBeNull();
    expect(result.current.profile).toBeNull();
    expect(SecureStore.deleteItemAsync).toHaveBeenCalledWith('koota_invite_token');
    expect(SecureStore.deleteItemAsync).toHaveBeenCalledWith('koota_invite_code');
  });
});
