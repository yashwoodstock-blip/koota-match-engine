import React, { useEffect, useRef } from 'react';
import {
  Modal,
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

interface Props {
  candidate: WeeklyMatchDTO | null;
  onDismiss: () => void;
}

export const MutualRevealAnimation: React.FC<Props> = ({ candidate, onDismiss }) => {
  const scaleAnim = useRef(new Animated.Value(0.3)).current;
  const opacityAnim = useRef(new Animated.Value(0)).current;
  const ringScaleAnim = useRef(new Animated.Value(1)).current;

  useEffect(() => {
    if (candidate) {
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success).catch(() => {});

      Animated.parallel([
        Animated.spring(scaleAnim, {
          toValue: 1,
          tension: 60,
          friction: 6,
          useNativeDriver: true,
        }),
        Animated.timing(opacityAnim, {
          toValue: 1,
          duration: 250,
          useNativeDriver: true,
        }),
      ]).start();

      // Radiating ring loop
      Animated.loop(
        Animated.sequence([
          Animated.timing(ringScaleAnim, {
            toValue: 1.25,
            duration: 1200,
            useNativeDriver: true,
          }),
          Animated.timing(ringScaleAnim, {
            toValue: 1,
            duration: 1000,
            useNativeDriver: true,
          }),
        ])
      ).start();
    } else {
      scaleAnim.setValue(0.3);
      opacityAnim.setValue(0);
    }
  }, [candidate]);

  if (!candidate) return null;

  return (
    <Modal visible={!!candidate} transparent animationType="fade" onRequestClose={onDismiss}>
      <View style={styles.backdrop}>
        <Animated.View
          style={[
            styles.card,
            {
              opacity: opacityAnim,
              transform: [{ scale: scaleAnim }],
            },
          ]}
        >
          {/* Radiating Rings */}
          <View style={styles.iconContainer}>
            <Animated.View
              style={[
                styles.pulseRing,
                {
                  transform: [{ scale: ringScaleAnim }],
                },
              ]}
            />
            <View style={styles.iconBadge}>
              <Text style={styles.icon}>💍</Text>
            </View>
          </View>

          <Text style={styles.eyebrow}>MUTUAL HARMONY UNLOCKED</Text>
          <Text style={styles.title}>It's a Match!</Text>

          <Text style={styles.body}>
            You and <Text style={styles.bold}>{candidate.candidate_name}</Text> have both expressed
            mutual interest across the 42-Koota scientific matrix.
          </Text>

          <View style={styles.scorePill}>
            <Text style={styles.scorePillText}>
              ✦ {Math.round(candidate.score * 100)}% COMPATIBILITY RESONANCE
            </Text>
          </View>

          <TouchableOpacity
            style={styles.ctaButton}
            onPress={onDismiss}
            activeOpacity={0.85}
            accessibilityRole="button"
            accessibilityLabel="Proceed to Connection"
          >
            <Text style={styles.ctaButtonText}>Proceed to Connection ✨</Text>
          </TouchableOpacity>
        </Animated.View>
      </View>
    </Modal>
  );
};

const styles = StyleSheet.create({
  backdrop: {
    flex: 1,
    backgroundColor: 'rgba(26, 22, 21, 0.85)', // Deep warm charcoal backdrop
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 24,
  },
  card: {
    backgroundColor: Colors.surface,
    borderRadius: 24,
    padding: 28,
    width: '100%',
    maxWidth: 380,
    alignItems: 'center',
    shadowColor: Colors.accent,
    shadowOffset: { width: 0, height: 6 },
    shadowOpacity: 0.35,
    shadowRadius: 16,
    elevation: 10,
    borderWidth: 2,
    borderColor: Colors.accent,
  },
  iconContainer: {
    alignItems: 'center',
    justifyContent: 'center',
    marginVertical: 12,
  },
  pulseRing: {
    position: 'absolute',
    width: 90,
    height: 90,
    borderRadius: 45,
    backgroundColor: Colors.accentLight,
    opacity: 0.5,
  },
  iconBadge: {
    width: 64,
    height: 64,
    borderRadius: 32,
    backgroundColor: Colors.background,
    borderWidth: 2,
    borderColor: Colors.accentDark,
    alignItems: 'center',
    justifyContent: 'center',
  },
  icon: {
    fontSize: 30,
  },
  eyebrow: {
    ...Typography.caption,
    fontSize: 11,
    color: Colors.accentDark,
    letterSpacing: 2,
    fontWeight: '800',
    marginTop: 8,
    marginBottom: 4,
  },
  title: {
    ...Typography.display,
    fontSize: 32,
    lineHeight: 38,
    fontFamily: 'serif',
    color: Colors.primary,
    fontWeight: '700',
    marginBottom: 12,
  },
  body: {
    ...Typography.body,
    fontSize: 15,
    lineHeight: 22,
    color: Colors.textSecondary,
    textAlign: 'center',
    marginBottom: 16,
  },
  bold: {
    fontWeight: '700',
    color: Colors.text,
  },
  scorePill: {
    backgroundColor: Colors.backgroundSecondary,
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 20,
    borderWidth: 1,
    borderColor: Colors.border,
    marginBottom: 24,
  },
  scorePillText: {
    ...Typography.caption,
    color: Colors.accentDark,
    fontWeight: '700',
    letterSpacing: 1,
  },
  ctaButton: {
    backgroundColor: Colors.primary,
    width: '100%',
    paddingVertical: 16,
    borderRadius: 14,
    alignItems: 'center',
    shadowColor: Colors.primary,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 4,
  },
  ctaButtonText: {
    ...Typography.button,
    color: Colors.textInverse,
    fontWeight: '700',
  },
});
