import React from 'react';
import { Bot, Loader2 } from 'lucide-react';

interface TypingIndicatorProps {
  statusText?: string;
}

export const TypingIndicator: React.FC<TypingIndicatorProps> = ({
  statusText = 'AI is searching for potential matches...',
}) => {
  return (
    <div className="typing-indicator-row">
      <div className="ai-avatar-mini">
        <Bot className="bot-icon-mini" />
      </div>
      <div className="typing-bubble">
        <Loader2 className="spinner-icon-sm" />
        <span className="typing-text-label">{statusText}</span>
      </div>
    </div>
  );
};
