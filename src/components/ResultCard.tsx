import React from 'react';
import { CheckCircle2, AlertTriangle, PackageCheck, UserCheck } from 'lucide-react';

interface ResultCardProps {
  verified: boolean;
  pickupRequestId?: string;
  escalationId?: string;
}

export const ResultCard: React.FC<ResultCardProps> = ({
  verified,
  pickupRequestId,
  escalationId,
}) => {
  if (verified) {
    return (
      <div className="result-card verified-success">
        <div className="result-header">
          <div className="result-badge-icon success">
            <CheckCircle2 className="r-icon" />
          </div>
          <div>
            <div className="status-tag success-tag">✓ Match Verified</div>
            <h4 className="result-title">Your item has been successfully verified</h4>
          </div>
        </div>

        <div className="result-body">
          <div className="pickup-box">
            <div className="pickup-icon-wrapper">
              <PackageCheck className="p-icon" />
            </div>
            <div>
              <span className="pickup-label">Pickup Request Created</span>
              <span className="pickup-id">{pickupRequestId || 'PK-89241'}</span>
            </div>
          </div>
          <p className="result-instructions">
            Please present this request ID at the <strong>Main Campus Security Desk</strong> (Building A, Room 102) along with a valid ID to retrieve your item.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="result-card escalated-amber">
      <div className="result-header">
        <div className="result-badge-icon warning">
          <AlertTriangle className="r-icon" />
        </div>
        <div>
          <div className="status-tag warning-tag">Verification Inconclusive</div>
          <h4 className="result-title">Verification could not be completed automatically</h4>
        </div>
      </div>

      <div className="result-body">
        <div className="escalation-box">
          <div className="escalation-icon-wrapper">
            <UserCheck className="e-icon" />
          </div>
          <div>
            <span className="escalation-label">Case Referred to Lost & Found Staff</span>
            <span className="escalation-id">{escalationId || 'ESC-4019'}</span>
          </div>
        </div>
        <p className="result-instructions">
          A Lost & Found team member will manually review your claim and follow up with you directly. You can also visit the staff office with additional proof of ownership.
        </p>
      </div>
    </div>
  );
};
