import React from 'react';
import { render, fireEvent, act, waitFor } from '@testing-library/react-native';
import { Share } from 'react-native';
import { CompatibilityCodeScreen } from '../src/screens/CompatibilityCodeScreen';
import { useAuth } from '../src/context/AuthContext';
import * as authApi from '../src/api/authApi';

jest.mock('../src/context/AuthContext', () => ({
  useAuth: jest.fn(),
}));

const mockGoBack = jest.fn();
jest.mock('@react-navigation/native', () => ({
  useNavigation: () => ({
    goBack: mockGoBack,
  }),
}));

describe('CompatibilityCodeScreen Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (useAuth as jest.Mock).mockReturnValue({
      session: { access_token: 'valid_jwt_token' },
      profile: { id: 'prof-user-1', name: 'Aarav Sharma' },
    });
    jest.spyOn(Share, 'share').mockResolvedValue({ action: 'sharedAction' });
  });

  test('renders guidance copy and generates 7-character compatibility code', async () => {
    jest.spyOn(authApi, 'generateCompatibilityCode').mockResolvedValueOnce({
      code: '7K4MN9P',
      creator_profile_id: 'prof-user-1',
      created_at: '2026-08-18T06:00:00Z',
      expires_at: '2026-08-19T06:00:00Z',
    });

    const { getByText } = render(<CompatibilityCodeScreen />);

    expect(getByText('Direct Match Check')).toBeTruthy();
    expect(getByText('HOW DIRECT CHECK WORKS')).toBeTruthy();
    expect(
      getByText(/Share this only with someone specific/i)
    ).toBeTruthy();

    const generateBtn = getByText('✦ Generate Compatibility Code');
    await act(async () => {
      fireEvent.press(generateBtn);
    });

    await waitFor(() => {
      expect(getByText('7K4MN9P')).toBeTruthy();
      expect(getByText('Share Code 📤')).toBeTruthy();
    });

    // Test Native Share trigger
    const shareBtn = getByText('Share Code 📤');
    await act(async () => {
      fireEvent.press(shareBtn);
    });

    expect(Share.share).toHaveBeenCalledWith(
      expect.objectContaining({
        message: expect.stringContaining('7K4MN9P'),
      })
    );
  });

  test('redeeming a viable code displays immediate full compatibility breakdown', async () => {
    jest.spyOn(authApi, 'checkCompatibilityCode').mockResolvedValueOnce({
      creator_profile_id: 'creator-1',
      redeemer_profile_id: 'prof-user-1',
      code: '7K4MN9P',
      is_viable: true,
      tier: 'strong match',
      overall_score: 0.89,
      alignment_points: ['Shared commitment to family life', 'Aligned career pacing'],
      friction_points: ['Different perspectives on long-term city preferences'],
      social_overlap_score: 0.25,
      shared_account_count: 2,
      calculated_at: '2026-08-18T06:00:00Z',
    });

    const { getByText, getByPlaceholderText } = render(<CompatibilityCodeScreen />);

    // Switch to Enter Code tab
    fireEvent.press(getByText('Enter a Code'));

    const input = getByPlaceholderText('e.g. 7K4MN9P');
    fireEvent.changeText(input, '7K4MN9P');

    const checkBtn = getByText('Evaluate Compatibility →');
    await act(async () => {
      fireEvent.press(checkBtn);
    });

    await waitFor(() => {
      expect(getByText('STRONG MATCH')).toBeTruthy();
      expect(getByText('89%')).toBeTruthy();
      expect(getByText('Shared commitment to family life')).toBeTruthy();
      expect(getByText('Different perspectives on long-term city preferences')).toBeTruthy();
    });
  });

  test('redeeming a non-viable code renders respectful boundary finding without error banner', async () => {
    jest.spyOn(authApi, 'checkCompatibilityCode').mockResolvedValueOnce({
      creator_profile_id: 'creator-2',
      redeemer_profile_id: 'prof-user-1',
      code: '8P2XQ9A',
      is_viable: false,
      tier: 'not viable',
      hard_filter_reason: 'Religion mismatch (Hindu vs Jain)',
      alignment_points: [],
      friction_points: [],
      calculated_at: '2026-08-18T06:00:00Z',
    });

    const { getByText, getByPlaceholderText, queryByText } = render(<CompatibilityCodeScreen />);

    fireEvent.press(getByText('Enter a Code'));

    const input = getByPlaceholderText('e.g. 7K4MN9P');
    fireEvent.changeText(input, '8P2XQ9A');

    const checkBtn = getByText('Evaluate Compatibility →');
    await act(async () => {
      fireEvent.press(checkBtn);
    });

    await waitFor(() => {
      expect(getByText('FOUNDATIONAL BOUNDARY FINDING')).toBeTruthy();
      expect(getByText('Criteria Divergence')).toBeTruthy();
      expect(getByText(/Religion mismatch \(Hindu vs Jain\)/i)).toBeTruthy();
      // Should not render red error banner
      expect(queryByText('VERIFICATION NOTICE')).toBeNull();
    });
  });

  test('handling own code error (400) and expired code error (410)', async () => {
    // 1. Test 400 own code error
    jest.spyOn(authApi, 'checkCompatibilityCode').mockRejectedValueOnce({
      detail: { message: 'Cannot redeem your own compatibility code.' },
    });

    const { getByText, getByPlaceholderText } = render(<CompatibilityCodeScreen />);
    fireEvent.press(getByText('Enter a Code'));

    const input = getByPlaceholderText('e.g. 7K4MN9P');
    fireEvent.changeText(input, 'MYCODE1');

    const checkBtn = getByText('Evaluate Compatibility →');
    await act(async () => {
      fireEvent.press(checkBtn);
    });

    await waitFor(() => {
      expect(getByText('OWN CODE DETECTED')).toBeTruthy();
      expect(getByText(/You cannot redeem your own code/i)).toBeTruthy();
    });

    // 2. Test 410 expired error
    jest.spyOn(authApi, 'checkCompatibilityCode').mockRejectedValueOnce({
      detail: { message: 'This compatibility code has expired.' },
    });

    fireEvent.changeText(input, 'EXPIRD1');
    await act(async () => {
      fireEvent.press(checkBtn);
    });

    await waitFor(() => {
      expect(getByText('CODE EXPIRED OR USED')).toBeTruthy();
      expect(getByText(/This compatibility code has expired/i)).toBeTruthy();
    });
  });
});
