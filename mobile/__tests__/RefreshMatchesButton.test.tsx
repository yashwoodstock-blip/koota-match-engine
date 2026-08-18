import React from 'react';
import { render, fireEvent, act, waitFor } from '@testing-library/react-native';
import { RefreshMatchesButton, formatRemainingTime } from '../src/components/RefreshMatchesButton';
import { useAuth } from '../src/context/AuthContext';
import * as authApi from '../src/api/authApi';

jest.mock('../src/context/AuthContext', () => ({
  useAuth: jest.fn(),
}));

describe('RefreshMatchesButton Component', () => {
  const mockOnRefreshSuccess = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
    (useAuth as jest.Mock).mockReturnValue({
      session: { access_token: 'valid_jwt_token' },
      profile: { id: 'prof-user-1' },
    });
  });

  test('formatRemainingTime formats hours, minutes, and seconds accurately', () => {
    expect(formatRemainingTime(0)).toBe('');
    expect(formatRemainingTime(45)).toBe('45s');
    expect(formatRemainingTime(125)).toBe('2m 5s');
    expect(formatRemainingTime(3665)).toBe('1h 1m 5s');
    expect(formatRemainingTime(86400)).toBe('24h 0m 0s');
  });

  test('renders active refresh button when not in cooldown', () => {
    const { getByText } = render(
      <RefreshMatchesButton onRefreshSuccess={mockOnRefreshSuccess} />
    );

    expect(getByText('✦ Refresh Matches Now')).toBeTruthy();
    expect(getByText('ON-DEMAND RECOMPUTATION')).toBeTruthy();
  });

  test('renders disabled cooldown timer when initialNextEligibleAt is in future', () => {
    // 2 hours in the future
    const futureTime = new Date(Date.now() + 7200 * 1000).toISOString();

    const { getByText, queryByText } = render(
      <RefreshMatchesButton
        onRefreshSuccess={mockOnRefreshSuccess}
        initialNextEligibleAt={futureTime}
      />
    );

    expect(queryByText('✦ Refresh Matches Now')).toBeNull();
    expect(getByText(/Refresh in (?:1h 59m|2h 0m)/)).toBeTruthy();
  });

  test('pressing refresh invokes API and calls onRefreshSuccess', async () => {
    const mockResponse: authApi.RefreshMatchesResponse = {
      profile_id: 'prof-user-1',
      total_matches: 4,
      refreshed_at: '2026-08-18T06:00:00Z',
      next_eligible_at: new Date(Date.now() + 86400 * 1000).toISOString(),
      matches: [],
    };

    const spyRefresh = jest
      .spyOn(authApi, 'refreshWeeklyMatches')
      .mockResolvedValueOnce(mockResponse);

    const { getByText } = render(
      <RefreshMatchesButton onRefreshSuccess={mockOnRefreshSuccess} />
    );

    const btn = getByText('✦ Refresh Matches Now');
    await act(async () => {
      fireEvent.press(btn);
    });

    expect(spyRefresh).toHaveBeenCalledWith('valid_jwt_token', 'prof-user-1');
    expect(mockOnRefreshSuccess).toHaveBeenCalledWith(mockResponse);
  });

  test('429 rate limit response updates cooldown countdown', async () => {
    const futureEligible = new Date(Date.now() + 3600 * 1000).toISOString();
    const error429 = {
      detail: {
        error: 'Rate limit exceeded',
        message: 'Matches can only be refreshed once every 24 hours.',
        next_eligible_at: futureEligible,
        retry_after_seconds: 3600,
      },
    };

    jest.spyOn(authApi, 'refreshWeeklyMatches').mockRejectedValueOnce(error429);

    const { getByText } = render(
      <RefreshMatchesButton onRefreshSuccess={mockOnRefreshSuccess} />
    );

    const btn = getByText('✦ Refresh Matches Now');
    await act(async () => {
      fireEvent.press(btn);
    });

    await waitFor(() => {
      expect(getByText(/Refresh in (?:59m|1h 0m)/)).toBeTruthy();
      expect(
        getByText('Refresh cooldown active. Available in upcoming window.')
      ).toBeTruthy();
    });
  });
});
