"""
config.py
=========
Single source of truth for the Hybrid AI Router labeling pipeline.

Every keyword list, regex pattern, threshold, and per-intent default profile
lives here. No other module should hardcode a keyword or a magic number —
if you want to tune the router's behavior, this is the only file you should
need to touch.

Sections:
    1. INTENT_KEYWORDS       -> keyword/phrase signals per intent (50+ intents)
    2. INTENT_REGEX          -> optional regex overrides for intents with a
                                 distinctive syntactic shape (SQL, code, etc.)
    3. INTENT_DEFAULT_PROFILE-> per-intent baseline attributes (complexity,
                                 local_model_confidence, output length, etc.)
    4. COMPLEXITY_KEYWORDS   -> keyword groups used purely for complexity
                                 scoring (independent of intent classification)
    5. FEATURE_PATTERNS      -> regex used for binary feature extraction
    6. THRESHOLDS            -> cutoffs for tier classification & routing
    7. TOKEN_ESTIMATION      -> heuristics for estimating token counts
"""

# ─────────────────────────────────────────────────────────────────────────
# 1. INTENT KEYWORDS
# ─────────────────────────────────────────────────────────────────────────
# Each intent maps to a list of lowercase keywords/phrases. The intent
# classifier scores every intent by counting keyword hits in the query
# (+ context if provided) and picks the highest-scoring intent.
#
# NOTE: Order does not matter for scoring, but intents are grouped by
# domain here for readability and easier maintenance.

INTENT_KEYWORDS = {
    # ── Coding & Software Engineering ──────────────────────────────
    "coding":                  ["write a function", "write code", "implement", "create a program",
                                 "code snippet", "write a script", "programming"],
    "debugging":               ["debug", "fix this bug", "why is this error", "not working",
                                 "traceback", "exception", "stack trace", "fix the error"],
    "code_explanation":        ["explain this code", "what does this code do", "walk me through this function",
                                 "explain the algorithm", "how does this work"],
    "code_review":             ["review this code", "code review", "improve this code", "refactor",
                                 "clean up this code", "best practices for this code"],
    "unit_testing":            ["write a test", "unit test", "test case", "write tests for"],
    "sql":                     ["sql query", "select * from", "join", "database query", "write a query",
                                 "sql", "postgres", "mysql query"],
    "algorithm_design":        ["algorithm", "time complexity", "big o", "optimize this algorithm",
                                 "data structure"],
    "system_design":           ["system design", "design a system", "scalable architecture",
                                 "microservices", "design an api"],
    "api_development":         ["rest api", "api endpoint", "build an api", "api development",
                                 "graphql", "webhook"],

    # ── DevOps / Infra ──────────────────────────────────────────────
    "linux":                   ["linux command", "bash command", "terminal", "shell script",
                                 "ls -", "grep", "chmod", "systemctl", "disk usage", "disk space",
                                 "running processes", "kill the process", "check permissions",
                                 "compress", "log files", "install", "restart the service",
                                 "network status", "check disk", "free space", "cpu usage",
                                 "memory usage", "environment variable", "cron job", "symlink",
                                 "mount", "package manager", "apt-get", "yum install", "tar -", "gzip"],
    "devops":                  ["ci/cd", "pipeline", "deployment", "devops", "terraform", "ansible"],
    "docker":                  ["docker", "dockerfile", "container image", "docker-compose"],
    "kubernetes":              ["kubernetes", "k8s", "pod", "helm chart", "kubectl"],
    "cybersecurity":           ["vulnerability", "penetration test", "exploit", "cve", "security audit",
                                 "encryption", "firewall", "malware"],
    "network_configuration":   ["configure network", "dns", "subnet", "vpn setup", "port forwarding"],
    "database_design":         ["schema design", "database design", "normalize", "er diagram",
                                 "database schema"],

    # ── Data / ML ────────────────────────────────────────────────────
    "machine_learning":        ["train a model", "neural network", "machine learning", "gradient descent",
                                 "hyperparameter", "overfitting", "loss function"],
    "data_science":            ["data analysis", "pandas", "dataframe", "data science", "feature engineering"],
    "statistics":              ["standard deviation", "p-value", "hypothesis test", "regression",
                                 "confidence interval", "statistics"],
    "data_visualization":      ["plot this data", "make a chart", "visualize", "bar chart", "histogram"],

    # ── Language tasks ───────────────────────────────────────────────
    "translation":             ["translate", "in spanish", "in french", "into german", "translation of"],
    "summarization":           ["summarize", "tl;dr", "give me a summary", "condense this", "key points of"],
    "grammar_correction":      ["fix grammar", "correct this sentence", "grammar check", "proofread"],
    "rewriting":               ["rewrite this", "rephrase", "make this sound better", "improve this text"],
    "paraphrasing":            ["paraphrase", "say this differently", "reword this"],
    "text_simplification":     ["simplify this", "explain like i'm five", "eli5", "make this simpler"],

    # ── Reasoning ─────────────────────────────────────────────────────
    "logical_reasoning":       ["if all", "logically", "syllogism", "deduce", "logical puzzle",
                                 "prove that"],
    "common_sense_reasoning":  ["would it make sense", "common sense", "is it reasonable"],
    "mathematics":             ["solve for x", "calculate", "equation", "derivative", "integral",
                                 "math problem", "algebra"],

    # ── Planning / Ideation ────────────────────────────────────────────
    "planning":                ["plan my", "create a schedule", "step-by-step plan", "itinerary",
                                 "roadmap", "timeline"],
    "brainstorming":           ["brainstorm", "give me ideas", "list of ideas", "what are some ways"],

    # ── Classification / Extraction ──────────────────────────────────
    "classification":          ["classify this", "which category", "is this positive or negative",
                                 "categorize"],
    "information_extraction":  ["extract the", "pull out the", "find all mentions of", "list the entities"],
    "reading_comprehension":   ["based on the passage", "according to the text", "in the given context",
                                 "based on the following"],
    "table_analysis":          ["analyze this table", "in this table", "table shows", "spreadsheet"],
    "chart_interpretation":    ["interpret this chart", "what does this graph show", "chart shows"],
    "document_analysis":       ["analyze this document", "review this document", "summarize this report"],

    # ── QA / Search ────────────────────────────────────────────────────
    "question_answering":      ["what is", "who is", "when did", "where is", "why does", "how does"],
    "fact_lookup":             ["what year", "how many", "what is the capital of", "population of"],
    "search":                  ["search for", "find information about", "look up"],
    "web_research":            ["research this topic", "find recent articles", "latest news on"],
    "technical_documentation_qa": ["according to the docs", "in the documentation", "api reference says"],

    # ── Creative / Writing ──────────────────────────────────────────────
    "creative_writing":        ["write a story", "write a poem", "write a script", "creative writing",
                                 "write fiction"],
    "email_writing":           ["write an email", "draft an email", "email to my"],
    "report_writing":          ["write a report", "draft a report", "business report", "write an essay",
                                 "essay comparing", "essay about", "compare and contrast"],
    "resume_writing":          ["write my resume", "resume for", "cv for", "improve my resume"],
    "cover_letter_writing":    ["cover letter", "write a cover letter"],
    "presentation_writing":    ["make a presentation", "slide deck", "presentation about"],

    # ── Career / Learning ──────────────────────────────────────────────
    "interview_preparation":   ["interview questions", "prepare for an interview", "mock interview"],
    "tutoring":                ["explain this concept", "teach me", "help me understand", "tutor me", "explain"],

    # ── Domain-specific advice ────────────────────────────────────────
    "legal":                   ["is it legal", "legal advice", "contract clause", "lawsuit", "law regarding"],
    "finance":                 ["investment advice", "stock price", "budget plan", "financial advice",
                                 "interest rate"],
    "medical":                 ["symptoms of", "medical advice", "is it safe to", "side effects of"],
    "travel":                  ["travel itinerary", "best time to visit", "flights to", "travel plan"],
    "shopping":                ["where to buy", "best price for", "shopping for", "product for"],
    "recommendations":         ["recommend a", "suggest a", "what should i", "best options for"],
    "product_comparison":      ["compare", "vs", "which is better", "difference between"],

    # ── Conversational ────────────────────────────────────────────────
    "greeting":                ["hello", "hi there", "good morning", "hey", "hi"],
    "small_talk":              ["how are you", "what's up", "nice to meet you"],
    "opinion":                 ["what do you think", "your opinion on", "do you believe"],
    "roleplay":                ["pretend you are", "act as", "roleplay as", "you are now a"],
    "conversation":            ["let's talk about", "i want to discuss"],
}


# ─────────────────────────────────────────────────────────────────────────
# 2. INTENT REGEX OVERRIDES
# ─────────────────────────────────────────────────────────────────────────
# Intents with a distinctive syntactic shape get regex boosts on top of
# keyword scoring. These add extra score points when matched.

INTENT_REGEX = {
    "sql":            [r"\bselect\b.+\bfrom\b", r"\binsert\s+into\b", r"\bcreate\s+table\b"],
    "coding":         [r"```", r"\bdef\s+\w+\(", r"\bfunction\s+\w+\(", r"\bclass\s+\w+",
                        r"\bwrite\b.{0,25}\bfunction\b", r"\bimplement\b.{0,25}\b(function|algorithm|class|method)\b",
                        r"\bwrite\b.{0,15}\b(program|script)\b"],
    "mathematics":    [r"\d+\s*[\+\-\*/\^]\s*\d+", r"\bx\s*=\s*", r"\\frac", r"\bsolve\b",
                        r"(how many|how much)\b.{0,80}\?"],
    "linux":          [r"^\s*(ls|cd|grep|chmod|chown|ps|kill|df|du|systemctl)\b",
                        r"\bis\b.{0,10}\brunning\b", r"\bupdate\s+\w+$",
                        r"\bshow me files\b", r"\bfiles? in\b.{0,25}\b(directory|folder|desktop|tmp|var)\b",
                        r"\bkill\b.{0,10}\bprocess\b", r"\bcheck status of\b"],
    "docker":         [r"\bdocker\s+(run|build|ps|exec)\b", r"dockerfile"],
    "kubernetes":     [r"\bkubectl\s+\w+"],
    "planning":       [r"\bhelp me plan\b", r"\bplan a\b.{0,15}\btrip\b", r"\bplan for\b.{0,15}\bdays?\b"],
    "travel":         [r"\btrip to\b", r"\bdays? (in|to)\b.{0,20}(japan|paris|italy|europe|asia)"],
    "creative_writing": [r"\bwrite\b.{0,25}\b(story|poem|script|fiction|tale)\b"],
    "email_writing":    [r"\b(write|draft|compose)\b.{0,25}\b(email|e-mail)\b"],
    "report_writing":   [r"\bwrite\b.{0,20}\b(report|essay)\b"],
    "data_science":     [r"\banalyz\w*\b.{0,25}\bdata\b", r"\bidentify\b.{0,20}\btrends?\b"],
    "tutoring":         [r"\bexplain\b.{0,30}\b(simple terms|simply|eli5)\b"],
}


# ─────────────────────────────────────────────────────────────────────────
# 3. INTENT DEFAULT PROFILES
# ─────────────────────────────────────────────────────────────────────────
# Baseline attributes per intent. These are STARTING PRIORS — the complexity
# and confidence modules adjust them using actual per-query signals rather
# than returning these values unmodified for every row of the same intent.
#
# Fields:
#   base_complexity        : 0.0-1.0 prior complexity for this task type
#   base_local_confidence  : 0.0-1.0 prior confidence a local model can do it
#   typical_output_length  : "short" | "medium" | "long"
#   coding_required / math_required / creativity_required : bool priors

INTENT_DEFAULT_PROFILE = {
    "coding":                     {"base_complexity": 0.65, "base_local_confidence": 0.35, "typical_output_length": "medium", "coding_required": True,  "math_required": False, "creativity_required": False},
    "debugging":                  {"base_complexity": 0.70, "base_local_confidence": 0.30, "typical_output_length": "medium", "coding_required": True,  "math_required": False, "creativity_required": False},
    "code_explanation":           {"base_complexity": 0.50, "base_local_confidence": 0.50, "typical_output_length": "medium", "coding_required": True,  "math_required": False, "creativity_required": False},
    "code_review":                {"base_complexity": 0.65, "base_local_confidence": 0.30, "typical_output_length": "medium", "coding_required": True,  "math_required": False, "creativity_required": False},
    "unit_testing":               {"base_complexity": 0.55, "base_local_confidence": 0.45, "typical_output_length": "medium", "coding_required": True,  "math_required": False, "creativity_required": False},
    "sql":                        {"base_complexity": 0.40, "base_local_confidence": 0.60, "typical_output_length": "short",  "coding_required": True,  "math_required": False, "creativity_required": False},
    "algorithm_design":           {"base_complexity": 0.75, "base_local_confidence": 0.25, "typical_output_length": "medium", "coding_required": True,  "math_required": True,  "creativity_required": False},
    "system_design":              {"base_complexity": 0.85, "base_local_confidence": 0.15, "typical_output_length": "long",   "coding_required": True,  "math_required": False, "creativity_required": False},
    "api_development":            {"base_complexity": 0.70, "base_local_confidence": 0.25, "typical_output_length": "long",   "coding_required": True,  "math_required": False, "creativity_required": False},

    "linux":                      {"base_complexity": 0.25, "base_local_confidence": 0.80, "typical_output_length": "short",  "coding_required": True,  "math_required": False, "creativity_required": False},
    "devops":                     {"base_complexity": 0.60, "base_local_confidence": 0.35, "typical_output_length": "medium", "coding_required": True,  "math_required": False, "creativity_required": False},
    "docker":                     {"base_complexity": 0.45, "base_local_confidence": 0.55, "typical_output_length": "medium", "coding_required": True,  "math_required": False, "creativity_required": False},
    "kubernetes":                 {"base_complexity": 0.65, "base_local_confidence": 0.30, "typical_output_length": "medium", "coding_required": True,  "math_required": False, "creativity_required": False},
    "cybersecurity":              {"base_complexity": 0.65, "base_local_confidence": 0.30, "typical_output_length": "medium", "coding_required": False, "math_required": False, "creativity_required": False},
    "network_configuration":      {"base_complexity": 0.55, "base_local_confidence": 0.40, "typical_output_length": "medium", "coding_required": True,  "math_required": False, "creativity_required": False},
    "database_design":            {"base_complexity": 0.60, "base_local_confidence": 0.35, "typical_output_length": "medium", "coding_required": True,  "math_required": False, "creativity_required": False},

    "machine_learning":           {"base_complexity": 0.75, "base_local_confidence": 0.20, "typical_output_length": "long",   "coding_required": True,  "math_required": True,  "creativity_required": False},
    "data_science":               {"base_complexity": 0.65, "base_local_confidence": 0.30, "typical_output_length": "medium", "coding_required": True,  "math_required": True,  "creativity_required": False},
    "statistics":                 {"base_complexity": 0.55, "base_local_confidence": 0.40, "typical_output_length": "medium", "coding_required": False, "math_required": True,  "creativity_required": False},
    "data_visualization":         {"base_complexity": 0.45, "base_local_confidence": 0.45, "typical_output_length": "medium", "coding_required": True,  "math_required": False, "creativity_required": False},

    "translation":                {"base_complexity": 0.35, "base_local_confidence": 0.55, "typical_output_length": "medium", "coding_required": False, "math_required": False, "creativity_required": False},
    "summarization":              {"base_complexity": 0.45, "base_local_confidence": 0.45, "typical_output_length": "medium", "coding_required": False, "math_required": False, "creativity_required": False},
    "grammar_correction":         {"base_complexity": 0.15, "base_local_confidence": 0.80, "typical_output_length": "short",  "coding_required": False, "math_required": False, "creativity_required": False},
    "rewriting":                  {"base_complexity": 0.30, "base_local_confidence": 0.60, "typical_output_length": "medium", "coding_required": False, "math_required": False, "creativity_required": True},
    "paraphrasing":               {"base_complexity": 0.20, "base_local_confidence": 0.70, "typical_output_length": "short",  "coding_required": False, "math_required": False, "creativity_required": True},
    "text_simplification":        {"base_complexity": 0.25, "base_local_confidence": 0.70, "typical_output_length": "medium", "coding_required": False, "math_required": False, "creativity_required": False},

    "logical_reasoning":          {"base_complexity": 0.65, "base_local_confidence": 0.30, "typical_output_length": "medium", "coding_required": False, "math_required": False, "creativity_required": False},
    "common_sense_reasoning":     {"base_complexity": 0.40, "base_local_confidence": 0.55, "typical_output_length": "short",  "coding_required": False, "math_required": False, "creativity_required": False},
    "mathematics":                {"base_complexity": 0.55, "base_local_confidence": 0.45, "typical_output_length": "medium", "coding_required": False, "math_required": True,  "creativity_required": False},

    "planning":                   {"base_complexity": 0.55, "base_local_confidence": 0.35, "typical_output_length": "medium", "coding_required": False, "math_required": False, "creativity_required": False},
    "brainstorming":              {"base_complexity": 0.45, "base_local_confidence": 0.40, "typical_output_length": "medium", "coding_required": False, "math_required": False, "creativity_required": True},

    "classification":             {"base_complexity": 0.15, "base_local_confidence": 0.85, "typical_output_length": "short",  "coding_required": False, "math_required": False, "creativity_required": False},
    "information_extraction":     {"base_complexity": 0.25, "base_local_confidence": 0.75, "typical_output_length": "short",  "coding_required": False, "math_required": False, "creativity_required": False},
    "reading_comprehension":      {"base_complexity": 0.30, "base_local_confidence": 0.70, "typical_output_length": "short",  "coding_required": False, "math_required": False, "creativity_required": False},
    "table_analysis":             {"base_complexity": 0.45, "base_local_confidence": 0.45, "typical_output_length": "medium", "coding_required": False, "math_required": True,  "creativity_required": False},
    "chart_interpretation":       {"base_complexity": 0.45, "base_local_confidence": 0.40, "typical_output_length": "medium", "coding_required": False, "math_required": False, "creativity_required": False},
    "document_analysis":          {"base_complexity": 0.55, "base_local_confidence": 0.35, "typical_output_length": "medium", "coding_required": False, "math_required": False, "creativity_required": False},

    "question_answering":         {"base_complexity": 0.25, "base_local_confidence": 0.65, "typical_output_length": "short",  "coding_required": False, "math_required": False, "creativity_required": False},
    "fact_lookup":                {"base_complexity": 0.15, "base_local_confidence": 0.80, "typical_output_length": "short",  "coding_required": False, "math_required": False, "creativity_required": False},
    "search":                     {"base_complexity": 0.30, "base_local_confidence": 0.40, "typical_output_length": "short",  "coding_required": False, "math_required": False, "creativity_required": False},
    "web_research":               {"base_complexity": 0.50, "base_local_confidence": 0.20, "typical_output_length": "long",   "coding_required": False, "math_required": False, "creativity_required": False},
    "technical_documentation_qa": {"base_complexity": 0.35, "base_local_confidence": 0.55, "typical_output_length": "medium", "coding_required": False, "math_required": False, "creativity_required": False},

    "creative_writing":           {"base_complexity": 0.60, "base_local_confidence": 0.25, "typical_output_length": "long",   "coding_required": False, "math_required": False, "creativity_required": True},
    "email_writing":              {"base_complexity": 0.30, "base_local_confidence": 0.55, "typical_output_length": "medium", "coding_required": False, "math_required": False, "creativity_required": True},
    "report_writing":             {"base_complexity": 0.55, "base_local_confidence": 0.30, "typical_output_length": "long",   "coding_required": False, "math_required": False, "creativity_required": True},
    "resume_writing":             {"base_complexity": 0.40, "base_local_confidence": 0.40, "typical_output_length": "medium", "coding_required": False, "math_required": False, "creativity_required": True},
    "cover_letter_writing":       {"base_complexity": 0.40, "base_local_confidence": 0.40, "typical_output_length": "medium", "coding_required": False, "math_required": False, "creativity_required": True},
    "presentation_writing":       {"base_complexity": 0.50, "base_local_confidence": 0.30, "typical_output_length": "long",   "coding_required": False, "math_required": False, "creativity_required": True},

    "interview_preparation":      {"base_complexity": 0.40, "base_local_confidence": 0.40, "typical_output_length": "medium", "coding_required": False, "math_required": False, "creativity_required": False},
    "tutoring":                   {"base_complexity": 0.50, "base_local_confidence": 0.35, "typical_output_length": "medium", "coding_required": False, "math_required": False, "creativity_required": False},

    "legal":                      {"base_complexity": 0.60, "base_local_confidence": 0.25, "typical_output_length": "medium", "coding_required": False, "math_required": False, "creativity_required": False},
    "finance":                    {"base_complexity": 0.55, "base_local_confidence": 0.30, "typical_output_length": "medium", "coding_required": False, "math_required": True,  "creativity_required": False},
    "medical":                    {"base_complexity": 0.60, "base_local_confidence": 0.20, "typical_output_length": "medium", "coding_required": False, "math_required": False, "creativity_required": False},
    "travel":                     {"base_complexity": 0.40, "base_local_confidence": 0.40, "typical_output_length": "medium", "coding_required": False, "math_required": False, "creativity_required": False},
    "shopping":                   {"base_complexity": 0.25, "base_local_confidence": 0.55, "typical_output_length": "short",  "coding_required": False, "math_required": False, "creativity_required": False},
    "recommendations":            {"base_complexity": 0.35, "base_local_confidence": 0.45, "typical_output_length": "medium", "coding_required": False, "math_required": False, "creativity_required": False},
    "product_comparison":         {"base_complexity": 0.40, "base_local_confidence": 0.40, "typical_output_length": "medium", "coding_required": False, "math_required": False, "creativity_required": False},

    "greeting":                   {"base_complexity": 0.05, "base_local_confidence": 0.95, "typical_output_length": "short",  "coding_required": False, "math_required": False, "creativity_required": False},
    "small_talk":                 {"base_complexity": 0.10, "base_local_confidence": 0.90, "typical_output_length": "short",  "coding_required": False, "math_required": False, "creativity_required": False},
    "opinion":                    {"base_complexity": 0.35, "base_local_confidence": 0.45, "typical_output_length": "medium", "coding_required": False, "math_required": False, "creativity_required": False},
    "roleplay":                   {"base_complexity": 0.45, "base_local_confidence": 0.35, "typical_output_length": "medium", "coding_required": False, "math_required": False, "creativity_required": True},
    "conversation":               {"base_complexity": 0.20, "base_local_confidence": 0.65, "typical_output_length": "short",  "coding_required": False, "math_required": False, "creativity_required": False},

    # fallback for anything unclassified
    "general":                    {"base_complexity": 0.35, "base_local_confidence": 0.60, "typical_output_length": "medium", "coding_required": False, "math_required": False, "creativity_required": False},
}


# ─────────────────────────────────────────────────────────────────────────
# 4. COMPLEXITY KEYWORDS
# ─────────────────────────────────────────────────────────────────────────
# Independent of intent classification — these keyword groups feed directly
# into the complexity scorer as weighted signals.

COMPLEXITY_KEYWORDS = {
    "reasoning_keywords": [
        "why", "explain why", "reason", "because", "therefore", "prove",
        "justify", "analyze", "evaluate", "compare and contrast", "infer",
    ],
    "coding_keywords": [
        "function", "class", "variable", "loop", "algorithm", "compile",
        "syntax", "code", "script", "debug", "api", "database",
    ],
    "math_keywords": [
        "calculate", "equation", "solve", "derivative", "integral", "sum",
        "average", "percentage", "probability", "matrix", "vector",
    ],
    "planning_keywords": [
        "step by step", "plan", "schedule", "roadmap", "timeline", "strategy",
        "sequence of steps", "phases",
    ],
    "multi_step_keywords": [
        "then", "after that", "next", "finally", "first", "second", "third",
        "and then", "once done", "followed by",
    ],
    "vague_keywords": [
        "something", "somehow", "whatever", "fix this", "make it better",
        "improve", "optimize", "help me with this",
    ],
    # Soft risk signal: raises complexity/lowers local confidence but does
    # NOT by itself trigger the hard CLOUD override (see
    # router_labeler.DESTRUCTIVE_OVERRIDE_KEYWORDS for the hard-override list,
    # reserved for unambiguously severe operations like "rm -rf" or "mkfs").
    "risk_keywords": [
        "delete", "remove", "wipe", "kill", "force", "drop", "permanently",
        "recursively", "overwrite", "destroy", "erase",
    ],
    # Narrative math word problems (e.g. GSM8K-style) rarely use explicit
    # math keywords like "calculate" or "solve" — they're phrased as a
    # story ("Natalia sold clips to 48 friends..."). These cue phrases,
    # combined with multiple numbers and a question mark, catch that
    # pattern (see feature_extractor.requires_math).
    "math_word_problem_cues": [
        "how many", "how much", "altogether", "in total", "left over",
        "as many as", "twice as many", "half as many", "each", "per",
        "more than", "less than", "combined",
    ],
}


# ─────────────────────────────────────────────────────────────────────────
# 5. FEATURE PATTERNS (for binary feature extraction)
# ─────────────────────────────────────────────────────────────────────────

FEATURE_PATTERNS = {
    "code_block":  r"```[\s\S]*?```|`[^`\n]+`",
    "url":         r"https?://\S+|www\.\S+",
    "table":       r"\|.+\|.+\|",
    "list":        r"(?:^|\n)\s*(?:[-*\u2022]|\d+[.)])\s+\S+",
    "number":      r"\b\d+(\.\d+)?\b",
    "date":        r"\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}-\d{2}-\d{2}|"
                   r"(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+\d{1,2},?\s+\d{2,4})\b",
    "file_ref":    r"\b[\w\-]+\.(txt|csv|json|pdf|docx|xlsx|py|js|html|png|jpg|log|yaml|yml|sql|md)\b",
    "constraint":  r"\b(must|should|at least|no more than|in less than|within \d+|exactly \d+|"
                   r"do not|don't|avoid|ensure that|make sure)\b",
    "example_ref": r"\b(for example|e\.g\.|for instance|such as|like this)\b",
    "question":    r"\?",
}


# ─────────────────────────────────────────────────────────────────────────
# 6. THRESHOLDS
# ─────────────────────────────────────────────────────────────────────────

THRESHOLDS = {
    # complexity_score -> expected_tier
    "tier_simple_max":  0.35,   # score < this -> "simple"
    "tier_medium_max":  0.65,   # score < this -> "medium", else "complex"

    # route decision: blended "cloud_pressure" score (see router_labeler.predict_route)
    # NOTE: 0.45 was the original guess, but empirical testing against 98 real
    # WizardLM-evol-instruct queries (deliberately engineered to be complex)
    # showed the median cloud_pressure for even that "hard" dataset is only
    # ~0.35 — meaning a 0.45 cutoff routed 75% of genuinely complex queries to
    # LOCAL. 0.35 is calibrated to route roughly half of that hard-instruction
    # sample to CLOUD; tune further once you've measured your own merged
    # dataset's cloud_pressure distribution the same way.
    "route_cloud_pressure_cutoff": 0.35,

    # length-based signals (word counts)
    "long_prompt_words":  60,
    "long_output_words":  150,
}


# ─────────────────────────────────────────────────────────────────────────
# 7. TOKEN ESTIMATION
# ─────────────────────────────────────────────────────────────────────────
# Simple, dependency-free heuristic: ~4 characters per token for English text.
# This is intentionally approximate — swap in a real tokenizer if precision
# matters more than portability for your hackathon build.

TOKEN_ESTIMATION = {
    "chars_per_token": 4.0,
    "output_length_token_map": {
        "short":  40,
        "medium": 150,
        "long":   350,
    },
}