import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ActivityIndicator,
  Animated,
} from 'react-native';
import * as Haptics from 'expo-haptics';
import { Colors } from '../theme/colors';
import { Typography } from '../theme/typography';
import { useAuth } from '../context/AuthContext';
import { refreshWeeklyMatches, RefreshMatchesResponse } from '../api/authApi';

interface Props {
  onRefreshSuccess: (res: RefreshMatchesResponse) => void;
  initialNextEligibleAt?: string | null;
}

export function formatRemainingTime(remainingSeconds: number): string {
  if (remainingSeconds <= 0) return '';
  const hours = Math.floor(remainingSeconds / 3600);
  const minutes = Math.floor((remainingSeconds % 3600) / 60);
  const seconds = remainingSeconds % 60;

  if (hours > 0) {
    return `${hours}h ${minutes}m ${seconds}s`;
  }
  if (minutes > 0) {
    return `${minutes}m ${seconds}s`;
  }
  return `${seconds}s`;
}

export const RefreshMatchesButton: React.FC<Props> = ({
  onRefreshSuccess,
  initialNextEligibleAt,
}) => {
  const { session, profile } = useAuth();
  const [nextEligibleAt, setNextEligibleAt] = useState<string | null>(
    initialNextEligibleAt || null
  );
  const [remainingSeconds, setRemainingSeconds] = useState<number>(0);
  const [isRefreshing, setIsRefreshing] = useState<boolean>(false);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);

  // Derive countdown from backend timestamp
  useEffect(() => {
    if (!nextEligibleAt) {
      setRemainingSeconds(0);
      return;
    }

    const updateCountdown = () => {
      const targetTime = new Date(nextEligibleAt).getTime();
      const now = Date.now();
      const diff = Math.max(0, Math.floor((targetTime - now) / 1000));
      setRemainingSeconds(diff);
      if (diff === 0) {
        setNextEligibleAt(null);
      }
    };

    updateCountdown();
    const interval = setInterval(updateCountdown, 1000);
    return () => clearInterval(interval);
  }, [nextEligibleAt]);

  const handlePressRefresh = async () => {
    if (!session?.access_token || !profile?.id || isRefreshing || remainingSeconds > 0) {
      return;
    }

    try {
      setIsRefreshing(true);
      setStatusMessage(null);
      Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium).catch(() => {});

      const res = await refreshWeeklyMatches(session.access_token, profile.id);
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success).catch(() => {});

      if (res.next_eligible_at) {
        setNextEligibleAt(res.next_eligible_at);
      }
      setStatusMessage(`Refreshed • Computed ${res.total_matches} viable candidates.`);
      onRefreshSuccess(res);
    } catch (err: any) {
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Warning).catch(() => {});

      // Parse 429 response structure
      const errorData = err?.detail || err;
      if (errorData?.next_eligible_at) {
        setNextEligibleAt(errorData.next_eligible_at);
        setStatusMessage('Refresh cooldown active. Available in upcoming window.');
      } else {
        setStatusMessage(err?.message || 'Unable to refresh matches at this time.');
      }
    } finally {
      setIsRefreshing(false);
    }
  };

  const isInCooldown = remainingSeconds > 0;

  return (
    <View style={styles.container}>
      <View style={styles.cardHeader}>
        <Text style={styles.eyebrow}>ON-DEMAND RECOMPUTATION</Text>
        <Text style={styles.cardTitle}>Refresh Match Funnel</Text>
        <Text style={styles.cardSubtitle}>
          Re-evaluates the candidate pool against your latest 42 dimensions and social graph.
        </Text>
      </View>

      <TouchableOpacity
        style={[
          styles.button,
          (isInCooldown || isRefreshing) && styles.buttonDisabled,
        ]}
        onPress={handlePressRefresh}
        disabled={isInCooldown || isRefreshing}
        activeOpacity={0.85}
        accessibilityRole="button"
        accessibilityLabel={
          isInCooldown
            ? `Refresh cooldown active. Available in ${formatRemainingTime(remainingSeconds)}`
            : 'Refresh Matches Now'
        }
      >
        {isRefreshing ? (
          <View style={styles.loadingRow}>
            <ActivityIndicator size="small" color={Colors.textInverse} />
            <Text style={styles.buttonText}>Evaluating 42-Koota Funnel...</Text>
          </View>
        ) : isInCooldown ? (
          <View style={styles.cooldownRow}>
            <Text style={styles.lockIcon}>⏳</Text>
            <Text style={styles.cooldownText}>
              Refresh in {formatRemainingTime(remainingSeconds)}
            </Text>
          </View>
        ) : (
          <Text style={styles.buttonText}>✦ Refresh Matches Now</Text>
        )}
      </TouchableOpacity>

      {statusMessage && (
        <Text
          style={[
            styles.statusText,
            isInCooldown && styles.statusTextMuted,
          ]}
        >
          {statusMessage}
        </Text>
      )}

      <Text style={styles.cooldownNotice}>
        {isInCooldown
          ? 'Next refresh available in 24 hours from your previous calculation.'
          : 'Runs once per 24 hours. Bound to ≤10 LLM judge evaluations per run.'}
      </Text>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    backgroundColor: Colors.surface,
    borderWidth: 1.5,
    borderColor: Colors.border,
    borderRadius: 20,
    padding: 20,
    marginBottom: 20,
    shadowColor: Colors.text,
    shadowOffset: { width: 0, height: 3 },
    shadowOpacity: 0.05,
    shadowRadius: 8,
    elevation: 2,
  },
  cardHeader: {
    marginBottom: 14,
  },
  eyebrow: {
    ...Typography.caption,
    fontSize: 10,
    letterSpacing: 1.5,
    color: Colors.accentDark,
    fontWeight: '800',
    marginBottom: 4,
  },
  cardTitle: {
    ...Typography.headline,
    fontSize: 18,
    fontFamily: 'serif',
    color: Colors.text,
    marginBottom: 4,
  },
  cardSubtitle: {
    ...Typography.bodySecondary,
    fontSize: 13,
    lineHeight: 18,
    color: Colors.textSecondary,
  },
  button: {
    backgroundColor: Colors.primary,
    paddingVertical: 14,
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
    shadowColor: Colors.primary,
    shadowOffset: { width: 0, height: 3 },
    shadowOpacity: 0.2,
    shadowRadius: 6,
    elevation: 3,
  },
  buttonDisabled: {
    backgroundColor: Colors.backgroundSecondary,
    borderWidth: 1,
    borderColor: Colors.border,
    shadowOpacity: 0,
    elevation: 0,
  },
  buttonText: {
    ...Typography.button,
    color: Colors.textInverse,
    fontSize: 14,
    fontWeight: '700',
  },
  loadingRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  cooldownRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  lockIcon: {
    fontSize: 14,
  },
  cooldownText: {
    ...Typography.button,
    color: Colors.textMuted,
    fontSize: 13,
    fontWeight: '600',
  },
  statusText: {
    ...Typography.caption,
    color: Colors.primary,
    textAlign: 'center',
    marginTop: 10,
    fontWeight: '600',
  },
  statusTextMuted: {
    color: Colors.textSecondary,
  },
  cooldownNotice: {
    ...Typography.caption,
    fontSize: 11,
    color: Colors.textMuted,
    textAlign: 'center',
    marginTop: 8,
  },
});
