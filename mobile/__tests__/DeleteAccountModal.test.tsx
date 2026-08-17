import React from 'react';
import { render, fireEvent, act } from '@testing-library/react-native';
import { DeleteAccountModal } from '../src/components/DeleteAccountModal';

describe('DeleteAccountModal Component', () => {
  const mockCancel = jest.fn();
  const mockConfirmDelete = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('renders DPDP right-to-be-forgotten notice when visible', () => {
    const { getByText, getByPlaceholderText } = render(
      <DeleteAccountModal
        visible={true}
        onCancel={mockCancel}
        onConfirmDelete={mockConfirmDelete}
      />
    );

    expect(getByText('Delete Account & Data')).toBeTruthy();
    expect(getByText('DPDP RIGHT-TO-BE-FORGOTTEN')).toBeTruthy();
    expect(getByPlaceholderText('DELETE')).toBeTruthy();
  });

  test('delete button remains disabled until typing DELETE', async () => {
    const { getByText, getByPlaceholderText } = render(
      <DeleteAccountModal
        visible={true}
        onCancel={mockCancel}
        onConfirmDelete={mockConfirmDelete}
      />
    );

    const deleteBtn = getByText('Permanently Delete Account');
    fireEvent.press(deleteBtn);
    expect(mockConfirmDelete).not.toHaveBeenCalled();

    // Type partial or wrong text
    const input = getByPlaceholderText('DELETE');
    fireEvent.changeText(input, 'DEL');
    fireEvent.press(deleteBtn);
    expect(mockConfirmDelete).not.toHaveBeenCalled();

    // Type full DELETE
    fireEvent.changeText(input, 'DELETE');
    await act(async () => {
      fireEvent.press(deleteBtn);
    });
    expect(mockConfirmDelete).toHaveBeenCalled();
  });

  test('tapping cancel invokes onCancel', () => {
    const { getByText } = render(
      <DeleteAccountModal
        visible={true}
        onCancel={mockCancel}
        onConfirmDelete={mockConfirmDelete}
      />
    );

    const cancelBtn = getByText('Cancel & Keep Account');
    fireEvent.press(cancelBtn);

    expect(mockCancel).toHaveBeenCalled();
    expect(mockConfirmDelete).not.toHaveBeenCalled();
  });
});
