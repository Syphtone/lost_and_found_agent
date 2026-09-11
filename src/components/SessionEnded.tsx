import React from 'react';
import { CheckCircle2, RotateCcw } from 'lucide-react';

interface SessionEndedProps {
  onStartNewSession: () => void;
}

export const SessionEnded: React.FC<SessionEndedProps> = ({ onStartNewSession }) => {
  return (
    <div className="session-ended-container">
      <div className="session-ended-card">
        <div className="session-ended-icon">
          <CheckCircle2 className="icon-lg" />
        </div>
        <h3 className="session-ended-title">Session Completed</h3>
        <p className="session-ended-message">
          Your Lost & Found session has ended because your previous item was successfully verified and a pickup claim was created.
        </p>
        <p className="session-ended-submessage">
          You can start a new session to report another lost item.
        </p>
        <button className="start-new-session-btn" onClick={onStartNewSession}>
          <RotateCcw className="btn-icon" />
          Start New Session
        </button>
      </div>
    </div>
  );
};
