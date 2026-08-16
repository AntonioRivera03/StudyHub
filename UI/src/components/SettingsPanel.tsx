import { useMutation, useQueryClient } from '@tanstack/react-query';
import { useState, type FormEvent } from 'react';
import { ApiError } from '../api/client';
import type { PomodoroSettings, UpdatePomodoroSettingsRequest } from '../api/contracts';
import { queryKeys } from '../api/queryKeys';
import { updatePomodoroSettings } from '../api/settings';
import styles from './SettingsPanel.module.css';

interface SettingsPanelProps {
  settings: PomodoroSettings;
  onClose: () => void;
}

type SettingsField = keyof UpdatePomodoroSettingsRequest;

export function SettingsPanel({ settings, onClose }: SettingsPanelProps) {
  const queryClient = useQueryClient();
  const [values, setValues] = useState<Record<SettingsField, string>>({
    focus_minutes: String(settings.focus_minutes),
    short_break_minutes: String(settings.short_break_minutes),
    long_break_minutes: String(settings.long_break_minutes),
    long_break_every: String(settings.long_break_every),
  });
  const [validationError, setValidationError] = useState('');
  const [saved, setSaved] = useState(false);

  const updateMutation = useMutation({
    mutationFn: (payload: UpdatePomodoroSettingsRequest) => updatePomodoroSettings(payload),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: queryKeys.settings });
      setSaved(true);
    },
  });

  function updateField(field: SettingsField, value: string) {
    setSaved(false);
    setValues((current) => ({ ...current, [field]: value }));
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const parsed = {
      focus_minutes: Number(values.focus_minutes),
      short_break_minutes: Number(values.short_break_minutes),
      long_break_minutes: Number(values.long_break_minutes),
      long_break_every: Number(values.long_break_every),
    } satisfies UpdatePomodoroSettingsRequest;
    if (!Number.isInteger(parsed.focus_minutes) || parsed.focus_minutes < 1 || parsed.focus_minutes > 180 ||
        !Number.isInteger(parsed.short_break_minutes) || parsed.short_break_minutes < 1 || parsed.short_break_minutes > 60 ||
        !Number.isInteger(parsed.long_break_minutes) || parsed.long_break_minutes < 1 || parsed.long_break_minutes > 120) {
      setValidationError('Use 1-180 minutes for focus, 1-60 for short breaks, and 1-120 for long breaks.');
      return;
    }
    if (!Number.isInteger(parsed.long_break_every) || parsed.long_break_every < 1 || parsed.long_break_every > 12) {
      setValidationError('Long break cadence must be between 1 and 12 focus sessions.');
      return;
    }
    setValidationError('');
    updateMutation.mutate(parsed);
  }

  return (
    <section className={styles.panel} aria-labelledby="settings-title">
      <div className={styles.heading}>
        <div>
          <p>Rhythm</p>
          <h2 id="settings-title">Timer settings</h2>
        </div>
        <button type="button" onClick={onClose}>Close</button>
      </div>

      <form onSubmit={handleSubmit} noValidate>
        <div className={styles.fields}>
          <label>
            Focus duration
            <span><input aria-label="Focus duration" type="number" min="1" max="180" value={values.focus_minutes} onChange={(event) => updateField('focus_minutes', event.target.value)} /> min</span>
          </label>
          <label>
            Short break
            <span><input aria-label="Short break" type="number" min="1" max="60" value={values.short_break_minutes} onChange={(event) => updateField('short_break_minutes', event.target.value)} /> min</span>
          </label>
          <label>
            Long break
            <span><input aria-label="Long break" type="number" min="1" max="120" value={values.long_break_minutes} onChange={(event) => updateField('long_break_minutes', event.target.value)} /> min</span>
          </label>
          <label>
            Long break every
            <span><input aria-label="Long break every" type="number" min="1" max="12" value={values.long_break_every} onChange={(event) => updateField('long_break_every', event.target.value)} /> sessions</span>
          </label>
        </div>

        {(validationError || updateMutation.isError) && (
          <p className={styles.error} role="alert">
            {validationError || (updateMutation.error instanceof ApiError
              ? updateMutation.error.message
              : 'Settings could not be saved. Please try again.')}
          </p>
        )}
        {saved && <p className={styles.saved} role="status">Timer rhythm saved.</p>}

        <button className={styles.save} type="submit" disabled={updateMutation.isPending}>
          {updateMutation.isPending ? 'Saving...' : 'Save settings'}
        </button>
      </form>
    </section>
  );
}
