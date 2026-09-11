import React, { useState, type KeyboardEvent } from 'react';
import { Send } from 'lucide-react';

interface InputBoxProps {
  onSendMessage: (text: string) => void;
  disabled?: boolean;
  placeholderText?: string;
}

export const InputBox: React.FC<InputBoxProps> = ({
  onSendMessage,
  disabled = false,
  placeholderText = 'Describe your lost item (e.g. "I lost my black Sony headphones near the library")...',
}) => {
  const [inputText, setInputText] = useState('');

  const handleSend = () => {
    if (!inputText.trim() || disabled) return;
    onSendMessage(inputText.trim());
    setInputText('');
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="input-box-wrapper">
      <div className="input-bar-inner">
        <input
          type="text"
          className="chat-text-input"
          placeholder={placeholderText}
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={disabled}
        />
        <button
          className="send-action-btn"
          onClick={handleSend}
          disabled={disabled || !inputText.trim()}
          title="Send message"
        >
          <Send className="send-icon-sm" />
        </button>
      </div>
    </div>
  );
};
