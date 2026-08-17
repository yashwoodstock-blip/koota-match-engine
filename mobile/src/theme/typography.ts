import { TextStyle } from 'react-native';
import { Colors } from './colors';

export const Typography: Record<string, TextStyle> = {
  display: {
    fontSize: 32,
    lineHeight: 40,
    fontWeight: '700',
    letterSpacing: -0.5,
    color: Colors.text,
  },
  headline: {
    fontSize: 24,
    lineHeight: 32,
    fontWeight: '600',
    letterSpacing: -0.3,
    color: Colors.text,
  },
  subheadline: {
    fontSize: 18,
    lineHeight: 26,
    fontWeight: '500',
    color: Colors.textSecondary,
  },
  body: {
    fontSize: 15,
    lineHeight: 22,
    fontWeight: '400',
    color: Colors.text,
  },
  bodySecondary: {
    fontSize: 14,
    lineHeight: 20,
    fontWeight: '400',
    color: Colors.textSecondary,
  },
  caption: {
    fontSize: 12,
    lineHeight: 16,
    fontWeight: '500',
    letterSpacing: 0.5,
    color: Colors.textMuted,
  },
  button: {
    fontSize: 16,
    lineHeight: 24,
    fontWeight: '600',
    letterSpacing: 0.2,
    color: Colors.textInverse,
  },
};
