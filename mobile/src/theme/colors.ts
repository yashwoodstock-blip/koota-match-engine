/**
 * Koota Match Design Tokens: Warm Indian Matrimonial Editorial Palette
 */
export const Colors = {
  background: '#FAF8F5',
  backgroundSecondary: '#F5F0EB',
  surface: '#FFFFFF',
  surfaceCard: '#FFFFFF',
  
  primary: '#C85A32',          // Deep Terracotta
  primaryDark: '#A93B18',
  primaryLight: '#E27B54',
  
  accent: '#D4AF37',           // Muted Royal Gold
  accentDark: '#B38F24',
  accentLight: '#F3E5AB',
  
  text: '#2C2523',             // Deep Charcoal
  textSecondary: '#7A6E69',    // Subdued Charcoal
  textMuted: '#9E938F',
  textInverse: '#FFFFFF',
  
  border: '#EADECF',           // Warm Sand Border
  borderFocus: '#C85A32',
  
  error: '#D32F2F',
  errorBackground: '#FDEDED',
  errorBorder: '#F5C6CB',
  
  success: '#2E7D32',
  successBackground: '#EDF7ED',
  successBorder: '#C3E6CB',
} as const;

export type ColorScheme = typeof Colors;
