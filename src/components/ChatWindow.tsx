import React, { useEffect, useRef } from 'react';
import type { ChatMessage } from '../types/chat';
import { MessageBubble } from './MessageBubble';
import { SuggestionChips } from './SuggestionChips';
import { TypingIndicator } from './TypingIndicator';

interface ChatWindowProps {
  messages: ChatMessage[];
  isSearching: boolean;
  searchStatusText?: string;
  onSelectSuggestion: (promptText: string) => void;
  onVerificationSubmit: (distinctiveFeature: string) => void;
}

export const ChatWindow: React.FC<ChatWindowProps> = ({
  messages,
  isSearching,
  searchStatusText,
  onSelectSuggestion,
  onVerificationSubmit,
}) => {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isSearching]);

  return (
    <div className="chat-window-container">
      {/* Welcome AI Card & Suggestion Chips shown when thread is empty */}
      {messages.length === 0 && (
        <div className="welcome-banner-card">
          <p className="welcome-ai-text">
            Hi! I can help you report a lost item or find a possible match. What did you lose?
          </p>
          <SuggestionChips onSelectSuggestion={onSelectSuggestion} disabled={isSearching} />
        </div>
      )}

      {/* Messages Thread */}
      <div className="messages-thread">
        {messages.map((message) => (
          <MessageBubble
            key={message.id}
            message={message}
            onVerificationSubmit={onVerificationSubmit}
            disabled={isSearching}
          />
        ))}

        {/* Typing / Searching Indicator */}
        {isSearching && <TypingIndicator statusText={searchStatusText} />}

        <div ref={bottomRef} />
      </div>
    </div>
  );
};
