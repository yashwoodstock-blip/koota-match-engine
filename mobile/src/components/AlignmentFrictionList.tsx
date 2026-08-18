import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { Colors } from '../theme/colors';
import { Typography } from '../theme/typography';

interface Props {
  alignments: string[];
  frictions: string[];
  highImpactUncertainties?: string[];
  cappedBy?: { koota_name?: string; pillar?: string; ceiling?: number };
}

export const AlignmentFrictionList: React.FC<Props> = ({
  alignments,
  frictions,
  highImpactUncertainties = [],
  cappedBy,
}) => {
  return (
    <View style={styles.container}>
      {/* Non-Compensatory Ceiling Alert if Present */}
      {cappedBy && (
        <View style={styles.ceilingAlert}>
          <Text style={styles.ceilingIcon}>⚖️</Text>
          <Text style={styles.ceilingText}>
            Score bounded by non-compensatory ceiling in {cappedBy.koota_name || 'Core Dimension'} ({Math.round((cappedBy.ceiling || 1.0) * 100)}% cap)
          </Text>
        </View>
      )}

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

      {/* High-Impact Uncertainty Exploration Callouts */}
      {highImpactUncertainties.length > 0 && (
        <View style={[styles.section, styles.uncertaintySection]}>
          <View style={styles.sectionHeader}>
            <Text style={styles.uncertaintyIcon}>🔍</Text>
            <Text style={styles.uncertaintyTitle}>AREAS TO EXPLORE DEEPER</Text>
          </View>
          <Text style={styles.uncertaintyIntro}>
            High-impact foundational areas with emerging or exploratory alignment:
          </Text>
          {highImpactUncertainties.map((item, i) => (
            <View key={i} style={styles.itemRow}>
              <Text style={styles.uncertaintyBullet}>✧</Text>
              <Text style={[styles.itemText, styles.uncertaintyItemText]}>{item}</Text>
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
  ceilingAlert: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#FDF3EE',
    borderRadius: 10,
    padding: 10,
    borderWidth: 1,
    borderColor: Colors.accent,
  },
  ceilingIcon: {
    fontSize: 14,
    marginRight: 8,
  },
  ceilingText: {
    ...Typography.caption,
    color: Colors.accentDark,
    fontSize: 12,
    fontWeight: '600',
    flex: 1,
  },
  uncertaintySection: {
    backgroundColor: '#F9F8F5',
    borderColor: Colors.border,
  },
  uncertaintyIcon: {
    fontSize: 12,
    marginRight: 6,
  },
  uncertaintyTitle: {
    ...Typography.caption,
    fontSize: 11,
    letterSpacing: 1,
    color: '#8C6D4F',
    fontWeight: '700',
  },
  uncertaintyIntro: {
    ...Typography.caption,
    fontSize: 11,
    color: Colors.textSecondary,
    marginBottom: 8,
  },
  uncertaintyBullet: {
    color: '#8C6D4F',
    fontSize: 12,
    marginRight: 8,
    marginTop: 2,
  },
  uncertaintyItemText: {
    color: Colors.text,
    fontSize: 12,
  },
});
