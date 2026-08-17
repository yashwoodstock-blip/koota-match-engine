export interface QuestionOption {
  label: string;
  value: string;
}

export const OBJECTIVE_OPTIONS: Record<string, QuestionOption[]> = {
  // Koota 1: Family structure & siblings
  "1_0": [
    { label: "Nuclear family in an urban metro", value: "nuclear_urban" },
    { label: "Joint family in an urban area", value: "joint_urban" },
    { label: "Semi-urban / Small town upbringing", value: "semi_urban" },
    { label: "Rural / Agricultural roots", value: "rural" },
  ],
  "1_1": [
    { label: "Only child", value: "only_child" },
    { label: "Eldest sibling", value: "eldest" },
    { label: "Middle sibling", value: "middle" },
    { label: "Youngest sibling", value: "youngest" },
  ],
  // Koota 2: Daily rhythms
  "2_0": [
    { label: "Morning person • Structured daily routine", value: "morning_structured" },
    { label: "Morning person • Spontaneous flow", value: "morning_spontaneous" },
    { label: "Night owl • Structured routine", value: "night_structured" },
    { label: "Night owl • Spontaneous & adaptable", value: "night_spontaneous" },
  ],
  "2_1": [
    { label: "Rest, quiet time, and reading at home", value: "rest_home" },
    { label: "Socializing with friends & hosting gatherings", value: "socializing" },
    { label: "Family visits, elder duties & community", value: "family_visits" },
    { label: "Outdoor activities, travel & fitness", value: "outdoor_travel" },
  ],
  // Koota 3: Stress & Coping
  "3_0": [
    { label: "Career & professional milestones", value: "career" },
    { label: "Family responsibilities & expectations", value: "family" },
    { label: "Financial planning & long-term stability", value: "financial" },
    { label: "Personal health & wellness", value: "health" },
  ],
  "3_1": [
    { label: "Very comfortable — I express vulnerability early", value: "very_comfortable" },
    { label: "Somewhat comfortable — once trust is proven", value: "somewhat" },
    { label: "I prefer to process independently before asking", value: "independent" },
  ],
  // Koota 5: Appreciation
  "5_0": [
    { label: "Daily verbal praise and affirmations", value: "daily" },
    { label: "Weekly / Situational affirmations", value: "weekly" },
    { label: "I express love more through quiet actions", value: "actions_focus" },
  ],
  "5_1": [
    { label: "Words of affirmation & sincere compliments", value: "words" },
    { label: "Acts of service & shared burden relief", value: "acts_of_service" },
    { label: "Undivided quality time and conversations", value: "quality_time" },
    { label: "Physical presence, warmth & thoughtful gestures", value: "touch_gifts" },
  ],
  // Koota 6: Mutual Respect & Income
  "6_0": [
    { label: "Completely comfortable with partner earning more", value: "very_comfortable" },
    { label: "Neutral — focus is on total household strength", value: "neutral" },
    { label: "Prefer rough financial parity between us", value: "prefer_parity" },
  ],
  "6_1": [
    { label: "Never disagree publicly — unified front always", value: "unified_public" },
    { label: "Calm private discussion, but polite in public", value: "context_dependent" },
  ],
  // Koota 7: Decision Making
  "7_0": [
    { label: "Consensus on everything major — both must agree", value: "consensus" },
    { label: "Clear domains — each leads their specialized area", value: "domain_lead" },
    { label: "High individual autonomy with mutual updates", value: "independent" },
  ],
  "7_1": [
    { label: "Above ₹10,000", value: "10k" },
    { label: "Above ₹25,000", value: "25k" },
    { label: "Above ₹50,000", value: "50k" },
    { label: "Above ₹1,00,000", value: "1L" },
  ],
  // Koota 8: Flexibility
  "8_0": [
    { label: "Gladly adapt habits if it helps my partner", value: "willing" },
    { label: "Open to gradual compromise with rationale", value: "compromise" },
    { label: "Deeply value preserving established habits", value: "prefer_stability" },
  ],
  "8_1": [
    { label: "Quickly — open to sound contrary evidence", value: "quickly" },
    { label: "Need time to reflect and process internally", value: "needs_time" },
    { label: "Deliberate and cautious before shifting positions", value: "cautious" },
  ],
  // Koota 9: Emotional Attunement
  "9_0": [
    { label: "Inquire gently right away with full presence", value: "inquire_immediately" },
    { label: "Offer space and comfort, then check in later", value: "give_space_first" },
    { label: "Wait for partner to open up at their own pace", value: "wait_for_them" },
  ],
  "9_1": [
    { label: "Daily evening emotional sync & check-in", value: "daily" },
    { label: "When either of us is going through something", value: "as_needed" },
    { label: "Organic flow without structured check-ins", value: "organic" },
  ],
  // Koota 11: Conflict Style
  "11_0": [
    { label: "Very direct and immediate — clear the air", value: "very_direct" },
    { label: "Diplomatic, gentle and tactful approach", value: "diplomatic" },
    { label: "Reflective and gradual — avoid immediate clash", value: "reflective" },
  ],
  "11_1": [
    { label: "Same day — never let resentment simmer overnight", value: "same_day" },
    { label: "After a 2-3 hour cooling off period", value: "cooling_period" },
    { label: "Next day during a calm, dedicated moment", value: "next_day" },
  ],
  // Koota 12: De-escalation
  "12_0": [
    { label: "Yes, I can accept a sincere apology immediately", value: "yes_immediate" },
    { label: "I need a brief quiet cooldown before reconnecting", value: "need_cooldown" },
    { label: "It takes me a while to reset emotional warmth", value: "takes_time" },
  ],
  "12_1": [
    { label: "A sincere verbal apology and ownership", value: "verbal_apology" },
    { label: "Physical touch, warmth and a hug", value: "warm_touch" },
    { label: "Gentle humor to break the tension", value: "humor" },
    { label: "Quiet acts of kindness or bringing food/tea", value: "acts_of_service" },
  ],
  // Koota 15: Trust & Boundaries
  "15_0": [
    { label: "Completely open with healthy transparency", value: "open_transparent" },
    { label: "Group hangouts preferred over 1-on-1 dinners", value: "group_preferred" },
    { label: "Strict traditional boundaries after marriage", value: "strict_boundaries" },
  ],
  "15_1": [
    { label: "Open access — nothing to hide between spouses", value: "open_access" },
    { label: "Private personal devices, but zero secrecy", value: "private_not_secretive" },
    { label: "Complete individual privacy and independence", value: "full_privacy" },
  ],
  // Koota 16: Permanence & Therapy
  "16_0": [
    { label: "Lifelong commitment — work through all solvable hurdles", value: "high_permanence" },
    { label: "Deep commitment, with healthy exit for abuse or betrayal", value: "principled_exit" },
    { label: "Partnership based on mutual happiness and growth", value: "pragmatic" },
  ],
  "16_1": [
    { label: "Proactively open to pre-marital / couples counseling", value: "proactive" },
    { label: "Willing if we ever encounter serious crisis", value: "crisis_willing" },
    { label: "Prefer solving issues privately between us two", value: "private_only" },
  ],
  // Koota 17: Living Arrangement (HARD FILTER)
  "17_0": [
    { label: "Nuclear home in the same city as family", value: "nuclear_same_city" },
    { label: "Joint family with parents under one roof", value: "joint_family" },
    { label: "Independent nuclear setup anywhere globally", value: "nuclear_independent" },
    { label: "Flexible based on career and life stages", value: "flexible" },
  ],
  "17_1": [
    { label: "Parents live with us in their senior years", value: "live_with_us" },
    { label: "Parents live in close neighboring apartment", value: "live_nearby" },
    { label: "Dedicated elder care community / home nursing", value: "care_facility" },
    { label: "Open to collaborative solution with siblings", value: "open_negotiation" },
  ],
  // Koota 18: In-law boundaries
  "18_0": [
    { label: "High deference to elder advice and wisdom", value: "high_deference" },
    { label: "Polite listening, then independent couple decision", value: "polite_independent" },
    { label: "Clear, firm boundaries set from the start", value: "firm_boundaries" },
  ],
  "18_1": [
    { label: "Daily phone calls and frequent weekend visits", value: "daily_calls" },
    { label: "Weekly calls and monthly family dinners", value: "weekly_calls" },
    { label: "Bi-weekly / Monthly structured visits", value: "monthly" },
  ],
  // Koota 19: Extended Family Finances
  "19_0": [
    { label: "Fixed monthly financial contribution to parents", value: "fixed_monthly" },
    { label: "Support available for medical / major emergencies", value: "emergency_only" },
    { label: "Parents are financially independent", value: "independent" },
  ],
  "19_1": [
    { label: "Always consult spouse before family gifts/loans", value: "always_consult" },
    { label: "Inform spouse if amount is above standard threshold", value: "inform_above_threshold" },
    { label: "Independent decision from personal discretionary funds", value: "independent" },
  ],
  // Koota 21: Domestic labor
  "21_0": [
    { label: "50/50 egalitarian split regardless of income", value: "equal_split" },
    { label: "Proportional split based on working hours", value: "proportional_hours" },
    { label: "Maximize domestic help (cook, maid) to minimize chores", value: "maximize_help" },
    { label: "Traditional role-based division", value: "traditional" },
  ],
  "21_1": [
    { label: "Shared cooking as a fun collaborative activity", value: "shared_cooking" },
    { label: "One partner primary cook with appreciation", value: "one_primary" },
    { label: "Dedicated cook / meal service for daily nutrition", value: "cook_service" },
  ],
  // Koota 22: Female Career Continuity
  "22_0": [
    { label: "Full-time career return as soon as feasible", value: "full_time_return" },
    { label: "Part-time or flexible consulting transition", value: "part_time_transition" },
    { label: "Extended break (1-3 years) for early childhood", value: "extended_break" },
    { label: "Flexible based on whose career has highest momentum", value: "flexible_momentum" },
  ],
  "22_1": [
    { label: "Take maximum paternity/partner leave available", value: "max_paternity" },
    { label: "Standard 2-4 weeks off then flexible support", value: "standard_leave" },
  ],
  // Koota 23: Relocation Priority
  "23_0": [
    { label: "Eager to relocate anywhere for partner's growth", value: "eager_relocate" },
    { label: "Willing only for transformative promotions", value: "transformative_only" },
    { label: "Strongly prefer staying in current city", value: "prefer_current_city" },
  ],
  "23_1": [
    { label: "Both careers carry equal weight and veto power", value: "equal_priority" },
    { label: "Higher earner's career leads location decisions", value: "higher_earner_leads" },
    { label: "Rotate opportunities every few years", value: "rotate_opportunities" },
  ],
  // Koota 24: Traditionalism
  "24_0": [
    { label: "Fully progressive and egalitarian lifestyle", value: "egalitarian" },
    { label: "Modern lifestyle with cherished cultural traditions", value: "modern_cultural" },
    { label: "Traditional values and time-tested customs", value: "traditional" },
  ],
  "24_1": [
    { label: "Active participation in standard festive rituals", value: "active_festive" },
    { label: "Minimal / Essential festive presence", value: "minimal" },
    { label: "Fully opt-in personal spiritual choices", value: "opt_in" },
  ],
  // Koota 25: Financial Structure
  "25_0": [
    { label: "Three-account model (Mine, Yours, Joint Household)", value: "three_accounts" },
    { label: "Fully merged pool — all income into one pot", value: "fully_merged" },
    { label: "Completely separate accounts with split bills", value: "separate_accounts" },
  ],
  "25_1": [
    { label: "Zero high-interest debt • High financial discipline", value: "zero_tolerance" },
    { label: "Strategic debt only (home loan / tax efficiency)", value: "strategic_debt" },
    { label: "Comfortable using EMIs for lifestyle assets", value: "lifestyle_emi" },
  ],
  // Koota 26: Money Personality
  "26_0": [
    { label: "Aggressive saver & investor (50%+ savings rate)", value: "aggressive_saver" },
    { label: "Balanced — save well, enjoy life responsibly", value: "balanced" },
    { label: "Experience-focused — travel and memories first", value: "experience_focused" },
  ],
  "26_1": [
    { label: "Invest in high quality, luxury experiences and travel", value: "luxury_valued" },
    { label: "Deliberate purchases only when surplus exists", value: "surplus_only" },
    { label: "Frugal and mindful — avoid unnecessary luxury", value: "frugal_mindful" },
  ],
  // Koota 27: Investment Risk
  "27_0": [
    { label: "Balanced Growth (Index Funds, Mutual Funds, Equity)", value: "moderate_growth" },
    { label: "Aggressive / High Risk (Direct Equities, Startups)", value: "aggressive_equity" },
    { label: "Conservative (Fixed Deposits, Gold, Real Estate)", value: "conservative" },
  ],
  "27_1": [
    { label: "Generational wealth and family security", value: "generational_wealth" },
    { label: "Early Financial Independence (FIRE)", value: "fire" },
    { label: "Comfortable retirement and freedom of time", value: "comfortable_retirement" },
  ],
  // Koota 28: Wedding Scale
  "28_0": [
    { label: "Intimate / Court / Destination (< 100 close guests)", value: "intimate" },
    { label: "Moderate elegant wedding (100 - 300 guests)", value: "moderate" },
    { label: "Large traditional celebration (300 - 800 guests)", value: "large_traditional" },
    { label: "Grand celebration (800+ guests)", value: "grand" },
  ],
  "28_1": [
    { label: "Self-funded completely by couple", value: "self_funded" },
    { label: "Shared 50/50 between couple and parents", value: "shared_parents" },
    { label: "Funded primarily by parents", value: "parents_funded" },
  ],
  // Koota 29: Physical Affection
  "29_0": [
    { label: "Essential — daily hugs, warmth and physical touch", value: "essential" },
    { label: "Nice to have — warm but not constant", value: "nice_to_have" },
    { label: "Low importance — I express love differently", value: "low_importance" },
  ],
  "29_1": [
    { label: "Very comfortable discussing before marriage", value: "very_comfortable" },
    { label: "Somewhat comfortable once rapport is deep", value: "somewhat" },
    { label: "Prefer letting it unfold naturally post-wedding", value: "post_wedding" },
  ],
  // Koota 31: Children & Family Size (HARD FILTER)
  "31_0": [
    { label: "Definitely want children", value: "want_children" },
    { label: "Open / Undecided — want to discuss with partner", value: "open_undecided" },
    { label: "Do not want children (DINK lifestyle)", value: "dink" },
  ],
  "31_1": [
    { label: "Within 1 - 2 years of marriage", value: "1_2_years" },
    { label: "In 3 - 4 years (enjoy couple time first)", value: "3_4_years" },
    { label: "In 5+ years or flexible", value: "5_plus_years" },
  ],
  // Koota 32: Parenting Philosophy
  "32_0": [
    { label: "Authoritative (High warmth, clear standards & empathy)", value: "authoritative" },
    { label: "Gentle / Permissive (High warmth, child autonomy)", value: "permissive" },
    { label: "Structured & disciplined traditional approach", value: "structured_traditional" },
  ],
  "32_1": [
    { label: "Strict limits on screens and social media", value: "strict_limits" },
    { label: "Balanced and educational screen usage", value: "balanced" },
    { label: "Pragmatic modern digital literacy", value: "pragmatic" },
  ],
  // Koota 33: Education Pressure
  "33_0": [
    { label: "Holistic development, creativity & arts", value: "holistic" },
    { label: "Top-tier academic excellence & competitive spirit", value: "academic_excellence" },
    { label: "Child-led curiosity and non-traditional vocations", value: "child_led" },
  ],
  "33_1": [
    { label: "Prioritize unstructured free play and joy", value: "free_play" },
    { label: "Moderate structured sports and music lessons", value: "moderate_structured" },
  ],
  // Koota 34: Social Battery
  "34_0": [
    { label: "Introvert — recharges in quiet solitude", value: "introvert" },
    { label: "Extrovert — energizes through people and events", value: "extrovert" },
    { label: "Ambivert — balance of social and solo time", value: "ambivert" },
  ],
  "34_1": [
    { label: "Encourage independent friends & solo trips", value: "independent_friends" },
    { label: "Prefer doing most social things as a couple", value: "couple_focused" },
  ],
  // Koota 35: Community & Language
  "35_0": [
    { label: "Deeply connected to cultural heritage and festivals", value: "active_heritage" },
    { label: "Warm appreciation without excessive obligation", value: "warm_appreciation" },
    { label: "Cosmopolitan / Indifferent to community rituals", value: "cosmopolitan" },
  ],
  "35_1": [
    { label: "Mother tongue spoken frequently at home", value: "native_language" },
    { label: "Mix of English and mother tongue", value: "bilingual_mix" },
    { label: "English primarily", value: "english_primary" },
  ],
  // Koota 36: Diet & Habits
  "36_0": [
    { label: "Vegetarian", value: "vegetarian" },
    { label: "Eggetarian", value: "eggetarian" },
    { label: "Non-Vegetarian", value: "non_vegetarian" },
    { label: "Jain Vegetarian", value: "jain_vegetarian" },
    { label: "Vegan", value: "vegan" },
  ],
  "36_1": [
    { label: "Non-drinker & Non-smoker", value: "teetotaler" },
    { label: "Social drinker • Non-smoker", value: "social_drinker" },
    { label: "Regular drinker or smoker", value: "regular" },
  ],
  // Koota 37: Spirituality
  "37_0": [
    { label: "Daily puja / prayer and spiritual practice", value: "daily_practice" },
    { label: "Weekly / Festive prayer and temple visits", value: "festive_occasional" },
    { label: "Spiritual but not ritualistic", value: "spiritual_not_religious" },
    { label: "Agnostic / Atheist / Rationalist", value: "agnostic_atheist" },
  ],
  "37_1": [
    { label: "Respectful presence is plenty — no pressure", value: "respectful_presence" },
    { label: "Must actively participate in family rituals", value: "must_participate" },
    { label: "Complete spiritual independence", value: "complete_independence" },
  ],
  // Koota 42: Gatekeepers (HARD FILTER)
  "42_0": [
    { label: "Max 1 - 2 years age difference", value: "2_years" },
    { label: "Max 3 - 5 years age difference", value: "5_years" },
    { label: "Age difference is flexible", value: "flexible" },
  ],
  "42_1": [
    { label: "Strict same-religion requirement", value: "same_religion_strict" },
    { label: "Open to inter-community within broad religion", value: "inter_community" },
    { label: "Completely open to all backgrounds", value: "fully_open" },
  ],
};
