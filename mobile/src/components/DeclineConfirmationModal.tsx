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
import { WeeklyMatchDTO } from '../api/authApi';

interface Props {
  visible: boolean;
  candidate: WeeklyMatchDTO | null;
  onCancel: () => void;
  onConfirmDecline: (candidateId: string) => Promise<void>;
  isSubmitting?: boolean;
}

export const DeclineConfirmationModal: React.FC<Props> = ({
  visible,
  candidate,
  onCancel,
  onConfirmDecline,
  isSubmitting = false,
}) => {
  if (!candidate) return null;

  const handleConfirm = async () => {
    Haptics.notificationAsync(Haptics.NotificationFeedbackType.Warning).catch(() => {});
    await onConfirmDecline(candidate.candidate_id);
  };

  return (
    <Modal
      visible={visible}
      transparent
      animationType="fade"
      onRequestClose={onCancel}
    >
      <TouchableWithoutFeedback onPress={onCancel}>
        <View style={styles.backdrop}>
          <TouchableWithoutFeedback>
            <View style={styles.sheet}>
              <View style={styles.warningIconBadge}>
                <Text style={styles.warningIcon}>⚠️</Text>
              </View>

              <Text style={styles.title}>Decline {candidate.candidate_name}?</Text>

              <View style={styles.dangerNotice}>
                <Text style={styles.dangerText}>
                  This action is permanent and cannot be undone.
                </Text>
                <Text style={styles.explanationText}>
                  Once declined, this match is closed permanently. Even if{' '}
                  <Text style={styles.bold}>{candidate.candidate_name}</Text> expresses interest in
                  you later, the engine will never reconnect you.
                </Text>
              </View>

              {/* Action Buttons */}
              <View style={styles.buttonGroup}>
                <TouchableOpacity
                  style={styles.cancelButton}
                  onPress={onCancel}
                  disabled={isSubmitting}
                  activeOpacity={0.85}
                  accessibilityRole="button"
                  accessibilityLabel="Keep Match"
                >
                  <Text style={styles.cancelButtonText}>Keep in Matches</Text>
                </TouchableOpacity>

                <TouchableOpacity
                  style={styles.declineButton}
                  onPress={handleConfirm}
                  disabled={isSubmitting}
                  activeOpacity={0.85}
                  accessibilityRole="button"
                  accessibilityLabel="Yes, Decline Permanently"
                >
                  {isSubmitting ? (
                    <ActivityIndicator color={Colors.textInverse} />
                  ) : (
                    <Text style={styles.declineButtonText}>Yes, Decline Permanently</Text>
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
    backgroundColor: Colors.errorBackground,
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
  dangerNotice: {
    backgroundColor: Colors.errorBackground,
    borderWidth: 1,
    borderColor: Colors.errorBorder,
    borderRadius: 12,
    padding: 14,
    width: '100%',
    marginBottom: 20,
  },
  dangerText: {
    ...Typography.caption,
    fontSize: 12,
    fontWeight: '800',
    color: Colors.error,
    letterSpacing: 0.5,
    marginBottom: 6,
    textTransform: 'uppercase',
  },
  explanationText: {
    ...Typography.bodySecondary,
    fontSize: 13,
    lineHeight: 18,
    color: Colors.text,
  },
  bold: {
    fontWeight: '700',
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
  declineButton: {
    backgroundColor: Colors.error,
    paddingVertical: 14,
    borderRadius: 12,
    alignItems: 'center',
    width: '100%',
    shadowColor: Colors.error,
    shadowOffset: { width: 0, height: 3 },
    shadowOpacity: 0.25,
    shadowRadius: 6,
    elevation: 3,
  },
  declineButtonText: {
    ...Typography.button,
    color: Colors.textInverse,
    fontWeight: '700',
    fontSize: 15,
  },
});
