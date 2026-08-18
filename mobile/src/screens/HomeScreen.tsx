import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  SafeAreaView,
  StatusBar,
  ScrollView,
} from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import * as Haptics from 'expo-haptics';
import { Colors } from '../theme/colors';
import { Typography } from '../theme/typography';
import { useAuth } from '../context/AuthContext';
import { MainStackParamList } from '../navigation/types';

type HomeNavProp = NativeStackNavigationProp<MainStackParamList, 'Home'>;

export const HomeScreen: React.FC = () => {
  const navigation = useNavigation<HomeNavProp>();
  const { profile, logout } = useAuth();

  const handleOpenMatches = () => {
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light).catch(() => {});
    navigation.navigate('WeeklyMatches');
  };

  const handleOpenSettings = () => {
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light).catch(() => {});
    navigation.navigate('EditProfile');
  };

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar barStyle="dark-content" backgroundColor={Colors.background} />
      <ScrollView contentContainerStyle={styles.scrollContent} showsVerticalScrollIndicator={false}>
        {/* Header Bar */}
        <View style={styles.header}>
          <View>
            <Text style={styles.eyebrow}>KOOTA MATCH • 42-DIMENSION ENGINE</Text>
            <Text style={styles.greeting}>Namaste, {profile?.name || 'Member'}</Text>
            <Text style={styles.email}>{profile?.email}</Text>
          </View>

          <TouchableOpacity
            style={styles.settingsIconBtn}
            onPress={handleOpenSettings}
            accessibilityRole="button"
            accessibilityLabel="Open Settings"
          >
            <Text style={styles.settingsIcon}>⚙️</Text>
          </TouchableOpacity>
        </View>

        {/* Weekly Matches Banner Card */}
        <View style={styles.statusCard}>
          <Text style={styles.cardEyebrow}>CURATED SUNDAY COHORT</Text>
          <Text style={styles.cardTitle}>Precomputed Matches Ready</Text>
          <Text style={styles.cardBody}>
            Your profile has been evaluated against the 42-Koota scientific matrix, NLI contradiction checks, and LLM judge shortlists.
          </Text>

          <TouchableOpacity
            style={styles.viewMatchesBtn}
            onPress={handleOpenMatches}
            activeOpacity={0.85}
            accessibilityRole="button"
            accessibilityLabel="View Weekly Matches"
          >
            <Text style={styles.viewMatchesBtnText}>Explore Weekly Matches →</Text>
          </TouchableOpacity>
        </View>

        {/* Compatibility Code Direct Match Card */}
        <View style={styles.directMatchCard}>
          <Text style={styles.cardEyebrow}>MUTUAL CONSENT CHECK</Text>
          <Text style={styles.cardTitle}>Direct Compatibility Check</Text>
          <Text style={styles.cardBody}>
            Evaluate compatibility with someone specific introduced by family using a 24-hour single-use consent code.
          </Text>

          <TouchableOpacity
            style={styles.directMatchBtn}
            onPress={() => navigation.navigate('CompatibilityCode')}
            activeOpacity={0.85}
            accessibilityRole="button"
            accessibilityLabel="Direct Compatibility Check"
          >
            <Text style={styles.directMatchBtnText}>Share or Enter Code 🔑</Text>
          </TouchableOpacity>
        </View>

        {/* Profile Settings Quick Card */}
        <View style={styles.settingsCard}>
          <Text style={styles.cardEyebrow}>PROFILE & PREFERENCES</Text>
          <Text style={styles.cardTitle}>42-Dimension Controls</Text>
          <Text style={styles.cardBody}>
            Review Layer 1 demographics, update objective choices, or refine reflective responses.
          </Text>

          <TouchableOpacity
            style={styles.settingsBtn}
            onPress={handleOpenSettings}
            activeOpacity={0.85}
            accessibilityRole="button"
            accessibilityLabel="Edit Profile & Answers"
          >
            <Text style={styles.settingsBtnText}>Edit Profile & 42 Answers ⚙️</Text>
          </TouchableOpacity>
        </View>

        <TouchableOpacity
          style={styles.logoutButton}
          onPress={logout}
          activeOpacity={0.85}
          accessibilityRole="button"
          accessibilityLabel="Sign Out"
        >
          <Text style={styles.logoutButtonText}>Sign Out</Text>
        </TouchableOpacity>
      </ScrollView>
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
    gap: 18,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginTop: 10,
  },
  eyebrow: {
    ...Typography.caption,
    color: Colors.accentDark,
    letterSpacing: 1.5,
    marginBottom: 6,
  },
  greeting: {
    ...Typography.headline,
    fontSize: 28,
    lineHeight: 34,
    fontFamily: 'serif',
    color: Colors.primary,
  },
  email: {
    ...Typography.bodySecondary,
    marginTop: 4,
  },
  settingsIconBtn: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: Colors.backgroundSecondary,
    borderWidth: 1,
    borderColor: Colors.border,
    alignItems: 'center',
    justifyContent: 'center',
  },
  settingsIcon: {
    fontSize: 20,
  },
  statusCard: {
    backgroundColor: Colors.surface,
    borderWidth: 1.5,
    borderColor: Colors.border,
    borderRadius: 20,
    padding: 22,
    shadowColor: Colors.text,
    shadowOffset: { width: 0, height: 3 },
    shadowOpacity: 0.06,
    shadowRadius: 8,
    elevation: 3,
  },
  settingsCard: {
    backgroundColor: Colors.surface,
    borderWidth: 1.5,
    borderColor: Colors.border,
    borderRadius: 20,
    padding: 22,
    shadowColor: Colors.text,
    shadowOffset: { width: 0, height: 3 },
    shadowOpacity: 0.06,
    shadowRadius: 8,
    elevation: 3,
  },
  cardEyebrow: {
    ...Typography.caption,
    color: Colors.accentDark,
    letterSpacing: 1,
    marginBottom: 6,
    fontWeight: '700',
  },
  cardTitle: {
    ...Typography.headline,
    fontSize: 20,
    color: Colors.text,
    fontFamily: 'serif',
    marginBottom: 8,
  },
  cardBody: {
    ...Typography.bodySecondary,
    lineHeight: 21,
    marginBottom: 16,
  },
  viewMatchesBtn: {
    backgroundColor: Colors.primary,
    paddingVertical: 14,
    borderRadius: 12,
    alignItems: 'center',
    shadowColor: Colors.primary,
    shadowOffset: { width: 0, height: 3 },
    shadowOpacity: 0.25,
    shadowRadius: 6,
    elevation: 3,
  },
  viewMatchesBtnText: {
    ...Typography.button,
    fontSize: 15,
  },
  settingsBtn: {
    backgroundColor: Colors.backgroundSecondary,
    borderWidth: 1.5,
    borderColor: Colors.border,
    paddingVertical: 14,
    borderRadius: 12,
    alignItems: 'center',
  },
  settingsBtnText: {
    ...Typography.button,
    color: Colors.text,
    fontSize: 14,
  },
  directMatchCard: {
    backgroundColor: Colors.surface,
    borderWidth: 1.5,
    borderColor: Colors.border,
    borderRadius: 20,
    padding: 22,
    shadowColor: Colors.text,
    shadowOffset: { width: 0, height: 3 },
    shadowOpacity: 0.06,
    shadowRadius: 8,
    elevation: 3,
  },
  directMatchBtn: {
    backgroundColor: Colors.backgroundSecondary,
    borderWidth: 1.5,
    borderColor: Colors.border,
    paddingVertical: 14,
    borderRadius: 12,
    alignItems: 'center',
  },
  directMatchBtnText: {
    ...Typography.button,
    color: Colors.primary,
    fontSize: 14,
    fontWeight: '700',
  },
  logoutButton: {
    backgroundColor: Colors.backgroundSecondary,
    borderWidth: 1,
    borderColor: Colors.border,
    width: '100%',
    paddingVertical: 14,
    borderRadius: 12,
    alignItems: 'center',
    marginTop: 8,
  },
  logoutButtonText: {
    ...Typography.button,
    color: Colors.textSecondary,
    fontSize: 14,
  },
});
