import React from 'react';
import type { AgentStage } from '../types/chat';
import { ChevronRight, Check } from 'lucide-react';

interface ProgressIndicatorProps {
  currentStage: AgentStage;
}

interface StageStep {
  id: AgentStage;
  label: string;
}

const STAGES: StageStep[] = [
  { id: 'new', label: 'New' },
  { id: 'searching', label: 'Searching' },
  { id: 'matches_shown', label: 'Matches Found' },
  { id: 'verification_required', label: 'Verification' },
  { id: 'verified', label: 'Verified' },
  { id: 'completed', label: 'Completed' },
];

export const ProgressIndicator: React.FC<ProgressIndicatorProps> = ({ currentStage }) => {
  const stageOrder: AgentStage[] = ['new', 'searching', 'matches_shown', 'verification_required', 'verified', 'completed'];
  const currentIndex = stageOrder.indexOf(currentStage);

  return (
    <div className="progress-indicator-bar">
      <div className="stages-flow">
        {STAGES.map((stage, idx) => {
          const stepIndex = stageOrder.indexOf(stage.id);
          const isPassed = currentIndex > stepIndex;
          const isCurrent = currentStage === stage.id;

          return (
            <React.Fragment key={stage.id}>
              <div
                className={`progress-step-item ${isPassed ? 'completed' : ''} ${
                  isCurrent ? 'active' : ''
                }`}
              >
                <div className="step-badge">
                  {isPassed ? <Check className="check-icon" /> : stepIndex + 1}
                </div>
                <span className="step-name">{stage.label}</span>
              </div>
              {idx < STAGES.length - 1 && <ChevronRight className="flow-arrow" />}
            </React.Fragment>
          );
        })}
      </div>
    </div>
  );
};
