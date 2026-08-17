import { apiClient } from './client';

export interface InviteRedeemResponse {
  status: string;
  message: string;
  invite_code: string;
  invite_token: string;
}

export interface GoogleAuthResponse {
  status: string;
  message: string;
  profile_id: string;
  email: string;
  name: string;
  is_new_user: boolean;
}

export interface AuthSessionResponse {
  authenticated: boolean;
  email?: string;
  name?: string;
  profile_id?: string;
  invite_code?: string;
}

/**
 * Redeem an 8-character invite code to obtain a signed invite session token.
 */
export async function redeemInviteCode(code: string): Promise<InviteRedeemResponse> {
  const cleanCode = (code || '').trim().toUpperCase();
  return await apiClient<InviteRedeemResponse>('/auth/invite/redeem', {
    method: 'POST',
    body: JSON.stringify({ code: cleanCode }),
  });
}

/**
 * Link/Create Profile using Supabase Google OAuth access token and redeemed invite token.
 */
export async function linkGoogleProfile(
  supabaseAccessToken: string,
  inviteToken?: string | null
): Promise<GoogleAuthResponse> {
  const queryParams = inviteToken ? `?invite_token=${encodeURIComponent(inviteToken)}` : '';
  return await apiClient<GoogleAuthResponse>(`/auth/google/callback${queryParams}`, {
    method: 'GET',
    token: supabaseAccessToken,
  });
}

/**
 * Verify active backend session with Supabase access token.
 */
export async function verifyBackendSession(supabaseAccessToken: string): Promise<AuthSessionResponse> {
  return await apiClient<AuthSessionResponse>('/auth/session', {
    method: 'GET',
    token: supabaseAccessToken,
  });
}
