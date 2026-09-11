import React, { useState } from 'react';
import { ShieldQuestion, Send } from 'lucide-react';

interface VerificationCardProps {
  onSubmitVerification: (distinctiveFeature: string) => void;
  disabled?: boolean;
}

export const VerificationCard: React.FC<VerificationCardProps> = ({
  onSubmitVerification,
  disabled = false,
}) => {
  const [inputVal, setInputVal] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputVal.trim() || disabled) return;
    onSubmitVerification(inputVal.trim());
    setInputVal('');
  };

  return (
    <div className="verification-card-box">
      <div className="verification-header">
        <ShieldQuestion className="verification-icon" />
        <span className="verification-title">Describe a distinctive feature</span>
      </div>

      <form onSubmit={handleSubmit} className="verification-form">
        <input
          type="text"
          className="verification-input"
          placeholder="e.g. scratch on left earcup, red sticker, engraving..."
          value={inputVal}
          onChange={(e) => setInputVal(e.target.value)}
          disabled={disabled}
        />
        <button
          type="submit"
          className="verification-submit"
          disabled={disabled || !inputVal.trim()}
        >
          <Send className="submit-icon" />
        </button>
      </form>
    </div>
  );
};
