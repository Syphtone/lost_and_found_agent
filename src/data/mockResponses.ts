import type { ApiResponse, MatchItem, DemoScenario } from '../types/chat';

export const DEMO_SCENARIOS: DemoScenario[] = [
  {
    id: 'wallet',
    title: 'Wallet',
    description: 'Matches brown wallet & card holder near library.',
    initialPrompt: 'I lost my wallet near the library.',
  },
  {
    id: 'phone',
    title: 'Mobile Phone',
    description: 'Matches iPhone & Samsung phones in classroom block.',
    initialPrompt: 'I lost my phone in the classroom.',
  },
  {
    id: 'keys',
    title: 'Keys',
    description: 'Matches keychains & car keys near parking area.',
    initialPrompt: 'I lost my keys near the parking area.',
  },
  {
    id: 'water_bottle',
    title: 'Water Bottle',
    description: 'Matches stainless steel & Hydro Flask bottles in library.',
    initialPrompt: 'I lost my water bottle in the library.',
  },
  {
    id: 'headphones',
    title: 'Headphones',
    description: 'Matches Sony headphones & wireless earbuds.',
    initialPrompt: 'I lost my headphones.',
  },
];

/**
 * Check if message looks like item refinement (contains item attributes)
 * vs verification feature (short distinctive description)
 */
export const isItemRefinement = (message: string): boolean => {
  const msg = message.toLowerCase();
  const itemKeywords = ['black', 'brown', 'blue', 'red', 'white', 'silver', 'wallet', 'phone', 'iphone', 'samsung', 'android', 'card holder', 'leather', 'watch', 'smart watch', 'headphones', 'earbuds', 'keys', 'keychain', 'bottle', 'backpack', 'laptop', 'umbrella', 'id card', 'student id'];

  return itemKeywords.some(keyword => msg.includes(keyword));
};

/**
 * Check if user message exactly matches one of the candidate names
 * Returns the matching candidate if found, null otherwise
 */
export const findExactCandidateMatch = (message: string, candidates: MatchItem[]): MatchItem | null => {
  const msg = message.toLowerCase().trim();

  for (const candidate of candidates) {
    const candidateName = candidate.name.toLowerCase();
    // Check for exact match
    if (candidateName === msg) {
      return candidate;
    }
    // Check if message contains the full candidate name
    if (msg.includes(candidateName)) {
      return candidate;
    }
  }

  return null;
};

/**
 * Rank matches based on user message attributes
 * Higher score = better match
 */
export const rankMatches = (message: string, matches: MatchItem[]): MatchItem[] => {
  const msg = message.toLowerCase();

  return matches.map(match => {
    let score = 0;

    // Check color match
    if (match.color && msg.includes(match.color.toLowerCase())) {
      score += 10;
    }

    // Check brand match
    if (match.brand && msg.includes(match.brand.toLowerCase())) {
      score += 8;
    }

    // Check name match (exact or partial)
    if (match.name) {
      const nameLower = match.name.toLowerCase();
      if (msg.includes(nameLower)) {
        score += 15;
      } else {
        // Check for partial matches
        const nameWords = nameLower.split(' ');
        nameWords.forEach(word => {
          if (msg.includes(word)) {
            score += 5;
          }
        });
      }
    }

    // Check category match
    if (match.category && msg.includes(match.category.toLowerCase())) {
      score += 3;
    }

    return { ...match, score };
  }).sort((a, b) => (b as any).score - (a as any).score);
};

export const CATEGORY_MATCH_DATABASE: Record<string, MatchItem[]> = {
  wallet: [
    {
      id: 'MATCH-W01',
      name: 'Brown Leather Wallet',
      category: 'Wallet',
      location: 'Library',
      foundDate: 'Sep 8, 4:20 PM',
      statusText: 'Strong potential match',
      matchStrength: 'Strong potential match',
      color: 'brown',
      pickupLocation: 'Library Security Desk',
    },
    {
      id: 'MATCH-W02',
      name: 'Black Card Holder',
      category: 'Wallet',
      location: 'Reading Room',
      foundDate: 'Sep 8, 3:45 PM',
      statusText: 'Possible match',
      matchStrength: 'Possible match',
      color: 'black',
      pickupLocation: 'Library Security Desk',
    },
    {
      id: 'MATCH-W03',
      name: 'Blue Wallet',
      category: 'Wallet',
      location: 'Cafeteria',
      foundDate: 'Sep 7, 6:10 PM',
      statusText: 'Possible match',
      matchStrength: 'Possible match',
      color: 'blue',
      pickupLocation: 'Main Security Desk',
    },
  ],
  phone: [
    {
      id: 'MATCH-P01',
      name: 'Black iPhone',
      category: 'Mobile Phone',
      location: 'Classroom Block',
      foundDate: 'Sep 8, 5:10 PM',
      statusText: 'Strong potential match',
      matchStrength: 'Strong potential match',
      brand: 'Apple',
      color: 'black',
      pickupLocation: 'Main Security Desk',
    },
    {
      id: 'MATCH-P02',
      name: 'Blue Samsung Phone',
      category: 'Mobile Phone',
      location: 'Classroom 204',
      foundDate: 'Sep 8, 2:30 PM',
      statusText: 'Possible match',
      matchStrength: 'Possible match',
      brand: 'Samsung',
      color: 'blue',
      pickupLocation: 'Main Security Desk',
    },
    {
      id: 'MATCH-P03',
      name: 'Black Android Phone',
      category: 'Mobile Phone',
      location: 'Computer Lab',
      foundDate: 'Sep 7, 11:15 AM',
      statusText: 'Possible match',
      matchStrength: 'Possible match',
      color: 'black',
      pickupLocation: 'Main Security Desk',
    },
  ],
  keys: [
    {
      id: 'MATCH-K01',
      name: 'Keychain with 3 Keys',
      category: 'Keys',
      location: 'Parking Area',
      foundDate: 'Sep 8, 1:20 PM',
      statusText: 'Strong potential match',
      matchStrength: 'Strong potential match',
      pickupLocation: 'Main Gate Security Desk',
    },
    {
      id: 'MATCH-K02',
      name: 'Black Keychain',
      category: 'Keys',
      location: 'Main Gate',
      foundDate: 'Sep 8, 11:00 AM',
      statusText: 'Possible match',
      matchStrength: 'Possible match',
      color: 'black',
      pickupLocation: 'Main Gate Security Desk',
    },
    {
      id: 'MATCH-K03',
      name: 'Car Key with Key Ring',
      category: 'Keys',
      location: 'Parking Area',
      foundDate: 'Sep 7, 4:45 PM',
      statusText: 'Possible match',
      matchStrength: 'Possible match',
      pickupLocation: 'Main Gate Security Desk',
    },
  ],
  bottle: [
    {
      id: 'MATCH-B01',
      name: 'Black Stainless Steel Bottle',
      category: 'Water Bottle',
      location: 'Library',
      foundDate: 'Sep 8, 3:15 PM',
      statusText: 'Strong potential match',
      matchStrength: 'Strong potential match',
      color: 'black',
      pickupLocation: 'Library Security Desk',
    },
    {
      id: 'MATCH-B02',
      name: 'Blue Water Bottle',
      category: 'Water Bottle',
      location: 'Reading Room',
      foundDate: 'Sep 8, 10:30 AM',
      statusText: 'Possible match',
      matchStrength: 'Possible match',
      color: 'blue',
      pickupLocation: 'Library Security Desk',
    },
    {
      id: 'MATCH-B03',
      name: 'Transparent Water Bottle',
      category: 'Water Bottle',
      location: 'Library Entrance',
      foundDate: 'Sep 7, 2:10 PM',
      statusText: 'Possible match',
      matchStrength: 'Possible match',
      pickupLocation: 'Library Security Desk',
    },
  ],
  headphones: [
    {
      id: 'MATCH-H01',
      name: 'Black Sony Headphones',
      category: 'Headphones',
      location: 'Library',
      foundDate: 'Sep 8, 4:20 PM',
      statusText: 'Strong potential match',
      matchStrength: 'Strong potential match',
      brand: 'Sony',
      color: 'black',
      pickupLocation: 'Library Security Desk',
    },
    {
      id: 'MATCH-H02',
      name: 'White Wireless Earbuds',
      category: 'Earphones',
      location: 'Classroom Block',
      foundDate: 'Sep 8, 1:15 PM',
      statusText: 'Possible match',
      matchStrength: 'Possible match',
      color: 'white',
      pickupLocation: 'Main Security Desk',
    },
    {
      id: 'MATCH-H03',
      name: 'Black Bluetooth Earphones',
      category: 'Earphones',
      location: 'Cafeteria',
      foundDate: 'Sep 7, 5:00 PM',
      statusText: 'Possible match',
      matchStrength: 'Possible match',
      color: 'black',
      pickupLocation: 'Main Security Desk',
    },
  ],
  id_card: [
    {
      id: 'MATCH-I01',
      name: 'Campus Student ID Card',
      category: 'ID Card',
      location: 'Student Center',
      foundDate: 'Sep 8, 12:00 PM',
      statusText: 'Strong potential match',
      matchStrength: 'Strong potential match',
      pickupLocation: 'Student Center Desk',
    },
    {
      id: 'MATCH-I02',
      name: 'Access Card in Lanyard',
      category: 'ID Card',
      location: 'Library Lobby',
      foundDate: 'Sep 8, 9:45 AM',
      statusText: 'Possible match',
      matchStrength: 'Possible match',
      pickupLocation: 'Library Security Desk',
    },
    {
      id: 'MATCH-I03',
      name: 'Membership ID Card',
      category: 'ID Card',
      location: 'Cafeteria',
      foundDate: 'Sep 7, 3:30 PM',
      statusText: 'Possible match',
      matchStrength: 'Possible match',
      pickupLocation: 'Main Security Desk',
    },
  ],
  watch: [
    {
      id: 'MATCH-WT01',
      name: 'Silver Analog Wristwatch',
      category: 'Watch',
      location: 'Gym Locker Room',
      foundDate: 'Sep 8, 2:40 PM',
      statusText: 'Strong potential match',
      matchStrength: 'Strong potential match',
      color: 'silver',
      pickupLocation: 'Gym Front Desk',
    },
    {
      id: 'MATCH-WT02',
      name: 'Black Smartwatch',
      category: 'Watch',
      location: 'Sports Complex',
      foundDate: 'Sep 8, 11:30 AM',
      statusText: 'Possible match',
      matchStrength: 'Possible match',
      color: 'black',
      pickupLocation: 'Sports Complex Desk',
    },
  ],
  backpack: [
    {
      id: 'MATCH-BP01',
      name: 'Dark Blue North Face Backpack',
      category: 'Backpack',
      location: 'Engineering Building',
      foundDate: 'Sep 8, 5:45 PM',
      statusText: 'Strong potential match',
      matchStrength: 'Strong potential match',
      brand: 'North Face',
      color: 'blue',
      pickupLocation: 'Engineering Building Security',
    },
    {
      id: 'MATCH-BP02',
      name: 'Black Canvas Backpack',
      category: 'Backpack',
      location: 'Bus Stop',
      foundDate: 'Sep 8, 8:20 AM',
      statusText: 'Possible match',
      matchStrength: 'Possible match',
      color: 'black',
      pickupLocation: 'Main Security Desk',
    },
  ],
  laptop: [
    {
      id: 'MATCH-LP01',
      name: '15-inch Silver Dell XPS Laptop',
      category: 'Laptop',
      location: 'Library 2nd Floor',
      foundDate: 'Sep 8, 6:00 PM',
      statusText: 'Strong potential match',
      matchStrength: 'Strong potential match',
      brand: 'Dell',
      color: 'silver',
      pickupLocation: 'Library Security Desk',
    },
    {
      id: 'MATCH-LP02',
      name: 'Space Grey MacBook Air',
      category: 'Laptop',
      location: 'Study Room B',
      foundDate: 'Sep 8, 1:45 PM',
      statusText: 'Possible match',
      matchStrength: 'Possible match',
      brand: 'Apple',
      color: 'grey',
      pickupLocation: 'Library Security Desk',
    },
  ],
  umbrella: [
    {
      id: 'MATCH-UM01',
      name: 'Black Compact Umbrella',
      category: 'Umbrella',
      location: 'Main Entrance',
      foundDate: 'Sep 8, 4:10 PM',
      statusText: 'Strong potential match',
      matchStrength: 'Strong potential match',
      color: 'black',
      pickupLocation: 'Main Entrance Security',
    },
    {
      id: 'MATCH-UM02',
      name: 'Blue Foldable Umbrella',
      category: 'Umbrella',
      location: 'Cafeteria Patio',
      foundDate: 'Sep 7, 5:30 PM',
      statusText: 'Possible match',
      matchStrength: 'Possible match',
      color: 'blue',
      pickupLocation: 'Main Security Desk',
    },
  ],
  generic: [
    {
      id: 'MATCH-GEN01',
      name: 'Unclaimed Found Item #104',
      category: 'General Item',
      location: 'Campus Grounds',
      foundDate: 'Sep 8, 2:00 PM',
      statusText: 'Possible match',
      matchStrength: 'Possible match',
    },
    {
      id: 'MATCH-GEN02',
      name: 'General Personal Belonging #108',
      category: 'General Item',
      location: 'Student Center',
      foundDate: 'Sep 7, 4:00 PM',
      statusText: 'Possible match',
      matchStrength: 'Possible match',
    },
  ],
};

export const detectCategoryKey = (message: string): string => {
  const msg = message.toLowerCase();

  if (msg.includes('wallet') || msg.includes('purse') || msg.includes('card holder')) {
    return 'wallet';
  }
  if (msg.includes('phone') || msg.includes('mobile') || msg.includes('iphone') || msg.includes('samsung') || msg.includes('android')) {
    return 'phone';
  }
  if (msg.includes('key') || msg.includes('keys') || msg.includes('keychain')) {
    return 'keys';
  }
  if (msg.includes('bottle') || msg.includes('water bottle') || msg.includes('flask') || msg.includes('hydro')) {
    return 'bottle';
  }
  if (msg.includes('headphone') || msg.includes('headphones') || msg.includes('earphone') || msg.includes('earphones') || msg.includes('earbud') || msg.includes('earbuds') || msg.includes('airpod') || msg.includes('airpods')) {
    return 'headphones';
  }
  if (msg.includes('id') || msg.includes('identity card') || msg.includes('student id') || msg.includes('card')) {
    return 'id_card';
  }
  if (msg.includes('watch') || msg.includes('smartwatch')) {
    return 'watch';
  }
  if (msg.includes('bag') || msg.includes('backpack') || msg.includes('pack')) {
    return 'backpack';
  }
  if (msg.includes('laptop') || msg.includes('macbook') || msg.includes('dell')) {
    return 'laptop';
  }
  if (msg.includes('umbrella')) {
    return 'umbrella';
  }

  return 'generic';
};

export const getMockResponse = (message: string, isVerificationStep: boolean = false): ApiResponse => {
  if (isVerificationStep) {
    return {
      response: 'Your item has been successfully verified. A pickup request has been created.',
      stage: 'completed',
      pickup_request_id: 'PK-89241',
    };
  }

  const categoryKey = detectCategoryKey(message);
  const matches = CATEGORY_MATCH_DATABASE[categoryKey] || CATEGORY_MATCH_DATABASE['generic'];
  const primaryMatch = matches[0];

  return {
    response: `I found ${matches.length} potential match${matches.length > 1 ? 'es' : ''}. Can you describe one distinctive feature of your item to verify ownership?`,
    stage: 'verification',
    match: primaryMatch,
    matches: matches,
  };
};
