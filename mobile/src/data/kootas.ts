export interface KootaDefinition {
  koota_id: number;
  pillar: string;
  name: string;
  weight: number;
  question_type: 'objective_only' | 'subjective_only' | 'mixed' | 'filter';
  is_hard_filter: boolean;
  objective_questions: string[];
  subjective_questions: string[];
}

export const KOOTAS_DATA: KootaDefinition[] = [
  {
    koota_id: 1,
    pillar: "PILLAR A — Knowing Each Other (Love Maps)",
    name: "Personal History & Formative Experiences",
    weight: 4,
    question_type: "mixed",
    is_hard_filter: false,
    objective_questions: [
      "Family structure growing up (joint/nuclear/single-parent/other); hometown type (urban/semi-urban/rural).",
      "Number of siblings and birth order."
    ],
    subjective_questions: [
      "What's a childhood experience that still shapes how you see relationships today?",
      "What's one value your family passed down that you don't fully agree with anymore?"
    ]
  },
  {
    koota_id: 2,
    pillar: "PILLAR A — Knowing Each Other (Love Maps)",
    name: "Daily Life Rhythm & Preferences",
    weight: 3,
    question_type: "mixed",
    is_hard_filter: false,
    objective_questions: [
      "Morning/night person; preferred pace of daily life (structured/spontaneous).",
      "Preferred weekend structure (family visits / rest / socializing / religious activities)."
    ],
    subjective_questions: [
      "Describe an ordinary Tuesday in the life you actually want — not a vacation, an ordinary day.",
      "What does a fulfilling weekend look like for you, realistically?"
    ]
  },
  {
    koota_id: 3,
    pillar: "PILLAR A — Knowing Each Other (Love Maps)",
    name: "Fears, Stresses & Coping Triggers",
    weight: 5,
    question_type: "mixed",
    is_hard_filter: false,
    objective_questions: [
      "Primary current life stressor category (career/family/health/financial/other).",
      "Comfort asking for help when stressed (Very comfortable / Somewhat / Not at all)."
    ],
    subjective_questions: [
      "What's something that quietly stresses you that most people wouldn't guess?",
      "What's a fear about marriage itself, not about your partner, that you rarely say out loud?"
    ]
  },
  {
    koota_id: 4,
    pillar: "PILLAR A — Knowing Each Other (Love Maps)",
    name: "Dreams, Hopes & Personal Aspirations",
    weight: 6,
    question_type: "subjective_only",
    is_hard_filter: false,
    objective_questions: [],
    subjective_questions: [
      "What's a personal dream you have that has nothing to do with marriage or family — just for you?",
      "If money and family expectations were no constraint, what would you actually be doing with your life?"
    ]
  },
  {
    koota_id: 5,
    pillar: "PILLAR B — Fondness, Admiration & Respect",
    name: "Appreciation & Verbal Affirmation Habits",
    weight: 6,
    question_type: "mixed",
    is_hard_filter: false,
    objective_questions: [
      "Frequency of expressing verbal appreciation in past relationships / family (Daily / Weekly / Rarely).",
      "Preferred mode of receiving appreciation (words / actions / gifts / quality time)."
    ],
    subjective_questions: [
      "When someone you love does something good, how do you naturally react?",
      "What makes you feel genuinely respected by a partner, specifically?"
    ]
  },
  {
    koota_id: 6,
    pillar: "PILLAR B — Fondness, Admiration & Respect",
    name: "Mutual Respect & Ego Dynamics",
    weight: 10,
    question_type: "mixed",
    is_hard_filter: false,
    objective_questions: [
      "Comfort with partner having higher income or professional status (Very comfortable / Neutral / Prefer parity).",
      "Handling public vs private disagreement (Never disagree publicly / Context dependent)."
    ],
    subjective_questions: [
      "How do you handle situations where your partner is publicly recognized and you are not?",
      "What does 'equality in marriage' look like in concrete, daily practice to you?"
    ]
  },
  {
    koota_id: 7,
    pillar: "PILLAR D — Mutual Influence & Decision Making",
    name: "Shared Decision-Making Philosophy",
    weight: 10,
    question_type: "mixed",
    is_hard_filter: false,
    objective_questions: [
      "Decision-making style for major decisions (career move, house purchase): Consensus always / One leads per domain / Independent.",
      "Financial threshold above which consultation is expected (INR 5k / 20k / 50k / 1L+)."
    ],
    subjective_questions: [
      "Tell me about a major decision you had to make with someone else — how did you handle genuine disagreement?",
      "What is a non-negotiable decision where you would expect your partner to defer to you, if any?"
    ]
  },
  {
    koota_id: 8,
    pillar: "PILLAR D — Mutual Influence & Decision Making",
    name: "Accepting Influence & Flexibility",
    weight: 8,
    question_type: "mixed",
    is_hard_filter: false,
    objective_questions: [
      "Past willingness to change significant habits for a partner (diet, social circle, location) — Done it willingly / Resisted / Never asked.",
      "Speed of changing mind when presented with contrary evidence (Quickly / Needs time / Rarely)."
    ],
    subjective_questions: [
      "What's an opinion you used to hold strongly that you changed because of someone you cared about?",
      "How do you feel when your partner asks you to change a small daily habit?"
    ]
  },
  {
    koota_id: 9,
    pillar: "PILLAR C — Emotional Attunement & Bids",
    name: "Emotional Bid Responsiveness",
    weight: 8,
    question_type: "mixed",
    is_hard_filter: false,
    objective_questions: [
      "Self-described response to partner's low mood: Immediately inquire / Give space first / Wait for them to bring it up.",
      "Preferred frequency of emotional check-ins (Daily / When needed / Rare)."
    ],
    subjective_questions: [
      "When you have had a hard day, what is the best thing a partner can do in the first 30 minutes you are home?",
      "How do you recognize when someone you love is hurting without them saying it?"
    ]
  },
  {
    koota_id: 10,
    pillar: "PILLAR C — Emotional Attunement & Bids",
    name: "Vulnerability & Emotional Disclosure",
    weight: 7,
    question_type: "subjective_only",
    is_hard_filter: false,
    objective_questions: [],
    subjective_questions: [
      "How long does it typically take you to share something deeply personal with someone you're dating?",
      "What is something you find very difficult to talk about with anyone, and why?"
    ]
  },
  {
    koota_id: 11,
    pillar: "PILLAR E — Conflict Style & De-escalation",
    name: "Conflict Initiation & Discussion Style",
    weight: 9,
    question_type: "mixed",
    is_hard_filter: false,
    objective_questions: [
      "Direct vs indirect communication preference (Very direct / Diplomatic / Hints).",
      "Timing preference for raising issues (Immediately / After cooling down / During scheduled talks)."
    ],
    subjective_questions: [
      "How did conflict look in the home you grew up in, and how did that affect how you fight?",
      "When you're angry with someone, what is your most honest, unfiltered reaction?"
    ]
  },
  {
    koota_id: 12,
    pillar: "PILLAR E — Conflict Style & De-escalation",
    name: "De-escalation & Repair Attempt Receptivity",
    weight: 10,
    question_type: "mixed",
    is_hard_filter: false,
    objective_questions: [
      "Ability to accept an apology during an active argument (Yes / Need cooling period / Takes days).",
      "Preferred repair mechanism (Humor / Touch / Verbal apology / Acts of service / Space)."
    ],
    subjective_questions: [
      "What is a repair attempt that actually works on you when you're furious?",
      "What is a de-escalation attempt that makes you angrier?"
    ]
  },
  {
    koota_id: 13,
    pillar: "PILLAR E — Conflict Style & De-escalation",
    name: "Anger Expression & Emotional Regulation",
    weight: 9,
    question_type: "mixed",
    is_hard_filter: false,
    objective_questions: [
      "Frequency of raised voice in arguments (Never / Occasionally / Normal part of passion).",
      "Stonewalling / silent treatment tendency (Never / Sometimes when overwhelmed / Frequent)."
    ],
    subjective_questions: [
      "What does losing your temper look like for you?",
      "How do you bring yourself back down when you feel flooded during an argument?"
    ]
  },
  {
    koota_id: 14,
    pillar: "PILLAR E — Conflict Style & De-escalation",
    name: "Solvable vs Perpetual Problem Navigation",
    weight: 8,
    question_type: "subjective_only",
    is_hard_filter: false,
    objective_questions: [],
    subjective_questions: [
      "What is a recurring disagreement you have had in a past relationship or with family that was never solved — how did you live with it?",
      "What is the difference for you between a compromise you can live with and one that breeds resentment?"
    ]
  },
  {
    koota_id: 15,
    pillar: "PILLAR E — Conflict Style & De-escalation",
    name: "Trust Baseline & Fidelity Boundaries",
    weight: 12,
    question_type: "mixed",
    is_hard_filter: false,
    objective_questions: [
      "Strictness of opposite-sex friendship boundaries after marriage (Completely open / Open with transparency / Minimal 1-on-1).",
      "Phone/account privacy expectation (Open access / Private but not secretive / Fully private)."
    ],
    subjective_questions: [
      "What does 'emotional infidelity' mean to you, specifically?",
      "What would permanently break your trust in a marriage, beyond physical infidelity?"
    ]
  },
  {
    koota_id: 16,
    pillar: "PILLAR E — Conflict Style & De-escalation",
    name: "Permanence Commitment & Exit Dynamics",
    weight: 11,
    question_type: "mixed",
    is_hard_filter: false,
    objective_questions: [
      "View on divorce (Acceptable for irreconcilable differences / Absolute last resort / Not an option except abuse).",
      "Attitude toward couples therapy (Would go proactively / Willing if in crisis / Reluctant)."
    ],
    subjective_questions: [
      "Under what conditions, if any, do you believe a marriage should end?",
      "What does 'working on a marriage' mean to you when things are genuinely terrible for months?"
    ]
  },
  {
    koota_id: 17,
    pillar: "PILLAR F — In-Law Dynamics & Elder Care",
    name: "Living Arrangement Expectations",
    weight: 13,
    question_type: "mixed",
    is_hard_filter: true,
    objective_questions: [
      "Living arrangement preference: Joint family immediately / Nuclear same city / Nuclear independent city / Flexible.",
      "Long-term plan for aging parents: Live with us / Live nearby / Dedicated care facility / Open to negotiation."
    ],
    subjective_questions: [
      "What is your honest, unfiltered view of living with in-laws?",
      "How do you imagine daily life working if one partner's parents need full-time care?"
    ]
  },
  {
    koota_id: 18,
    pillar: "PILLAR F — In-Law Dynamics & Elder Care",
    name: "In-Law Boundary Setting & Deference",
    weight: 11,
    question_type: "mixed",
    is_hard_filter: false,
    objective_questions: [
      "Handling in-law unsolicited advice (Deference always / Polite nod then do what we want / Direct boundary setting).",
      "Frequency of parental visits/calls expectation (Daily / Weekly / Monthly / Occasional)."
    ],
    subjective_questions: [
      "If your parents and your partner have a direct conflict, what is your instinct on whose side you take publicly?",
      "What is a boundary with extended family that you would insist on protecting, no matter what?"
    ]
  },
  {
    koota_id: 19,
    pillar: "PILLAR F — In-Law Dynamics & Elder Care",
    name: "Financial Obligations to Extended Family",
    weight: 10,
    question_type: "mixed",
    is_hard_filter: false,
    objective_questions: [
      "Regular financial support to parents: Required fixed monthly / As needed in emergencies / Not expected.",
      "Consultation on financial gifts to siblings/family (Always consult / Inform after / Independent decision)."
    ],
    subjective_questions: [
      "How much of your income do you consider 'ours' versus having a responsibility to your birth family?",
      "What would you do if a family member asked for a large loan that your partner objected to?"
    ]
  },
  {
    koota_id: 20,
    pillar: "PILLAR F — In-Law Dynamics & Elder Care",
    name: "Caregiving Division for Aging Parents",
    weight: 10,
    question_type: "subjective_only",
    is_hard_filter: false,
    objective_questions: [],
    subjective_questions: [
      "Both partners have parents who may need care. How do you envision balancing both sides equitably?",
      "Are you willing to relocate for your partner's aging parents? Under what conditions?"
    ]
  },
  {
    koota_id: 21,
    pillar: "PILLAR G — Career Continuity & Gender Roles",
    name: "Domestic Labor & Chore Division",
    weight: 11,
    question_type: "mixed",
    is_hard_filter: false,
    objective_questions: [
      "Preferred chore split model: 50/50 split regardless of income / Split proportional to working hours / Traditional gender roles / Maximize domestic help.",
      "Cooking responsibility expectation (Shared / One primary / Domestic help / Takeout)."
    ],
    subjective_questions: [
      "What does fairness in daily household management look like to you in practice?",
      "How do you react when you feel you are doing noticeably more domestic work than your partner?"
    ]
  },
  {
    koota_id: 22,
    pillar: "PILLAR G — Career Continuity & Gender Roles",
    name: "Female Career Continuity Post-Children",
    weight: 13,
    question_type: "mixed",
    is_hard_filter: false,
    objective_questions: [
      "Post-child career expectation: Full-time return as soon as feasible / Part-time transition / Extended break / Primary homemaker / Flexible depending on career.",
      "Paternity leave expectation: Take maximum available / Minimal time off / Not planned."
    ],
    subjective_questions: [
      "How do you envision career compromises being made when a child is born?",
      "If both partners have demanding careers, how do you prevent one career from automatically taking precedence?"
    ]
  },
  {
    koota_id: 23,
    pillar: "PILLAR G — Career Continuity & Gender Roles",
    name: "Relocation & Career Priority",
    weight: 9,
    question_type: "mixed",
    is_hard_filter: false,
    objective_questions: [
      "Willingness to relocate for partner's career: Yes eagerly / Only for major advancement / Strongly prefer staying / Never.",
      "Priority career approach: Equal priority / Higher earner leads / Rotate based on opportunity."
    ],
    subjective_questions: [
      "Describe a scenario where you would expect your partner to relocate for your job.",
      "Describe a scenario where you would decline a career-making promotion because of your partner's life/family."
    ]
  },
  {
    koota_id: 24,
    pillar: "PILLAR G — Career Continuity & Gender Roles",
    name: "Gender Role Ideology & Traditionalism",
    weight: 10,
    question_type: "mixed",
    is_hard_filter: false,
    objective_questions: [
      "General gender role orientation: Modern egalitarian / Traditional with modern elements / Fully traditional.",
      "Religious/ritual expectations from wife/husband (Standard traditional expectations / Minimal / Fully opt-in)."
    ],
    subjective_questions: [
      "What is one traditional expectation of your gender in marriage that you fully embrace, and one you reject?",
      "How do you handle extended family who expect traditional gender roles that you may not agree with?"
    ]
  },
  {
    koota_id: 25,
    pillar: "PILLAR H — Financial Architecture & Money",
    name: "Financial Integration & Account Structure",
    weight: 11,
    question_type: "mixed",
    is_hard_filter: false,
    objective_questions: [
      "Account structure preference: Fully merged / Three-account model (mine, yours, ours) / Completely separate.",
      "Approach to debt (credit cards, personal loans): Zero tolerance / Strategic use only / Normal part of life."
    ],
    subjective_questions: [
      "How were finances handled in your childhood home, and what did that teach you about money in marriage?",
      "What does financial transparency between spouses look like to you in practice?"
    ]
  },
  {
    koota_id: 26,
    pillar: "PILLAR H — Financial Architecture & Money",
    name: "Spending Philosophy & Frugality vs Indulgence",
    weight: 8,
    question_type: "mixed",
    is_hard_filter: false,
    objective_questions: [
      "Self-described money personality: Aggressive saver / Balanced / Enjoys spending on experiences / Spender.",
      "Big purchase comfort (luxury travel, cars, high-end electronics): Valued life quality / Only if surplus exists / Wasteful."
    ],
    subjective_questions: [
      "What is something you spend money on that others might consider a waste, but matters deeply to you?",
      "When have you felt most anxious about money, and how did you handle it?"
    ]
  },
  {
    koota_id: 27,
    pillar: "PILLAR H — Financial Architecture & Money",
    name: "Investment Risk Tolerance & Wealth Creation",
    weight: 7,
    question_type: "mixed",
    is_hard_filter: false,
    objective_questions: [
      "Risk profile: Conservative (FDs/Gold/Real Estate) / Moderate (Mutual Funds/Index) / Aggressive (Equities/Startups/Crypto).",
      "Goal for wealth: Generational wealth / Comfortable retirement / Financial independence early (FIRE) / Experience-focused."
    ],
    subjective_questions: [
      "How would you react if your partner lost a significant amount of money in a high-risk investment?",
      "What does 'financial security' actually mean to you in numbers or lifestyle?"
    ]
  },
  {
    koota_id: 28,
    pillar: "PILLAR H — Financial Architecture & Money",
    name: "Wedding Scale & Expenditure Alignment",
    weight: 6,
    question_type: "mixed",
    is_hard_filter: false,
    objective_questions: [
      "Preferred wedding scale: Intimate/Court (under 100) / Moderate (100-300) / Large traditional (300-800) / Grand (800+).",
      "Wedding funding: Self-funded completely / Split with parents / Parents fund fully."
    ],
    subjective_questions: [
      "What is your honest preference for wedding expenditure versus investing that money for your future?",
      "How will you handle differences between what your parents want for the wedding and what you want?"
    ]
  },
  {
    koota_id: 29,
    pillar: "PILLAR J — Intimacy & Affection",
    name: "Physical Affection & Intimacy Expectations",
    weight: 8,
    question_type: "mixed",
    is_hard_filter: false,
    objective_questions: [
      "Importance of physical affection (hugs, hand-holding, touch) daily: Essential / Nice to have / Low importance.",
      "Comfort discussing sexual expectations before marriage: Very comfortable / Somewhat / Prefer waiting."
    ],
    subjective_questions: [
      "How do you communicate what you need physically or affectionately from a partner?",
      "What does a healthy intimate life in marriage look like after the honeymoon phase?"
    ]
  },
  {
    koota_id: 30,
    pillar: "PILLAR J — Intimacy & Affection",
    name: "Emotional vs Physical Intimacy Balance",
    weight: 7,
    question_type: "subjective_only",
    is_hard_filter: false,
    objective_questions: [],
    subjective_questions: [
      "For you, does emotional closeness lead to physical intimacy, or does physical intimacy create emotional closeness?",
      "How do you handle periods where physical or emotional intimacy drops due to stress or life transitions?"
    ]
  },
  {
    koota_id: 31,
    pillar: "PILLAR I — Parenting Philosophy & Family Size",
    name: "Desire for Children & Timeline",
    weight: 14,
    question_type: "mixed",
    is_hard_filter: true,
    objective_questions: [
      "Desire for children: Definitely want / Open/undecided / Do not want (DINK).",
      "Target timeline post-marriage: Within 1-2 years / 3-4 years / 5+ years / Flexible."
    ],
    subjective_questions: [
      "Why do you want (or not want) children? What is the real, personal reason?",
      "If you discover you cannot have biological children, what path would you want to pursue (IVF, adoption, child-free)?"
    ]
  },
  {
    koota_id: 32,
    pillar: "PILLAR I — Parenting Philosophy & Family Size",
    name: "Parenting Philosophy & Discipline",
    weight: 9,
    question_type: "mixed",
    is_hard_filter: false,
    objective_questions: [
      "Parenting style leaning: Authoritative (high warmth, high standards) / Permissive (high warmth, low rules) / Traditional disciplined.",
      "Attitude toward screen time and modern upbringing: Highly restricted / Balanced / Pragmatic."
    ],
    subjective_questions: [
      "What is one thing your parents did that you will definitely do differently with your own children?",
      "How do you handle disagreements about child-rearing in front of the child versus in private?"
    ]
  },
  {
    koota_id: 33,
    pillar: "PILLAR I — Parenting Philosophy & Family Size",
    name: "Education & Achievement Pressure on Children",
    weight: 8,
    question_type: "mixed",
    is_hard_filter: false,
    objective_questions: [
      "Education priority: Top-tier academic competitive / Holistic & arts / Child-led interests.",
      "Extracurricular pressure: High structured schedule / Moderate / Free play prioritized."
    ],
    subjective_questions: [
      "How will you react if your child is average academically and wants to pursue a non-traditional career?",
      "What is the most important value you want to instill in your children above all else?"
    ]
  },
  {
    koota_id: 34,
    pillar: "PILLAR K — Social Architecture & Community",
    name: "Social Battery & Couple vs Individual Socializing",
    weight: 6,
    question_type: "mixed",
    is_hard_filter: false,
    objective_questions: [
      "Social orientation: Introvert (recharges alone) / Extrovert (recharges with people) / Ambivert.",
      "Socializing style: Do everything as a couple / Independent friendships encouraged / Mostly family social circle."
    ],
    subjective_questions: [
      "How much alone time do you realistically need in a week to stay sane and happy?",
      "How do you feel when your partner wants to spend a weekend with their friends without you?"
    ]
  },
  {
    koota_id: 35,
    pillar: "PILLAR K — Social Architecture & Community",
    name: "Community & Cultural Anchoring",
    weight: 6,
    question_type: "mixed",
    is_hard_filter: false,
    objective_questions: [
      "Importance of community/caste/regional cultural events: Very important active participant / Cultural appreciation / Indifferent / Resist.",
      "Language spoken at home preference: Native mother tongue / Mix with English / English primarily."
    ],
    subjective_questions: [
      "What cultural or community tradition from your heritage is non-negotiable for you to carry forward?",
      "How do you feel about participating in cultural practices that are not meaningful to you personally?"
    ]
  },
  {
    koota_id: 36,
    pillar: "PILLAR L — Crisis Resilience & Life Transitions",
    name: "Health, Lifestyle & Habit Alignment",
    weight: 7,
    question_type: "mixed",
    is_hard_filter: false,
    objective_questions: [
      "Dietary lifestyle: Vegetarian / Non-vegetarian / Eggetarian / Vegan / Jain vegetarian.",
      "Alcohol/Smoking stance: Non-drinker / Social drinker / Regular / Smoker / Strict non-smoker."
    ],
    subjective_questions: [
      "How important is it to you that your partner shares your dietary and lifestyle habits in the home?",
      "How do you deal with personal health crises or major body/fitness changes in yourself or a partner?"
    ]
  },
  {
    koota_id: 37,
    pillar: "PILLAR L — Crisis Resilience & Life Transitions",
    name: "Spiritual & Religious Practice Intensity",
    weight: 9,
    question_type: "mixed",
    is_hard_filter: false,
    objective_questions: [
      "Religious practice frequency: Daily puja/prayers / Weekly / Festival/occasional / Agnostic/Atheist / Spiritual not religious.",
      "Expectation of partner's religious participation: Must participate fully / Respectful presence / Complete independence."
    ],
    subjective_questions: [
      "What role does faith, religion, or spirituality genuinely play in your daily life, beyond rituals?",
      "How will you navigate religious education and rituals for your children if you and your partner have different levels of faith?"
    ]
  },
  {
    koota_id: 38,
    pillar: "PILLAR M — Shared Meaning & Life Purpose",
    name: "Existential Purpose of Marriage",
    weight: 15,
    question_type: "subjective_only",
    is_hard_filter: false,
    objective_questions: [],
    subjective_questions: [
      "At its deepest level, why are you getting married? What is the fundamental purpose of marriage to you?",
      "When you look back on your life at age 80, what will have made your marriage a true success?"
    ]
  },
  {
    koota_id: 39,
    pillar: "PILLAR M — Shared Meaning & Life Purpose",
    name: "10-Year Life Vision & Legacy",
    weight: 11,
    question_type: "subjective_only",
    is_hard_filter: false,
    objective_questions: [],
    subjective_questions: [
      "Where do you see yourself living, working, and being in 10 years, in vivid detail?",
      "What kind of legacy do you want to create as a family unit?"
    ]
  },
  {
    koota_id: 40,
    pillar: "PILLAR M — Shared Meaning & Life Purpose",
    name: "Rituals of Connection & Family Traditions",
    weight: 8,
    question_type: "subjective_only",
    is_hard_filter: false,
    objective_questions: [],
    subjective_questions: [
      "What is a small, daily or weekly ritual of connection you want to build into your marriage from Day 1?",
      "How do you want your home to feel to anyone who walks through the front door?"
    ]
  },
  {
    koota_id: 41,
    pillar: "PILLAR M — Shared Meaning & Life Purpose",
    name: "Philosophical Alignment on Life & Morality",
    weight: 14,
    question_type: "subjective_only",
    is_hard_filter: false,
    objective_questions: [],
    subjective_questions: [
      "What is a core moral conviction you hold that you will not compromise on, even if it costs you relationships or opportunities?",
      "How do you make sense of suffering or unfairness when life goes terribly wrong?"
    ]
  },
  {
    koota_id: 42,
    pillar: "PILLAR N — Hard Demographics & Filters",
    name: "Hard Demographic & Cultural Gatekeepers",
    weight: 1,
    question_type: "filter",
    is_hard_filter: true,
    objective_questions: [
      "Age gap preference tolerance (Max acceptable age difference in years: 1 / 2 / 3 / 5 / Flexible).",
      "Religion and caste strictness (Strict same-community requirement / Open within religion / Completely open)."
    ],
    subjective_questions: []
  }
];
