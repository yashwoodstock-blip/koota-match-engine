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

export interface ProfileCreatePayload {
  name: string;
  age: number;
  gender: string;
  religion: string;
  caste: string;
  caste_preference: string;
  city: string;
}

export interface ProfileResponse {
  id: string;
  name: string;
  age: number;
  gender: string;
  religion: string;
  caste: string;
  caste_preference: string;
  city: string;
  is_active: boolean;
  answered_kootas_count?: number;
  total_kootas_count?: number;
  is_complete?: boolean;
}

export interface AnswerItem {
  koota_id: number;
  question_index: number;
  question_type: 'objective' | 'subjective';
  raw_value: string;
}

export interface CompletionStatusResponse {
  is_complete: boolean;
  missing_koota_ids?: number[];
  answered_count?: number;
  total_required?: number;
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

/**
 * Create Layer 1 Demographics Profile.
 */
export async function createProfile(
  token: string,
  payload: ProfileCreatePayload
): Promise<ProfileResponse> {
  return await apiClient<ProfileResponse>('/profiles', {
    method: 'POST',
    token,
    body: JSON.stringify(payload),
  });
}

/**
 * Retrieve Profile summary and completion status.
 */
export async function getProfileDetails(
  token: string,
  profileId: string
): Promise<ProfileResponse> {
  return await apiClient<ProfileResponse>(`/profiles/${profileId}`, {
    method: 'GET',
    token,
  });
}

/**
 * Submit bulk answers for 42-Koota questionnaire.
 */
export async function submitAnswers(
  token: string,
  profileId: string,
  answers: AnswerItem[]
): Promise<{ status: string; count: number }> {
  return await apiClient<{ status: string; count: number }>(`/profiles/${profileId}/answers`, {
    method: 'POST',
    token,
    body: JSON.stringify({ answers }),
  });
}

/**
 * Check if all 42 Kootas have been answered.
 */
export async function getProfileCompletion(
  token: string,
  profileId: string
): Promise<CompletionStatusResponse> {
  return await apiClient<CompletionStatusResponse>(`/profiles/${profileId}/completion`, {
    method: 'GET',
    token,
  });
}
