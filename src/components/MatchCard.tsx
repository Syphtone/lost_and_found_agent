import React from 'react';
import type { MatchItem } from '../types/chat';
import { MapPin, ShieldCheck, ChevronRight } from 'lucide-react';

interface MatchCardProps {
  match?: MatchItem;
  matches?: MatchItem[];
  onSelectMatch?: (match: MatchItem) => void;
}

export const MatchCard: React.FC<MatchCardProps> = ({ match, matches, onSelectMatch }) => {
  const itemList = matches && matches.length > 0 ? matches : match ? [match] : [];

  if (itemList.length === 0) return null;

  return (
    <div className="matches-list-container">
      {itemList.map((item, idx) => (
        <div
          key={item.id || idx}
          className={`compact-match-card ${onSelectMatch ? 'cursor-pointer' : ''}`}
          onClick={() => onSelectMatch && onSelectMatch(item)}
        >
          <div className="match-card-content">
            <div className="match-card-main">
              <div className="match-item-info">
                <h4 className="match-item-name">{item.name}</h4>
                <div className="match-item-details">
                  <span className="match-detail-item">
                    <MapPin className="detail-icon" />
                    {item.location}
                  </span>
                  {item.brand && (
                    <span className="match-detail-item">
                      {item.brand}
                    </span>
                  )}
                  {item.color && (
                    <span className="match-detail-item">
                      {item.color}
                    </span>
                  )}
                </div>
              </div>
              <div className="match-card-right">
                <div className={`match-confidence ${item.matchStrength.includes('Strong') ? 'high' : 'medium'}`}>
                  <ShieldCheck className="confidence-icon" />
                  <span>{item.matchStrength}</span>
                </div>
                {onSelectMatch && <ChevronRight className="expand-icon" />}
              </div>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
};
