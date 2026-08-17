import { WeeklyMatchDTO } from '../api/authApi';

export interface MatchesState {
  matches: WeeklyMatchDTO[];
  decliningCandidate: WeeklyMatchDTO | null;
  activeMutualCandidate: WeeklyMatchDTO | null;
  isLoading: boolean;
  error: string | null;
}

export type MatchesAction =
  | { type: 'FETCH_START' }
  | { type: 'FETCH_SUCCESS'; payload: WeeklyMatchDTO[] }
  | { type: 'FETCH_ERROR'; payload: string }
  | { type: 'OPTIMISTIC_EXPRESS_INTEREST'; candidateId: string }
  | {
      type: 'EXPRESS_INTEREST_SUCCESS';
      candidateId: string;
      status: 'pending' | 'mutual' | 'declined';
      isMutual: boolean;
    }
  | { type: 'EXPRESS_INTEREST_FAILURE'; candidateId: string; prevStatus: 'none' | 'pending' | 'mutual' | 'declined'; error: string }
  | { type: 'OPEN_DECLINE_MODAL'; candidate: WeeklyMatchDTO }
  | { type: 'CLOSE_DECLINE_MODAL' }
  | { type: 'CONFIRM_DECLINE_SUCCESS'; candidateId: string }
  | { type: 'DISMISS_MUTUAL_REVEAL' };

export const initialMatchesState: MatchesState = {
  matches: [],
  decliningCandidate: null,
  activeMutualCandidate: null,
  isLoading: false,
  error: null,
};

export function interestReducer(state: MatchesState, action: MatchesAction): MatchesState {
  switch (action.type) {
    case 'FETCH_START':
      return {
        ...state,
        isLoading: true,
        error: null,
      };

    case 'FETCH_SUCCESS': {
      // Filter out any candidates marked as declined
      const visibleMatches = action.payload.filter((m) => m.interest_status !== 'declined');
      return {
        ...state,
        isLoading: false,
        matches: visibleMatches,
        error: null,
      };
    }

    case 'FETCH_ERROR':
      return {
        ...state,
        isLoading: false,
        error: action.payload,
      };

    case 'OPTIMISTIC_EXPRESS_INTEREST':
      return {
        ...state,
        matches: state.matches.map((m) =>
          m.candidate_id === action.candidateId
            ? { ...m, interest_status: 'pending' }
            : m
        ),
      };

    case 'EXPRESS_INTEREST_SUCCESS': {
      let triggeredMutualCandidate: WeeklyMatchDTO | null = state.activeMutualCandidate;

      const updatedMatches = state.matches.map((m) => {
        if (m.candidate_id === action.candidateId) {
          const updated: WeeklyMatchDTO = {
            ...m,
            interest_status: action.status,
            is_mutual: action.isMutual,
          };
          if (action.isMutual) {
            triggeredMutualCandidate = updated;
          }
          return updated;
        }
        return m;
      });

      return {
        ...state,
        matches: updatedMatches,
        activeMutualCandidate: triggeredMutualCandidate,
      };
    }

    case 'EXPRESS_INTEREST_FAILURE':
      return {
        ...state,
        matches: state.matches.map((m) =>
          m.candidate_id === action.candidateId
            ? { ...m, interest_status: action.prevStatus }
            : m
        ),
        error: action.error,
      };

    case 'OPEN_DECLINE_MODAL':
      return {
        ...state,
        decliningCandidate: action.candidate,
      };

    case 'CLOSE_DECLINE_MODAL':
      return {
        ...state,
        decliningCandidate: null,
      };

    case 'CONFIRM_DECLINE_SUCCESS':
      return {
        ...state,
        matches: state.matches.filter((m) => m.candidate_id !== action.candidateId),
        decliningCandidate: null,
      };

    case 'DISMISS_MUTUAL_REVEAL':
      return {
        ...state,
        activeMutualCandidate: null,
      };

    default:
      return state;
  }
}
