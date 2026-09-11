import type { ApiResponse, AgentStage, ChatRequest } from '../types/chat';
import { detectCategoryKey, CATEGORY_MATCH_DATABASE } from '../data/mockResponses';

export interface ApiConfig {
  isMockMode: boolean;
  backendUrl: string;
}

const DEFAULT_CONFIG: ApiConfig = {
  isMockMode: false,
  backendUrl: 'http://localhost:8000/chat',
};

class ApiService {
  private config: ApiConfig = { ...DEFAULT_CONFIG };

  public getConfig(): ApiConfig {
    return { ...this.config };
  }

  public setConfig(newConfig: Partial<ApiConfig>): void {
    this.config = { ...this.config, ...newConfig };
  }

  public async sendMessage(
    request: ChatRequest,
    isVerificationStep: boolean = false,
    onStageUpdate?: (stage: AgentStage) => void
  ): Promise<ApiResponse> {
    const delay = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

    if (!this.config.isMockMode) {
      try {
        if (onStageUpdate) onStageUpdate('understanding');
        await delay(200);
        if (onStageUpdate) onStageUpdate('searching');

        const payload = {
          conversation_id: request.session_id || 'conv_demo_01',
          message: request.message,
        };

        const res = await fetch(this.config.backendUrl, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
        });

        if (!res.ok) {
          throw new Error(`HTTP error ${res.status}`);
        }

        const data = await res.json();

        // Map backend stage to frontend AgentStage
        let mappedStage: AgentStage = 'understanding';
        if (data.stage === 'verification_required' || data.stage === 'verifying') {
          mappedStage = 'verification';
        } else if (data.stage === 'verified' || data.stage === 'escalated') {
          mappedStage = 'completed';
        } else if (data.stage === 'searching' || data.stage === 'need_more_information') {
          mappedStage = 'matching';
        }

        if (onStageUpdate) onStageUpdate(mappedStage);

        let matchItem = undefined;
        if (data.match) {
          matchItem = {
            id: data.match.id || 'MATCH-001',
            name: `${data.match.brand || ''} ${data.match.category || 'Item'}`.trim(),
            category: data.match.category || 'General',
            location: data.match.location || 'Unknown',
            statusText: data.stage === 'verification_required' ? 'Verification required' : 'Match found',
            matchStrength: data.confidence_level === 'HIGH' ? 'Strong potential match' : 'Possible match',
            brand: data.match.brand,
            color: data.match.color,
          };
        }

        return {
          response: data.response,
          stage: mappedStage,
          confidence_level: (data.confidence_level || 'medium').toLowerCase() as any,
          match: matchItem,
          pickup_request_id: data.pickup_request_id || (data.pickup ? 'PK-89241' : undefined),
          escalation_id: data.escalation_id,
        };
      } catch (err) {
        console.warn('Backend API request failed, falling back to mock response:', err);
      }
    }

    // Mock Mode Fallback
    if (onStageUpdate) onStageUpdate('understanding');
    await delay(400);

    if (!isVerificationStep) {
      if (onStageUpdate) onStageUpdate('searching');
      await delay(600);

      if (onStageUpdate) onStageUpdate('matching');
      await delay(500);

      if (onStageUpdate) onStageUpdate('verification');

      // Detect category from user message and get relevant matches
      const categoryKey = detectCategoryKey(request.message);
      const matches = CATEGORY_MATCH_DATABASE[categoryKey] || CATEGORY_MATCH_DATABASE['generic'];
      const primaryMatch = matches[0];

      return {
        response: `I found ${matches.length} potential match${matches.length > 1 ? 'es' : ''}. Can you describe one distinctive feature of your item to verify ownership?`,
        stage: 'verification',
        match: primaryMatch,
        matches: matches,
      };
    } else {
      if (onStageUpdate) onStageUpdate('verification');
      await delay(700);

      if (onStageUpdate) onStageUpdate('completed');

      return {
        response: 'Your item has been successfully verified.',
        stage: 'completed',
        pickup_request_id: 'PK-89241',
      };
    }
  }
}

export const apiService = new ApiService();
