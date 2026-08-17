import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  SafeAreaView,
  StatusBar,
} from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import * as Haptics from 'expo-haptics';
import { Colors } from '../theme/colors';
import { Typography } from '../theme/typography';
import { AuthStackParamList } from '../navigation/types';

type WelcomeNavigationProp = NativeStackNavigationProp<AuthStackParamList, 'Welcome'>;

export const WelcomeScreen: React.FC = () => {
  const navigation = useNavigation<WelcomeNavigationProp>();

  const handleProceed = () => {
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light).catch(() => {});
    navigation.navigate('InviteCode');
  };

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar barStyle="dark-content" backgroundColor={Colors.background} />
      
      <View style={styles.content}>
        {/* Editorial Brand Header */}
        <View style={styles.headerContainer}>
          <Text style={styles.eyebrow}>SCIENTIFIC MATRIMONIAL COMPATIBILITY</Text>
          <Text style={styles.title}>Koota Match</Text>
          <View style={styles.divider} />
        </View>

        {/* Narrative Value Proposition */}
        <View style={styles.bodyContainer}>
          <Text style={styles.quote}>
            "Beyond horoscope charts and superficial metrics — 42 empirical dimensions of deep cultural and psychological resonance."
          </Text>

          <View style={styles.featureList}>
            <View style={styles.featureItem}>
              <Text style={styles.featureBullet}>✦</Text>
              <Text style={styles.featureText}>14 Core Life Pillars & Nuanced Indian Realities</Text>
            </View>
            <View style={styles.featureItem}>
              <Text style={styles.featureBullet}>✦</Text>
              <Text style={styles.featureText}>NLI Contradiction Screening & LLM-as-a-Judge</Text>
            </View>
            <View style={styles.featureItem}>
              <Text style={styles.featureBullet}>✦</Text>
              <Text style={styles.featureText}>Precomputed Sunday Matches & Mutual Staged Disclosure</Text>
            </View>
          </View>
        </View>

        {/* Action Gate */}
        <View style={styles.footerContainer}>
          <View style={styles.badgeContainer}>
            <Text style={styles.badgeText}>INVITE-ONLY ACCESS</Text>
          </View>

          <TouchableOpacity
            style={styles.primaryButton}
            onPress={handleProceed}
            activeOpacity={0.85}
            accessibilityRole="button"
            accessibilityLabel="Enter Invite Code"
          >
            <Text style={styles.primaryButtonText}>Enter Invite Code</Text>
          </TouchableOpacity>

          <Text style={styles.footerSubtext}>
            Registration is currently restricted to curated cohort invitations.
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
    paddingHorizontal: 28,
    paddingVertical: 24,
    justifyContent: 'space-between',
  },
  headerContainer: {
    marginTop: 40,
  },
  eyebrow: {
    ...Typography.caption,
    color: Colors.accentDark,
    letterSpacing: 1.5,
    marginBottom: 8,
  },
  title: {
    ...Typography.display,
    fontFamily: 'serif',
    color: Colors.primary,
    fontSize: 38,
    lineHeight: 46,
  },
  divider: {
    height: 3,
    width: 48,
    backgroundColor: Colors.accent,
    marginTop: 16,
    borderRadius: 2,
  },
  bodyContainer: {
    marginVertical: 24,
  },
  quote: {
    ...Typography.subheadline,
    fontStyle: 'italic',
    color: Colors.textSecondary,
    marginBottom: 32,
    lineHeight: 28,
  },
  featureList: {
    gap: 16,
  },
  featureItem: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  featureBullet: {
    fontSize: 16,
    color: Colors.accentDark,
    marginRight: 12,
  },
  featureText: {
    ...Typography.body,
    color: Colors.text,
    flex: 1,
  },
  footerContainer: {
    marginBottom: 16,
    alignItems: 'center',
  },
  badgeContainer: {
    backgroundColor: Colors.backgroundSecondary,
    paddingHorizontal: 14,
    paddingVertical: 6,
    borderRadius: 20,
    borderWidth: 1,
    borderColor: Colors.border,
    marginBottom: 16,
  },
  badgeText: {
    ...Typography.caption,
    color: Colors.textSecondary,
    fontWeight: '600',
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
  primaryButtonText: {
    ...Typography.button,
  },
  footerSubtext: {
    ...Typography.caption,
    textAlign: 'center',
    marginTop: 12,
    color: Colors.textMuted,
  },
});
