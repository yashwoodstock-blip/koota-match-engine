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

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar barStyle="dark-content" backgroundColor={Colors.background} />
      <View style={styles.content}>
        <View style={styles.header}>
          <Text style={styles.eyebrow}>KOOTA MATCH • 42-DIMENSION ENGINE</Text>
          <Text style={styles.greeting}>Namaste, {profile?.name || 'Member'}</Text>
          <Text style={styles.email}>{profile?.email}</Text>
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

        <TouchableOpacity
          style={styles.logoutButton}
          onPress={logout}
          activeOpacity={0.85}
          accessibilityRole="button"
          accessibilityLabel="Sign Out"
        >
          <Text style={styles.logoutButtonText}>Sign Out</Text>
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
  content: {
    flex: 1,
    paddingHorizontal: 24,
    paddingVertical: 24,
    justifyContent: 'space-between',
  },
  header: {
    marginTop: 20,
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
    marginBottom: 20,
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
  logoutButton: {
    backgroundColor: Colors.backgroundSecondary,
    borderWidth: 1,
    borderColor: Colors.border,
    width: '100%',
    paddingVertical: 14,
    borderRadius: 12,
    alignItems: 'center',
    marginBottom: 12,
  },
  logoutButtonText: {
    ...Typography.button,
    color: Colors.textSecondary,
    fontSize: 14,
  },
});
