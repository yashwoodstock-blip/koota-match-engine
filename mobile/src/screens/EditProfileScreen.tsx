import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  TextInput,
  StyleSheet,
  TouchableOpacity,
  SafeAreaView,
  ScrollView,
  KeyboardAvoidingView,
  Platform,
  ActivityIndicator,
  Alert,
} from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import * as Haptics from 'expo-haptics';
import { Colors } from '../theme/colors';
import { Typography } from '../theme/typography';
import { useAuth } from '../context/AuthContext';
import {
  getProfileDetails,
  updateProfile,
  deleteProfile,
  ProfileCreatePayload,
  ProfileResponse,
} from '../api/authApi';
import { HardFilterWarningModal } from '../components/HardFilterWarningModal';
import { DeleteAccountModal } from '../components/DeleteAccountModal';
import { EditorialHeader } from '../components/EditorialHeader';
import { MainStackParamList } from '../navigation/types';

type NavProp = NativeStackNavigationProp<MainStackParamList, 'EditProfile'>;

const GENDERS = ['male', 'female', 'non-binary'];
const CASTE_PREFS = [
  { label: 'No Community Preference', value: 'no_preference' },
  { label: 'Same Community Preferred', value: 'same_caste_preferred' },
  { label: 'Same Community Required (Hard Filter)', value: 'same_caste_required' },
];

export const EditProfileScreen: React.FC = () => {
  const navigation = useNavigation<NavProp>();
  const { session, profile, logout } = useAuth();

  const [initialData, setInitialData] = useState<ProfileResponse | null>(null);
  const [name, setName] = useState<string>('');
  const [age, setAge] = useState<string>('');
  const [gender, setGender] = useState<string>('male');
  const [religion, setReligion] = useState<string>('Hindu');
  const [caste, setCaste] = useState<string>('');
  const [castePreference, setCastePreference] = useState<string>('no_preference');
  const [city, setCity] = useState<string>('');

  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isSaving, setIsSaving] = useState<boolean>(false);
  const [isDeleting, setIsDeleting] = useState<boolean>(false);
  const [saveSuccessMsg, setSaveSuccessMsg] = useState<string | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const [showHardFilterModal, setShowHardFilterModal] = useState<boolean>(false);
  const [showDeleteModal, setShowDeleteModal] = useState<boolean>(false);

  useEffect(() => {
    const fetchProfile = async () => {
      if (!session?.access_token || !profile?.id) return;
      try {
        setIsLoading(true);
        const data = await getProfileDetails(session.access_token, profile.id);
        setInitialData(data);
        setName(data.name || '');
        setAge(data.age ? String(data.age) : '28');
        setGender(data.gender || 'male');
        setReligion(data.religion || 'Hindu');
        setCaste(data.caste || '');
        setCastePreference(data.caste_preference || 'no_preference');
        setCity(data.city || '');
      } catch (err: any) {
        setErrorMsg('Failed to load profile details.');
      } finally {
        setIsLoading(false);
      }
    };
    fetchProfile();
  }, [session?.access_token, profile?.id]);

  // Compute changed partial payload
  const getChangedPayload = (): Partial<ProfileCreatePayload> => {
    if (!initialData) return {};
    const payload: Partial<ProfileCreatePayload> = {};

    if (name.trim() !== (initialData.name || '')) payload.name = name.trim();
    const parsedAge = parseInt(age, 10);
    if (!isNaN(parsedAge) && parsedAge !== initialData.age) payload.age = parsedAge;
    if (gender !== (initialData.gender || '')) payload.gender = gender;
    if (religion.trim() !== (initialData.religion || '')) payload.religion = religion.trim();
    if (caste.trim() !== (initialData.caste || '')) payload.caste = caste.trim();
    if (castePreference !== (initialData.caste_preference || 'no_preference')) {
      payload.caste_preference = castePreference;
    }
    if (city.trim() !== (initialData.city || '')) payload.city = city.trim();

    return payload;
  };

  const handlePressSave = () => {
    setErrorMsg(null);
    setSaveSuccessMsg(null);

    const changed = getChangedPayload();
    if (Object.keys(changed).length === 0) {
      setSaveSuccessMsg('No changes detected.');
      return;
    }

    // Check if hard-filter fields were modified
    const isReligionChanged = changed.religion !== undefined;
    const isCastePrefChanged =
      changed.caste_preference === 'same_caste_required' ||
      (initialData?.caste_preference === 'same_caste_required' && changed.caste_preference !== undefined) ||
      (castePreference === 'same_caste_required' && changed.caste !== undefined);

    if (isReligionChanged || isCastePrefChanged) {
      setShowHardFilterModal(true);
    } else {
      executeSave(changed);
    }
  };

  const executeSave = async (payloadToSave?: Partial<ProfileCreatePayload>) => {
    if (!session?.access_token || !profile?.id) return;
    const payload = payloadToSave || getChangedPayload();

    try {
      setIsSaving(true);
      setShowHardFilterModal(false);

      const res = await updateProfile(session.access_token, profile.id, payload);

      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success).catch(() => {});

      // Use backend warning if present, else standard feedback
      if (res.warning) {
        setSaveSuccessMsg(`Saved • ${res.warning}`);
      } else {
        setSaveSuccessMsg('Profile updated. Weekly matches will refresh in the upcoming run.');
      }

      setInitialData({
        ...initialData!,
        ...payload,
        name: res.name,
        age: res.age,
        religion: res.religion,
        caste: res.caste || '',
        caste_preference: res.caste_preference || 'no_preference',
        city: res.city || '',
      });
    } catch (err: any) {
      setErrorMsg(err?.message || 'Failed to save profile changes.');
    } finally {
      setIsSaving(false);
    }
  };

  const handleConfirmDelete = async () => {
    if (!session?.access_token || !profile?.id) return;
    try {
      setIsDeleting(true);
      await deleteProfile(session.access_token, profile.id);
      setShowDeleteModal(false);
      await logout();
    } catch (err: any) {
      setErrorMsg(err?.message || 'Failed to delete account.');
    } finally {
      setIsDeleting(false);
    }
  };

  if (isLoading) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color={Colors.primary} />
          <Text style={styles.loadingText}>Loading settings...</Text>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
        style={styles.container}
      >
        <ScrollView
          contentContainerStyle={styles.scrollContent}
          showsVerticalScrollIndicator={false}
        >
          {/* Header */}
          <TouchableOpacity
            onPress={() => navigation.goBack()}
            style={styles.backButton}
            accessibilityRole="button"
            accessibilityLabel="Back to Dashboard"
          >
            <Text style={styles.backButtonText}>← Dashboard</Text>
          </TouchableOpacity>

          <EditorialHeader
            eyebrow="ACCOUNT & PREFERENCES"
            title="Profile Settings"
            subtitle="Manage your demographic baseline, revisit 42-Koota dimensions, or exercise data privacy controls."
          />

          {/* Pre-Save Invalidation Notice */}
          <View style={styles.preSaveNotice}>
            <Text style={styles.noticeIcon}>ℹ️</Text>
            <Text style={styles.noticeText}>
              Saving profile revisions invalidates your current match cohort and schedules fresh
              calculations for next Sunday.
            </Text>
          </View>

          {/* Feedback messages */}
          {errorMsg && (
            <View style={styles.errorBox}>
              <Text style={styles.errorText}>⚠ {errorMsg}</Text>
            </View>
          )}

          {saveSuccessMsg && (
            <View style={styles.successBox}>
              <Text style={styles.successText}>✓ {saveSuccessMsg}</Text>
            </View>
          )}

          {/* Section 1: Demographics Form */}
          <View style={styles.sectionCard}>
            <Text style={styles.sectionTitle}>Layer 1 Demographics</Text>

            {/* Name */}
            <View style={styles.inputGroup}>
              <Text style={styles.label}>Full Name</Text>
              <TextInput
                style={styles.input}
                value={name}
                onChangeText={setName}
                placeholder="Full Name"
                placeholderTextColor={Colors.textMuted}
              />
            </View>

            {/* Age */}
            <View style={styles.inputGroup}>
              <Text style={styles.label}>Age (18–99)</Text>
              <TextInput
                style={styles.input}
                value={age}
                onChangeText={setAge}
                keyboardType="numeric"
                placeholder="28"
                placeholderTextColor={Colors.textMuted}
              />
            </View>

            {/* Gender */}
            <View style={styles.inputGroup}>
              <Text style={styles.label}>Gender</Text>
              <View style={styles.pillRow}>
                {GENDERS.map((g) => (
                  <TouchableOpacity
                    key={g}
                    style={[styles.pill, gender === g && styles.pillActive]}
                    onPress={() => setGender(g)}
                  >
                    <Text style={[styles.pillText, gender === g && styles.pillTextActive]}>
                      {g.charAt(0).toUpperCase() + g.slice(1)}
                    </Text>
                  </TouchableOpacity>
                ))}
              </View>
            </View>

            {/* Religion */}
            <View style={styles.inputGroup}>
              <Text style={styles.label}>Religion (Universal Hard Filter)</Text>
              <TextInput
                style={styles.input}
                value={religion}
                onChangeText={setReligion}
                placeholder="e.g. Hindu, Jain, Sikh"
                placeholderTextColor={Colors.textMuted}
              />
            </View>

            {/* Community / Caste */}
            <View style={styles.inputGroup}>
              <Text style={styles.label}>Community / Caste</Text>
              <TextInput
                style={styles.input}
                value={caste}
                onChangeText={setCaste}
                placeholder="e.g. Brahmin, Rajput, Iyer"
                placeholderTextColor={Colors.textMuted}
              />
            </View>

            {/* Caste Preference */}
            <View style={styles.inputGroup}>
              <Text style={styles.label}>Community Filter Rule</Text>
              {CASTE_PREFS.map((pref) => (
                <TouchableOpacity
                  key={pref.value}
                  style={[
                    styles.radioOption,
                    castePreference === pref.value && styles.radioOptionActive,
                  ]}
                  onPress={() => setCastePreference(pref.value)}
                >
                  <View
                    style={[
                      styles.radioCircle,
                      castePreference === pref.value && styles.radioCircleActive,
                    ]}
                  >
                    {castePreference === pref.value && <View style={styles.radioDot} />}
                  </View>
                  <Text style={styles.radioText}>{pref.label}</Text>
                </TouchableOpacity>
              ))}
            </View>

            {/* City */}
            <View style={styles.inputGroup}>
              <Text style={styles.label}>Current City</Text>
              <TextInput
                style={styles.input}
                value={city}
                onChangeText={setCity}
                placeholder="e.g. Bengaluru, Mumbai"
                placeholderTextColor={Colors.textMuted}
              />
            </View>

            <TouchableOpacity
              style={styles.saveButton}
              onPress={handlePressSave}
              disabled={isSaving}
              activeOpacity={0.85}
              accessibilityRole="button"
              accessibilityLabel="Save Demographic Changes"
            >
              {isSaving ? (
                <ActivityIndicator color={Colors.textInverse} />
              ) : (
                <Text style={styles.saveButtonText}>Save Demographic Changes</Text>
              )}
            </TouchableOpacity>
          </View>

          {/* Section 2: Revisit 42 Dimensions Questionnaire */}
          <View style={styles.sectionCard}>
            <Text style={styles.sectionTitle}>Questionnaire Responses</Text>
            <Text style={styles.sectionSubtitle}>
              Revisit and update any of your objective choices or reflective responses across the
              42-Koota scientific matrix.
            </Text>

            <TouchableOpacity
              style={styles.revisitButton}
              onPress={() => navigation.navigate('ObjectiveQuestionnaire', { isEditMode: true })}
              activeOpacity={0.85}
              accessibilityRole="button"
              accessibilityLabel="Edit Objective Responses"
            >
              <Text style={styles.revisitButtonText}>✦ Edit Objective Choices (Pillars A–M)</Text>
            </TouchableOpacity>

            <TouchableOpacity
              style={[styles.revisitButton, { marginTop: 10 }]}
              onPress={() => navigation.navigate('SubjectiveQuestionnaire', { isEditMode: true })}
              activeOpacity={0.85}
              accessibilityRole="button"
              accessibilityLabel="Edit Reflective Responses"
            >
              <Text style={styles.revisitButtonText}>✦ Edit Reflective Responses (Pillars A–M)</Text>
            </TouchableOpacity>
          </View>

          {/* Section 3: Danger Zone */}
          <View style={[styles.sectionCard, styles.dangerZone]}>
            <Text style={styles.dangerTitle}>Data Privacy & Erasure</Text>
            <Text style={styles.dangerSubtitle}>
              Exercise your DPDP right-to-be-forgotten. Permanently purges all profile records,
              answers, vector embeddings, following lists, and match records.
            </Text>

            <TouchableOpacity
              style={styles.deleteAccountBtn}
              onPress={() => setShowDeleteModal(true)}
              activeOpacity={0.85}
              accessibilityRole="button"
              accessibilityLabel="Delete Account and Data"
            >
              <Text style={styles.deleteAccountBtnText}>Permanently Delete Account & Data</Text>
            </TouchableOpacity>
          </View>
        </ScrollView>

        {/* Hard-Filter Confirmation Modal */}
        <HardFilterWarningModal
          visible={showHardFilterModal}
          onCancel={() => setShowHardFilterModal(false)}
          onConfirm={executeSave}
          isSubmitting={isSaving}
        />

        {/* Delete Account Modal */}
        <DeleteAccountModal
          visible={showDeleteModal}
          onCancel={() => setShowDeleteModal(false)}
          onConfirmDelete={handleConfirmDelete}
          isSubmitting={isDeleting}
        />
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
    paddingBottom: 40,
  },
  backButton: {
    alignSelf: 'flex-start',
    marginTop: 10,
    marginBottom: 8,
    paddingVertical: 4,
  },
  backButtonText: {
    ...Typography.bodySecondary,
    color: Colors.textSecondary,
    fontWeight: '600',
  },
  preSaveNotice: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#FFF9E6',
    borderWidth: 1,
    borderColor: '#FFE08A',
    borderRadius: 12,
    padding: 12,
    marginBottom: 16,
  },
  noticeIcon: {
    fontSize: 16,
    marginRight: 10,
  },
  noticeText: {
    ...Typography.caption,
    fontSize: 12,
    lineHeight: 16,
    color: Colors.accentDark,
    flex: 1,
  },
  errorBox: {
    backgroundColor: Colors.errorBackground,
    borderWidth: 1,
    borderColor: Colors.errorBorder,
    borderRadius: 10,
    padding: 12,
    marginBottom: 14,
  },
  errorText: {
    ...Typography.caption,
    color: Colors.error,
    textAlign: 'center',
  },
  successBox: {
    backgroundColor: Colors.successBackground,
    borderWidth: 1,
    borderColor: Colors.successBorder,
    borderRadius: 10,
    padding: 12,
    marginBottom: 14,
  },
  successText: {
    ...Typography.caption,
    color: Colors.success,
    textAlign: 'center',
  },
  sectionCard: {
    backgroundColor: Colors.surface,
    borderRadius: 20,
    borderWidth: 1.5,
    borderColor: Colors.border,
    padding: 20,
    marginBottom: 20,
  },
  sectionTitle: {
    ...Typography.headline,
    fontSize: 18,
    fontFamily: 'serif',
    color: Colors.text,
    marginBottom: 6,
  },
  sectionSubtitle: {
    ...Typography.bodySecondary,
    fontSize: 13,
    lineHeight: 18,
    color: Colors.textSecondary,
    marginBottom: 16,
  },
  inputGroup: {
    marginBottom: 14,
  },
  label: {
    ...Typography.caption,
    fontWeight: '700',
    color: Colors.textSecondary,
    marginBottom: 6,
  },
  input: {
    ...Typography.body,
    borderWidth: 1.5,
    borderColor: Colors.border,
    borderRadius: 12,
    paddingHorizontal: 14,
    paddingVertical: 10,
    backgroundColor: Colors.backgroundSecondary,
    color: Colors.text,
  },
  pillRow: {
    flexDirection: 'row',
    gap: 8,
  },
  pill: {
    flex: 1,
    paddingVertical: 10,
    borderRadius: 10,
    borderWidth: 1,
    borderColor: Colors.border,
    backgroundColor: Colors.backgroundSecondary,
    alignItems: 'center',
  },
  pillActive: {
    backgroundColor: Colors.primary,
    borderColor: Colors.primary,
  },
  pillText: {
    ...Typography.caption,
    fontWeight: '600',
    color: Colors.textSecondary,
  },
  pillTextActive: {
    color: Colors.textInverse,
    fontWeight: '700',
  },
  radioOption: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 10,
    paddingHorizontal: 12,
    borderRadius: 10,
    borderWidth: 1,
    borderColor: Colors.border,
    backgroundColor: Colors.backgroundSecondary,
    marginBottom: 6,
  },
  radioOptionActive: {
    borderColor: Colors.primary,
    backgroundColor: '#FFF4E5',
  },
  radioCircle: {
    width: 18,
    height: 18,
    borderRadius: 9,
    borderWidth: 2,
    borderColor: Colors.textMuted,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 10,
  },
  radioCircleActive: {
    borderColor: Colors.primary,
  },
  radioDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: Colors.primary,
  },
  radioText: {
    ...Typography.bodySecondary,
    fontSize: 13,
    color: Colors.text,
    flex: 1,
  },
  saveButton: {
    backgroundColor: Colors.primary,
    paddingVertical: 14,
    borderRadius: 12,
    alignItems: 'center',
    marginTop: 8,
  },
  saveButtonText: {
    ...Typography.button,
    color: Colors.textInverse,
    fontSize: 15,
  },
  revisitButton: {
    backgroundColor: Colors.backgroundSecondary,
    borderWidth: 1.5,
    borderColor: Colors.border,
    paddingVertical: 14,
    paddingHorizontal: 16,
    borderRadius: 12,
    alignItems: 'center',
  },
  revisitButtonText: {
    ...Typography.button,
    color: Colors.text,
    fontSize: 14,
  },
  dangerZone: {
    borderColor: Colors.errorBorder,
    backgroundColor: '#FFFDFD',
  },
  dangerTitle: {
    ...Typography.headline,
    fontSize: 18,
    fontFamily: 'serif',
    color: Colors.error,
    marginBottom: 4,
  },
  dangerSubtitle: {
    ...Typography.bodySecondary,
    fontSize: 13,
    lineHeight: 18,
    color: Colors.textMuted,
    marginBottom: 16,
  },
  deleteAccountBtn: {
    backgroundColor: Colors.errorBackground,
    borderWidth: 1.5,
    borderColor: Colors.errorBorder,
    paddingVertical: 14,
    borderRadius: 12,
    alignItems: 'center',
  },
  deleteAccountBtnText: {
    ...Typography.button,
    color: Colors.error,
    fontWeight: '700',
    fontSize: 14,
  },
  loadingContainer: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
  },
  loadingText: {
    ...Typography.bodySecondary,
    marginTop: 12,
  },
});
