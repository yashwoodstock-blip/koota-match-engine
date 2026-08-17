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
import { useNavigation } from '@react-navigation/native';
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
      navigation.navigate('SubjectiveQuestionnaire');
    }
  };

  const handlePrev = () => {
    if (currentIndex > 0) {
      animateTransition('prev', () => {
        setCurrentIndex((prev) => prev - 1);
      });
    }
  };

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.headerBar}>
        <TouchableOpacity
          onPress={handlePrev}
          disabled={currentIndex === 0}
          style={[styles.navBtn, currentIndex === 0 ? styles.navBtnDisabled : null]}
        >
          <Text style={[styles.navBtnText, currentIndex === 0 ? styles.navBtnTextDisabled : null]}>
            ← Previous
          </Text>
        </TouchableOpacity>

        <Text style={styles.categoryBadge}>STAGE 1 • OBJECTIVE PASS</Text>

        <View style={{ width: 60 }} />
      </View>

      <View style={styles.content}>
        <QuestionnaireProgress
          current={currentIndex + 1}
          total={ALL_OBJECTIVE_QUESTIONS.length}
          pillarTitle={currentItem.koota.pillar}
        />

        <ScrollView showsVerticalScrollIndicator={false} contentContainerStyle={styles.scrollBody}>
          <Animated.View
            style={{
              opacity: fadeAnim,
              transform: [{ translateX: slideAnim }],
            }}
          >
            {/* Koota Card */}
            <View style={styles.kootaMeta}>
              <Text style={styles.kootaName}>
                {currentItem.koota.koota_id}. {currentItem.koota.name}
              </Text>
              {currentItem.koota.is_hard_filter && (
                <View style={styles.hardFilterBadge}>
                  <Text style={styles.hardFilterText}>CRITICAL GATEKEEPER</Text>
                </View>
              )}
            </View>

            <Text style={styles.questionText}>{currentItem.questionText}</Text>

            {/* Selectable Options */}
            <View style={styles.optionsList}>
              {currentItem.options.map((opt, idx) => (
                <SelectableCard
                  key={opt.value}
                  label={opt.label}
                  selected={selectedValue === opt.value}
                  onSelect={() => handleSelectOption(opt.value)}
                  index={idx}
                />
              ))}
            </View>
          </Animated.View>
        </ScrollView>

        {/* Footer Navigation */}
        <View style={styles.footer}>
          {error && (
            <View style={styles.errorContainer}>
              <Text style={styles.errorText}>⚠ {error}</Text>
            </View>
          )}

          <TouchableOpacity
            style={[
              styles.nextButton,
              !selectedValue || isSubmitting ? styles.nextButtonDisabled : null,
            ]}
            onPress={handleNext}
            disabled={!selectedValue || isSubmitting}
            activeOpacity={0.85}
          >
            {isSubmitting ? (
              <ActivityIndicator color={Colors.textInverse} />
            ) : (
              <Text style={styles.nextButtonText}>
                {currentIndex === ALL_OBJECTIVE_QUESTIONS.length - 1
                  ? 'Complete Objective Pass →'
                  : 'Save & Continue →'}
              </Text>
            )}
          </TouchableOpacity>
        </View>
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
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    paddingVertical: 10,
    borderBottomWidth: 1,
    borderBottomColor: Colors.border,
  },
  navBtn: {
    paddingVertical: 6,
    paddingHorizontal: 8,
  },
  navBtnDisabled: {
    opacity: 0.3,
  },
  navBtnText: {
    ...Typography.bodySecondary,
    fontWeight: '600',
    color: Colors.textSecondary,
  },
  navBtnTextDisabled: {
    color: Colors.textMuted,
  },
  categoryBadge: {
    ...Typography.caption,
    color: Colors.accentDark,
    letterSpacing: 1,
    fontWeight: '700',
  },
  content: {
    flex: 1,
    paddingHorizontal: 24,
    justifyContent: 'space-between',
  },
  scrollBody: {
    paddingVertical: 16,
  },
  kootaMeta: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 10,
  },
  kootaName: {
    ...Typography.headline,
    fontSize: 20,
    lineHeight: 28,
    fontFamily: 'serif',
    color: Colors.primary,
    flex: 1,
  },
  hardFilterBadge: {
    backgroundColor: Colors.errorBackground,
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 6,
    borderWidth: 1,
    borderColor: Colors.errorBorder,
  },
  hardFilterText: {
    ...Typography.caption,
    fontSize: 10,
    color: Colors.error,
    fontWeight: '700',
  },
  questionText: {
    ...Typography.body,
    fontSize: 16,
    lineHeight: 24,
    color: Colors.text,
    marginBottom: 20,
    fontStyle: 'italic',
  },
  optionsList: {
    marginTop: 8,
  },
  footer: {
    paddingVertical: 16,
  },
  errorContainer: {
    backgroundColor: Colors.errorBackground,
    padding: 8,
    borderRadius: 8,
    marginBottom: 8,
  },
  errorText: {
    ...Typography.caption,
    color: Colors.error,
    textAlign: 'center',
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
    backgroundColor: Colors.textMuted,
    shadowOpacity: 0,
    elevation: 0,
  },
  nextButtonText: {
    ...Typography.button,
  },
});
