import React, { useState, useRef } from 'react';
import {
  View,
  Text,
  TextInput,
  StyleSheet,
  TouchableOpacity,
  SafeAreaView,
  ScrollView,
  Animated,
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform,
} from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import * as Haptics from 'expo-haptics';
import { Colors } from '../theme/colors';
import { Typography } from '../theme/typography';
import { useAuth } from '../context/AuthContext';
import { useQuestionnaire } from '../context/QuestionnaireContext';
import { KOOTAS_DATA, KootaDefinition } from '../data/kootas';
import { QuestionnaireProgress } from '../components/QuestionnaireProgress';
import { MainStackParamList } from '../navigation/types';

type NavProp = NativeStackNavigationProp<MainStackParamList, 'SubjectiveQuestionnaire'>;

interface FlatSubjectiveQuestion {
  koota: KootaDefinition;
  qIndex: number;
  questionText: string;
  batchNumber: number;
}

// Flatten and batch subjective questions
const ALL_SUBJECTIVE_QUESTIONS: FlatSubjectiveQuestion[] = [];
KOOTAS_DATA.forEach((koota) => {
  let batch = 1;
  if (koota.koota_id > 16 && koota.koota_id <= 30) batch = 2;
  if (koota.koota_id > 30) batch = 3;

  koota.subjective_questions.forEach((qText, qIdx) => {
    ALL_SUBJECTIVE_QUESTIONS.push({
      koota,
      qIndex: qIdx,
      questionText: qText,
      batchNumber: batch,
    });
  });
});

export const SubjectiveQuestionnaireScreen: React.FC = () => {
  const navigation = useNavigation<NavProp>();
  const { session, profile } = useAuth();
  const { setAnswer, getAnswer, submitAllAnswers, refreshCompletion, isSubmitting, error } =
    useQuestionnaire();

  const [currentIndex, setCurrentIndex] = useState<number>(0);
  const fadeAnim = useRef(new Animated.Value(1)).current;
  const slideAnim = useRef(new Animated.Value(0)).current;

  const currentItem = ALL_SUBJECTIVE_QUESTIONS[currentIndex];
  const textValue = getAnswer(currentItem.koota.koota_id, currentItem.qIndex, 'subjective');

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

  const handleTextChange = (text: string) => {
    setAnswer(currentItem.koota.koota_id, currentItem.qIndex, 'subjective', text);
  };

  const handleNext = async () => {
    if (!textValue.trim()) return;

    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light).catch(() => {});

    // Submit in background
    if (profile?.id && session?.access_token) {
      submitAllAnswers(profile.id, session.access_token).catch(() => {});
    }

    if (currentIndex < ALL_SUBJECTIVE_QUESTIONS.length - 1) {
      animateTransition('next', () => {
        setCurrentIndex((prev) => prev + 1);
      });
    } else {
      // Completed full subjective pass!
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success).catch(() => {});
      if (profile?.id && session?.access_token) {
        await submitAllAnswers(profile.id, session.access_token);
        await refreshCompletion(profile.id, session.access_token);
      }
      navigation.navigate('Home');
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
      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
        style={{ flex: 1 }}
      >
        <View style={styles.headerBar}>
          <TouchableOpacity
            onPress={handlePrev}
            disabled={currentIndex === 0}
            style={[styles.navBtn, currentIndex === 0 ? styles.navBtnDisabled : null]}
          >
            <Text
              style={[
                styles.navBtnText,
                currentIndex === 0 ? styles.navBtnTextDisabled : null,
              ]}
            >
              ← Previous
            </Text>
          </TouchableOpacity>

          <View style={styles.batchBadge}>
            <Text style={styles.batchText}>BATCH {currentItem.batchNumber} • REFLECTIONS</Text>
          </View>

          <View style={{ width: 60 }} />
        </View>

        <View style={styles.content}>
          <QuestionnaireProgress
            current={currentIndex + 1}
            total={ALL_SUBJECTIVE_QUESTIONS.length}
            pillarTitle={currentItem.koota.pillar}
          />

          <ScrollView showsVerticalScrollIndicator={false} contentContainerStyle={styles.scrollBody}>
            <Animated.View
              style={{
                opacity: fadeAnim,
                transform: [{ translateX: slideAnim }],
              }}
            >
              {/* Koota Metadata */}
              <View style={styles.kootaMeta}>
                <Text style={styles.kootaName}>
                  {currentItem.koota.koota_id}. {currentItem.koota.name}
                </Text>
                {currentItem.koota.koota_id === 41 && (
                  <View style={styles.vetoBadge}>
                    <Text style={styles.vetoText}>FOUNDATIONAL EXISTENTIAL VETO</Text>
                  </View>
                )}
              </View>

              <Text style={styles.questionText}>"{currentItem.questionText}"</Text>

              <View style={styles.inputContainer}>
                <TextInput
                  style={styles.textInput}
                  multiline
                  numberOfLines={6}
                  value={textValue}
                  onChangeText={handleTextChange}
                  placeholder="Share your authentic perspective. Thoughtful reflections create mathematically superior matches..."
                  placeholderTextColor={Colors.textMuted}
                  textAlignVertical="top"
                />
                <View style={styles.charCountContainer}>
                  <Text
                    style={[
                      styles.charCount,
                      textValue.length >= 40 ? styles.charCountGood : null,
                    ]}
                  >
                    {textValue.length} characters (min 40 recommended)
                  </Text>
                </View>
              </View>

              <View style={styles.editorialNote}>
                <Text style={styles.noteIcon}>✦</Text>
                <Text style={styles.noteText}>
                  Zero-Knowledge Privacy: Raw text responses are never displayed to matches. They are analyzed exclusively by our NLI model and Groq Llama-3.3-70B judge for semantic alignment.
                </Text>
              </View>
            </Animated.View>
          </ScrollView>

          {/* Footer Action */}
          <View style={styles.footer}>
            {error && (
              <View style={styles.errorContainer}>
                <Text style={styles.errorText}>⚠ {error}</Text>
              </View>
            )}

            <TouchableOpacity
              style={[
                styles.nextButton,
                !textValue.trim() || isSubmitting ? styles.nextButtonDisabled : null,
              ]}
              onPress={handleNext}
              disabled={!textValue.trim() || isSubmitting}
              activeOpacity={0.85}
            >
              {isSubmitting ? (
                <ActivityIndicator color={Colors.textInverse} />
              ) : (
                <Text style={styles.nextButtonText}>
                  {currentIndex === ALL_SUBJECTIVE_QUESTIONS.length - 1
                    ? 'Finalize All 42 Kootas ✓'
                    : 'Save Reflection & Next →'}
                </Text>
              )}
            </TouchableOpacity>
          </View>
        </View>
      </KeyboardAvoidingView>
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
  batchBadge: {
    backgroundColor: Colors.backgroundSecondary,
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  batchText: {
    ...Typography.caption,
    fontSize: 11,
    color: Colors.accentDark,
    fontWeight: '700',
    letterSpacing: 0.8,
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
    marginBottom: 10,
  },
  kootaName: {
    ...Typography.headline,
    fontSize: 22,
    lineHeight: 30,
    fontFamily: 'serif',
    color: Colors.primary,
  },
  vetoBadge: {
    backgroundColor: Colors.errorBackground,
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 6,
    borderWidth: 1,
    borderColor: Colors.errorBorder,
    alignSelf: 'flex-start',
    marginTop: 6,
  },
  vetoText: {
    ...Typography.caption,
    fontSize: 10,
    color: Colors.error,
    fontWeight: '800',
    letterSpacing: 0.5,
  },
  questionText: {
    ...Typography.body,
    fontSize: 17,
    lineHeight: 26,
    color: Colors.text,
    marginVertical: 16,
    fontStyle: 'italic',
  },
  inputContainer: {
    backgroundColor: Colors.surface,
    borderWidth: 1.5,
    borderColor: Colors.border,
    borderRadius: 14,
    padding: 16,
    shadowColor: Colors.text,
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 4,
    elevation: 2,
  },
  textInput: {
    ...Typography.body,
    fontSize: 15,
    lineHeight: 22,
    color: Colors.text,
    minHeight: 120,
  },
  charCountContainer: {
    alignItems: 'flex-end',
    marginTop: 8,
    borderTopWidth: 1,
    borderTopColor: Colors.border,
    paddingTop: 6,
  },
  charCount: {
    ...Typography.caption,
    color: Colors.textMuted,
  },
  charCountGood: {
    color: Colors.success,
    fontWeight: '600',
  },
  editorialNote: {
    flexDirection: 'row',
    backgroundColor: Colors.backgroundSecondary,
    padding: 14,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: Colors.border,
    marginTop: 20,
  },
  noteIcon: {
    color: Colors.accentDark,
    marginRight: 10,
    fontSize: 14,
  },
  noteText: {
    ...Typography.caption,
    color: Colors.textSecondary,
    flex: 1,
    lineHeight: 18,
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
