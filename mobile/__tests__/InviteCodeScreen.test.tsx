import React from 'react';
import { render, fireEvent, act } from '@testing-library/react-native';
import { InviteCodeScreen } from '../src/screens/InviteCodeScreen';
import { useAuth } from '../src/context/AuthContext';

// Mock useAuth
jest.mock('../src/context/AuthContext', () => ({
  useAuth: jest.fn(),
}));

const mockNavigate = jest.fn();
const mockGoBack = jest.fn();
jest.mock('@react-navigation/native', () => ({
  useNavigation: () => ({
    navigate: mockNavigate,
    goBack: mockGoBack,
  }),
}));

describe('InviteCodeScreen Component', () => {
  const mockRedeemInvite = jest.fn();
  const mockClearError = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
    (useAuth as jest.Mock).mockReturnValue({
      redeemInvite: mockRedeemInvite,
      isLoading: false,
      error: null,
      clearError: mockClearError,
    });
  });

  test('renders prompt and input correctly', () => {
    const { getByPlaceholderText, getByText } = render(<InviteCodeScreen />);
    expect(getByText('Redeem Invite')).toBeTruthy();
    expect(getByPlaceholderText('e.g. A9K2M4P7')).toBeTruthy();
  });

  test('formats typed text to uppercase and limits to 8 alphanumeric characters', () => {
    const { getByPlaceholderText } = render(<InviteCodeScreen />);
    const input = getByPlaceholderText('e.g. A9K2M4P7');

    fireEvent.changeText(input, 'a9k2m4p7extra');
    expect(input.props.value).toBe('A9K2M4P7');
  });

  test('triggers redeemInvite and navigates to GoogleLogin on success', async () => {
    mockRedeemInvite.mockResolvedValueOnce(true);

    const { getByPlaceholderText, getByText } = render(<InviteCodeScreen />);
    const input = getByPlaceholderText('e.g. A9K2M4P7');
    const button = getByText('Verify & Continue');

    fireEvent.changeText(input, 'A9K2M4P7');

    await act(async () => {
      fireEvent.press(button);
    });

    expect(mockRedeemInvite).toHaveBeenCalledWith('A9K2M4P7');
    expect(mockNavigate).toHaveBeenCalledWith('GoogleLogin');
  });

  test('displays inline error banner when error is present', () => {
    (useAuth as jest.Mock).mockReturnValue({
      redeemInvite: mockRedeemInvite,
      isLoading: false,
      error: 'This invite code has already been redeemed.',
      clearError: mockClearError,
    });

    const { getByText } = render(<InviteCodeScreen />);
    expect(getByText('This invite code has already been redeemed.')).toBeTruthy();
  });
});
