import React, { createContext, useContext, useEffect, useState } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';
import {
  submitAnswers,
  getProfileCompletion,
  AnswerItem,
  CompletionStatusResponse,
} from '../api/authApi';
import { KOOTAS_DATA } from '../data/kootas';

const STORAGE_KEY = 'koota_local_questionnaire_state_v1';

export type AnswerKey = `${number}_${number}_${'objective' | 'subjective'}`;

interface QuestionnaireState {
  answers: Record<string, string>;
  isSaving: boolean;
  isSubmitting: boolean;
  error: string | null;
  completionStatus: CompletionStatusResponse | null;
  setAnswer: (
    kootaId: number,
    questionIndex: number,
    questionType: 'objective' | 'subjective',
    rawValue: string
  ) => Promise<void>;
  getAnswer: (
    kootaId: number,
    questionIndex: number,
    questionType: 'objective' | 'subjective'
  ) => string;
  submitAllAnswers: (profileId: string, token: string) => Promise<boolean>;
  refreshCompletion: (profileId: string, token: string) => Promise<boolean>;
  clearLocalAnswers: () => Promise<void>;
}

const QuestionnaireContext = createContext<QuestionnaireState | undefined>(undefined);

export const QuestionnaireProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [isSaving, setIsSaving] = useState<boolean>(false);
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [completionStatus, setCompletionStatus] = useState<CompletionStatusResponse | null>(null);

  // Restore local answers from storage on mount
  useEffect(() => {
    async function loadSavedState() {
      try {
        const saved = await AsyncStorage.getItem(STORAGE_KEY);
        if (saved) {
          const parsed = JSON.parse(saved);
          if (parsed && typeof parsed === 'object') {
            setAnswers(parsed);
          }
        }
      } catch (e) {
        console.warn('[QuestionnaireContext] Failed to restore local answers:', e);
      }
    }
    loadSavedState();
  }, []);

  const setAnswer = async (
    kootaId: number,
    questionIndex: number,
    questionType: 'objective' | 'subjective',
    rawValue: string
  ) => {
    const key = `${kootaId}_${questionIndex}_${questionType}`;
    const updated = { ...answers, [key]: rawValue };
    setAnswers(updated);

    try {
      setIsSaving(true);
      await AsyncStorage.setItem(STORAGE_KEY, JSON.stringify(updated));
    } catch (e) {
      console.warn('[QuestionnaireContext] Failed to persist answer locally:', e);
    } finally {
      setIsSaving(false);
    }
  };

  const getAnswer = (
    kootaId: number,
    questionIndex: number,
    questionType: 'objective' | 'subjective'
  ): string => {
    const key = `${kootaId}_${questionIndex}_${questionType}`;
    return answers[key] || '';
  };

  const submitAllAnswers = async (profileId: string, token: string): Promise<boolean> => {
    try {
      setIsSubmitting(true);
      setError(null);

      const payload: AnswerItem[] = Object.entries(answers).map(([key, raw_value]) => {
        const [kId, qIdx, qType] = key.split('_');
        return {
          koota_id: parseInt(kId, 10),
          question_index: parseInt(qIdx, 10),
          question_type: qType as 'objective' | 'subjective',
          raw_value,
        };
      });

      if (payload.length === 0) {
        return false;
      }

      await submitAnswers(token, profileId, payload);
      await refreshCompletion(profileId, token);
      return true;
    } catch (err: any) {
      setError(err?.message || 'Failed to submit answers to matching engine.');
      return false;
    } finally {
      setIsSubmitting(false);
    }
  };

  const refreshCompletion = async (profileId: string, token: string): Promise<boolean> => {
    try {
      const res = await getProfileCompletion(token, profileId);
      setCompletionStatus(res);
      return res.is_complete;
    } catch (err) {
      console.warn('[QuestionnaireContext] Completion query error:', err);
      return false;
    }
  };

  const clearLocalAnswers = async () => {
    try {
      await AsyncStorage.removeItem(STORAGE_KEY);
      setAnswers({});
    } catch (e) {
      console.warn('[QuestionnaireContext] Failed to clear local storage:', e);
    }
  };

  return (
    <QuestionnaireContext.Provider
      value={{
        answers,
        isSaving,
        isSubmitting,
        error,
        completionStatus,
        setAnswer,
        getAnswer,
        submitAllAnswers,
        refreshCompletion,
        clearLocalAnswers,
      }}
    >
      {children}
    </QuestionnaireContext.Provider>
  );
};

export const useQuestionnaire = (): QuestionnaireState => {
  const context = useContext(QuestionnaireContext);
  if (!context) {
    throw new Error('useQuestionnaire must be used within a QuestionnaireProvider');
  }
  return context;
};
