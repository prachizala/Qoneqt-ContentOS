/**
 * Contextual Emoji Keyword Matcher for Viral Captions (Hormozi / MrBeast Style)
 * Maps high-impact script words to animated contextual emojis.
 */

export const EMOJI_DICTIONARY: Record<string, string> = {
  // Tech & AI
  ai: '🤖',
  robot: '🤖',
  cyber: '💻',
  quantum: '⚡',
  code: '👨‍💻',
  hacker: '👾',
  shield: '🛡️',
  security: '🔒',
  cloud: '☁️',
  neural: '🧠',
  network: '🌐',
  future: '🔮',
  data: '📊',

  // Money & Wealth
  money: '💰',
  cash: '💵',
  rich: '🤑',
  profit: '📈',
  grow: '🚀',
  growth: '🚀',
  revenue: '💸',
  dollar: '💲',
  crypto: '🪙',
  bitcoin: '🪙',
  millionaire: '👑',

  // Emotion & Attention
  secret: '🤫',
  stop: '🛑',
  danger: '⚠️',
  warning: '🚨',
  fire: '🔥',
  hot: '🔥',
  shock: '😱',
  insane: '🤯',
  mindblown: '🤯',
  boom: '💥',
  break: '⚡',
  magic: '✨',
  win: '🏆',
  king: '👑',
  target: '🎯',
  super: '⭐',
  star: '🌟',
  check: '✅',
  fast: '⚡',
  speed: '🏎️',
  power: '💪',
  muscle: '💪',
  love: '❤️',
  look: '👀',
  scroll: '📱',
  video: '🎬',
  creator: '🎨',
};

/**
 * Strips punctuation and searches for matching emoji from dictionary
 */
export function getEmojiForWord(rawWord: string): string | null {
  if (!rawWord) return null;
  const clean = rawWord.toLowerCase().replace(/[^a-z0-9]/g, '');
  
  if (EMOJI_DICTIONARY[clean]) {
    return EMOJI_DICTIONARY[clean];
  }

  // Check prefix / substrings
  for (const [key, emoji] of Object.entries(EMOJI_DICTIONARY)) {
    if (clean.startsWith(key) || (key.length >= 4 && clean.includes(key))) {
      return emoji;
    }
  }

  return null;
}
