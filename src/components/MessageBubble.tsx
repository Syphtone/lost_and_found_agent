import React from 'react';
import type { ChatMessage } from '../types/chat';
import { MatchCard } from './MatchCard';
import { VerificationCard } from './VerificationCard';
import { PickupCard } from './PickupCard';
import { Bot, User } from 'lucide-react';

interface MessageBubbleProps {
  message: ChatMessage;
  onVerificationSubmit?: (distinctiveFeature: string) => void;
  disabled?: boolean;
}

export const MessageBubble: React.FC<MessageBubbleProps> = ({
  message,
  onVerificationSubmit,
  disabled = false,
}) => {
  const isUser = message.sender === 'user';

  return (
    <div className={`chat-message-row ${isUser ? 'user-msg' : 'ai-msg'}`}>
      <div className={`msg-avatar ${isUser ? 'user-avatar-bg' : 'ai-avatar-bg'}`}>
        {isUser ? <User className="avatar-icon-sm" /> : <Bot className="avatar-icon-sm" />}
      </div>

      <div className="msg-body-wrapper">
        <div className="msg-bubble-box">
          <p className="msg-text-content">{message.text}</p>

          {/* Embedded Potential Match Card */}
          {(message.matches || message.match) && (
            <div className="card-embed-slot">
              <MatchCard match={message.match} matches={message.matches} />
            </div>
          )}

          {/* Embedded Ownership Verification Form */}
          {message.isVerificationPrompt && onVerificationSubmit && (
            <div className="card-embed-slot">
              <VerificationCard
                onSubmitVerification={onVerificationSubmit}
                disabled={disabled}
              />
            </div>
          )}

          {/* Embedded Verification Outcome / Pickup Card */}
          {message.verificationResult && (
            <div className="card-embed-slot">
              <PickupCard
                verified={message.verificationResult === 'success'}
                itemName={message.match?.name}
                pickupLocation={message.pickupLocation}
                pickupId={message.pickupId}
              />
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
