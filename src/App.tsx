import { useState } from 'react';
import { Sidebar } from './components/Sidebar';
import { ProgressIndicator } from './components/ProgressIndicator';
import { ChatWindow } from './components/ChatWindow';
import { InputBox } from './components/InputBox';
import { SessionEnded } from './components/SessionEnded';
import { detectCategoryKey, CATEGORY_MATCH_DATABASE, rankMatches, isItemRefinement, findExactCandidateMatch } from './data/mockResponses';
import type { ChatMessage, AgentStage, MatchItem } from './types/chat';

type SessionStatus = 'active' | 'completed' | 'ended';

export function App() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [currentStage, setCurrentStage] = useState<AgentStage>('new');
  const [isSearching, setIsSearching] = useState(false);
  const [searchStatusText, setSearchStatusText] = useState('AI is searching...');
  const [sessionStatus, setSessionStatus] = useState<SessionStatus>('active');
  const [candidateMatches, setCandidateMatches] = useState<MatchItem[]>([]);
  const [selectedMatch, setSelectedMatch] = useState<MatchItem | null>(null);

  const delay = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

  // Check if thread is waiting for distinctive feature verification
  const isWaitingVerification = currentStage === 'verification_required';

  const handleSendMessage = async (text: string) => {
    if (!text.trim() || isSearching) return;

    // Prevent new searches if session is completed
    if (sessionStatus === 'completed') {
      setSessionStatus('ended');
      return;
    }

    // Prevent any action if session is ended
    if (sessionStatus === 'ended') {
      return;
    }

    const userMessage: ChatMessage = {
      id: `usr-${Date.now()}`,
      sender: 'user',
      text,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    setMessages((prev) => [...prev, userMessage]);
    setIsSearching(true);

    // STATE MACHINE: Determine next action based on current stage
    switch (currentStage) {
      case 'new':
      case 'matches_shown':
        // Initial lost report OR item refinement - search/rank matches
        await handleSearchAndRank(text);
        break;

      case 'verification_required':
        // First check if user is selecting an exact candidate from the list
        const exactCandidateMatch = findExactCandidateMatch(text, candidateMatches.length > 0 ? candidateMatches : []);
        if (exactCandidateMatch) {
          // User selected a specific candidate - select it and stay in verification
          setSelectedMatch(exactCandidateMatch);
          const selectionMessage: ChatMessage = {
            id: `ai-select-${Date.now()}`,
            sender: 'ai',
            text: `You've selected: ${exactCandidateMatch.name}. Can you describe one distinctive feature of your item to verify ownership?`,
            timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
            stage: 'verification_required',
            match: exactCandidateMatch,
            matches: [exactCandidateMatch], // Only show selected item
            isVerificationPrompt: true,
          };
          setMessages((prev) => [...prev, selectionMessage]);
          setIsSearching(false);
        } else if (isItemRefinement(text)) {
          // User is refining their item description - re-rank
          await handleSearchAndRank(text);
        } else {
          // User is providing verification feature
          await handleVerification();
        }
        break;

      case 'verifying':
      case 'verified':
      case 'pickup_claim':
      case 'completed':
      case 'ended':
        // These states should not accept new messages in normal flow
        setIsSearching(false);
        break;

      default:
        setIsSearching(false);
    }
  };

  const handleSearchAndRank = async (text: string) => {
    setCurrentStage('searching');
    setSearchStatusText('Understanding request...');
    await delay(500);

    setCurrentStage('searching');
    setSearchStatusText('Searching for potential matches...');
    await delay(700);

    setCurrentStage('searching');
    setSearchStatusText('Evaluating item features...');
    await delay(500);

    // Detect category from user message and get relevant matches
    const categoryKey = detectCategoryKey(text);
    const baseMatches = CATEGORY_MATCH_DATABASE[categoryKey] || CATEGORY_MATCH_DATABASE['generic'];

    // Check if user message exactly matches one of the existing candidates
    const exactMatch = findExactCandidateMatch(text, candidateMatches.length > 0 ? candidateMatches : baseMatches);

    if (exactMatch) {
      // User has explicitly identified a candidate - select it and move to verification
      setSelectedMatch(exactMatch);

      const aiMatchMessage: ChatMessage = {
        id: `ai-match-${Date.now()}`,
        sender: 'ai',
        text: `You've selected: ${exactMatch.name}. Can you describe one distinctive feature of your item to verify ownership?`,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        stage: 'verification_required',
        match: exactMatch,
        matches: [exactMatch], // Only show the selected item, not the full list
        isVerificationPrompt: true,
      };

      setMessages((prev) => [...prev, aiMatchMessage]);
      setCurrentStage('verification_required');
      setIsSearching(false);
      return;
    }

    // No exact match - rank and show all candidates
    const rankedMatches = rankMatches(text, baseMatches);

    // Update state with ranked candidates
    setCandidateMatches(rankedMatches);

    // Select the top-ranked match as the current selected match
    const primaryMatch = rankedMatches[0];
    setSelectedMatch(primaryMatch);

    const aiMatchMessage: ChatMessage = {
      id: `ai-match-${Date.now()}`,
      sender: 'ai',
      text: `I found ${rankedMatches.length} potential match${rankedMatches.length > 1 ? 'es' : ''}. Can you describe one distinctive feature of your item to verify ownership?`,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      stage: 'verification_required',
      match: primaryMatch,
      matches: rankedMatches,
      isVerificationPrompt: true,
    };

    setMessages((prev) => [...prev, aiMatchMessage]);
    setCurrentStage('matches_shown');
    setIsSearching(false);
  };

  const handleVerification = async () => {
    setCurrentStage('verifying');
    setSearchStatusText('Verifying ownership...');
    await delay(900);

    setCurrentStage('verified');
    setIsSearching(false);

    // Success verification flow - use the current selectedMatch
    const match = selectedMatch;

    if (match) {
      const successMessage: ChatMessage = {
        id: `ai-res-${Date.now()}`,
        sender: 'ai',
        text: 'Your item has been successfully verified.',
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        stage: 'verified',
        verificationResult: 'success',
        match: match,
        pickupLocation: match.pickupLocation || 'Library Security Desk',
        pickupId: `PK-${Math.random().toString(36).substring(2, 8).toUpperCase()}`,
      };
      setMessages((prev) => [...prev, successMessage]);
      setCurrentStage('pickup_claim');
      setSessionStatus('completed');
    }
  };

  const handleStartNewSession = () => {
    setMessages([]);
    setCurrentStage('new');
    setIsSearching(false);
    setSearchStatusText('AI is searching...');
    setSessionStatus('active');
    setCandidateMatches([]);
    setSelectedMatch(null);
  };

  return (
    <div className="app-layout">
      <Sidebar onNewChat={handleStartNewSession} currentStage={currentStage} />

      <div className="main-content">
        {sessionStatus === 'ended' ? (
          <SessionEnded onStartNewSession={handleStartNewSession} />
        ) : (
          <>
            <ProgressIndicator currentStage={currentStage} />

            <ChatWindow
              messages={messages}
              isSearching={isSearching}
              searchStatusText={searchStatusText}
              onSelectSuggestion={handleSendMessage}
              onVerificationSubmit={handleSendMessage}
            />

            <InputBox
              onSendMessage={handleSendMessage}
              disabled={isSearching || sessionStatus === 'completed'}
              placeholderText={
                isWaitingVerification
                  ? 'Describe a distinctive feature (e.g. "Scratch on left earcup")...'
                  : 'Describe the item you lost...'
              }
            />
          </>
        )}
      </div>
    </div>
  );
}

export default App;
