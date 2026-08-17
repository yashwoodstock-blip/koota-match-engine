import React, { useState } from 'react';
import {
  Modal,
  View,
  Text,
  TextInput,
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
  onConfirmDelete: () => Promise<void>;
  isSubmitting?: boolean;
}

export const DeleteAccountModal: React.FC<Props> = ({
  visible,
  onCancel,
  onConfirmDelete,
  isSubmitting = false,
}) => {
  const [confirmInput, setConfirmInput] = useState<string>('');

  const isConfirmed = confirmInput.trim().toUpperCase() === 'DELETE';

  const handleConfirm = async () => {
    if (!isConfirmed || isSubmitting) return;
    Haptics.notificationAsync(Haptics.NotificationFeedbackType.Warning).catch(() => {});
    await onConfirmDelete();
  };

  const handleClose = () => {
    setConfirmInput('');
    onCancel();
  };

  return (
    <Modal visible={visible} transparent animationType="fade" onRequestClose={handleClose}>
      <TouchableWithoutFeedback onPress={handleClose}>
        <View style={styles.backdrop}>
          <TouchableWithoutFeedback>
            <View style={styles.sheet}>
              <View style={styles.dangerIconBadge}>
                <Text style={styles.dangerIcon}>🗑️</Text>
              </View>

              <Text style={styles.title}>Delete Account & Data</Text>

              <View style={styles.dangerBox}>
                <Text style={styles.dangerTitle}>DPDP RIGHT-TO-BE-FORGOTTEN</Text>
                <Text style={styles.dangerBody}>
                  This action is permanent and completely irreversible. All your demographic data,
                  42-koota answers, 384-dimension vector embeddings, social following list, and
                  match history will be purged with zero recoverable artifacts.
                </Text>
              </View>

              <Text style={styles.instructionText}>
                To proceed, type <Text style={styles.bold}>DELETE</Text> below:
              </Text>

              <TextInput
                style={styles.input}
                value={confirmInput}
                onChangeText={setConfirmInput}
                placeholder="DELETE"
                placeholderTextColor={Colors.textMuted}
                autoCapitalize="characters"
                autoCorrect={false}
                editable={!isSubmitting}
                accessibilityLabel="Confirm delete by typing DELETE"
              />

              <View style={styles.buttonGroup}>
                <TouchableOpacity
                  style={styles.cancelButton}
                  onPress={handleClose}
                  disabled={isSubmitting}
                  activeOpacity={0.85}
                  accessibilityRole="button"
                  accessibilityLabel="Keep Account"
                >
                  <Text style={styles.cancelButtonText}>Cancel & Keep Account</Text>
                </TouchableOpacity>

                <TouchableOpacity
                  style={[
                    styles.deleteButton,
                    !isConfirmed && styles.deleteButtonDisabled,
                  ]}
                  onPress={handleConfirm}
                  disabled={!isConfirmed || isSubmitting}
                  activeOpacity={0.85}
                  accessibilityRole="button"
                  accessibilityLabel="Permanently Delete Account"
                >
                  {isSubmitting ? (
                    <ActivityIndicator color={Colors.textInverse} />
                  ) : (
                    <Text style={styles.deleteButtonText}>Permanently Delete Account</Text>
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
    backgroundColor: 'rgba(0, 0, 0, 0.65)',
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
    shadowOpacity: 0.25,
    shadowRadius: 12,
    elevation: 8,
  },
  dangerIconBadge: {
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: Colors.errorBackground,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 12,
  },
  dangerIcon: {
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
  dangerBox: {
    backgroundColor: Colors.errorBackground,
    borderWidth: 1,
    borderColor: Colors.errorBorder,
    borderRadius: 12,
    padding: 14,
    width: '100%',
    marginBottom: 16,
  },
  dangerTitle: {
    ...Typography.caption,
    fontSize: 11,
    fontWeight: '800',
    color: Colors.error,
    letterSpacing: 0.8,
    marginBottom: 6,
  },
  dangerBody: {
    ...Typography.bodySecondary,
    fontSize: 13,
    lineHeight: 18,
    color: Colors.text,
  },
  instructionText: {
    ...Typography.bodySecondary,
    fontSize: 13,
    color: Colors.textSecondary,
    marginBottom: 8,
    alignSelf: 'flex-start',
  },
  bold: {
    fontWeight: '700',
    color: Colors.error,
  },
  input: {
    ...Typography.body,
    width: '100%',
    borderWidth: 1.5,
    borderColor: Colors.border,
    borderRadius: 12,
    paddingHorizontal: 16,
    paddingVertical: 12,
    fontSize: 16,
    backgroundColor: Colors.background,
    color: Colors.text,
    textAlign: 'center',
    fontWeight: '700',
    letterSpacing: 2,
    marginBottom: 20,
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
  deleteButton: {
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
  deleteButtonDisabled: {
    opacity: 0.45,
    shadowOpacity: 0,
    elevation: 0,
  },
  deleteButtonText: {
    ...Typography.button,
    color: Colors.textInverse,
    fontWeight: '700',
    fontSize: 15,
  },
});
