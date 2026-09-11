import React from 'react';
import type { AgentStage } from '../types/chat';
import { Check, Clock, Search, ShieldCheck, CheckCircle2 } from 'lucide-react';

interface ProgressIndicatorProps {
  currentStage: AgentStage;
}

const STAGE_CONFIG: Record<string, { label: string; icon: React.ReactNode }> = {
  'new': { label: 'Ready', icon: <Clock className="stage-icon" /> },
  'searching': { label: 'Searching', icon: <Search className="stage-icon" /> },
  'matches_shown': { label: 'Matches Found', icon: <Search className="stage-icon" /> },
  'match_selected': { label: 'Match Selected', icon: <Search className="stage-icon" /> },
  'verification_required': { label: 'Verification', icon: <ShieldCheck className="stage-icon" /> },
  'verifying': { label: 'Verifying', icon: <ShieldCheck className="stage-icon" /> },
  'verified': { label: 'Verified', icon: <CheckCircle2 className="stage-icon" /> },
  'pickup_claim': { label: 'Pickup Claim', icon: <CheckCircle2 className="stage-icon" /> },
  'completed': { label: 'Completed', icon: <CheckCircle2 className="stage-icon" /> },
  'ended': { label: 'Ended', icon: <Check className="stage-icon" /> },
};

export const ProgressIndicator: React.FC<ProgressIndicatorProps> = ({ currentStage }) => {
  const config = STAGE_CONFIG[currentStage] || STAGE_CONFIG['new'];

  return (
    <div className="progress-indicator-bar">
      <div className="progress-content">
        <div className="progress-icon-wrapper">
          {config.icon}
        </div>
        <div className="progress-text">
          <span className="progress-label">{config.label}</span>
        </div>
      </div>
    </div>
  );
};
