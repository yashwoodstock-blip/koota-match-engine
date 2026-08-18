import React, { useEffect, useReducer, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  SafeAreaView,
  FlatList,
  RefreshControl,
  ActivityIndicator,
  TouchableOpacity,
} from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import * as Haptics from 'expo-haptics';
import { Colors } from '../theme/colors';
import { Typography } from '../theme/typography';
import { useAuth } from '../context/AuthContext';
import {
  getWeeklyMatches,
  postInterestAction,
  WeeklyMatchDTO,
  RefreshMatchesResponse,
} from '../api/authApi';
import {
  interestReducer,
  initialMatchesState,
} from '../context/interestReducer';
import { MatchCard } from '../components/MatchCard';
import { DeclineConfirmationModal } from '../components/DeclineConfirmationModal';
import { MutualRevealAnimation } from '../components/MutualRevealAnimation';
import { EditorialHeader } from '../components/EditorialHeader';
import { RefreshMatchesButton } from '../components/RefreshMatchesButton';
import { MainStackParamList } from '../navigation/types';

type NavProp = NativeStackNavigationProp<MainStackParamList, 'WeeklyMatches'>;

export const WeeklyMatchesScreen: React.FC = () => {
  const navigation = useNavigation<NavProp>();
  const { session, profile } = useAuth();
  const [state, dispatch] = useReducer(interestReducer, initialMatchesState);
  const [isDeclineSubmitting, setIsDeclineSubmitting] = useState<boolean>(false);

  const fetchMatches = async () => {
    if (!session?.access_token || !profile?.id) return;

    try {
      dispatch({ type: 'FETCH_START' });
      const res = await getWeeklyMatches(session.access_token, profile.id);
      dispatch({ type: 'FETCH_SUCCESS', payload: res.matches || [] });
    } catch (err: any) {
      dispatch({
        type: 'FETCH_ERROR',
        payload: err?.message || 'Unable to load weekly matches.',
      });
    }
  };

  useEffect(() => {
    fetchMatches();
  }, [session?.access_token, profile?.id]);

  // 1. One-Tap Optimistic Express Interest
  const handleExpressInterest = async (candidateId: string) => {
    if (!session?.access_token || !profile?.id) return;

    const currentCandidate = state.matches.find((m) => m.candidate_id === candidateId);
    const prevStatus = currentCandidate?.interest_status || 'none';

    // Instant optimistic update
    dispatch({ type: 'OPTIMISTIC_EXPRESS_INTEREST', candidateId });

    try {
      const res = await postInterestAction(
        session.access_token,
        profile.id,
        candidateId,
        'pending'
      );
      dispatch({
        type: 'EXPRESS_INTEREST_SUCCESS',
        candidateId,
        status: res.status,
        isMutual: res.is_mutual,
      });
    } catch (err: any) {
      dispatch({
        type: 'EXPRESS_INTEREST_FAILURE',
        candidateId,
        prevStatus,
        error: err?.message || 'Failed to express interest.',
      });
    }
  };

  // 2. Open Decline Confirmation Modal
  const handleOpenDeclineModal = (candidate: WeeklyMatchDTO) => {
    dispatch({ type: 'OPEN_DECLINE_MODAL', candidate });
  };

  // 3. Confirm Hard Decline
  const handleConfirmDecline = async (candidateId: string) => {
    if (!session?.access_token || !profile?.id) return;

    try {
      setIsDeclineSubmitting(true);
      await postInterestAction(session.access_token, profile.id, candidateId, 'declined');
      dispatch({ type: 'CONFIRM_DECLINE_SUCCESS', candidateId });
    } catch (err: any) {
      console.warn('[WeeklyMatches] Decline error:', err);
      dispatch({ type: 'CLOSE_DECLINE_MODAL' });
    } finally {
      setIsDeclineSubmitting(false);
    }
  };

  // 4. Handle On-Demand Funnel Refresh Result
  const handleRefreshSuccess = (res: RefreshMatchesResponse) => {
    fetchMatches();
  };

  const renderHeader = () => (
    <View>
      {/* On-Demand Refresh Button */}
      <RefreshMatchesButton onRefreshSuccess={handleRefreshSuccess} />

      {/* Direct Compatibility Code Banner */}
      <TouchableOpacity
        style={styles.directCodeBanner}
        onPress={() => navigation.navigate('CompatibilityCode')}
        activeOpacity={0.85}
        accessibilityRole="button"
        accessibilityLabel="Check Direct Compatibility with someone specific"
      >
        <View style={styles.directCodeIconBadge}>
          <Text style={styles.directCodeIcon}>🔑</Text>
        </View>
        <View style={styles.directCodeTextWrap}>
          <Text style={styles.directCodeTitle}>Have someone specific in mind?</Text>
          <Text style={styles.directCodeSubtitle}>
            Share or enter a 24h mutual consent code →
          </Text>
        </View>
      </TouchableOpacity>

      <Text style={styles.sectionHeader}>CURATED CANDIDATES ({state.matches.length})</Text>
    </View>
  );

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.content}>
        {/* Editorial Header */}
        <View style={styles.header}>
          <TouchableOpacity
            onPress={() => navigation.goBack()}
            style={styles.backButton}
            accessibilityRole="button"
            accessibilityLabel="Go back to dashboard"
          >
            <Text style={styles.backButtonText}>← Dashboard</Text>
          </TouchableOpacity>

          <EditorialHeader
            eyebrow="PRECOMPUTED SUNDAY COHORT"
            title="Weekly Matches"
            subtitle="Curated using SQL filters, 42-Koota vector retrieval, NLI contradiction checks, and LLM-as-a-Judge evaluations."
          />
        </View>

        {state.error && (
          <View style={styles.errorBanner}>
            <Text style={styles.errorText}>⚠ {state.error}</Text>
          </View>
        )}

        {/* Matches List */}
        {state.isLoading && state.matches.length === 0 ? (
          <View style={styles.loadingContainer}>
            <ActivityIndicator size="large" color={Colors.primary} />
            <Text style={styles.loadingText}>Retrieving your precomputed cohort...</Text>
          </View>
        ) : (
          <FlatList
            data={state.matches}
            keyExtractor={(item) => item.candidate_id}
            ListHeaderComponent={renderHeader}
            renderItem={({ item }) => (
              <MatchCard
                match={item}
                onExpressInterest={handleExpressInterest}
                onPressDecline={handleOpenDeclineModal}
              />
            )}
            contentContainerStyle={styles.listContent}
            showsVerticalScrollIndicator={false}
            refreshControl={
              <RefreshControl
                refreshing={state.isLoading}
                onRefresh={fetchMatches}
                tintColor={Colors.primary}
              />
            }
            ListEmptyComponent={
              <View style={styles.emptyContainer}>
                <Text style={styles.emptyTitle}>No Active Matches In Pool</Text>
                <Text style={styles.emptySubtitle}>
                  Your profile has recently been updated or no compatible candidates match your hard filters. Use the button above to run the 5-stage funnel on demand.
                </Text>
              </View>
            }
          />
        )}

        {/* Decline Confirmation Hard-Stop Modal */}
        <DeclineConfirmationModal
          visible={!!state.decliningCandidate}
          candidate={state.decliningCandidate}
          onCancel={() => dispatch({ type: 'CLOSE_DECLINE_MODAL' })}
          onConfirmDecline={handleConfirmDecline}
          isSubmitting={isDeclineSubmitting}
        />

        {/* Mutual Match Celebration Modal */}
        {state.activeMutualCandidate && (
          <MutualRevealAnimation
            candidate={state.activeMutualCandidate}
            onDismiss={() => dispatch({ type: 'DISMISS_MUTUAL_REVEAL' })}
          />
        )}
      </View>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.background,
  },
  content: {
    flex: 1,
  },
  header: {
    paddingHorizontal: 24,
    paddingTop: 10,
    paddingBottom: 6,
  },
  backButton: {
    alignSelf: 'flex-start',
    paddingVertical: 6,
    marginBottom: 4,
  },
  backButtonText: {
    ...Typography.bodySecondary,
    color: Colors.textSecondary,
    fontWeight: '600',
  },
  directCodeBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#FFF9E6',
    borderWidth: 1,
    borderColor: '#FFE08A',
    borderRadius: 14,
    padding: 14,
    marginBottom: 20,
  },
  directCodeIconBadge: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: Colors.surface,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 12,
  },
  directCodeIcon: {
    fontSize: 16,
  },
  directCodeTextWrap: {
    flex: 1,
  },
  directCodeTitle: {
    ...Typography.body,
    fontSize: 13,
    fontWeight: '700',
    color: Colors.accentDark,
  },
  directCodeSubtitle: {
    ...Typography.caption,
    color: Colors.textSecondary,
    marginTop: 2,
  },
  sectionHeader: {
    ...Typography.caption,
    fontSize: 10,
    letterSpacing: 1.5,
    color: Colors.accentDark,
    fontWeight: '800',
    marginBottom: 12,
  },
  listContent: {
    paddingHorizontal: 24,
    paddingBottom: 40,
  },
  loadingContainer: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 40,
  },
  loadingText: {
    ...Typography.bodySecondary,
    color: Colors.textSecondary,
    marginTop: 14,
    textAlign: 'center',
  },
  errorBanner: {
    backgroundColor: Colors.errorBackground,
    borderWidth: 1,
    borderColor: Colors.errorBorder,
    marginHorizontal: 24,
    borderRadius: 10,
    padding: 12,
    marginBottom: 10,
  },
  errorText: {
    ...Typography.caption,
    color: Colors.error,
    textAlign: 'center',
  },
  emptyContainer: {
    backgroundColor: Colors.surface,
    borderWidth: 1.5,
    borderColor: Colors.border,
    borderRadius: 20,
    padding: 30,
    alignItems: 'center',
    marginTop: 10,
  },
  emptyTitle: {
    ...Typography.headline,
    fontSize: 20,
    fontFamily: 'serif',
    color: Colors.primary,
    marginBottom: 8,
  },
  emptySubtitle: {
    ...Typography.bodySecondary,
    color: Colors.textSecondary,
    textAlign: 'center',
    lineHeight: 20,
  },
});
