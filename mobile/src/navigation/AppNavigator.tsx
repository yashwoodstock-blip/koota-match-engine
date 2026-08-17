import React from 'react';
import { View, ActivityIndicator, StyleSheet } from 'react-native';
import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { Colors } from '../theme/colors';
import { useAuth } from '../context/AuthContext';
import { AuthStackParamList, MainStackParamList } from './types';
import { WelcomeScreen } from '../screens/WelcomeScreen';
import { InviteCodeScreen } from '../screens/InviteCodeScreen';
import { GoogleLoginScreen } from '../screens/GoogleLoginScreen';
import { HomeScreen } from '../screens/HomeScreen';

const AuthStack = createNativeStackNavigator<AuthStackParamList>();
const MainStack = createNativeStackNavigator<MainStackParamList>();

export const AppNavigator: React.FC = () => {
  const { isLoading, isAuthenticated } = useAuth();

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
        <MainStack.Navigator screenOptions={{ headerShown: false }}>
          <MainStack.Screen name="Home" component={HomeScreen} />
        </MainStack.Navigator>
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
