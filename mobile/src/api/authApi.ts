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
  is_active?: boolean;
  answered_kootas_count?: number;
  total_kootas_count?: number;
  is_complete?: boolean;
  created_at?: string;
}

export interface ProfileUpdateResponse {
  id: string;
  name: string;
  age: number;
  gender?: string;
  religion: string;
  caste?: string;
  caste_preference?: string;
  city?: string;
  stale_matches_invalidated: boolean;
  hard_filter_changed: boolean;
  warning?: string;
  updated_at: string;
}

export interface ProfileDeleteResponse {
  status: string;
  message: string;
  deleted_profile_id: string;
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

export interface WeeklyMatchDTO {
  candidate_id: string;
  candidate_name: string;
  score: number;
  tier: string;
  alignment_points: string[];
  friction_points: string[];
  contradiction_gates?: any[];
  social_overlap_score?: number;
  shared_account_count?: number;
  interest_status: 'none' | 'pending' | 'mutual' | 'declined';
  is_mutual: boolean;
  generated_at?: string;
}

export interface WeeklyMatchListResponse {
  profile_id: string;
  total_matches: number;
  mutual_matches_count: number;
  matches: WeeklyMatchDTO[];
  is_precomputed: boolean;
}

export interface InterestResponse {
  profile_id: string;
  target_profile_id: string;
  status: 'pending' | 'mutual' | 'declined';
  is_mutual: boolean;
  expressed_at?: string;
}

export interface CandidateInterestStatus {
  candidate_id: string;
  status: 'none' | 'pending' | 'mutual' | 'declined';
  is_mutual: boolean;
  expressed_at?: string;
}

export interface InterestStatusListResponse {
  profile_id: string;
  statuses: CandidateInterestStatus[];
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
 * Partially update Layer 1 Demographics Profile.
 */
export async function updateProfile(
  token: string,
  profileId: string,
  payload: Partial<ProfileCreatePayload>
): Promise<ProfileUpdateResponse> {
  return await apiClient<ProfileUpdateResponse>(`/profiles/${profileId}`, {
    method: 'PATCH',
    token,
    body: JSON.stringify(payload),
  });
}

/**
 * Permanently delete Profile and all associated artifacts (DPDP).
 */
export async function deleteProfile(
  token: string,
  profileId: string
): Promise<ProfileDeleteResponse> {
  return await apiClient<ProfileDeleteResponse>(`/profiles/${profileId}`, {
    method: 'DELETE',
    token,
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
 * Submit bulk answers for 42-Koota questionnaire (explicit UPSERT).
 */
export async function submitAnswers(
  token: string,
  profileId: string,
  answers: AnswerItem[]
): Promise<{ status: string; count: number; stale_matches_invalidated?: boolean }> {
  return await apiClient<{ status: string; count: number; stale_matches_invalidated?: boolean }>(
    `/profiles/${profileId}/answers`,
    {
      method: 'POST',
      token,
      body: JSON.stringify({ answers }),
    }
  );
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

/**
 * Retrieve precomputed weekly matches for a profile.
 */
export async function getWeeklyMatches(
  token: string,
  profileId: string
): Promise<WeeklyMatchListResponse> {
  return await apiClient<WeeklyMatchListResponse>(`/profiles/${profileId}/weekly-matches`, {
    method: 'GET',
    token,
  });
}

/**
 * Express pending interest or terminal decline on a candidate.
 */
export async function postInterestAction(
  token: string,
  profileId: string,
  targetProfileId: string,
  action: 'pending' | 'declined'
): Promise<InterestResponse> {
  return await apiClient<InterestResponse>('/interest', {
    method: 'POST',
    token,
    body: JSON.stringify({
      profile_id: profileId,
      target_profile_id: targetProfileId,
      action,
    }),
  });
}

/**
 * Retrieve interest status list under staged disclosure rules.
 */
export async function getInterestStatusList(
  token: string,
  profileId: string
): Promise<InterestStatusListResponse> {
  return await apiClient<InterestStatusListResponse>(`/interest/${profileId}/status`, {
    method: 'GET',
    token,
  });
}
