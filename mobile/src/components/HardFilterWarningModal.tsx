import React from 'react';
import {
  Modal,
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  TouchableWithoutFeedback,
  ActivityIndicator,
} from 'react-native';
import * as Haptics from 'expo-haptics';
import { Colors } from '../theme/colors';
import { Typography } from '../theme/typography';

interface Props {
  visible: boolean;
  onCancel: () => void;
  onConfirm: () => Promise<void>;
  isSubmitting?: boolean;
}

export const HardFilterWarningModal: React.FC<Props> = ({
  visible,
  onCancel,
  onConfirm,
  isSubmitting = false,
}) => {
  const handleConfirm = async () => {
    Haptics.notificationAsync(Haptics.NotificationFeedbackType.Warning).catch(() => {});
    await onConfirm();
  };

  return (
    <Modal visible={visible} transparent animationType="fade" onRequestClose={onCancel}>
      <TouchableWithoutFeedback onPress={onCancel}>
        <View style={styles.backdrop}>
          <TouchableWithoutFeedback>
            <View style={styles.sheet}>
              <View style={styles.warningIconBadge}>
                <Text style={styles.warningIcon}>⚖️</Text>
              </View>

              <Text style={styles.title}>Reset Candidate Pool?</Text>

              <View style={styles.noticeBox}>
                <Text style={styles.noticeTitle}>HARD-FILTER ALTERATION DETECTED</Text>
                <Text style={styles.noticeBody}>
                  Changing your fundamental demographic preferences (Religion or Community
                  Requirement) invalidates your current match cohort.
                </Text>
                <Text style={[styles.noticeBody, { marginTop: 8 }]}>
                  Your active weekly matches will be cleared immediately, and fresh calculations
                  will be generated in the upcoming Sunday cohort run.
                </Text>
              </View>

              <View style={styles.buttonGroup}>
                <TouchableOpacity
                  style={styles.cancelButton}
                  onPress={onCancel}
                  disabled={isSubmitting}
                  activeOpacity={0.85}
                  accessibilityRole="button"
                  accessibilityLabel="Keep Previous Filters"
                >
                  <Text style={styles.cancelButtonText}>Cancel & Keep Current</Text>
                </TouchableOpacity>

                <TouchableOpacity
                  style={styles.confirmButton}
                  onPress={handleConfirm}
                  disabled={isSubmitting}
                  activeOpacity={0.85}
                  accessibilityRole="button"
                  accessibilityLabel="Confirm & Reset Matches"
                >
                  {isSubmitting ? (
                    <ActivityIndicator color={Colors.textInverse} />
                  ) : (
                    <Text style={styles.confirmButtonText}>Confirm & Reset Pool</Text>
                  )}
                </TouchableOpacity>
              </View>
            </View>
          </TouchableWithoutFeedback>
        </View>
      </TouchableWithoutFeedback>
    </Modal>
  );
};

const styles = StyleSheet.create({
  backdrop: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.55)',
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 20,
  },
  sheet: {
    backgroundColor: Colors.surface,
    borderRadius: 20,
    padding: 24,
    width: '100%',
    maxWidth: 380,
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.2,
    shadowRadius: 12,
    elevation: 8,
  },
  warningIconBadge: {
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: '#FFF4E5',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 12,
  },
  warningIcon: {
    fontSize: 22,
  },
  title: {
    ...Typography.headline,
    fontSize: 22,
    lineHeight: 28,
    fontFamily: 'serif',
    color: Colors.text,
    textAlign: 'center',
    marginBottom: 12,
  },
  noticeBox: {
    backgroundColor: Colors.backgroundSecondary,
    borderWidth: 1,
    borderColor: Colors.border,
    borderRadius: 12,
    padding: 14,
    width: '100%',
    marginBottom: 20,
  },
  noticeTitle: {
    ...Typography.caption,
    fontSize: 11,
    fontWeight: '800',
    color: Colors.accentDark,
    letterSpacing: 0.8,
    marginBottom: 6,
  },
  noticeBody: {
    ...Typography.bodySecondary,
    fontSize: 13,
    lineHeight: 18,
    color: Colors.text,
  },
  buttonGroup: {
    width: '100%',
    gap: 10,
  },
  cancelButton: {
    backgroundColor: Colors.backgroundSecondary,
    borderWidth: 1.5,
    borderColor: Colors.border,
    paddingVertical: 14,
    borderRadius: 12,
    alignItems: 'center',
    width: '100%',
  },
  cancelButtonText: {
    ...Typography.button,
    color: Colors.text,
    fontSize: 15,
  },
  confirmButton: {
    backgroundColor: Colors.primary,
    paddingVertical: 14,
    borderRadius: 12,
    alignItems: 'center',
    width: '100%',
    shadowColor: Colors.primary,
    shadowOffset: { width: 0, height: 3 },
    shadowOpacity: 0.25,
    shadowRadius: 6,
    elevation: 3,
  },
  confirmButtonText: {
    ...Typography.button,
    color: Colors.textInverse,
    fontWeight: '700',
    fontSize: 15,
  },
});
