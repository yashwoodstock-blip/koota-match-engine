export type AuthStackParamList = {
  Welcome: undefined;
  InviteCode: undefined;
  GoogleLogin: undefined;
};

export type MainStackParamList = {
  ProfileSetup: undefined;
  ObjectiveQuestionnaire: { isEditMode?: boolean } | undefined;
  SubjectiveQuestionnaire: { isEditMode?: boolean } | undefined;
  Home: undefined;
  WeeklyMatches: undefined;
  EditProfile: undefined;
};
