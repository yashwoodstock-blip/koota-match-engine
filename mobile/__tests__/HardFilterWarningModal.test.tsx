import React from 'react';
import { render, fireEvent, act } from '@testing-library/react-native';
import { HardFilterWarningModal } from '../src/components/HardFilterWarningModal';

describe('HardFilterWarningModal Component', () => {
  const mockCancel = jest.fn();
  const mockConfirm = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('renders hard-filter reset warning when visible', () => {
    const { getByText } = render(
      <HardFilterWarningModal
        visible={true}
        onCancel={mockCancel}
        onConfirm={mockConfirm}
      />
    );

    expect(getByText('Reset Candidate Pool?')).toBeTruthy();
    expect(getByText('HARD-FILTER ALTERATION DETECTED')).toBeTruthy();
    expect(
      getByText(/Changing your fundamental demographic preferences/i)
    ).toBeTruthy();
  });

  test('tapping cancel invokes onCancel', () => {
    const { getByText } = render(
      <HardFilterWarningModal
        visible={true}
        onCancel={mockCancel}
        onConfirm={mockConfirm}
      />
    );

    const cancelBtn = getByText('Cancel & Keep Current');
    fireEvent.press(cancelBtn);

    expect(mockCancel).toHaveBeenCalled();
    expect(mockConfirm).not.toHaveBeenCalled();
  });

  test('tapping confirm invokes onConfirm', async () => {
    const { getByText } = render(
      <HardFilterWarningModal
        visible={true}
        onCancel={mockCancel}
        onConfirm={mockConfirm}
      />
    );

    const confirmBtn = getByText('Confirm & Reset Pool');
    await act(async () => {
      fireEvent.press(confirmBtn);
    });

    expect(mockConfirm).toHaveBeenCalled();
  });
});
