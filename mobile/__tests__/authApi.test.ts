import { redeemInviteCode, linkGoogleProfile, verifyBackendSession } from '../src/api/authApi';

// Mock global fetch
const mockFetch = jest.fn();
(global as any).fetch = mockFetch;

describe('authApi test suite', () => {
  beforeEach(() => {
    mockFetch.mockReset();
  });

  test('redeemInviteCode capitalizes code and returns token on 200 OK', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        status: 'valid',
        message: 'Invite code verified successfully.',
        invite_code: 'A9K2M4P7',
        invite_token: 'A9K2M4P7:1787002000:hash123',
      }),
    });

    const res = await redeemInviteCode('a9k2m4p7');
    expect(res.status).toBe('valid');
    expect(res.invite_token).toContain('A9K2M4P7');
    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining('/auth/invite/redeem'),
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({ code: 'A9K2M4P7' }),
      })
    );
  });

  test('redeemInviteCode throws descriptive error on 400 bad request', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 400,
      json: async () => ({
        detail: 'Invite code has expired.',
      }),
    });

    await expect(redeemInviteCode('EXPIRED1')).rejects.toThrow('Invite code has expired.');
  });

  test('linkGoogleProfile passes Supabase JWT in Bearer header and invite_token in query', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        status: 'success',
        message: 'Profile created successfully.',
        profile_id: 'prof-123',
        email: 'user@example.com',
        name: 'Aarav',
        is_new_user: true,
      }),
    });

    const res = await linkGoogleProfile('supabase_jwt_xyz', 'invite_token_123');
    expect(res.profile_id).toBe('prof-123');
    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining('/auth/google/callback?invite_token=invite_token_123'),
      expect.objectContaining({
        method: 'GET',
        headers: expect.objectContaining({
          Authorization: 'Bearer supabase_jwt_xyz',
        }),
      })
    );
  });

  test('verifyBackendSession sends Bearer token to /auth/session', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        authenticated: true,
        email: 'user@example.com',
        name: 'Aarav',
        profile_id: 'prof-123',
      }),
    });

    const res = await verifyBackendSession('valid_jwt');
    expect(res.authenticated).toBe(true);
    expect(res.email).toBe('user@example.com');
  });
});
