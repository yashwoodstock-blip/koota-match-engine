import React, { createContext, useContext, useEffect, useState } from 'react';
import * as WebBrowser from 'expo-web-browser';
import * as Linking from 'expo-linking';
import * as SecureStore from 'expo-secure-store';
import { Session } from '@supabase/supabase-js';
import { supabase } from '../lib/supabase';
import {
  redeemInviteCode,
  linkGoogleProfile,
  verifyBackendSession,
  GoogleAuthResponse,
} from '../api/authApi';

// Ensure browser session completes auth properly
WebBrowser.maybeCompleteAuthSession();

export interface UserProfile {
  id: string;
  email: string;
  name: string;
  isNewUser?: boolean;
}

interface AuthContextType {
  isLoading: boolean;
  isAuthenticated: boolean;
  session: Session | null;
  profile: UserProfile | null;
  inviteCode: string | null;
  inviteToken: string | null;
  error: string | null;
  redeemInvite: (code: string) => Promise<boolean>;
  loginWithGoogle: () => Promise<void>;
  logout: () => Promise<void>;
  clearError: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(false);
  const [session, setSession] = useState<Session | null>(null);
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [inviteCode, setInviteCode] = useState<string | null>(null);
  const [inviteToken, setInviteToken] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const clearError = () => setError(null);

  // 1. Cold Start Boot: Check existing Supabase session and restore
  useEffect(() => {
    async function bootstrapSession() {
      try {
        setIsLoading(true);
        // Check stored invite token if any
        const savedToken = await SecureStore.getItemAsync('koota_invite_token');
        const savedCode = await SecureStore.getItemAsync('koota_invite_code');
        if (savedToken) setInviteToken(savedToken);
        if (savedCode) setInviteCode(savedCode);

        // Check Supabase session
        const { data: { session: existingSession }, error: sessionError } = await supabase.auth.getSession();
        if (sessionError || !existingSession) {
          setIsLoading(false);
          return;
        }

        // Verify active token against backend
        try {
          const backendSession = await verifyBackendSession(existingSession.access_token);
          if (backendSession.authenticated && backendSession.profile_id) {
            setSession(existingSession);
            setProfile({
              id: backendSession.profile_id,
              email: backendSession.email || existingSession.user.email || '',
              name: backendSession.name || existingSession.user.user_metadata?.full_name || 'Member',
            });
            setIsAuthenticated(true);
          }
        } catch (verifyErr) {
          console.warn('[AuthContext] Backend session verification failed:', verifyErr);
        }
      } catch (err: any) {
        console.warn('[AuthContext] Bootstrap error:', err);
      } finally {
        setIsLoading(false);
      }
    }

    bootstrapSession();
  }, []);

  // 2. Redeem Single-Use Invite Code
  const redeemInvite = async (code: string): Promise<boolean> => {
    try {
      setIsLoading(true);
      setError(null);
      const res = await redeemInviteCode(code);
      if (res.status === 'valid' && res.invite_token) {
        setInviteCode(res.invite_code);
        setInviteToken(res.invite_token);
        await SecureStore.setItemAsync('koota_invite_token', res.invite_token);
        await SecureStore.setItemAsync('koota_invite_code', res.invite_code);
        return true;
      }
      setError('Invalid invite code.');
      return false;
    } catch (err: any) {
      setError(err?.message || 'Failed to verify invite code.');
      return false;
    } finally {
      setIsLoading(false);
    }
  };

  // 3. Initiate Supabase Google OAuth Flow with WebBrowser
  const loginWithGoogle = async (): Promise<void> => {
    try {
      setIsLoading(true);
      setError(null);

      const redirectUrl = Linking.createURL('auth/callback', { scheme: 'kootamatch' });

      // Request Google OAuth URL from Supabase
      const { data, error: oauthError } = await supabase.auth.signInWithOAuth({
        provider: 'google',
        options: {
          redirectTo: redirectUrl,
          skipBrowserRedirect: true,
        },
      });

      if (oauthError || !data?.url) {
        throw new Error(oauthError?.message || 'Could not initialize Google login.');
      }

      // Open hosted Supabase Google OAuth in browser session
      const result = await WebBrowser.openAuthSessionAsync(data.url, redirectUrl);

      if (result.type === 'cancel' || result.type === 'dismiss') {
        // User voluntarily dismissed browser - exit cleanly without stuck loading state
        setIsLoading(false);
        return;
      }

      if (result.type === 'success' && result.url) {
        // Parse access_token and refresh_token from redirect hash URL
        const parsedUrl = result.url;
        let accessToken: string | null = null;
        let refreshToken: string | null = null;

        if (parsedUrl.includes('#')) {
          const fragment = parsedUrl.split('#')[1];
          const params = new URLSearchParams(fragment);
          accessToken = params.get('access_token');
          refreshToken = params.get('refresh_token');
        } else if (parsedUrl.includes('?')) {
          const query = parsedUrl.split('?')[1];
          const params = new URLSearchParams(query);
          accessToken = params.get('access_token');
          refreshToken = params.get('refresh_token');
        }

        if (!accessToken || !refreshToken) {
          throw new Error('Authentication succeeded but tokens were not returned in callback.');
        }

        // Establish Supabase Client Session
        const { data: sessionData, error: setSessionError } = await supabase.auth.setSession({
          access_token: accessToken,
          refresh_token: refreshToken,
        });

        if (setSessionError || !sessionData.session) {
          throw new Error(setSessionError?.message || 'Failed to establish Supabase session.');
        }

        setSession(sessionData.session);

        // Handshake with FastAPI backend: Link verified Google account with invite code
        const profileRes: GoogleAuthResponse = await linkGoogleProfile(
          sessionData.session.access_token,
          inviteToken
        );

        setProfile({
          id: profileRes.profile_id,
          email: profileRes.email,
          name: profileRes.name,
          isNewUser: profileRes.is_new_user,
        });

        setIsAuthenticated(true);
      }
    } catch (err: any) {
      setError(err?.message || 'Google authentication failed.');
    } finally {
      setIsLoading(false);
    }
  };

  // 4. Logout & Purge Session
  const logout = async (): Promise<void> => {
    try {
      setIsLoading(true);
      await supabase.auth.signOut();
      await SecureStore.deleteItemAsync('koota_invite_token');
      await SecureStore.deleteItemAsync('koota_invite_code');
      setSession(null);
      setProfile(null);
      setInviteToken(null);
      setInviteCode(null);
      setIsAuthenticated(false);
    } catch (err: any) {
      console.warn('[AuthContext] Logout error:', err);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <AuthContext.Provider
      value={{
        isLoading,
        isAuthenticated,
        session,
        profile,
        inviteCode,
        inviteToken,
        error,
        redeemInvite,
        loginWithGoogle,
        logout,
        clearError,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
