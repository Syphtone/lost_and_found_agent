import React, { useState } from 'react';
import { ShieldQuestion, Send, HelpCircle } from 'lucide-react';

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
      <div className="v-card-header">
        <ShieldQuestion className="v-card-icon" />
        <div>
          <h4 className="v-card-title">Ownership Verification</h4>
          <p className="v-card-question">
            Can you describe one distinctive feature of your item?
          </p>
        </div>
      </div>

      <div className="v-card-hint">
        <HelpCircle className="hint-icon" />
        <span>Describe something only the owner would know (e.g. scratch, sticker, engraving).</span>
      </div>

      <form onSubmit={handleSubmit} className="v-form-row">
        <input
          type="text"
          className="v-text-input"
          placeholder="e.g. There is a scratch on the left earcup..."
          value={inputVal}
          onChange={(e) => setInputVal(e.target.value)}
          disabled={disabled}
        />
        <button
          type="submit"
          className="v-submit-btn"
          disabled={disabled || !inputVal.trim()}
        >
          <span>Verify</span>
          <Send className="btn-icon-xs" />
        </button>
      </form>
    </div>
  );
};
