import React, { useState } from 'react';
import { CheckCircle2, MapPin, Ticket, ShieldAlert, X, QrCode } from 'lucide-react';

interface PickupCardProps {
  verified: boolean;
  itemName?: string;
  pickupLocation?: string;
  pickupId?: string;
}

export const PickupCard: React.FC<PickupCardProps> = ({
  verified,
  itemName = 'Item',
  pickupLocation = 'Library Security Desk',
  pickupId = 'PK-89241',
}) => {
  const [showModal, setShowModal] = useState(false);

  if (verified) {
    return (
      <>
        <div className="pickup-card-container success">
          <div className="pickup-card-header">
            <CheckCircle2 className="success-check-icon" />
            <div>
              <div className="match-verified-badge">✓ Match verified</div>
              <h4 className="pickup-title">Your item has been successfully verified.</h4>
            </div>
          </div>

          <div className="pickup-action-box">
            <div className="pickup-info-group">
              <Ticket className="ticket-icon" />
              <div>
                <span className="action-label">Pickup request created</span>
                <span className="location-name"><MapPin className="pin-xs" /> {pickupLocation}</span>
              </div>
            </div>
            <button
              className="view-details-btn"
              onClick={() => setShowModal(true)}
            >
              View pickup details
            </button>
          </div>
        </div>

        {/* Claim Details Modal Popup */}
        {showModal && (
          <div className="modal-overlay" onClick={() => setShowModal(false)}>
            <div className="modal-dialog" onClick={(e) => e.stopPropagation()}>
              <div className="modal-header">
                <h3>Pickup Claim Details</h3>
                <button className="close-modal-btn" onClick={() => setShowModal(false)}>
                  <X className="btn-icon-sm" />
                </button>
              </div>

              <div className="claim-qr-box">
                <QrCode className="qr-code-icon" />
                <span className="claim-id-text">Claim ID: <strong>{pickupId}</strong></span>
              </div>

              <div className="claim-details-list">
                <div className="claim-detail-row">
                  <span>Item Verified:</span>
                  <strong>{itemName}</strong>
                </div>
                <div className="claim-detail-row">
                  <span>Pickup Location:</span>
                  <strong>{pickupLocation}</strong>
                </div>
                <div className="claim-detail-row">
                  <span>Operating Hours:</span>
                  <strong>Mon - Fri (8:00 AM - 8:00 PM)</strong>
                </div>
              </div>

              <button className="confirm-close-btn" onClick={() => setShowModal(false)}>
                Done
              </button>
            </div>
          </div>
        )}
      </>
    );
  }

  return (
    <div className="pickup-card-container failed">
      <div className="pickup-card-header">
        <ShieldAlert className="failed-alert-icon" />
        <div>
          <div className="match-failed-badge">Verification could not be completed</div>
          <h4 className="pickup-title">Your case has been referred to Lost & Found staff.</h4>
        </div>
      </div>
      <p className="failed-subtext">
        Our support team will manually review your lost report and follow up with you.
      </p>
    </div>
  );
};
