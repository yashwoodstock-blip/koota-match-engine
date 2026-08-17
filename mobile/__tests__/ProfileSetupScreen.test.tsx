import React from 'react';
import { render, fireEvent, act } from '@testing-library/react-native';
import { ProfileSetupScreen } from '../src/screens/ProfileSetupScreen';
import { useAuth } from '../src/context/AuthContext';
import * as authApi from '../src/api/authApi';

jest.mock('../src/context/AuthContext', () => ({
  useAuth: jest.fn(),
}));

const mockNavigate = jest.fn();
jest.mock('@react-navigation/native', () => ({
  useNavigation: () => ({
    navigate: mockNavigate,
  }),
}));

describe('ProfileSetupScreen Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (useAuth as jest.Mock).mockReturnValue({
      session: { access_token: 'valid_jwt_token' },
      profile: { name: 'Aarav' },
      logout: jest.fn(),
    });
  });

  test('renders all demographic input fields', () => {
    const { getByText, getByPlaceholderText } = render(<ProfileSetupScreen />);
    expect(getByText('Essential Demographics')).toBeTruthy();
    expect(getByPlaceholderText('e.g. Aarav Sharma')).toBeTruthy();
    expect(getByText('GENDER')).toBeTruthy();
    expect(getByText('RELIGION / FAITH TRADITION')).toBeTruthy();
  });

  test('shows validation error when full name is empty', async () => {
    const { getByPlaceholderText, getByText } = render(<ProfileSetupScreen />);
    const nameInput = getByPlaceholderText('e.g. Aarav Sharma');
    const submitBtn = getByText('Begin 42-Koota Questionnaire →');

    fireEvent.changeText(nameInput, '');

    await act(async () => {
      fireEvent.press(submitBtn);
    });

    expect(getByText('⚠ Please enter your full name.')).toBeTruthy();
  });

  test('submits valid profile data and navigates to ObjectiveQuestionnaire', async () => {
    const spyCreateProfile = jest.spyOn(authApi, 'createProfile').mockResolvedValueOnce({
      id: 'profile_123',
      name: 'Aarav Sharma',
      age: 27,
      gender: 'Male',
      religion: 'Hindu',
      caste: 'Brahmin',
      caste_preference: 'no_preference',
      city: 'Bengaluru',
      is_active: true,
    });

    const { getByPlaceholderText, getByText } = render(<ProfileSetupScreen />);
    const nameInput = getByPlaceholderText('e.g. Aarav Sharma');
    const submitBtn = getByText('Begin 42-Koota Questionnaire →');

    fireEvent.changeText(nameInput, 'Aarav Sharma');

    await act(async () => {
      fireEvent.press(submitBtn);
    });

    expect(spyCreateProfile).toHaveBeenCalledWith(
      'valid_jwt_token',
      expect.objectContaining({
        name: 'Aarav Sharma',
        age: 27,
        city: 'Bengaluru',
      })
    );
    expect(mockNavigate).toHaveBeenCalledWith('ObjectiveQuestionnaire');
  });
});
