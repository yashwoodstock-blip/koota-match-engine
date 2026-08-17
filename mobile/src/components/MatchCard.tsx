import React, { useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  Animated,
} from 'react-native';
import * as Haptics from 'expo-haptics';
import { Colors } from '../theme/colors';
import { Typography } from '../theme/typography';
import { WeeklyMatchDTO } from '../api/authApi';
import { AlignmentFrictionList } from './AlignmentFrictionList';

interface Props {
  match: WeeklyMatchDTO;
  onExpressInterest: (candidateId: string) => void;
  onPressDecline: (match: WeeklyMatchDTO) => void;
}

export const MatchCard: React.FC<Props> = ({ match, onExpressInterest, onPressDecline }) => {
  const scaleAnim = useRef(new Animated.Value(1)).current;

  const isStrongMatch = match.tier === 'strong match';
  const isMutual = match.is_mutual || match.interest_status === 'mutual';
  const isPending = match.interest_status === 'pending';

  const handleExpress = () => {
    if (isPending || isMutual) return;

    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium).catch(() => {});

    Animated.sequence([
      Animated.spring(scaleAnim, {
        toValue: 0.95,
        tension: 100,
        friction: 6,
        useNativeDriver: true,
      }),
      Animated.spring(scaleAnim, {
        toValue: 1,
        tension: 80,
        friction: 5,
        useNativeDriver: true,
      }),
    ]).start();

    onExpressInterest(match.candidate_id);
  };

  const handleDecline = () => {
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light).catch(() => {});
    onPressDecline(match);
  };

  return (
    <Animated.View style={[styles.card, { transform: [{ scale: scaleAnim }] }]}>
      {/* Top Meta Bar */}
      <View style={styles.topRow}>
        <View
          style={[
            styles.tierBadge,
            isStrongMatch ? styles.tierBadgeStrong : styles.tierBadgeCompatible,
          ]}
        >
          <Text
            style={[
              styles.tierText,
              isStrongMatch ? styles.tierTextStrong : styles.tierTextCompatible,
            ]}
          >
            {isStrongMatch ? '✦ STRONG MATCH' : '✦ COMPATIBLE'}
          </Text>
        </View>

        <View style={styles.scoreContainer}>
          <Text style={styles.scoreNumber}>{Math.round(match.score * 100)}%</Text>
          <Text style={styles.scoreLabel}>COMPATIBILITY</Text>
        </View>
      </View>

      {/* Candidate Name */}
      <Text style={styles.candidateName}>{match.candidate_name}</Text>

      {/* Optional Social Overlap Badge */}
      {(match.shared_account_count ?? 0) > 0 && (
        <View style={styles.socialBadge}>
          <Text style={styles.socialIcon}>👥</Text>
          <Text style={styles.socialText}>
            {match.shared_account_count} Shared Following Accounts
          </Text>
        </View>
      )}

      {/* Harmonious Alignment & Conversation Starter Insights */}
      <AlignmentFrictionList
        alignments={match.alignment_points || []}
        frictions={match.friction_points || []}
      />

      {/* Actions */}
      <View style={styles.actionRow}>
        {isMutual ? (
          <View style={styles.mutualBanner}>
            <Text style={styles.mutualBannerText}>✦ Mutual Match Confirmed 💍</Text>
          </View>
        ) : isPending ? (
          <View style={styles.pendingBanner}>
            <Text style={styles.pendingBannerText}>✓ Interest Expressed</Text>
          </View>
        ) : (
          <>
            <TouchableOpacity
              style={styles.declineButton}
              onPress={handleDecline}
              activeOpacity={0.7}
              accessibilityRole="button"
              accessibilityLabel="Decline candidate"
            >
              <Text style={styles.declineButtonText}>Pass</Text>
            </TouchableOpacity>

            <TouchableOpacity
              style={styles.expressButton}
              onPress={handleExpress}
              activeOpacity={0.85}
              accessibilityRole="button"
              accessibilityLabel="Express Interest"
            >
              <Text style={styles.expressButtonText}>Express Interest ✦</Text>
            </TouchableOpacity>
          </>
        )}
      </View>
    </Animated.View>
  );
};

const styles = StyleSheet.create({
  card: {
    backgroundColor: Colors.surface,
    borderRadius: 20,
    padding: 22,
    marginBottom: 20,
    borderWidth: 1.5,
    borderColor: Colors.border,
    shadowColor: Colors.text,
    shadowOffset: { width: 0, height: 3 },
    shadowOpacity: 0.06,
    shadowRadius: 8,
    elevation: 3,
  },
  topRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  tierBadge: {
    paddingHorizontal: 12,
    paddingVertical: 5,
    borderRadius: 14,
    borderWidth: 1,
  },
  tierBadgeStrong: {
    backgroundColor: Colors.successBackground,
    borderColor: Colors.successBorder,
  },
  tierBadgeCompatible: {
    backgroundColor: '#FFF9E6',
    borderColor: '#FFE08A',
  },
  tierText: {
    ...Typography.caption,
    fontSize: 11,
    fontWeight: '800',
    letterSpacing: 0.8,
  },
  tierTextStrong: {
    color: Colors.success,
  },
  tierTextCompatible: {
    color: Colors.accentDark,
  },
  scoreContainer: {
    alignItems: 'flex-end',
  },
  scoreNumber: {
    ...Typography.headline,
    fontSize: 22,
    color: Colors.primary,
    fontWeight: '800',
    lineHeight: 26,
  },
  scoreLabel: {
    ...Typography.caption,
    fontSize: 9,
    color: Colors.textMuted,
    letterSpacing: 1,
  },
  candidateName: {
    ...Typography.display,
    fontSize: 26,
    lineHeight: 32,
    fontFamily: 'serif',
    color: Colors.text,
    marginBottom: 6,
  },
  socialBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: Colors.backgroundSecondary,
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: 8,
    alignSelf: 'flex-start',
    marginBottom: 8,
  },
  socialIcon: {
    fontSize: 12,
    marginRight: 6,
  },
  socialText: {
    ...Typography.caption,
    color: Colors.textSecondary,
    fontWeight: '600',
  },
  actionRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    marginTop: 14,
  },
  declineButton: {
    paddingVertical: 14,
    paddingHorizontal: 20,
    borderRadius: 12,
    borderWidth: 1.5,
    borderColor: Colors.border,
    alignItems: 'center',
    justifyContent: 'center',
  },
  declineButtonText: {
    ...Typography.button,
    color: Colors.textSecondary,
    fontSize: 14,
  },
  expressButton: {
    flex: 1,
    backgroundColor: Colors.primary,
    paddingVertical: 14,
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
    shadowColor: Colors.primary,
    shadowOffset: { width: 0, height: 3 },
    shadowOpacity: 0.2,
    shadowRadius: 6,
    elevation: 2,
  },
  expressButtonText: {
    ...Typography.button,
    fontSize: 15,
  },
  pendingBanner: {
    flex: 1,
    backgroundColor: Colors.backgroundSecondary,
    borderWidth: 1,
    borderColor: Colors.border,
    paddingVertical: 14,
    borderRadius: 12,
    alignItems: 'center',
  },
  pendingBannerText: {
    ...Typography.button,
    color: Colors.textSecondary,
    fontSize: 14,
  },
  mutualBanner: {
    flex: 1,
    backgroundColor: Colors.successBackground,
    borderWidth: 1.5,
    borderColor: Colors.success,
    paddingVertical: 14,
    borderRadius: 12,
    alignItems: 'center',
  },
  mutualBannerText: {
    ...Typography.button,
    color: Colors.success,
    fontSize: 15,
    fontWeight: '700',
  },
});
