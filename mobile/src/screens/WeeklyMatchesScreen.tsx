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
import { Colors } from '../theme/colors';
import { Typography } from '../theme/typography';
import { useAuth } from '../context/AuthContext';
import {
  getWeeklyMatches,
  postInterestAction,
  WeeklyMatchDTO,
} from '../api/authApi';
import {
  interestReducer,
  initialMatchesState,
} from '../context/interestReducer';
import { MatchCard } from '../components/MatchCard';
import { DeclineConfirmationModal } from '../components/DeclineConfirmationModal';
import { MutualRevealAnimation } from '../components/MutualRevealAnimation';
import { EditorialHeader } from '../components/EditorialHeader';

export const WeeklyMatchesScreen: React.FC = () => {
  const navigation = useNavigation();
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
                <Text style={styles.emptyIcon}>✦</Text>
                <Text style={styles.emptyTitle}>No Active Cohort Matches</Text>
                <Text style={styles.emptySubtitle}>
                  Your compatibility profile is queued for the upcoming Sunday precomputation run.
                </Text>
              </View>
            }
          />
        )}

        {/* Irreversible Decline Modal */}
        <DeclineConfirmationModal
          visible={state.decliningCandidate !== null}
          candidate={state.decliningCandidate}
          onCancel={() => dispatch({ type: 'CLOSE_DECLINE_MODAL' })}
          onConfirmDecline={handleConfirmDecline}
          isSubmitting={isDeclineSubmitting}
        />

        {/* Celebratory Mutual Reveal Animation */}
        <MutualRevealAnimation
          candidate={state.activeMutualCandidate}
          onDismiss={() => dispatch({ type: 'DISMISS_MUTUAL_REVEAL' })}
        />
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
    paddingHorizontal: 20,
  },
  header: {
    marginTop: 10,
  },
  backButton: {
    alignSelf: 'flex-start',
    marginBottom: 8,
    paddingVertical: 4,
  },
  backButtonText: {
    ...Typography.bodySecondary,
    color: Colors.textSecondary,
    fontWeight: '600',
  },
  errorBanner: {
    backgroundColor: Colors.errorBackground,
    borderWidth: 1,
    borderColor: Colors.errorBorder,
    borderRadius: 12,
    padding: 12,
    marginBottom: 12,
  },
  errorText: {
    ...Typography.caption,
    color: Colors.error,
    textAlign: 'center',
  },
  listContent: {
    paddingBottom: 24,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: {
    ...Typography.bodySecondary,
    marginTop: 12,
    color: Colors.textSecondary,
  },
  emptyContainer: {
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 60,
    paddingHorizontal: 20,
  },
  emptyIcon: {
    fontSize: 28,
    color: Colors.accentDark,
    marginBottom: 12,
  },
  emptyTitle: {
    ...Typography.headline,
    fontSize: 20,
    color: Colors.text,
    marginBottom: 8,
    textAlign: 'center',
  },
  emptySubtitle: {
    ...Typography.bodySecondary,
    textAlign: 'center',
    lineHeight: 20,
    color: Colors.textMuted,
  },
});
