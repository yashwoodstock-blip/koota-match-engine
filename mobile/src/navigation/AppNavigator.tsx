import React from 'react';
import { View, ActivityIndicator, StyleSheet } from 'react-native';
import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { Colors } from '../theme/colors';
import { useAuth } from '../context/AuthContext';
import { QuestionnaireProvider } from '../context/QuestionnaireContext';
import { AuthStackParamList, MainStackParamList } from './types';
import { WelcomeScreen } from '../screens/WelcomeScreen';
import { InviteCodeScreen } from '../screens/InviteCodeScreen';
import { GoogleLoginScreen } from '../screens/GoogleLoginScreen';
import { ProfileSetupScreen } from '../screens/ProfileSetupScreen';
import { ObjectiveQuestionnaireScreen } from '../screens/ObjectiveQuestionnaireScreen';
import { SubjectiveQuestionnaireScreen } from '../screens/SubjectiveQuestionnaireScreen';
import { HomeScreen } from '../screens/HomeScreen';

const AuthStack = createNativeStackNavigator<AuthStackParamList>();
const MainStack = createNativeStackNavigator<MainStackParamList>();

export const AppNavigator: React.FC = () => {
  const { isLoading, isAuthenticated, profile } = useAuth();

  if (isLoading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color={Colors.primary} />
      </View>
    );
  }

  return (
    <NavigationContainer>
      {isAuthenticated ? (
        <QuestionnaireProvider>
          <MainStack.Navigator
            initialRouteName={profile?.isNewUser ? 'ProfileSetup' : 'Home'}
            screenOptions={{
              headerShown: false,
              animation: 'slide_from_right',
              contentStyle: { backgroundColor: Colors.background },
            }}
          >
            <MainStack.Screen name="ProfileSetup" component={ProfileSetupScreen} />
            <MainStack.Screen
              name="ObjectiveQuestionnaire"
              component={ObjectiveQuestionnaireScreen}
            />
            <MainStack.Screen
              name="SubjectiveQuestionnaire"
              component={SubjectiveQuestionnaireScreen}
            />
            <MainStack.Screen name="Home" component={HomeScreen} />
          </MainStack.Navigator>
        </QuestionnaireProvider>
      ) : (
        <AuthStack.Navigator
          initialRouteName="Welcome"
          screenOptions={{
            headerShown: false,
            animation: 'slide_from_right',
            contentStyle: { backgroundColor: Colors.background },
          }}
        >
          <AuthStack.Screen name="Welcome" component={WelcomeScreen} />
          <AuthStack.Screen name="InviteCode" component={InviteCodeScreen} />
          <AuthStack.Screen name="GoogleLogin" component={GoogleLoginScreen} />
        </AuthStack.Navigator>
      )}
    </NavigationContainer>
  );
};

const styles = StyleSheet.create({
  loadingContainer: {
    flex: 1,
    backgroundColor: Colors.background,
    justifyContent: 'center',
    alignItems: 'center',
  },
});
