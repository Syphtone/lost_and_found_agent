import React from 'react';
import { Sparkles, RotateCcw, ShieldAlert, CheckCircle } from 'lucide-react';

interface HeaderProps {
  onReset: () => void;
  forceFailMode: boolean;
  onToggleForceFail: () => void;
}

export const Header: React.FC<HeaderProps> = ({ onReset, forceFailMode, onToggleForceFail }) => {
  return (
    <header className="main-header">
      <div className="header-brand-group">
        <div className="brand-logo shadow-glow">
          <Sparkles className="logo-sparkle" />
        </div>
        <div>
          <div className="brand-title-row">
            <h1 className="brand-title">Lost & Found AI</h1>
          </div>
          <p className="brand-tagline">Find what matters. Verify with confidence.</p>
        </div>
      </div>

      <div className="header-right-group">
        {/* AI Online Status Indicator */}
        <div className="ai-online-status">
          <span className="online-dot"></span>
          <span className="status-text">AI Assistant • Online</span>
        </div>

        {/* Hackathon Demo Verification Simulator Toggle */}
        <button
          className={`demo-toggle-btn ${forceFailMode ? 'fail-mode' : 'pass-mode'}`}
          onClick={onToggleForceFail}
          title={forceFailMode ? "Demo Mode: Simulating Verification Failure/Escalation" : "Demo Mode: Simulating Verification Success"}
        >
          {forceFailMode ? <ShieldAlert className="btn-icon-xs" /> : <CheckCircle className="btn-icon-xs" />}
          <span>{forceFailMode ? 'Test: Fail Mode' : 'Test: Success Mode'}</span>
        </button>

        <button className="reset-btn" onClick={onReset} title="Reset Conversation">
          <RotateCcw className="btn-icon-xs" />
          <span>Reset</span>
        </button>
      </div>
    </header>
  );
};
