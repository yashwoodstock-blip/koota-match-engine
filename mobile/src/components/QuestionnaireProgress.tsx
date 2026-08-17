import React, { useEffect, useRef } from 'react';
import { View, Text, StyleSheet, Animated } from 'react-native';
import { Colors } from '../theme/colors';
import { Typography } from '../theme/typography';

interface Props {
  current: number;
  total: number;
  pillarTitle?: string;
}

export const QuestionnaireProgress: React.FC<Props> = ({ current, total, pillarTitle }) => {
  const animatedWidth = useRef(new Animated.Value(0)).current;

  const progressPercent = Math.min(100, Math.max(0, (current / total) * 100));

  useEffect(() => {
    Animated.spring(animatedWidth, {
      toValue: progressPercent,
      tension: 45,
      friction: 8,
      useNativeDriver: false,
    }).start();
  }, [progressPercent]);

  const widthInterpolation = animatedWidth.interpolate({
    inputRange: [0, 100],
    outputRange: ['0%', '100%'],
  });

  return (
    <View style={styles.container}>
      <View style={styles.topRow}>
        <Text style={styles.stepText}>
          DIMENSION <Text style={styles.stepHighlight}>{current}</Text> OF {total}
        </Text>
        <Text style={styles.percentText}>{Math.round(progressPercent)}%</Text>
      </View>

      {pillarTitle && (
        <Text style={styles.pillarText} numberOfLines={1}>
          {pillarTitle}
        </Text>
      )}

      {/* Progress Track */}
      <View style={styles.track}>
        <Animated.View style={[styles.fill, { width: widthInterpolation }]} />
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    paddingVertical: 12,
  },
  topRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 4,
  },
  stepText: {
    ...Typography.caption,
    letterSpacing: 1.2,
    color: Colors.textSecondary,
  },
  stepHighlight: {
    fontWeight: '800',
    color: Colors.primary,
  },
  percentText: {
    ...Typography.caption,
    fontWeight: '700',
    color: Colors.accentDark,
  },
  pillarText: {
    ...Typography.caption,
    fontSize: 11,
    color: Colors.textMuted,
    marginBottom: 8,
    fontStyle: 'italic',
  },
  track: {
    height: 6,
    backgroundColor: Colors.border,
    borderRadius: 3,
    overflow: 'hidden',
  },
  fill: {
    height: '100%',
    backgroundColor: Colors.primary,
    borderRadius: 3,
  },
});
