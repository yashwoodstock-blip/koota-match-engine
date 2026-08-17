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
import { useNavigation, useRoute, RouteProp } from '@react-navigation/native';
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
type ScreenRouteProp = RouteProp<MainStackParamList, 'SubjectiveQuestionnaire'>;

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
  let isEditMode = false;
  try {
    const route = useRoute<ScreenRouteProp>();
    isEditMode = !!route?.params?.isEditMode;
  } catch {
    isEditMode = false;
  }

  const { session, profile } = useAuth();
  const { setAnswer, getAnswer, submitAllAnswers, refreshCompletion, isSubmitting, error } =
    useQuestionnaire();

  const [currentIndex, setCurrentIndex] = useState<number>(0);
  const fadeAnim = useRef(new Animated.Value(1)).current;
  const slideAnim = useRef(new Animated.Value(0)).current;

  const currentItem = ALL_SUBJECTIVE_QUESTIONS[currentIndex];
  const textValue =
    getAnswer(currentItem.koota.koota_id, currentItem.qIndex, 'subjective') || '';

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

  const handleChangeText = (val: string) => {
    setAnswer(currentItem.koota.koota_id, currentItem.qIndex, 'subjective', val);
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
      if (isEditMode) {
        navigation.navigate('EditProfile');
      } else {
        navigation.navigate('Home');
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
      await refreshCompletion(profile.id, session.access_token);
    }
    navigation.navigate('EditProfile');
  };

  return (
    <SafeAreaView style={styles.container}>
      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
        style={{ flex: 1 }}
      >
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

          <View style={styles.batchBadge}>
            <Text style={styles.batchText}>
              {isEditMode ? 'EDITING RESPONSES' : `BATCH ${currentItem.batchNumber} • REFLECTIONS`}
            </Text>
          </View>

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
          total={ALL_SUBJECTIVE_QUESTIONS.length}
          pillarTitle={`${currentItem.koota.pillar} • ${currentItem.koota.name}`}
        />

        {/* Question & Reflection input */}
        <ScrollView
          contentContainerStyle={styles.scrollContent}
          showsVerticalScrollIndicator={false}
        >
          <Animated.View
            style={[
              styles.card,
              {
                opacity: fadeAnim,
                transform: [{ translateX: slideAnim }],
              },
            ]}
          >
            <Text style={styles.pillarEyebrow}>{currentItem.koota.pillar.toUpperCase()}</Text>
            <Text style={styles.kootaTitle}>
              {currentItem.koota.koota_id}. {currentItem.koota.name}
            </Text>
            <Text style={styles.questionPrompt}>{currentItem.questionText}</Text>

            {/* Reflection Input */}
            <View style={styles.inputContainer}>
              <TextInput
                style={styles.textInput}
                value={textValue}
                onChangeText={handleChangeText}
                placeholder="Share your authentic perspective... (at least 2–3 sentences recommended)"
                placeholderTextColor={Colors.textMuted}
                multiline
                numberOfLines={6}
                textAlignVertical="top"
                autoCapitalize="sentences"
                accessibilityLabel="Reflective Answer Input"
              />
              <View style={styles.inputMeta}>
                <Text style={styles.charCount}>
                  {textValue.length} characters
                  {textValue.length < 40 ? ' (aim for 40+ for deeper embeddings)' : ' ✓'}
                </Text>
              </View>
            </View>

            {/* Existential Veto Notice for Koota 41 */}
            {currentItem.koota.koota_id === 41 && (
              <View style={styles.vetoCallout}>
                <Text style={styles.vetoIcon}>✦</Text>
                <Text style={styles.vetoText}>
                  FOUNDATIONAL PILLAR: Koota 41 reflects your existential vision of marriage.
                  Honesty here prevents long-term misalignment.
                </Text>
              </View>
            )}
          </Animated.View>
        </ScrollView>

        {/* Footer Navigation */}
        <View style={styles.footer}>
          <TouchableOpacity
            style={[styles.nextButton, !textValue.trim() && styles.nextButtonDisabled]}
            onPress={handleNext}
            disabled={!textValue.trim() || isSubmitting}
            activeOpacity={0.85}
            accessibilityRole="button"
            accessibilityLabel={
              currentIndex === ALL_SUBJECTIVE_QUESTIONS.length - 1
                ? 'Save and Complete'
                : 'Next Reflection'
            }
          >
            {isSubmitting ? (
              <ActivityIndicator color={Colors.textInverse} />
            ) : (
              <Text style={styles.nextButtonText}>
                {currentIndex === ALL_SUBJECTIVE_QUESTIONS.length - 1
                  ? isEditMode
                    ? 'Save & Return to Settings →'
                    : 'Save & Complete Questionnaire ✨'
                  : 'Save Reflection & Next →'}
              </Text>
            )}
          </TouchableOpacity>
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
  batchBadge: {
    backgroundColor: Colors.backgroundSecondary,
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  batchText: {
    ...Typography.caption,
    fontSize: 10,
    letterSpacing: 1,
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
  card: {
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
  pillarEyebrow: {
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
  inputContainer: {
    borderRadius: 14,
    borderWidth: 1.5,
    borderColor: Colors.border,
    backgroundColor: Colors.backgroundSecondary,
    padding: 14,
  },
  textInput: {
    ...Typography.body,
    fontSize: 15,
    lineHeight: 22,
    color: Colors.text,
    minHeight: 120,
  },
  inputMeta: {
    flexDirection: 'row',
    justifyContent: 'flex-end',
    marginTop: 8,
  },
  charCount: {
    ...Typography.caption,
    fontSize: 11,
    color: Colors.textMuted,
  },
  vetoCallout: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#FFF9E6',
    borderWidth: 1,
    borderColor: '#FFE08A',
    borderRadius: 12,
    padding: 12,
    marginTop: 18,
  },
  vetoIcon: {
    color: Colors.accentDark,
    fontSize: 16,
    marginRight: 8,
  },
  vetoText: {
    ...Typography.caption,
    fontSize: 11,
    lineHeight: 16,
    color: Colors.accentDark,
    flex: 1,
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
