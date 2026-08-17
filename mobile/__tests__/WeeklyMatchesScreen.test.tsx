import React from 'react';
import { render, fireEvent, act, waitFor } from '@testing-library/react-native';
import { WeeklyMatchesScreen } from '../src/screens/WeeklyMatchesScreen';
import { useAuth } from '../src/context/AuthContext';
import * as authApi from '../src/api/authApi';

jest.mock('../src/context/AuthContext', () => ({
  useAuth: jest.fn(),
}));

const mockGoBack = jest.fn();
jest.mock('@react-navigation/native', () => ({
  useNavigation: () => ({
    goBack: mockGoBack,
    navigate: jest.fn(),
  }),
}));

const mockCandidate: authApi.WeeklyMatchDTO = {
  candidate_id: 'cand-01',
  candidate_name: 'Ananya Sharma',
  score: 0.94,
  tier: 'strong match',
  alignment_points: ['Shared egalitarian career vision'],
  friction_points: ['Morning routine differences'],
  interest_status: 'none',
  is_mutual: false,
};

describe('WeeklyMatchesScreen Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (useAuth as jest.Mock).mockReturnValue({
      session: { access_token: 'valid_jwt_token' },
      profile: { id: 'prof-user-1' },
    });
  });

  test('fetches and renders weekly matches on mount', async () => {
    jest.spyOn(authApi, 'getWeeklyMatches').mockResolvedValueOnce({
      profile_id: 'prof-user-1',
      total_matches: 1,
      mutual_matches_count: 0,
      matches: [mockCandidate],
      is_precomputed: true,
    });

    const { getByText } = render(<WeeklyMatchesScreen />);

    await waitFor(() => {
      expect(getByText('Ananya Sharma')).toBeTruthy();
      expect(getByText('✦ STRONG MATCH')).toBeTruthy();
    });
  });

  test('optimistically expresses interest on single tap', async () => {
    jest.spyOn(authApi, 'getWeeklyMatches').mockResolvedValueOnce({
      profile_id: 'prof-user-1',
      total_matches: 1,
      mutual_matches_count: 0,
      matches: [mockCandidate],
      is_precomputed: true,
    });

    const spyPostInterest = jest.spyOn(authApi, 'postInterestAction').mockResolvedValueOnce({
      profile_id: 'prof-user-1',
      target_profile_id: 'cand-01',
      status: 'pending',
      is_mutual: false,
    });

    const { getByText } = render(<WeeklyMatchesScreen />);

    await waitFor(() => {
      expect(getByText('Ananya Sharma')).toBeTruthy();
    });

    const expressBtn = getByText('Express Interest ✦');
    await act(async () => {
      fireEvent.press(expressBtn);
    });

    expect(getByText('✓ Interest Expressed')).toBeTruthy();
    expect(spyPostInterest).toHaveBeenCalledWith(
      'valid_jwt_token',
      'prof-user-1',
      'cand-01',
      'pending'
    );
  });
});
