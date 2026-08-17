import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { Colors } from '../theme/colors';
import { Typography } from '../theme/typography';

interface Props {
  eyebrow?: string;
  title: string;
  subtitle?: string;
}

export const EditorialHeader: React.FC<Props> = ({ eyebrow, title, subtitle }) => {
  return (
    <View style={styles.container}>
      {eyebrow && <Text style={styles.eyebrow}>{eyebrow.toUpperCase()}</Text>}
      <Text style={styles.title}>{title}</Text>
      <View style={styles.accentRule} />
      {subtitle && <Text style={styles.subtitle}>{subtitle}</Text>}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    marginBottom: 20,
  },
  eyebrow: {
    ...Typography.caption,
    color: Colors.accentDark,
    letterSpacing: 1.5,
    marginBottom: 6,
  },
  title: {
    ...Typography.headline,
    fontSize: 26,
    lineHeight: 34,
    fontFamily: 'serif',
    color: Colors.primary,
    fontWeight: '700',
  },
  accentRule: {
    height: 2.5,
    width: 36,
    backgroundColor: Colors.accent,
    borderRadius: 1.5,
    marginVertical: 10,
  },
  subtitle: {
    ...Typography.bodySecondary,
    lineHeight: 22,
    color: Colors.textSecondary,
  },
});
