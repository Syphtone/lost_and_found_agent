import React from 'react';
import type { MatchItem } from '../types/chat';
import { MapPin, ShieldCheck, Tag, Calendar } from 'lucide-react';

interface MatchCardProps {
  match?: MatchItem;
  matches?: MatchItem[];
  onSelectMatch?: (match: MatchItem) => void;
}

export const MatchCard: React.FC<MatchCardProps> = ({ match, matches, onSelectMatch }) => {
  const itemList = matches && matches.length > 0 ? matches : match ? [match] : [];

  if (itemList.length === 0) return null;

  return (
    <div className="matches-list-container flex flex-col gap-2">
      <div className="matches-header-label font-bold text-xs uppercase tracking-wider text-indigo-400 mb-1">
        Potential Matches ({itemList.length})
      </div>
      {itemList.map((item, idx) => (
        <div
          key={item.id || idx}
          className={`compact-match-card ${onSelectMatch ? 'cursor-pointer hover:border-indigo-500 transition-all' : ''}`}
          onClick={() => onSelectMatch && onSelectMatch(item)}
        >
          <div className="card-top-bar">
            <span className="potential-match-label">
              {idx === 0 ? 'Top Match' : `Option #${idx + 1}`}
            </span>
            <div className={`status-pill-badge ${item.matchStrength.includes('Strong') ? 'bg-emerald-500/15 border-emerald-500/30 text-emerald-300' : ''}`}>
              <ShieldCheck className="badge-icon-xs" />
              <span>{item.statusText || item.matchStrength}</span>
            </div>
          </div>

          <h3 className="card-item-title">{item.name}</h3>

          <div className="card-meta-rows">
            <div className="meta-row-item">
              <MapPin className="meta-icon" />
              <span>Found near: <strong>{item.location}</strong></span>
            </div>
            {item.foundDate && (
              <div className="meta-row-item">
                <Calendar className="meta-icon" />
                <span>Found on: <strong>{item.foundDate}</strong></span>
              </div>
            )}
            <div className="meta-row-item">
              <Tag className="meta-icon" />
              <span>Match Confidence: <strong>{item.matchStrength}</strong></span>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
};
