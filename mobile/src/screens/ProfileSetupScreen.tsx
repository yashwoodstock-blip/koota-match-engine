import React, { useState } from 'react';
import {
  View,
  Text,
  TextInput,
  StyleSheet,
  TouchableOpacity,
  SafeAreaView,
  ScrollView,
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
import { createProfile } from '../api/authApi';
import { EditorialHeader } from '../components/EditorialHeader';
import { MainStackParamList } from '../navigation/types';

type ProfileNavProp = NativeStackNavigationProp<MainStackParamList, 'ProfileSetup'>;

const GENDERS = ['Male', 'Female', 'Other'];
const RELIGIONS = ['Hindu', 'Muslim', 'Sikh', 'Christian', 'Jain', 'Buddhist', 'Parsi', 'Other'];
const CASTE_PREFERENCES = [
  { label: 'No Preference / Open to all communities', value: 'no_preference' },
  { label: 'Same community preferred', value: 'same_caste_preferred' },
  { label: 'Same community strictly required', value: 'same_caste_required' },
];

export const ProfileSetupScreen: React.FC = () => {
  const navigation = useNavigation<ProfileNavProp>();
  const { session, profile, logout } = useAuth();

  const [name, setName] = useState<string>(profile?.name || '');
  const [age, setAge] = useState<string>('27');
  const [gender, setGender] = useState<string>('Male');
  const [religion, setReligion] = useState<string>('Hindu');
  const [caste, setCaste] = useState<string>('General / Open');
  const [castePreference, setCastePreference] = useState<string>('no_preference');
  const [city, setCity] = useState<string>('Bengaluru');

  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);

  const handleValidateAndSubmit = async () => {
    setError(null);

    if (!name.trim()) {
      setError('Please enter your full name.');
      return;
    }

    const numAge = parseInt(age, 10);
    if (isNaN(numAge) || numAge < 18 || numAge > 99) {
      setError('Age must be a valid number between 18 and 99.');
      return;
    }

    if (!city.trim()) {
      setError('Please enter your current city.');
      return;
    }

    if (!session?.access_token) {
      setError('Authentication session not found. Please log in again.');
      return;
    }

    try {
      setIsSubmitting(true);
      Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium).catch(() => {});

      await createProfile(session.access_token, {
        name: name.trim(),
        age: numAge,
        gender,
        religion,
        caste: caste.trim() || 'General',
        caste_preference: castePreference,
        city: city.trim(),
      });

      navigation.navigate('ObjectiveQuestionnaire');
    } catch (err: any) {
      setError(err?.message || 'Failed to create matrimonial profile.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <SafeAreaView style={styles.container}>
      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
        style={{ flex: 1 }}
      >
        <ScrollView contentContainerStyle={styles.scrollContent}>
          <EditorialHeader
            eyebrow="FOUNDATIONAL PROFILE • STEP 1"
            title="Essential Demographics"
            subtitle="These primary parameters establish your baseline matchmaking pool."
          />

          {error && (
            <View style={styles.errorBanner}>
              <Text style={styles.errorText}>⚠ {error}</Text>
            </View>
          )}

          {/* Full Name */}
          <View style={styles.fieldGroup}>
            <Text style={styles.label}>FULL NAME</Text>
            <TextInput
              style={styles.input}
              value={name}
              onChangeText={setName}
              placeholder="e.g. Aarav Sharma"
              placeholderTextColor={Colors.textMuted}
            />
          </View>

          {/* Age & City */}
          <View style={styles.row}>
            <View style={[styles.fieldGroup, { flex: 1, marginRight: 12 }]}>
              <Text style={styles.label}>AGE</Text>
              <TextInput
                style={styles.input}
                value={age}
                onChangeText={setAge}
                keyboardType="numeric"
                maxLength={2}
              />
            </View>
            <View style={[styles.fieldGroup, { flex: 2 }]}>
              <Text style={styles.label}>CURRENT CITY</Text>
              <TextInput
                style={styles.input}
                value={city}
                onChangeText={setCity}
                placeholder="e.g. Bengaluru"
                placeholderTextColor={Colors.textMuted}
              />
            </View>
          </View>

          {/* Gender */}
          <View style={styles.fieldGroup}>
            <Text style={styles.label}>GENDER</Text>
            <View style={styles.chipRow}>
              {GENDERS.map((g) => (
                <TouchableOpacity
                  key={g}
                  style={[styles.chip, gender === g ? styles.chipSelected : null]}
                  onPress={() => setGender(g)}
                  activeOpacity={0.8}
                >
                  <Text style={[styles.chipText, gender === g ? styles.chipTextSelected : null]}>
                    {g}
                  </Text>
                </TouchableOpacity>
              ))}
            </View>
          </View>

          {/* Religion */}
          <View style={styles.fieldGroup}>
            <Text style={styles.label}>RELIGION / FAITH TRADITION</Text>
            <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.chipScroll}>
              {RELIGIONS.map((r) => (
                <TouchableOpacity
                  key={r}
                  style={[styles.chip, religion === r ? styles.chipSelected : null]}
                  onPress={() => setReligion(r)}
                  activeOpacity={0.8}
                >
                  <Text style={[styles.chipText, religion === r ? styles.chipTextSelected : null]}>
                    {r}
                  </Text>
                </TouchableOpacity>
              ))}
            </ScrollView>
          </View>

          {/* Caste & Privacy Disclaimer */}
          <View style={styles.fieldGroup}>
            <Text style={styles.label}>COMMUNITY / CASTE CONTEXT</Text>
            <TextInput
              style={styles.input}
              value={caste}
              onChangeText={setCaste}
              placeholder="e.g. Brahmin, Khatri, Maratha, or Open"
              placeholderTextColor={Colors.textMuted}
            />
            <View style={styles.privacyNotice}>
              <Text style={styles.privacyIcon}>🔒</Text>
              <Text style={styles.privacyText}>
                Zero-Knowledge Privacy: Community data is processed exclusively on the backend for hard-filter compatibility and is never publicly shown on your profile card.
              </Text>
            </View>
          </View>

          {/* Caste Preference */}
          <View style={styles.fieldGroup}>
            <Text style={styles.label}>COMMUNITY PREFERENCE FILTER</Text>
            {CASTE_PREFERENCES.map((pref) => (
              <TouchableOpacity
                key={pref.value}
                style={[
                  styles.prefCard,
                  castePreference === pref.value ? styles.prefCardSelected : null,
                ]}
                onPress={() => setCastePreference(pref.value)}
                activeOpacity={0.85}
              >
                <Text
                  style={[
                    styles.prefText,
                    castePreference === pref.value ? styles.prefTextSelected : null,
                  ]}
                >
                  {pref.label}
                </Text>
              </TouchableOpacity>
            ))}
          </View>

          {/* Submit Action */}
          <TouchableOpacity
            style={[styles.submitButton, isSubmitting ? styles.submitButtonDisabled : null]}
            onPress={handleValidateAndSubmit}
            disabled={isSubmitting}
            activeOpacity={0.85}
          >
            {isSubmitting ? (
              <ActivityIndicator color={Colors.textInverse} />
            ) : (
              <Text style={styles.submitButtonText}>Begin 42-Koota Questionnaire →</Text>
            )}
          </TouchableOpacity>
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.background,
  },
  scrollContent: {
    paddingHorizontal: 24,
    paddingVertical: 20,
  },
  errorBanner: {
    backgroundColor: Colors.errorBackground,
    borderWidth: 1,
    borderColor: Colors.errorBorder,
    borderRadius: 12,
    padding: 12,
    marginBottom: 16,
  },
  errorText: {
    ...Typography.bodySecondary,
    color: Colors.error,
    fontSize: 13,
  },
  fieldGroup: {
    marginBottom: 20,
  },
  row: {
    flexDirection: 'row',
  },
  label: {
    ...Typography.caption,
    letterSpacing: 1,
    color: Colors.textSecondary,
    marginBottom: 8,
    fontWeight: '600',
  },
  input: {
    backgroundColor: Colors.surface,
    borderWidth: 1.5,
    borderColor: Colors.border,
    borderRadius: 12,
    paddingHorizontal: 16,
    paddingVertical: 12,
    fontSize: 16,
    color: Colors.text,
  },
  chipRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  chipScroll: {
    flexDirection: 'row',
  },
  chip: {
    backgroundColor: Colors.surface,
    borderWidth: 1.5,
    borderColor: Colors.border,
    borderRadius: 20,
    paddingHorizontal: 16,
    paddingVertical: 10,
    marginRight: 8,
  },
  chipSelected: {
    borderColor: Colors.primary,
    backgroundColor: Colors.primary,
  },
  chipText: {
    ...Typography.bodySecondary,
    fontSize: 14,
    color: Colors.text,
    fontWeight: '500',
  },
  chipTextSelected: {
    color: Colors.textInverse,
    fontWeight: '600',
  },
  privacyNotice: {
    flexDirection: 'row',
    backgroundColor: Colors.backgroundSecondary,
    borderRadius: 10,
    padding: 12,
    marginTop: 8,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  privacyIcon: {
    marginRight: 8,
    fontSize: 14,
  },
  privacyText: {
    ...Typography.caption,
    color: Colors.textSecondary,
    flex: 1,
    lineHeight: 16,
  },
  prefCard: {
    backgroundColor: Colors.surface,
    borderWidth: 1.5,
    borderColor: Colors.border,
    borderRadius: 12,
    padding: 14,
    marginBottom: 8,
  },
  prefCardSelected: {
    borderColor: Colors.primary,
    backgroundColor: '#FFF9F6',
  },
  prefText: {
    ...Typography.bodySecondary,
    color: Colors.text,
  },
  prefTextSelected: {
    color: Colors.primaryDark,
    fontWeight: '600',
  },
  submitButton: {
    backgroundColor: Colors.primary,
    paddingVertical: 16,
    borderRadius: 14,
    alignItems: 'center',
    marginTop: 16,
    marginBottom: 32,
    shadowColor: Colors.primary,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.25,
    shadowRadius: 8,
    elevation: 3,
  },
  submitButtonDisabled: {
    backgroundColor: Colors.textMuted,
  },
  submitButtonText: {
    ...Typography.button,
  },
});
