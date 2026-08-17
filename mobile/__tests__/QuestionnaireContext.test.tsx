import React from 'react';
import { renderHook, act } from '@testing-library/react-hooks';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { QuestionnaireProvider, useQuestionnaire } from '../src/context/QuestionnaireContext';
import * as authApi from '../src/api/authApi';

jest.mock('@react-native-async-storage/async-storage', () => ({
  getItem: jest.fn().mockResolvedValue(null),
  setItem: jest.fn().mockResolvedValue(null),
  removeItem: jest.fn().mockResolvedValue(null),
}));

describe('QuestionnaireContext Hook', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('setAnswer updates dictionary and persists to AsyncStorage', async () => {
    const wrapper = ({ children }: { children: React.ReactNode }) => (
      <QuestionnaireProvider>{children}</QuestionnaireProvider>
    );
    const { result } = renderHook(() => useQuestionnaire(), { wrapper });

    await act(async () => {
      await result.current.setAnswer(1, 0, 'objective', 'nuclear_urban');
    });

    expect(result.current.getAnswer(1, 0, 'objective')).toBe('nuclear_urban');
    expect(AsyncStorage.setItem).toHaveBeenCalledWith(
      expect.stringContaining('koota_local_questionnaire_state'),
      expect.stringContaining('nuclear_urban')
    );
  });

  test('submitAllAnswers formats payload and calls backend API', async () => {
    const spySubmit = jest.spyOn(authApi, 'submitAnswers').mockResolvedValueOnce({
      status: 'success',
      count: 2,
    });
    jest.spyOn(authApi, 'getProfileCompletion').mockResolvedValueOnce({
      is_complete: false,
      answered_count: 2,
      total_required: 42,
    });

    const wrapper = ({ children }: { children: React.ReactNode }) => (
      <QuestionnaireProvider>{children}</QuestionnaireProvider>
    );
    const { result } = renderHook(() => useQuestionnaire(), { wrapper });

    await act(async () => {
      await result.current.setAnswer(1, 0, 'objective', 'nuclear_urban');
      await result.current.setAnswer(1, 0, 'subjective', 'Childhood reflection text');
    });

    let success = false;
    await act(async () => {
      success = await result.current.submitAllAnswers('profile_123', 'token_xyz');
    });

    expect(success).toBe(true);
    expect(spySubmit).toHaveBeenCalledWith(
      'token_xyz',
      'profile_123',
      expect.arrayContaining([
        expect.objectContaining({ koota_id: 1, raw_value: 'nuclear_urban' }),
      ])
    );
  });
});
