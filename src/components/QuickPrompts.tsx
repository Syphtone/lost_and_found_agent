import React from 'react';
import { DEMO_SCENARIOS } from '../data/mockResponses';
import { Sparkles, ArrowUpRight } from 'lucide-react';

interface QuickPromptsProps {
  onSelectPrompt: (promptText: string) => void;
  disabled?: boolean;
}

export const QuickPrompts: React.FC<QuickPromptsProps> = ({ onSelectPrompt, disabled }) => {
  return (
    <div className="quick-prompts-container">
      <div className="quick-prompts-header">
        <Sparkles className="qp-sparkle" />
        <span>Hackathon Demo Scenarios:</span>
      </div>

      <div className="quick-prompts-chips">
        {DEMO_SCENARIOS.map((scenario) => (
          <button
            key={scenario.id}
            className="prompt-chip"
            onClick={() => onSelectPrompt(scenario.initialPrompt)}
            disabled={disabled}
            title={scenario.description}
          >
            <span className="chip-title">{scenario.title}</span>
            <ArrowUpRight className="chip-arrow" />
          </button>
        ))}
      </div>
    </div>
  );
};
