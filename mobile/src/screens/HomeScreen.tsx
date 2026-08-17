import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  SafeAreaView,
  StatusBar,
} from 'react-native';
import { Colors } from '../theme/colors';
import { Typography } from '../theme/typography';
import { useAuth } from '../context/AuthContext';

export const HomeScreen: React.FC = () => {
  const { profile, logout } = useAuth();

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar barStyle="dark-content" backgroundColor={Colors.background} />
      <View style={styles.content}>
        <View style={styles.header}>
          <Text style={styles.eyebrow}>KOOTA MATCH DASHBOARD</Text>
          <Text style={styles.greeting}>Welcome, {profile?.name || 'Member'}</Text>
          <Text style={styles.email}>{profile?.email}</Text>
        </View>

        <View style={styles.statusCard}>
          <Text style={styles.cardEyebrow}>CURRENT STATUS</Text>
          <Text style={styles.cardTitle}>Cohort Verification Complete</Text>
          <Text style={styles.cardBody}>
            Your profile is linked to the 42-Koota Matching Engine. Sunday candidate precomputations will appear here.
          </Text>
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
    borderWidth: 1,
    borderColor: Colors.border,
    borderRadius: 16,
    padding: 20,
    shadowColor: Colors.text,
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05,
    shadowRadius: 6,
    elevation: 2,
  },
  cardEyebrow: {
    ...Typography.caption,
    color: Colors.accentDark,
    letterSpacing: 1,
    marginBottom: 6,
  },
  cardTitle: {
    ...Typography.subheadline,
    color: Colors.text,
    fontWeight: '700',
    marginBottom: 8,
  },
  cardBody: {
    ...Typography.bodySecondary,
    lineHeight: 20,
  },
  logoutButton: {
    backgroundColor: Colors.backgroundSecondary,
    borderWidth: 1,
    borderColor: Colors.border,
    width: '100%',
    paddingVertical: 15,
    borderRadius: 14,
    alignItems: 'center',
    marginBottom: 16,
  },
  logoutButtonText: {
    ...Typography.button,
    color: Colors.textSecondary,
  },
});
