import React, { useState } from 'react';
import {
  View,
  Text,
  TextInput,
  StyleSheet,
  TouchableOpacity,
  SafeAreaView,
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
import { AuthStackParamList } from '../navigation/types';

type InviteNavigationProp = NativeStackNavigationProp<AuthStackParamList, 'InviteCode'>;

export const InviteCodeScreen: React.FC = () => {
  const [code, setCode] = useState<string>('');
  const { redeemInvite, isLoading, error, clearError } = useAuth();
  const navigation = useNavigation<InviteNavigationProp>();

  const handleTextChange = (text: string) => {
    clearError();
    // Allow only alphanumeric characters, max 8 chars, uppercase
    const cleaned = text.replace(/[^a-zA-Z0-9]/g, '').toUpperCase().slice(0, 8);
    setCode(cleaned);

    if (cleaned.length === 8) {
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success).catch(() => {});
    }
  };

  const handleVerify = async () => {
    if (code.length < 8) return;
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium).catch(() => {});
    const success = await redeemInvite(code);
    if (success) {
      navigation.navigate('GoogleLogin');
    }
  };

  return (
    <SafeAreaView style={styles.container}>
      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        style={styles.keyboardAvoid}
      >
        <View style={styles.content}>
          {/* Header */}
          <View style={styles.header}>
            <TouchableOpacity
              onPress={() => navigation.goBack()}
              style={styles.backButton}
              accessibilityRole="button"
              accessibilityLabel="Go Back"
            >
              <Text style={styles.backButtonText}>← Back</Text>
            </TouchableOpacity>
            
            <Text style={styles.stepIndicator}>STEP 1 OF 2</Text>
            <Text style={styles.title}>Redeem Invite</Text>
            <Text style={styles.subtitle}>
              Enter the 8-character single-use invite code provided by your cohort host.
            </Text>
          </View>

          {/* Form / Code Input */}
          <View style={styles.formContainer}>
            <Text style={styles.inputLabel}>INVITE CODE</Text>
            <View style={[styles.inputWrapper, error ? styles.inputWrapperError : null]}>
              <TextInput
                style={styles.input}
                value={code}
                onChangeText={handleTextChange}
                placeholder="e.g. A9K2M4P7"
                placeholderTextColor={Colors.textMuted}
                autoCapitalize="characters"
                autoCorrect={false}
                autoFocus={true}
                maxLength={8}
                editable={!isLoading}
                accessibilityLabel="8-character invite code input"
              />
              <Text style={styles.charCount}>{code.length}/8</Text>
            </View>

            {/* Inline Error Message */}
            {error && (
              <View style={styles.errorBanner}>
                <Text style={styles.errorIcon}>⚠</Text>
                <Text style={styles.errorText}>{error}</Text>
              </View>
            )}

            <View style={styles.infoBox}>
              <Text style={styles.infoText}>
                🔒 Invite codes are strictly single-use and link directly to your verified account upon registration.
              </Text>
            </View>
          </View>

          {/* Verification CTA */}
          <View style={styles.footer}>
            <TouchableOpacity
              style={[
                styles.primaryButton,
                code.length < 8 || isLoading ? styles.primaryButtonDisabled : null,
              ]}
              onPress={handleVerify}
              disabled={code.length < 8 || isLoading}
              activeOpacity={0.85}
              accessibilityRole="button"
              accessibilityLabel="Verify and Continue"
            >
              {isLoading ? (
                <ActivityIndicator color={Colors.textInverse} />
              ) : (
                <Text style={styles.primaryButtonText}>Verify & Continue</Text>
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
  keyboardAvoid: {
    flex: 1,
  },
  content: {
    flex: 1,
    paddingHorizontal: 24,
    paddingVertical: 16,
    justifyContent: 'space-between',
  },
  header: {
    marginTop: 16,
  },
  backButton: {
    marginBottom: 20,
    alignSelf: 'flex-start',
  },
  backButtonText: {
    ...Typography.bodySecondary,
    color: Colors.textSecondary,
    fontWeight: '600',
  },
  stepIndicator: {
    ...Typography.caption,
    color: Colors.accentDark,
    letterSpacing: 1.5,
    marginBottom: 6,
  },
  title: {
    ...Typography.headline,
    fontSize: 28,
    lineHeight: 36,
    fontFamily: 'serif',
    color: Colors.primary,
    marginBottom: 8,
  },
  subtitle: {
    ...Typography.bodySecondary,
    lineHeight: 22,
  },
  formContainer: {
    marginVertical: 24,
  },
  inputLabel: {
    ...Typography.caption,
    color: Colors.textSecondary,
    marginBottom: 8,
    letterSpacing: 1,
  },
  inputWrapper: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: Colors.surface,
    borderWidth: 1.5,
    borderColor: Colors.border,
    borderRadius: 14,
    paddingHorizontal: 16,
    paddingVertical: 12,
  },
  inputWrapperError: {
    borderColor: Colors.error,
    backgroundColor: Colors.errorBackground,
  },
  input: {
    flex: 1,
    fontSize: 22,
    fontWeight: '700',
    letterSpacing: 4,
    color: Colors.text,
  },
  charCount: {
    ...Typography.caption,
    color: Colors.textMuted,
  },
  errorBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: Colors.errorBackground,
    borderWidth: 1,
    borderColor: Colors.errorBorder,
    borderRadius: 10,
    paddingHorizontal: 12,
    paddingVertical: 10,
    marginTop: 12,
  },
  errorIcon: {
    color: Colors.error,
    fontSize: 16,
    marginRight: 8,
  },
  errorText: {
    ...Typography.bodySecondary,
    color: Colors.error,
    flex: 1,
    fontSize: 13,
  },
  infoBox: {
    backgroundColor: Colors.backgroundSecondary,
    padding: 14,
    borderRadius: 12,
    marginTop: 20,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  infoText: {
    ...Typography.caption,
    color: Colors.textSecondary,
    lineHeight: 18,
  },
  footer: {
    marginBottom: 16,
  },
  primaryButton: {
    backgroundColor: Colors.primary,
    width: '100%',
    paddingVertical: 16,
    borderRadius: 14,
    alignItems: 'center',
    shadowColor: Colors.primary,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.2,
    shadowRadius: 8,
    elevation: 3,
  },
  primaryButtonDisabled: {
    backgroundColor: Colors.textMuted,
    shadowOpacity: 0,
    elevation: 0,
  },
  primaryButtonText: {
    ...Typography.button,
  },
});
