import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { settingsFixture } from '../test/fixtures';
import { renderWithProviders } from '../test/render';
import { SettingsPanel } from './SettingsPanel';

const mocks = vi.hoisted(() => ({ updatePomodoroSettings: vi.fn() }));

vi.mock('../api/settings', () => ({ updatePomodoroSettings: mocks.updatePomodoroSettings }));

describe('SettingsPanel', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mocks.updatePomodoroSettings.mockResolvedValue(settingsFixture);
  });

  it('validates timer duration ranges before submitting', async () => {
    const user = userEvent.setup();
    renderWithProviders(<SettingsPanel settings={settingsFixture} onClose={vi.fn()} />);

    const focusInput = screen.getByLabelText('Focus duration');
    await user.clear(focusInput);
    await user.type(focusInput, '0');
    await user.click(screen.getByRole('button', { name: 'Save settings' }));

    expect(screen.getByRole('alert')).toHaveTextContent('Use 1-180 minutes for focus');
    expect(mocks.updatePomodoroSettings).not.toHaveBeenCalled();
  });

  it('saves a valid timer rhythm', async () => {
    const user = userEvent.setup();
    renderWithProviders(<SettingsPanel settings={settingsFixture} onClose={vi.fn()} />);

    const focusInput = screen.getByLabelText('Focus duration');
    await user.clear(focusInput);
    await user.type(focusInput, '50');
    await user.click(screen.getByRole('button', { name: 'Save settings' }));

    await waitFor(() => {
      expect(mocks.updatePomodoroSettings).toHaveBeenCalledWith({
        focus_minutes: 50,
        short_break_minutes: 5,
        long_break_minutes: 15,
        long_break_every: 4,
      });
    });
    expect(await screen.findByText('Timer rhythm saved.')).toBeInTheDocument();
  });
});
