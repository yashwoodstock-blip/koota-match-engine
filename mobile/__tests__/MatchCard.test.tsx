import React from 'react';
import { render, fireEvent } from '@testing-library/react-native';
import { MatchCard } from '../src/components/MatchCard';
import { WeeklyMatchDTO } from '../src/api/authApi';

const mockMatch: WeeklyMatchDTO = {
  candidate_id: 'cand-01',
  candidate_name: 'Ananya Sharma',
  score: 0.94,
  tier: 'strong match',
  alignment_points: ['Shared egalitarian career vision', 'Deep mutual respect'],
  friction_points: ['Morning routine differences'],
  interest_status: 'none',
  is_mutual: false,
};

describe('MatchCard Component', () => {
  const mockExpressInterest = jest.fn();
  const mockPressDecline = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('renders candidate name, tier badge, percentage score, and insights', () => {
    const { getByText } = render(
      <MatchCard
        match={mockMatch}
        onExpressInterest={mockExpressInterest}
        onPressDecline={mockPressDecline}
      />
    );

    expect(getByText('Ananya Sharma')).toBeTruthy();
    expect(getByText('✦ STRONG MATCH')).toBeTruthy();
    expect(getByText('94%')).toBeTruthy();
    expect(getByText('Shared egalitarian career vision')).toBeTruthy();
    expect(getByText('Morning routine differences')).toBeTruthy();
  });

  test('tapping Express Interest triggers callback instantly in one tap', () => {
    const { getByText } = render(
      <MatchCard
        match={mockMatch}
        onExpressInterest={mockExpressInterest}
        onPressDecline={mockPressDecline}
      />
    );

    const expressBtn = getByText('Express Interest ✦');
    fireEvent.press(expressBtn);

    expect(mockExpressInterest).toHaveBeenCalledWith('cand-01');
  });

  test('tapping Pass triggers decline modal trigger callback', () => {
    const { getByText } = render(
      <MatchCard
        match={mockMatch}
        onExpressInterest={mockExpressInterest}
        onPressDecline={mockPressDecline}
      />
    );

    const passBtn = getByText('Pass');
    fireEvent.press(passBtn);

    expect(mockPressDecline).toHaveBeenCalledWith(mockMatch);
  });
});
