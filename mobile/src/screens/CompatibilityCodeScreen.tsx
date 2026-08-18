import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  TextInput,
  StyleSheet,
  TouchableOpacity,
  SafeAreaView,
  ScrollView,
  Share,
  ActivityIndicator,
  Alert,
} from 'react-native';
import * as Haptics from 'expo-haptics';
import { useNavigation } from '@react-navigation/native';
import { Colors } from '../theme/colors';
import { Typography } from '../theme/typography';
import { useAuth } from '../context/AuthContext';
import {
  generateCompatibilityCode,
  checkCompatibilityCode,
  getMyCompatibilityCodes,
  CompatibilityCodeCreateResponse,
  CompatibilityCheckResponse,
  CompatibilityCodeItemDTO,
} from '../api/authApi';
import { AlignmentFrictionList } from '../components/AlignmentFrictionList';
import { EditorialHeader } from '../components/EditorialHeader';

type ActiveTab = 'generate' | 'redeem' | 'history';

export const CompatibilityCodeScreen: React.FC = () => {
  const navigation = useNavigation();
  const { session, profile } = useAuth();

  const [activeTab, setActiveTab] = useState<ActiveTab>('generate');

  // Generate State
  const [isGenerating, setIsGenerating] = useState<boolean>(false);
  const [generatedCode, setGeneratedCode] = useState<CompatibilityCodeCreateResponse | null>(null);
  const [generateError, setGenerateError] = useState<string | null>(null);
  const [copiedToast, setCopiedToast] = useState<boolean>(false);

  // Redeem State
  const [inputCode, setInputCode] = useState<string>('');
  const [isChecking, setIsChecking] = useState<boolean>(false);
  const [checkResult, setCheckResult] = useState<CompatibilityCheckResponse | null>(null);
  const [checkError, setCheckError] = useState<string | null>(null);
  const [errorType, setErrorType] = useState<'400' | '410' | '404' | '429' | 'generic' | null>(null);

  // History State
  const [historyCodes, setHistoryCodes] = useState<CompatibilityCodeItemDTO[]>([]);
  const [isLoadingHistory, setIsLoadingHistory] = useState<boolean>(false);

  useEffect(() => {
    if (activeTab === 'history' && session?.access_token && profile?.id) {
      loadHistory();
    }
  }, [activeTab, session?.access_token, profile?.id]);

  const loadHistory = async () => {
    if (!session?.access_token || !profile?.id) return;
    try {
      setIsLoadingHistory(true);
      const res = await getMyCompatibilityCodes(session.access_token, profile.id);
      setHistoryCodes(res.codes || []);
    } catch (err: any) {
      // Ignore or show empty
    } finally {
      setIsLoadingHistory(false);
    }
  };

  // 1. Generate Flow
  const handleGenerateCode = async () => {
    if (!session?.access_token || !profile?.id || isGenerating) return;

    try {
      setIsGenerating(true);
      setGenerateError(null);
      Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium).catch(() => {});

      const res = await generateCompatibilityCode(session.access_token, profile.id);
      setGeneratedCode(res);
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success).catch(() => {});
    } catch (err: any) {
      setGenerateError(
        err?.detail?.message || err?.message || 'Unable to generate code at this time.'
      );
    } finally {
      setIsGenerating(false);
    }
  };

  const handleShareNative = async () => {
    if (!generatedCode) return;
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light).catch(() => {});

    try {
      await Share.share({
        message: `Namaste! Here is my Koota Match compatibility code: ${generatedCode.code}\n\nEnter this code in your Koota Match app within 24 hours to view our mutual 42-dimension compatibility report.`,
        title: 'Koota Match Compatibility Code',
      });
    } catch (err) {
      // User cancelled share
    }
  };

  const handleCopyClipboard = async () => {
    if (!generatedCode) return;
    Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success).catch(() => {});
    setCopiedToast(true);
    setTimeout(() => setCopiedToast(false), 2500);
  };

  // 2. Redeem Flow
  const handleRedeemCode = async () => {
    const clean = inputCode.trim().toUpperCase();
    if (!clean || !session?.access_token || !profile?.id || isChecking) return;

    try {
      setIsChecking(true);
      setCheckError(null);
      setErrorType(null);
      setCheckResult(null);
      Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium).catch(() => {});

      const res = await checkCompatibilityCode(session.access_token, profile.id, clean);
      setCheckResult(res);
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success).catch(() => {});
    } catch (err: any) {
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Warning).catch(() => {});
      const msg = err?.detail?.message || err?.message || err?.detail || 'Failed to check code.';

      if (typeof msg === 'string' && msg.includes('Cannot redeem your own')) {
        setErrorType('400');
        setCheckError('You cannot redeem your own code. Please share it with your prospective match.');
      } else if (typeof msg === 'string' && (msg.includes('expired') || msg.includes('already been redeemed'))) {
        setErrorType('410');
        setCheckError('This compatibility code has expired or has already been redeemed.');
      } else if (typeof msg === 'string' && msg.includes('limit')) {
        setErrorType('429');
        setCheckError('Weekly limit of 5 compatibility redemptions reached.');
      } else {
        setErrorType('generic');
        setCheckError(typeof msg === 'string' ? msg : 'Invalid compatibility code.');
      }
    } finally {
      setIsChecking(false);
    }
  };

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView contentContainerStyle={styles.scrollContent} showsVerticalScrollIndicator={false}>
        {/* Back Button */}
        <TouchableOpacity
          onPress={() => navigation.goBack()}
          style={styles.backButton}
          accessibilityRole="button"
          accessibilityLabel="Back"
        >
          <Text style={styles.backButtonText}>← Back</Text>
        </TouchableOpacity>

        <EditorialHeader
          eyebrow="MUTUAL CONSENT COMPATIBILITY"
          title="Direct Match Check"
          subtitle="Check compatibility with someone specific using single-use, 24-hour mutual consent codes."
        />

        {/* Tab Switcher */}
        <View style={styles.tabContainer}>
          <TouchableOpacity
            style={[styles.tab, activeTab === 'generate' && styles.tabActive]}
            onPress={() => setActiveTab('generate')}
          >
            <Text style={[styles.tabText, activeTab === 'generate' && styles.tabTextActive]}>
              Share a Code
            </Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={[styles.tab, activeTab === 'redeem' && styles.tabActive]}
            onPress={() => setActiveTab('redeem')}
          >
            <Text style={[styles.tabText, activeTab === 'redeem' && styles.tabTextActive]}>
              Enter a Code
            </Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={[styles.tab, activeTab === 'history' && styles.tabActive]}
            onPress={() => setActiveTab('history')}
          >
            <Text style={[styles.tabText, activeTab === 'history' && styles.tabTextActive]}>
              History
            </Text>
          </TouchableOpacity>
        </View>

        {/* TAB 1: GENERATE */}
        {activeTab === 'generate' && (
          <View style={styles.card}>
            <View style={styles.guidanceBox}>
              <Text style={styles.guidanceTitle}>HOW DIRECT CHECK WORKS</Text>
              <Text style={styles.guidanceBody}>
                Share this only with someone specific — like a prospective match introduced by family or friends. This is not for open browsing; it allows two people who already know of each other to discover their mutual compatibility matrix.
              </Text>
            </View>

            {generatedCode ? (
              <View style={styles.codeResultBox}>
                <Text style={styles.codeEyebrow}>YOUR SINGLE-USE CODE (24H EXPIRY)</Text>
                <Text style={styles.codeDisplay}>{generatedCode.code}</Text>

                <View style={styles.actionRow}>
                  <TouchableOpacity
                    style={styles.shareButton}
                    onPress={handleShareNative}
                    activeOpacity={0.85}
                    accessibilityRole="button"
                    accessibilityLabel="Share on WhatsApp or SMS"
                  >
                    <Text style={styles.shareButtonText}>Share Code 📤</Text>
                  </TouchableOpacity>

                  <TouchableOpacity
                    style={styles.copyButton}
                    onPress={handleCopyClipboard}
                    activeOpacity={0.85}
                    accessibilityRole="button"
                    accessibilityLabel="Copy Code"
                  >
                    <Text style={styles.copyButtonText}>
                      {copiedToast ? 'Copied ✓' : 'Copy'}
                    </Text>
                  </TouchableOpacity>
                </View>

                <Text style={styles.codeExpiryNote}>
                  Valid for 24 hours. Single-use only. Both parties will see the compatibility report upon redemption.
                </Text>
              </View>
            ) : (
              <TouchableOpacity
                style={styles.generateButton}
                onPress={handleGenerateCode}
                disabled={isGenerating}
                activeOpacity={0.85}
                accessibilityRole="button"
                accessibilityLabel="Generate Mutual Consent Code"
              >
                {isGenerating ? (
                  <ActivityIndicator color={Colors.textInverse} />
                ) : (
                  <Text style={styles.generateButtonText}>✦ Generate Compatibility Code</Text>
                )}
              </TouchableOpacity>
            )}

            {generateError && (
              <View style={styles.errorBox}>
                <Text style={styles.errorText}>⚠ {generateError}</Text>
              </View>
            )}
          </View>
        )}

        {/* TAB 2: REDEEM */}
        {activeTab === 'redeem' && (
          <View style={styles.card}>
            <Text style={styles.cardTitle}>Enter Prospective Match's Code</Text>
            <Text style={styles.cardSubtitle}>
              Paste the 7-character code shared by your prospective match or family.
            </Text>

            <TextInput
              style={styles.codeInput}
              value={inputCode}
              onChangeText={setInputCode}
              placeholder="e.g. 7K4MN9P"
              placeholderTextColor={Colors.textMuted}
              autoCapitalize="characters"
              autoCorrect={false}
              maxLength={10}
              editable={!isChecking}
              accessibilityLabel="Compatibility Code Input"
            />

            <TouchableOpacity
              style={[
                styles.checkButton,
                (!inputCode.trim() || isChecking) && styles.buttonDisabled,
              ]}
              onPress={handleRedeemCode}
              disabled={!inputCode.trim() || isChecking}
              activeOpacity={0.85}
              accessibilityRole="button"
              accessibilityLabel="Evaluate Mutual Compatibility"
            >
              {isChecking ? (
                <View style={styles.loadingRow}>
                  <ActivityIndicator size="small" color={Colors.textInverse} />
                  <Text style={styles.checkButtonText}>Calculating 42 Dimensions...</Text>
                </View>
              ) : (
                <Text style={styles.checkButtonText}>Evaluate Compatibility →</Text>
              )}
            </TouchableOpacity>

            {/* ERROR / ADVISORY BOX */}
            {checkError && (
              <View
                style={[
                  styles.advisoryBox,
                  errorType === '410' && styles.advisoryExpired,
                ]}
              >
                <Text style={styles.advisoryTitle}>
                  {errorType === '400'
                    ? 'OWN CODE DETECTED'
                    : errorType === '410'
                    ? 'CODE EXPIRED OR USED'
                    : errorType === '429'
                    ? 'RATE LIMIT REACHED'
                    : 'VERIFICATION NOTICE'}
                </Text>
                <Text style={styles.advisoryBody}>{checkError}</Text>
              </View>
            )}

            {/* RESULT A: VIABLE COMPATIBILITY RESULT */}
            {checkResult && checkResult.is_viable && (
              <View style={styles.resultBox}>
                <View style={styles.resultHeader}>
                  <View style={styles.tierBadge}>
                    <Text style={styles.tierText}>
                      {checkResult.tier?.toUpperCase()}
                    </Text>
                  </View>
                  {checkResult.overall_score && (
                    <Text style={styles.scoreText}>
                      {Math.round(checkResult.overall_score * 100)}%
                    </Text>
                  )}
                </View>

                <Text style={styles.resultSubhead}>
                  Evaluated across 42 Koota dimensions, NLI logic, and multi-provider judging.
                </Text>

                {/* Alignment & Friction breakdown */}
                <AlignmentFrictionList
                  alignments={checkResult.alignment_points}
                  frictions={checkResult.friction_points}
                />
              </View>
            )}

            {/* RESULT B: NON-VIABLE HARD FILTER FINDING (RESPECTFUL PRESENTATION) */}
            {checkResult && !checkResult.is_viable && (
              <View style={styles.nonViableBox}>
                <Text style={styles.nonViableEyebrow}>FOUNDATIONAL BOUNDARY FINDING</Text>
                <Text style={styles.nonViableTitle}>Criteria Divergence</Text>
                <Text style={styles.nonViableBody}>
                  {checkResult.hard_filter_reason || 'Fundamental criteria mismatch'}.
                </Text>
                <Text style={[styles.nonViableBody, { marginTop: 8 }]}>
                  Based on core criteria, this prospective match does not align with mutual foundational filters. Knowing this early protects both families from prolonged misalignment.
                </Text>
              </View>
            )}
          </View>
        )}

        {/* TAB 3: HISTORY */}
        {activeTab === 'history' && (
          <View style={styles.card}>
            <Text style={styles.cardTitle}>Generated Codes & Outcomes</Text>
            <Text style={styles.cardSubtitle}>
              Codes you have generated and the mutual compatibility outcomes once redeemed.
            </Text>

            {isLoadingHistory ? (
              <View style={styles.loadingHistory}>
                <ActivityIndicator size="small" color={Colors.primary} />
                <Text style={styles.loadingHistoryText}>Loading history...</Text>
              </View>
            ) : historyCodes.length === 0 ? (
              <View style={styles.emptyHistory}>
                <Text style={styles.emptyHistoryText}>No compatibility codes generated yet.</Text>
              </View>
            ) : (
              historyCodes.map((item) => (
                <View key={item.code} style={styles.historyCard}>
                  <View style={styles.historyTopRow}>
                    <Text style={styles.historyCode}>{item.code}</Text>
                    <View
                      style={[
                        styles.statusBadge,
                        item.is_used ? styles.statusBadgeUsed : styles.statusBadgeActive,
                      ]}
                    >
                      <Text
                        style={[
                          styles.statusBadgeText,
                          item.is_used ? styles.statusBadgeTextUsed : styles.statusBadgeTextActive,
                        ]}
                      >
                        {item.is_used ? 'REDEEMED' : 'PENDING'}
                      </Text>
                    </View>
                  </View>

                  {item.match_result ? (
                    <View style={styles.historyMatchDetails}>
                      <Text style={styles.historyMatchName}>
                        Redeemed by {item.match_result.candidate_name}
                      </Text>
                      <Text style={styles.historyMatchScore}>
                        Result: {item.match_result.tier} ({Math.round((item.match_result.overall_score || 0) * 100)}%)
                      </Text>
                    </View>
                  ) : (
                    <Text style={styles.historyPendingText}>
                      Awaiting redemption by prospective match before expiration.
                    </Text>
                  )}
                </View>
              ))
            )}
          </View>
        )}
      </ScrollView>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.background,
  },
  scrollContent: {
    paddingHorizontal: 24,
    paddingBottom: 40,
  },
  backButton: {
    alignSelf: 'flex-start',
    marginTop: 10,
    marginBottom: 8,
    paddingVertical: 4,
  },
  backButtonText: {
    ...Typography.bodySecondary,
    color: Colors.textSecondary,
    fontWeight: '600',
  },
  tabContainer: {
    flexDirection: 'row',
    backgroundColor: Colors.backgroundSecondary,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: Colors.border,
    padding: 4,
    marginBottom: 20,
  },
  tab: {
    flex: 1,
    paddingVertical: 10,
    alignItems: 'center',
    borderRadius: 8,
  },
  tabActive: {
    backgroundColor: Colors.surface,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 2,
    elevation: 1,
  },
  tabText: {
    ...Typography.caption,
    fontWeight: '600',
    color: Colors.textSecondary,
  },
  tabTextActive: {
    color: Colors.primary,
    fontWeight: '800',
  },
  card: {
    backgroundColor: Colors.surface,
    borderWidth: 1.5,
    borderColor: Colors.border,
    borderRadius: 20,
    padding: 22,
    shadowColor: Colors.text,
    shadowOffset: { width: 0, height: 3 },
    shadowOpacity: 0.05,
    shadowRadius: 8,
    elevation: 2,
  },
  guidanceBox: {
    backgroundColor: '#FFF9E6',
    borderWidth: 1,
    borderColor: '#FFE08A',
    borderRadius: 14,
    padding: 16,
    marginBottom: 20,
  },
  guidanceTitle: {
    ...Typography.caption,
    fontSize: 11,
    fontWeight: '800',
    color: Colors.accentDark,
    letterSpacing: 0.8,
    marginBottom: 6,
  },
  guidanceBody: {
    ...Typography.bodySecondary,
    fontSize: 13,
    lineHeight: 19,
    color: Colors.text,
  },
  generateButton: {
    backgroundColor: Colors.primary,
    paddingVertical: 16,
    borderRadius: 14,
    alignItems: 'center',
    shadowColor: Colors.primary,
    shadowOffset: { width: 0, height: 3 },
    shadowOpacity: 0.25,
    shadowRadius: 6,
    elevation: 3,
  },
  generateButtonText: {
    ...Typography.button,
    color: Colors.textInverse,
    fontSize: 15,
  },
  codeResultBox: {
    alignItems: 'center',
    backgroundColor: Colors.backgroundSecondary,
    borderRadius: 16,
    padding: 20,
    borderWidth: 1.5,
    borderColor: Colors.border,
  },
  codeEyebrow: {
    ...Typography.caption,
    fontSize: 10,
    letterSpacing: 1.2,
    color: Colors.accentDark,
    fontWeight: '800',
    marginBottom: 8,
  },
  codeDisplay: {
    ...Typography.headline,
    fontSize: 32,
    fontFamily: 'serif',
    fontWeight: '800',
    letterSpacing: 4,
    color: Colors.primary,
    marginBottom: 16,
  },
  actionRow: {
    flexDirection: 'row',
    gap: 10,
    width: '100%',
  },
  shareButton: {
    flex: 2,
    backgroundColor: Colors.primary,
    paddingVertical: 12,
    borderRadius: 10,
    alignItems: 'center',
  },
  shareButtonText: {
    ...Typography.button,
    color: Colors.textInverse,
    fontSize: 14,
  },
  copyButton: {
    flex: 1,
    backgroundColor: Colors.surface,
    borderWidth: 1,
    borderColor: Colors.border,
    paddingVertical: 12,
    borderRadius: 10,
    alignItems: 'center',
  },
  copyButtonText: {
    ...Typography.button,
    color: Colors.text,
    fontSize: 14,
  },
  codeExpiryNote: {
    ...Typography.caption,
    fontSize: 11,
    color: Colors.textMuted,
    textAlign: 'center',
    marginTop: 14,
    lineHeight: 16,
  },
  cardTitle: {
    ...Typography.headline,
    fontSize: 18,
    fontFamily: 'serif',
    color: Colors.text,
    marginBottom: 6,
  },
  cardSubtitle: {
    ...Typography.bodySecondary,
    fontSize: 13,
    lineHeight: 18,
    color: Colors.textSecondary,
    marginBottom: 18,
  },
  codeInput: {
    ...Typography.body,
    borderWidth: 1.5,
    borderColor: Colors.border,
    borderRadius: 12,
    paddingHorizontal: 16,
    paddingVertical: 14,
    fontSize: 20,
    textAlign: 'center',
    fontWeight: '700',
    letterSpacing: 3,
    backgroundColor: Colors.backgroundSecondary,
    color: Colors.text,
    marginBottom: 14,
  },
  checkButton: {
    backgroundColor: Colors.primary,
    paddingVertical: 14,
    borderRadius: 12,
    alignItems: 'center',
  },
  buttonDisabled: {
    opacity: 0.45,
  },
  checkButtonText: {
    ...Typography.button,
    color: Colors.textInverse,
    fontSize: 14,
  },
  loadingRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  advisoryBox: {
    backgroundColor: '#FFF4E5',
    borderWidth: 1,
    borderColor: '#FFD199',
    borderRadius: 12,
    padding: 14,
    marginTop: 16,
  },
  advisoryExpired: {
    backgroundColor: Colors.backgroundSecondary,
    borderColor: Colors.border,
  },
  advisoryTitle: {
    ...Typography.caption,
    fontSize: 11,
    fontWeight: '800',
    color: Colors.accentDark,
    letterSpacing: 0.8,
    marginBottom: 4,
  },
  advisoryBody: {
    ...Typography.bodySecondary,
    fontSize: 13,
    lineHeight: 18,
    color: Colors.text,
  },
  resultBox: {
    marginTop: 20,
    paddingTop: 18,
    borderTopWidth: 1,
    borderTopColor: Colors.border,
  },
  resultHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  tierBadge: {
    backgroundColor: '#FFF4E5',
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#FFD199',
  },
  tierText: {
    ...Typography.caption,
    fontSize: 11,
    fontWeight: '800',
    color: Colors.accentDark,
  },
  scoreText: {
    ...Typography.headline,
    fontSize: 22,
    fontWeight: '800',
    color: Colors.primary,
    fontFamily: 'serif',
  },
  resultSubhead: {
    ...Typography.caption,
    color: Colors.textSecondary,
    marginBottom: 14,
  },
  nonViableBox: {
    backgroundColor: '#FBF9F7',
    borderWidth: 1.5,
    borderColor: Colors.border,
    borderRadius: 16,
    padding: 18,
    marginTop: 20,
  },
  nonViableEyebrow: {
    ...Typography.caption,
    fontSize: 10,
    letterSpacing: 1.2,
    color: Colors.textSecondary,
    fontWeight: '800',
    marginBottom: 4,
  },
  nonViableTitle: {
    ...Typography.headline,
    fontSize: 18,
    fontFamily: 'serif',
    color: Colors.text,
    marginBottom: 8,
  },
  nonViableBody: {
    ...Typography.bodySecondary,
    fontSize: 13,
    lineHeight: 18,
    color: Colors.textSecondary,
  },
  errorBox: {
    backgroundColor: Colors.errorBackground,
    borderRadius: 10,
    padding: 12,
    marginTop: 14,
  },
  errorText: {
    ...Typography.caption,
    color: Colors.error,
    textAlign: 'center',
  },
  loadingHistory: {
    paddingVertical: 20,
    alignItems: 'center',
  },
  loadingHistoryText: {
    ...Typography.caption,
    marginTop: 8,
    color: Colors.textMuted,
  },
  emptyHistory: {
    paddingVertical: 24,
    alignItems: 'center',
  },
  emptyHistoryText: {
    ...Typography.bodySecondary,
    color: Colors.textMuted,
  },
  historyCard: {
    backgroundColor: Colors.backgroundSecondary,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: Colors.border,
    padding: 14,
    marginBottom: 10,
  },
  historyTopRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 6,
  },
  historyCode: {
    ...Typography.body,
    fontWeight: '800',
    letterSpacing: 2,
    color: Colors.primary,
  },
  statusBadge: {
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 6,
  },
  statusBadgeActive: {
    backgroundColor: '#E8F5E9',
  },
  statusBadgeUsed: {
    backgroundColor: '#ECEFF1',
  },
  statusBadgeText: {
    ...Typography.caption,
    fontSize: 10,
    fontWeight: '800',
  },
  statusBadgeTextActive: {
    color: '#2E7D32',
  },
  statusBadgeTextUsed: {
    color: '#546E7A',
  },
  historyMatchDetails: {
    marginTop: 6,
  },
  historyMatchName: {
    ...Typography.body,
    fontSize: 13,
    fontWeight: '700',
    color: Colors.text,
  },
  historyMatchScore: {
    ...Typography.caption,
    color: Colors.textSecondary,
    marginTop: 2,
  },
  historyPendingText: {
    ...Typography.caption,
    fontSize: 11,
    color: Colors.textMuted,
    fontStyle: 'italic',
  },
});
