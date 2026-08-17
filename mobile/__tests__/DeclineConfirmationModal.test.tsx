import React from 'react';
import { render, fireEvent, act } from '@testing-library/react-native';
import { DeclineConfirmationModal } from '../src/components/DeclineConfirmationModal';
import { WeeklyMatchDTO } from '../src/api/authApi';

const mockCandidate: WeeklyMatchDTO = {
  candidate_id: 'cand-01',
  candidate_name: 'Ananya Sharma',
  score: 0.94,
  tier: 'strong match',
  alignment_points: [],
  friction_points: [],
  interest_status: 'none',
  is_mutual: false,
};

describe('DeclineConfirmationModal Component', () => {
  const mockCancel = jest.fn();
  const mockConfirmDecline = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('renders danger warning text when visible', () => {
    const { getByText } = render(
      <DeclineConfirmationModal
        visible={true}
        candidate={mockCandidate}
        onCancel={mockCancel}
        onConfirmDecline={mockConfirmDecline}
      />
    );

    expect(getByText('Decline Ananya Sharma?')).toBeTruthy();
    expect(getByText(/This action is permanent and cannot be undone/i)).toBeTruthy();
    expect(getByText(/even if Ananya Sharma expresses interest in you later/i)).toBeTruthy();
  });

  test('tapping Keep in Matches triggers onCancel', () => {
    const { getByText } = render(
      <DeclineConfirmationModal
        visible={true}
        candidate={mockCandidate}
        onCancel={mockCancel}
        onConfirmDecline={mockConfirmDecline}
      />
    );

    const cancelBtn = getByText('Keep in Matches');
    fireEvent.press(cancelBtn);

    expect(mockCancel).toHaveBeenCalled();
    expect(mockConfirmDecline).not.toHaveBeenCalled();
  });

  test('tapping Yes, Decline Permanently triggers onConfirmDecline with candidate ID', async () => {
    const { getByText } = render(
      <DeclineConfirmationModal
        visible={true}
        candidate={mockCandidate}
        onCancel={mockCancel}
        onConfirmDecline={mockConfirmDecline}
      />
    );

    const confirmBtn = getByText('Yes, Decline Permanently');
    await act(async () => {
      fireEvent.press(confirmBtn);
    });

    expect(mockConfirmDecline).toHaveBeenCalledWith('cand-01');
  });
});
