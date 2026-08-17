import React from 'react';
import { render, fireEvent, act, waitFor } from '@testing-library/react-native';
import { EditProfileScreen } from '../src/screens/EditProfileScreen';
import { useAuth } from '../src/context/AuthContext';
import * as authApi from '../src/api/authApi';

jest.mock('../src/context/AuthContext', () => ({
  useAuth: jest.fn(),
}));

const mockGoBack = jest.fn();
const mockNavigate = jest.fn();
jest.mock('@react-navigation/native', () => ({
  useNavigation: () => ({
    goBack: mockGoBack,
    navigate: mockNavigate,
  }),
}));

const mockProfileData: authApi.ProfileResponse = {
  id: 'prof-user-1',
  name: 'Aarav Sharma',
  age: 28,
  gender: 'male',
  religion: 'Hindu',
  caste: 'Brahmin',
  caste_preference: 'no_preference',
  city: 'Bengaluru',
  is_complete: true,
  answered_kootas_count: 42,
  total_kootas_count: 42,
  created_at: '2026-08-18T00:00:00Z',
};

describe('EditProfileScreen Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (useAuth as jest.Mock).mockReturnValue({
      session: { access_token: 'valid_jwt_token' },
      profile: { id: 'prof-user-1', name: 'Aarav Sharma' },
      logout: jest.fn(),
    });
  });

  test('loads and pre-populates demographic form on mount', async () => {
    jest.spyOn(authApi, 'getProfileDetails').mockResolvedValueOnce(mockProfileData);

    const { getByDisplayValue, getByText } = render(<EditProfileScreen />);

    await waitFor(() => {
      expect(getByDisplayValue('Aarav Sharma')).toBeTruthy();
      expect(getByDisplayValue('28')).toBeTruthy();
      expect(getByDisplayValue('Bengaluru')).toBeTruthy();
      expect(getByText('Layer 1 Demographics')).toBeTruthy();
    });
  });

  test('submits only partial changed fields for low-stakes updates', async () => {
    jest.spyOn(authApi, 'getProfileDetails').mockResolvedValueOnce(mockProfileData);
    const spyUpdate = jest.spyOn(authApi, 'updateProfile').mockResolvedValueOnce({
      id: 'prof-user-1',
      name: 'Aarav Sharma',
      age: 28,
      religion: 'Hindu',
      city: 'Mumbai',
      stale_matches_invalidated: true,
      hard_filter_changed: false,
      updated_at: '2026-08-18T01:00:00Z',
    });

    const { getByDisplayValue, getByText } = render(<EditProfileScreen />);

    await waitFor(() => {
      expect(getByDisplayValue('Bengaluru')).toBeTruthy();
    });

    // Change city to Mumbai
    const cityInput = getByDisplayValue('Bengaluru');
    fireEvent.changeText(cityInput, 'Mumbai');

    const saveBtn = getByText('Save Demographic Changes');
    await act(async () => {
      fireEvent.press(saveBtn);
    });

    expect(spyUpdate).toHaveBeenCalledWith('valid_jwt_token', 'prof-user-1', {
      city: 'Mumbai',
    });
  });

  test('editing religion triggers hard filter confirmation modal before saving', async () => {
    jest.spyOn(authApi, 'getProfileDetails').mockResolvedValueOnce(mockProfileData);
    const spyUpdate = jest.spyOn(authApi, 'updateProfile').mockResolvedValueOnce({
      id: 'prof-user-1',
      name: 'Aarav Sharma',
      age: 28,
      religion: 'Jain',
      stale_matches_invalidated: true,
      hard_filter_changed: true,
      warning: 'Updating hard-filter demographic preferences (religion/caste) resets your active candidate pool.',
      updated_at: '2026-08-18T01:00:00Z',
    });

    const { getByDisplayValue, getByText } = render(<EditProfileScreen />);

    await waitFor(() => {
      expect(getByDisplayValue('Hindu')).toBeTruthy();
    });

    // Change religion to Jain
    const relInput = getByDisplayValue('Hindu');
    fireEvent.changeText(relInput, 'Jain');

    const saveBtn = getByText('Save Demographic Changes');
    fireEvent.press(saveBtn);

    // Hard filter modal should open without immediate API call
    expect(getByText('Reset Candidate Pool?')).toBeTruthy();
    expect(spyUpdate).not.toHaveBeenCalled();

    // Confirm in modal
    const confirmBtn = getByText('Confirm & Reset Pool');
    await act(async () => {
      fireEvent.press(confirmBtn);
    });

    expect(spyUpdate).toHaveBeenCalledWith('valid_jwt_token', 'prof-user-1', {
      religion: 'Jain',
    });
  });
});
