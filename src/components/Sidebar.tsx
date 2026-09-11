import React from 'react';
import { Plus, MessageSquare, Settings, HelpCircle, Sparkles } from 'lucide-react';

interface SidebarProps {
  onNewChat: () => void;
  currentStage?: string;
}

export const Sidebar: React.FC<SidebarProps> = ({ onNewChat, currentStage }) => {
  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <div className="sidebar-brand">
          <Sparkles className="brand-icon" />
          <span className="brand-text">Lost & Found AI</span>
        </div>
      </div>

      <div className="sidebar-content">
        <button className="new-chat-btn" onClick={onNewChat}>
          <Plus className="btn-icon" />
          <span>New Report</span>
        </button>

        <div className="sidebar-section">
          <div className="section-label">Current Session</div>
          <div className="current-session-card">
            <MessageSquare className="session-icon" />
            <div className="session-info">
              <div className="session-title">Lost Item Report</div>
              <div className="session-status">{currentStage || 'Ready'}</div>
            </div>
          </div>
        </div>

        <div className="sidebar-section">
          <div className="section-label">Recent</div>
          <div className="recent-item">
            <MessageSquare className="recent-icon" />
            <span className="recent-text">Wallet near library</span>
          </div>
          <div className="recent-item">
            <MessageSquare className="recent-icon" />
            <span className="recent-text">Phone in classroom</span>
          </div>
        </div>
      </div>

      <div className="sidebar-footer">
        <button className="sidebar-action-btn">
          <Settings className="action-icon" />
          <span>Settings</span>
        </button>
        <button className="sidebar-action-btn">
          <HelpCircle className="action-icon" />
          <span>Help</span>
        </button>
      </div>
    </aside>
  );
};