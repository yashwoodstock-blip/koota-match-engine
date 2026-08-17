import {
  interestReducer,
  initialMatchesState,
  MatchesState,
} from '../src/context/interestReducer';
import { WeeklyMatchDTO } from '../src/api/authApi';

const mockCandidateA: WeeklyMatchDTO = {
  candidate_id: 'cand-01',
  candidate_name: 'Ananya Sharma',
  score: 0.94,
  tier: 'strong match',
  alignment_points: ['Shared egalitarian career vision'],
  friction_points: ['Morning routine differences'],
  interest_status: 'none',
  is_mutual: false,
};

const mockCandidateB: WeeklyMatchDTO = {
  candidate_id: 'cand-02',
  candidate_name: 'Neha Verma',
  score: 0.86,
  tier: 'compatible with flagged friction points',
  alignment_points: ['Mutual love for travel'],
  friction_points: ['Living arrangement preferences'],
  interest_status: 'none',
  is_mutual: false,
};

describe('interestReducer Pure State Machine', () => {
  test('FETCH_SUCCESS populates matches and filters out declined candidates', () => {
    const declinedCandidate: WeeklyMatchDTO = {
      ...mockCandidateB,
      candidate_id: 'cand-declined',
      interest_status: 'declined',
    };

    const state = interestReducer(initialMatchesState, {
      type: 'FETCH_SUCCESS',
      payload: [mockCandidateA, declinedCandidate],
    });

    expect(state.matches.length).toBe(1);
    expect(state.matches[0].candidate_id).toBe('cand-01');
    expect(state.isLoading).toBe(false);
  });

  test('OPTIMISTIC_EXPRESS_INTEREST changes interest_status to pending immediately', () => {
    const startState: MatchesState = {
      ...initialMatchesState,
      matches: [mockCandidateA],
    };

    const state = interestReducer(startState, {
      type: 'OPTIMISTIC_EXPRESS_INTEREST',
      candidateId: 'cand-01',
    });

    expect(state.matches[0].interest_status).toBe('pending');
  });

  test('EXPRESS_INTEREST_SUCCESS with isMutual=true sets activeMutualCandidate', () => {
    const startState: MatchesState = {
      ...initialMatchesState,
      matches: [{ ...mockCandidateA, interest_status: 'pending' }],
    };

    const state = interestReducer(startState, {
      type: 'EXPRESS_INTEREST_SUCCESS',
      candidateId: 'cand-01',
      status: 'mutual',
      isMutual: true,
    });

    expect(state.matches[0].interest_status).toBe('mutual');
    expect(state.matches[0].is_mutual).toBe(true);
    expect(state.activeMutualCandidate).not.toBeNull();
    expect(state.activeMutualCandidate?.candidate_id).toBe('cand-01');
  });

  test('OPEN_DECLINE_MODAL and CLOSE_DECLINE_MODAL manage confirmation state without network', () => {
    const startState: MatchesState = {
      ...initialMatchesState,
      matches: [mockCandidateA],
    };

    const openState = interestReducer(startState, {
      type: 'OPEN_DECLINE_MODAL',
      candidate: mockCandidateA,
    });

    expect(openState.decliningCandidate?.candidate_id).toBe('cand-01');

    const closedState = interestReducer(openState, {
      type: 'CLOSE_DECLINE_MODAL',
    });

    expect(closedState.decliningCandidate).toBeNull();
    expect(closedState.matches.length).toBe(1); // Candidate still in list
  });

  test('CONFIRM_DECLINE_SUCCESS permanently removes candidate from active matches', () => {
    const startState: MatchesState = {
      ...initialMatchesState,
      matches: [mockCandidateA, mockCandidateB],
      decliningCandidate: mockCandidateA,
    };

    const state = interestReducer(startState, {
      type: 'CONFIRM_DECLINE_SUCCESS',
      candidateId: 'cand-01',
    });

    expect(state.matches.length).toBe(1);
    expect(state.matches[0].candidate_id).toBe('cand-02');
    expect(state.decliningCandidate).toBeNull();
  });

  test('DISMISS_MUTUAL_REVEAL clears activeMutualCandidate', () => {
    const startState: MatchesState = {
      ...initialMatchesState,
      activeMutualCandidate: mockCandidateA,
    };

    const state = interestReducer(startState, {
      type: 'DISMISS_MUTUAL_REVEAL',
    });

    expect(state.activeMutualCandidate).toBeNull();
  });
});
