export type AgentStage = 'new' | 'searching' | 'matches_shown' | 'match_selected' | 'verification_required' | 'verifying' | 'verified' | 'pickup_claim' | 'completed' | 'ended';

export interface MatchItem {
  id: string;
  name: string;
  category: string;
  location: string;
  statusText: string;
  matchStrength: string;
  foundDate?: string;
  foundTime?: string;
  brand?: string;
  color?: string;
  pickupLocation?: string;
}

export interface ChatMessage {
  id: string;
  sender: 'user' | 'ai';
  text: string;
  timestamp: string;
  stage?: AgentStage;
  match?: MatchItem;
  matches?: MatchItem[];
  isVerificationPrompt?: boolean;
  verificationResult?: 'success' | 'failed';
  pickupLocation?: string;
  pickupId?: string;
}

export interface SuggestionChip {
  id: string;
  label: string;
  prompt: string;
}

export interface ApiResponse {
  response: string;
  stage: AgentStage;
  confidence_level?: 'high' | 'medium' | 'low';
  match?: MatchItem;
  matches?: MatchItem[];
  pickup_request_id?: string;
  escalation_id?: string;
}

export interface ChatRequest {
  message: string;
  session_id?: string;
  distinctive_feature?: string;
  stage?: AgentStage;
}

export interface DemoScenario {
  id: string;
  title: string;
  description: string;
  initialPrompt: string;
}
