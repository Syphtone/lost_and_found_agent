import React from 'react';
import type { SuggestionChip } from '../types/chat';

interface SuggestionChipsProps {
  onSelectSuggestion: (promptText: string) => void;
  disabled?: boolean;
}

const SUGGESTIONS: SuggestionChip[] = [
  {
    id: 'find_item',
    label: '🔍 Find my item',
    prompt: 'I lost my black Sony headphones near the library around 4 PM.',
  },
  {
    id: 'report_found',
    label: '📦 Report a found item',
    prompt: 'I found a blue Hydro Flask water bottle near the sports gym.',
  },
  {
    id: 'help_me',
    label: '❓ Help me',
    prompt: 'How does Lost & Found AI verify ownership of found items?',
  },
];

export const SuggestionChips: React.FC<SuggestionChipsProps> = ({
  onSelectSuggestion,
  disabled = false,
}) => {
  return (
    <div className="suggestion-chips-wrapper">
      {SUGGESTIONS.map((chip) => (
        <button
          key={chip.id}
          className="suggestion-chip-btn"
          onClick={() => onSelectSuggestion(chip.prompt)}
          disabled={disabled}
        >
          {chip.label}
        </button>
      ))}
    </div>
  );
};
