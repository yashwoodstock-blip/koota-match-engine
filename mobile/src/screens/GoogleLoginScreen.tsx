import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  SafeAreaView,
  ActivityIndicator,
} from 'react-native';
import { useNavigation } from '@react-navigation/native';
import * as Haptics from 'expo-haptics';
import { Colors } from '../theme/colors';
import { Typography } from '../theme/typography';
import { useAuth } from '../context/AuthContext';

export const GoogleLoginScreen: React.FC = () => {
  const navigation = useNavigation();
  const { loginWithGoogle, isLoading, inviteCode, error } = useAuth();

  const handleGoogleLogin = async () => {
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium).catch(() => {});
    await loginWithGoogle();
  };

  return (
    <SafeAreaView style={styles.container}>
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

          <Text style={styles.stepIndicator}>STEP 2 OF 2</Text>
          <Text style={styles.title}>Verified Access</Text>

          {/* Verified Invite Code Badge */}
          <View style={styles.verifiedBadge}>
            <Text style={styles.checkMark}>✓</Text>
            <Text style={styles.verifiedText}>
              Invite Code <Text style={styles.boldCode}>{inviteCode || 'VERIFIED'}</Text> Unlocked
            </Text>
          </View>

          <Text style={styles.subtitle}>
            Link your Google account to finalize identity gating. Exactly one matrimonial profile is tied per verified email.
          </Text>
        </View>

        {/* Central Illustration / Trust Card */}
        <View style={styles.trustCard}>
          <Text style={styles.trustIcon}>🛡</Text>
          <Text style={styles.trustTitle}>Zero-Knowledge Privacy</Text>
          <Text style={styles.trustDescription}>
            Your email is never shown publicly. Only precomputed compatibility scores and templated insights are generated.
          </Text>
        </View>

        {/* Action Button */}
        <View style={styles.footer}>
          {error && (
            <View style={styles.errorBanner}>
              <Text style={styles.errorText}>⚠ {error}</Text>
            </View>
          )}

          <TouchableOpacity
            style={styles.googleButton}
            onPress={handleGoogleLogin}
            disabled={isLoading}
            activeOpacity={0.85}
            accessibilityRole="button"
            accessibilityLabel="Continue with Google"
          >
            {isLoading ? (
              <ActivityIndicator color={Colors.text} />
            ) : (
              <View style={styles.googleButtonContent}>
                <Text style={styles.googleIcon}>G</Text>
                <Text style={styles.googleButtonText}>Continue with Google</Text>
              </View>
            )}
          </TouchableOpacity>

          <Text style={styles.termsText}>
            By continuing, you agree to the Koota Match Matrimonial Trust & Cohort Guidelines.
          </Text>
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
    marginBottom: 16,
  },
  verifiedBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: Colors.successBackground,
    borderWidth: 1,
    borderColor: Colors.successBorder,
    borderRadius: 20,
    paddingHorizontal: 14,
    paddingVertical: 8,
    alignSelf: 'flex-start',
    marginBottom: 16,
  },
  checkMark: {
    color: Colors.success,
    fontWeight: '700',
    marginRight: 6,
    fontSize: 14,
  },
  verifiedText: {
    ...Typography.caption,
    color: Colors.success,
    fontWeight: '600',
  },
  boldCode: {
    fontWeight: '800',
    color: Colors.text,
  },
  subtitle: {
    ...Typography.bodySecondary,
    lineHeight: 22,
  },
  trustCard: {
    backgroundColor: Colors.surface,
    borderWidth: 1,
    borderColor: Colors.border,
    borderRadius: 16,
    padding: 20,
    alignItems: 'center',
    shadowColor: Colors.text,
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05,
    shadowRadius: 6,
    elevation: 2,
  },
  trustIcon: {
    fontSize: 32,
    marginBottom: 10,
  },
  trustTitle: {
    ...Typography.subheadline,
    color: Colors.text,
    fontWeight: '600',
    marginBottom: 6,
  },
  trustDescription: {
    ...Typography.caption,
    color: Colors.textSecondary,
    textAlign: 'center',
    lineHeight: 18,
  },
  footer: {
    marginBottom: 16,
    alignItems: 'center',
  },
  errorBanner: {
    backgroundColor: Colors.errorBackground,
    borderWidth: 1,
    borderColor: Colors.errorBorder,
    borderRadius: 10,
    padding: 10,
    marginBottom: 12,
    width: '100%',
  },
  errorText: {
    ...Typography.caption,
    color: Colors.error,
    textAlign: 'center',
  },
  googleButton: {
    backgroundColor: Colors.surface,
    borderWidth: 1.5,
    borderColor: Colors.border,
    width: '100%',
    paddingVertical: 15,
    borderRadius: 14,
    alignItems: 'center',
    shadowColor: Colors.text,
    shadowOffset: { width: 0, height: 3 },
    shadowOpacity: 0.1,
    shadowRadius: 6,
    elevation: 2,
  },
  googleButtonContent: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  googleIcon: {
    fontSize: 18,
    fontWeight: '700',
    color: Colors.primary,
    marginRight: 10,
  },
  googleButtonText: {
    ...Typography.button,
    color: Colors.text,
  },
  termsText: {
    ...Typography.caption,
    textAlign: 'center',
    marginTop: 12,
    color: Colors.textMuted,
    lineHeight: 16,
    paddingHorizontal: 8,
  },
});
