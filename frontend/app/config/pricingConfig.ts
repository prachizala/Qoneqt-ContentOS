export interface PricingTier {
  id: string;
  name: string;
  price: string;
  period: string;
  badge?: string;
  description: string;
  isPopular?: boolean;
  buttonText: string;
  buttonVariant: 'outline' | 'primary' | 'pro' | 'custom';
  features: {
    aiVideos: string;
    aiScripts: string;
    aiVisuals: string;
    aiVoice: string;
    brandKit: string;
    aiQualityCheck: string;
    qoneqtPublishing: string;
    analytics: string;
    teamMembers: string;
    autopilot: string;
    priorityProcessing: string;
  };
}

export const PRICING_TIERS: PricingTier[] = [
  {
    id: 'free',
    name: 'Free',
    price: '₹0',
    period: '/month',
    badge: 'Starter',
    description: 'Essential AI tools to test and start producing short-form video content.',
    buttonText: 'Current Plan',
    buttonVariant: 'outline',
    features: {
      aiVideos: '2 / month',
      aiScripts: '10 / month',
      aiVisuals: 'Limited',
      aiVoice: 'Basic',
      brandKit: '1',
      aiQualityCheck: '✓',
      qoneqtPublishing: '✓',
      analytics: 'Basic',
      teamMembers: '1',
      autopilot: '—',
      priorityProcessing: '—',
    },
  },
  {
    id: 'creator',
    name: 'Creator',
    price: '₹499',
    period: '/month',
    badge: 'Popular',
    isPopular: true,
    description: 'High-volume generation and premium assets for active social creators.',
    buttonText: 'Upgrade to Creator',
    buttonVariant: 'primary',
    features: {
      aiVideos: '15 / month',
      aiScripts: '100 / month',
      aiVisuals: '✓',
      aiVoice: 'Premium',
      brandKit: '3',
      aiQualityCheck: '✓',
      qoneqtPublishing: '✓',
      analytics: 'Advanced',
      teamMembers: '2',
      autopilot: '✓',
      priorityProcessing: '✓',
    },
  },
  {
    id: 'pro',
    name: 'Pro',
    price: '₹1,499',
    period: '/month',
    badge: 'Best Value',
    description: 'Maximum AI generation capacity with deep AI insights & priority queues.',
    buttonText: 'Upgrade to Pro',
    buttonVariant: 'pro',
    features: {
      aiVideos: '50 / month',
      aiScripts: 'Unlimited',
      aiVisuals: '✓',
      aiVoice: 'Premium',
      brandKit: '10',
      aiQualityCheck: 'Advanced',
      qoneqtPublishing: '✓',
      analytics: 'Advanced + AI Insights',
      teamMembers: '5',
      autopilot: '✓',
      priorityProcessing: '✓✓',
    },
  },
  {
    id: 'enterprise',
    name: 'Enterprise',
    price: 'Custom',
    period: '',
    badge: 'Custom',
    description: 'Bespoke AI pipelines, custom cloned voices, dedicated GPU cluster.',
    buttonText: 'Contact Sales',
    buttonVariant: 'custom',
    features: {
      aiVideos: 'Unlimited*',
      aiScripts: 'Unlimited',
      aiVisuals: '✓',
      aiVoice: 'Custom Voice',
      brandKit: 'Unlimited',
      aiQualityCheck: '✓',
      qoneqtPublishing: '✓',
      analytics: 'Full Analytics',
      teamMembers: 'Custom',
      autopilot: '✓',
      priorityProcessing: '✓✓✓',
    },
  },
];

export const MATRIX_FEATURE_ROWS = [
  { key: 'aiVideos', label: 'AI Videos' },
  { key: 'aiScripts', label: 'AI Scripts' },
  { key: 'aiVisuals', label: 'AI Visuals' },
  { key: 'aiVoice', label: 'AI Voice' },
  { key: 'brandKit', label: 'Brand Kit' },
  { key: 'aiQualityCheck', label: 'AI Quality Check' },
  { key: 'qoneqtPublishing', label: 'Qoneqt Publishing' },
  { key: 'analytics', label: 'Analytics' },
  { key: 'teamMembers', label: 'Team Members' },
  { key: 'autopilot', label: 'Autopilot' },
  { key: 'priorityProcessing', label: 'Priority Processing' },
] as const;
