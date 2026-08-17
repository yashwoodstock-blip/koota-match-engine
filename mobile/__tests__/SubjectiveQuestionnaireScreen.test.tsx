import React from 'react';
import { render, fireEvent } from '@testing-library/react-native';
import { SubjectiveQuestionnaireScreen } from '../src/screens/SubjectiveQuestionnaireScreen';
import { useAuth } from '../src/context/AuthContext';
import { useQuestionnaire } from '../src/context/QuestionnaireContext';

jest.mock('../src/context/AuthContext', () => ({
  useAuth: jest.fn(),
}));

jest.mock('../src/context/QuestionnaireContext', () => ({
  useQuestionnaire: jest.fn(),
}));

const mockNavigate = jest.fn();
jest.mock('@react-navigation/native', () => ({
  useNavigation: () => ({
    navigate: mockNavigate,
  }),
}));

describe('SubjectiveQuestionnaireScreen Component', () => {
  const mockSetAnswer = jest.fn();
  const mockGetAnswer = jest.fn();
  const mockSubmitAllAnswers = jest.fn();
  const mockRefreshCompletion = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
    (useAuth as jest.Mock).mockReturnValue({
      session: { access_token: 'token_123' },
      profile: { id: 'prof_123' },
    });

    (useQuestionnaire as jest.Mock).mockReturnValue({
      setAnswer: mockSetAnswer,
      getAnswer: mockGetAnswer.mockReturnValue('My childhood reflection and thoughtful answer...'),
      submitAllAnswers: mockSubmitAllAnswers.mockResolvedValue(true),
      refreshCompletion: mockRefreshCompletion.mockResolvedValue(true),
      isSubmitting: false,
      error: null,
    });
  });

  test('renders subjective prompt and character counter', () => {
    const { getByText, getByPlaceholderText } = render(<SubjectiveQuestionnaireScreen />);
    expect(getByText('BATCH 1 • REFLECTIONS')).toBeTruthy();
    expect(getByText('1. Personal History & Formative Experiences')).toBeTruthy();
    expect(getByPlaceholderText(/Share your authentic perspective/i)).toBeTruthy();
  });

  test('typing updates subjective answer in context', () => {
    const { getByPlaceholderText } = render(<SubjectiveQuestionnaireScreen />);
    const input = getByPlaceholderText(/Share your authentic perspective/i);

    fireEvent.changeText(input, 'New authentic perspective text here.');
    expect(mockSetAnswer).toHaveBeenCalledWith(
      1,
      0,
      'subjective',
      'New authentic perspective text here.'
    );
  });
});
