import React, { useState, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  SafeAreaView,
  ScrollView,
  Animated,
  ActivityIndicator,
} from 'react-native';
import { useNavigation, useRoute, RouteProp } from '@react-navigation/native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import * as Haptics from 'expo-haptics';
import { Colors } from '../theme/colors';
import { Typography } from '../theme/typography';
import { useAuth } from '../context/AuthContext';
import { useQuestionnaire } from '../context/QuestionnaireContext';
import { KOOTAS_DATA, KootaDefinition } from '../data/kootas';
import { OBJECTIVE_OPTIONS, QuestionOption } from '../data/kootaOptions';
import { QuestionnaireProgress } from '../components/QuestionnaireProgress';
import { SelectableCard } from '../components/SelectableCard';
import { MainStackParamList } from '../navigation/types';

type NavProp = NativeStackNavigationProp<MainStackParamList, 'ObjectiveQuestionnaire'>;
type ScreenRouteProp = RouteProp<MainStackParamList, 'ObjectiveQuestionnaire'>;

interface FlatObjectiveQuestion {
  koota: KootaDefinition;
  qIndex: number;
  questionText: string;
  options: QuestionOption[];
}

// Flatten all objective questions
const ALL_OBJECTIVE_QUESTIONS: FlatObjectiveQuestion[] = [];
KOOTAS_DATA.forEach((koota) => {
  koota.objective_questions.forEach((qText, qIdx) => {
    const key = `${koota.koota_id}_${qIdx}`;
    const opts = OBJECTIVE_OPTIONS[key] || [
      { label: "Option A", value: "opt_a" },
      { label: "Option B", value: "opt_b" },
      { label: "Option C", value: "opt_c" },
    ];
    ALL_OBJECTIVE_QUESTIONS.push({
      koota,
      qIndex: qIdx,
      questionText: qText,
      options: opts,
    });
  });
});

export const ObjectiveQuestionnaireScreen: React.FC = () => {
  const navigation = useNavigation<NavProp>();
  let isEditMode = false;
  try {
    const route = useRoute<ScreenRouteProp>();
    isEditMode = !!route?.params?.isEditMode;
  } catch {
    isEditMode = false;
  }

  const { session, profile } = useAuth();
  const { setAnswer, getAnswer, submitAllAnswers, isSubmitting, error } = useQuestionnaire();

  const [currentIndex, setCurrentIndex] = useState<number>(0);
  const fadeAnim = useRef(new Animated.Value(1)).current;
  const slideAnim = useRef(new Animated.Value(0)).current;

  const currentItem = ALL_OBJECTIVE_QUESTIONS[currentIndex];
  const selectedValue = getAnswer(currentItem.koota.koota_id, currentItem.qIndex, 'objective');

  const animateTransition = (direction: 'next' | 'prev', callback: () => void) => {
    const slideOffset = direction === 'next' ? -30 : 30;

    Animated.parallel([
      Animated.timing(fadeAnim, {
        toValue: 0,
        duration: 120,
        useNativeDriver: true,
      }),
      Animated.timing(slideAnim, {
        toValue: slideOffset,
        duration: 120,
        useNativeDriver: true,
      }),
    ]).start(() => {
      callback();
      slideAnim.setValue(direction === 'next' ? 30 : -30);
      Animated.parallel([
        Animated.timing(fadeAnim, {
          toValue: 1,
          duration: 180,
          useNativeDriver: true,
        }),
        Animated.spring(slideAnim, {
          toValue: 0,
          tension: 80,
          friction: 8,
          useNativeDriver: true,
        }),
      ]).start();
    });
  };

  const handleSelectOption = (value: string) => {
    setAnswer(currentItem.koota.koota_id, currentItem.qIndex, 'objective', value);
  };

  const handleNext = async () => {
    if (!selectedValue) return;

    if (currentIndex < ALL_OBJECTIVE_QUESTIONS.length - 1) {
      animateTransition('next', () => {
        setCurrentIndex((prev) => prev + 1);
      });
    } else {
      // Completed all objective questions!
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success).catch(() => {});
      if (profile?.id && session?.access_token) {
        await submitAllAnswers(profile.id, session.access_token);
      }
      if (isEditMode) {
        navigation.navigate('EditProfile');
      } else {
        navigation.navigate('SubjectiveQuestionnaire');
      }
    }
  };

  const handlePrev = () => {
    if (currentIndex > 0) {
      animateTransition('prev', () => {
        setCurrentIndex((prev) => prev - 1);
      });
    }
  };

  const handleSaveAndExit = async () => {
    if (profile?.id && session?.access_token) {
      await submitAllAnswers(profile.id, session.access_token);
    }
    navigation.navigate('EditProfile');
  };

  return (
    <SafeAreaView style={styles.container}>
      {/* Top Header Bar */}
      <View style={styles.headerBar}>
        <TouchableOpacity
          onPress={isEditMode && currentIndex === 0 ? handleSaveAndExit : handlePrev}
          disabled={!isEditMode && currentIndex === 0}
          style={[styles.navBtn, !isEditMode && currentIndex === 0 ? styles.navBtnDisabled : null]}
        >
          <Text
            style={[
              styles.navBtnText,
              !isEditMode && currentIndex === 0 ? styles.navBtnTextDisabled : null,
            ]}
          >
            {isEditMode && currentIndex === 0 ? '← Settings' : '← Previous'}
          </Text>
        </TouchableOpacity>

        <Text style={styles.categoryBadge}>
          {isEditMode ? 'EDITING • OBJECTIVE PASS' : 'STAGE 1 • OBJECTIVE PASS'}
        </Text>

        {isEditMode && (
          <TouchableOpacity onPress={handleSaveAndExit} style={styles.finishBtn}>
            <Text style={styles.finishBtnText}>Done</Text>
          </TouchableOpacity>
        )}
      </View>

      {/* Edit Mode Notice */}
      {isEditMode && (
        <View style={styles.editModeNotice}>
          <Text style={styles.editModeNoticeText}>
            Updating answers will invalidate active matches and trigger fresh calculations.
          </Text>
        </View>
      )}

      {/* Progress */}
      <QuestionnaireProgress
        current={currentIndex + 1}
        total={ALL_OBJECTIVE_QUESTIONS.length}
        pillarTitle={`${currentItem.koota.pillar} • ${currentItem.koota.name}`}
      />

      {error && (
        <View style={styles.errorBox}>
          <Text style={styles.errorText}>⚠ {error}</Text>
        </View>
      )}

      {/* Question Body */}
      <ScrollView
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
      >
        <Animated.View
          style={[
            styles.questionCard,
            {
              opacity: fadeAnim,
              transform: [{ translateX: slideAnim }],
            },
          ]}
        >
          <Text style={styles.kootaPillar}>{currentItem.koota.pillar.toUpperCase()}</Text>
          <Text style={styles.kootaTitle}>
            {currentItem.koota.koota_id}. {currentItem.koota.name}
          </Text>
          <Text style={styles.questionPrompt}>{currentItem.questionText}</Text>

          {/* Options */}
          <View style={styles.optionsList}>
            {currentItem.options.map((option) => (
              <SelectableCard
                key={option.value}
                label={option.label}
                selected={selectedValue === option.value}
                onSelect={() => handleSelectOption(option.value)}
              />
            ))}
          </View>
        </Animated.View>
      </ScrollView>

      {/* Footer Navigation */}
      <View style={styles.footer}>
        <TouchableOpacity
          style={[styles.nextButton, !selectedValue && styles.nextButtonDisabled]}
          onPress={handleNext}
          disabled={!selectedValue || isSubmitting}
          activeOpacity={0.85}
          accessibilityRole="button"
          accessibilityLabel={
            currentIndex === ALL_OBJECTIVE_QUESTIONS.length - 1
              ? 'Save and Continue'
              : 'Next Question'
          }
        >
          {isSubmitting ? (
            <ActivityIndicator color={Colors.textInverse} />
          ) : (
            <Text style={styles.nextButtonText}>
              {currentIndex === ALL_OBJECTIVE_QUESTIONS.length - 1
                ? isEditMode
                  ? 'Save & Return to Settings →'
                  : 'Save & Proceed to Reflective Stage →'
                : 'Next Question →'}
            </Text>
          )}
        </TouchableOpacity>
      </View>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.background,
  },
  headerBar: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingTop: 10,
    paddingBottom: 4,
  },
  navBtn: {
    paddingVertical: 6,
    paddingHorizontal: 8,
  },
  navBtnDisabled: {
    opacity: 0.2,
  },
  navBtnText: {
    ...Typography.caption,
    color: Colors.textSecondary,
    fontWeight: '700',
  },
  navBtnTextDisabled: {
    color: Colors.textMuted,
  },
  categoryBadge: {
    ...Typography.caption,
    fontSize: 10,
    letterSpacing: 1.5,
    color: Colors.accentDark,
    fontWeight: '800',
  },
  finishBtn: {
    backgroundColor: Colors.backgroundSecondary,
    paddingHorizontal: 12,
    paddingVertical: 5,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  finishBtnText: {
    ...Typography.caption,
    fontWeight: '700',
    color: Colors.primary,
  },
  editModeNotice: {
    backgroundColor: '#FFF9E6',
    paddingVertical: 6,
    paddingHorizontal: 20,
    borderBottomWidth: 1,
    borderBottomColor: '#FFE08A',
  },
  editModeNoticeText: {
    ...Typography.caption,
    fontSize: 11,
    color: Colors.accentDark,
    textAlign: 'center',
  },
  scrollContent: {
    paddingHorizontal: 20,
    paddingBottom: 24,
  },
  questionCard: {
    backgroundColor: Colors.surface,
    borderRadius: 20,
    padding: 24,
    marginTop: 8,
    borderWidth: 1.5,
    borderColor: Colors.border,
    shadowColor: Colors.text,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.05,
    shadowRadius: 10,
    elevation: 2,
  },
  kootaPillar: {
    ...Typography.caption,
    color: Colors.accentDark,
    letterSpacing: 1.5,
    marginBottom: 4,
  },
  kootaTitle: {
    ...Typography.headline,
    fontSize: 22,
    lineHeight: 28,
    fontFamily: 'serif',
    color: Colors.primary,
    marginBottom: 14,
  },
  questionPrompt: {
    ...Typography.body,
    fontSize: 16,
    lineHeight: 24,
    color: Colors.text,
    marginBottom: 20,
  },
  optionsList: {
    gap: 4,
  },
  errorBox: {
    marginHorizontal: 20,
    marginBottom: 10,
    padding: 10,
    backgroundColor: Colors.errorBackground,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: Colors.errorBorder,
  },
  errorText: {
    ...Typography.caption,
    color: Colors.error,
    textAlign: 'center',
  },
  footer: {
    paddingHorizontal: 20,
    paddingVertical: 16,
    borderTopWidth: 1,
    borderTopColor: Colors.border,
    backgroundColor: Colors.background,
  },
  nextButton: {
    backgroundColor: Colors.primary,
    paddingVertical: 16,
    borderRadius: 14,
    alignItems: 'center',
    shadowColor: Colors.primary,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.25,
    shadowRadius: 8,
    elevation: 3,
  },
  nextButtonDisabled: {
    opacity: 0.4,
    shadowOpacity: 0,
    elevation: 0,
  },
  nextButtonText: {
    ...Typography.button,
    color: Colors.textInverse,
    fontWeight: '700',
    fontSize: 15,
  },
});
