import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { Colors } from '../theme/colors';
import { Typography } from '../theme/typography';

interface Props {
  alignments: string[];
  frictions: string[];
}

export const AlignmentFrictionList: React.FC<Props> = ({ alignments, frictions }) => {
  return (
    <View style={styles.container}>
      {/* Alignment Highlights */}
      {alignments.length > 0 && (
        <View style={styles.section}>
          <View style={styles.sectionHeader}>
            <Text style={styles.headerDot}>✦</Text>
            <Text style={styles.headerTitle}>KEY HARMONIES</Text>
          </View>
          {alignments.map((pt, i) => (
            <View key={i} style={styles.itemRow}>
              <Text style={styles.alignBullet}>✓</Text>
              <Text style={styles.itemText}>{pt}</Text>
            </View>
          ))}
        </View>
      )}

      {/* Friction Points (Constructive Conversation Starters) */}
      {frictions.length > 0 && (
        <View style={styles.section}>
          <View style={styles.sectionHeader}>
            <Text style={[styles.headerDot, { color: Colors.accentDark }]}>💡</Text>
            <Text style={[styles.headerTitle, { color: Colors.accentDark }]}>
              CONVERSATION STARTERS
            </Text>
          </View>
          {frictions.map((pt, i) => (
            <View key={i} style={styles.itemRow}>
              <Text style={styles.frictionBullet}>•</Text>
              <Text style={[styles.itemText, styles.frictionText]}>{pt}</Text>
            </View>
          ))}
        </View>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    marginVertical: 12,
    gap: 12,
  },
  section: {
    backgroundColor: Colors.backgroundSecondary,
    borderRadius: 12,
    padding: 12,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  sectionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  headerDot: {
    color: Colors.success,
    fontSize: 12,
    marginRight: 6,
  },
  headerTitle: {
    ...Typography.caption,
    fontSize: 11,
    letterSpacing: 1,
    color: Colors.textSecondary,
    fontWeight: '700',
  },
  itemRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    marginBottom: 6,
  },
  alignBullet: {
    color: Colors.success,
    fontSize: 12,
    fontWeight: '700',
    marginRight: 8,
    marginTop: 2,
  },
  frictionBullet: {
    color: Colors.accentDark,
    fontSize: 14,
    fontWeight: '800',
    marginRight: 8,
    marginTop: -1,
  },
  itemText: {
    ...Typography.bodySecondary,
    fontSize: 13,
    lineHeight: 18,
    color: Colors.text,
    flex: 1,
  },
  frictionText: {
    color: Colors.textSecondary,
    fontStyle: 'italic',
  },
});
