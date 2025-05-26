# Configuration file for the Dual System & Critique Prompt Improver

# === MODEL CONFIGURATION ===
# You can change these to use different models for different tasks
MODEL_GENERATION = "claude-sonnet-4-20250514"       # For generating responses with the system prompt
MODEL_CRITIQUE = "claude-sonnet-4-20250514"         # For critiquing system prompts
MODEL_REFINEMENT = "claude-sonnet-4-20250514"       # For refining system prompts
MODEL_CRITIQUE_REFINEMENT = "claude-sonnet-4-20250514"  # For refining critique prompts

# === IMPROVEMENT PARAMETERS ===
TARGET_SCORE = 95                             # Target score for system prompt (1-100)
MAX_ITERATIONS = 15                           # Maximum number of improvement iterations
IMPROVE_CRITIQUE_EVERY = 3                    # Evaluate critique prompt every N iterations
CRITIQUE_IMPROVEMENT_THRESHOLD = 85           # Meta-score threshold for critique improvement

# === INPUT FILES ===
USER_INPUT_FILE = "user_input.txt"
INITIAL_SYSTEM_PROMPT_FILE = "initial_system_prompt.txt"
INITIAL_CRITIQUE_PROMPT_FILE = "critique_system_prompt.txt"

# === LOGGING CONFIGURATION ===
LOG_LEVEL = "INFO"                            # Options: DEBUG, INFO, WARNING, ERROR
DETAILED_LOGGING = True                       # Show detailed iteration logs

# === OUTPUT CONFIGURATION ===
SAVE_INTERMEDIATE_RESULTS = True              # Save results after each iteration
OUTPUT_PREFIX = "dual_improvement"            # Prefix for output files

# === ADVANCED OPTIONS ===
# Enable/disable specific improvement features
ENABLE_CRITIQUE_IMPROVEMENT = True            # Whether to improve critique prompts
ENABLE_SYSTEM_PROMPT_IMPROVEMENT = True       # Whether to improve system prompts
PARALLEL_EVALUATION = False                   # Future feature: parallel processing

# === META-EVALUATION CRITERIA WEIGHTS ===
# These control how the critique prompt itself is evaluated
META_EVALUATION_WEIGHTS = {
    "issue_identification": 25,    # How well it identifies real problems
    "scoring_calibration": 20,     # Appropriateness of scores given
    "actionability": 25,           # Concrete, actionable suggestions
    "comprehensiveness": 15,       # Coverage of all important aspects
    "consistency": 15              # Internal logic and consistency
}

# === PROMPTING STRATEGIES ===
# Different approaches for different model types
PROMPTING_STRATEGY = "detailed"  # Options: "detailed", "concise", "chain_of_thought"

# === SAFETY & CONSTRAINTS ===
MAX_PROMPT_LENGTH = 200000        # Maximum length for prompts (characters) - Claude can handle more
MIN_SCORE_IMPROVEMENT = 2         # Minimum score improvement to continue
EARLY_STOPPING_PATIENCE = 3       # Stop if no improvement for N iterations 