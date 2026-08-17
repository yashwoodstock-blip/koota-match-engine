import React from 'react';
import { render, fireEvent, act } from '@testing-library/react-native';
import { ObjectiveQuestionnaireScreen } from '../src/screens/ObjectiveQuestionnaireScreen';
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

describe('ObjectiveQuestionnaireScreen Component', () => {
  const mockSetAnswer = jest.fn();
  const mockGetAnswer = jest.fn();
  const mockSubmitAllAnswers = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
    (useAuth as jest.Mock).mockReturnValue({
      session: { access_token: 'token_123' },
      profile: { id: 'prof_123' },
    });

    (useQuestionnaire as jest.Mock).mockReturnValue({
      setAnswer: mockSetAnswer,
      getAnswer: mockGetAnswer.mockReturnValue('nuclear_urban'),
      submitAllAnswers: mockSubmitAllAnswers.mockResolvedValue(true),
      isSubmitting: false,
      error: null,
    });
  });

  test('renders objective koota title and options', () => {
    const { getByText } = render(<ObjectiveQuestionnaireScreen />);
    expect(getByText('STAGE 1 • OBJECTIVE PASS')).toBeTruthy();
    expect(getByText('1. Personal History & Formative Experiences')).toBeTruthy();
    expect(getByText('Nuclear family in an urban metro')).toBeTruthy();
  });

  test('clicking option calls setAnswer with selected option value', () => {
    const { getByText } = render(<ObjectiveQuestionnaireScreen />);
    const option = getByText('Joint family in an urban area');

    fireEvent.press(option);
    expect(mockSetAnswer).toHaveBeenCalledWith(1, 0, 'objective', 'joint_urban');
  });
});
