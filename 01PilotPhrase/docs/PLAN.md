# 01PilotPhrase Plan

## Goal
Build two concrete outputs for the pilot study:
1. A full prompt matrix CSV generated from controlled framing factors and problem IDs.
2. An initial set of original, non-trivial Python coding problems suitable for objective evaluation.

## Scope and Constraints
- Focus on coding tasks only (Python).
- Avoid direct reuse of known benchmark items (MBPP/HumanEval style prompts).
- Keep prompts comparable enough to isolate framing effects.
- Keep tasks solvable in a reasonable runtime with deterministic tests.
- Pilot-friendly scale first, then expand.

## Deliverables
- `problems.csv`
- `prompt_matrix.csv`
- `generate_prompt_matrix.py`
- `evaluation_protocol.md`
- `progress_tracker.md`

## Work Plan

### Phase 1: Matrix Design
Objective: Define CSV schema and generation rules for the prompt matrix.

Steps:
1. Lock prompt dimensions and levels.
2. Define category IDs and naming convention.
3. Define matrix CSV fields and allowed values.
4. Define prompt templating rules for plain/JSON/XML output styles.
5. Implement generator script that expands all combinations for each problem ID.

Output:
- Prompt matrix schema and script-based generation pipeline.

### Phase 2: Problem Set Drafting
Objective: Build the first set of original, non-trivial Python tasks.

Steps:
1. Define `problems.csv` schema: ID, Problem, Eval.
2. Draft 30-50 candidate tasks across difficulty levels.
3. Remove tasks too similar to common benchmark archetypes.
4. Build or outline tests and store evaluator hints in `Eval`.
5. Validate that problem IDs are unique and stable for matrix generation.

Output:
- Initial `problems.csv` (30-50 items).

### Phase 3: Quality Gate + Pilot Readiness
Objective: Ensure both deliverables are usable for pilot runs.

Steps:
1. Run generator script and validate CSV output completeness.
2. Validate problem clarity and testability.
3. Run mini sanity pass on 5-10 generated prompts across formats.
4. Freeze v1 and record known risks.

Output:
- Pilot-ready `prompt_matrix.csv` + `problems.csv` + evaluation protocol.

## Prompt Category Matrix Design

### Dimensions
- Tone: neutral, polite, aggressive
- Pressure: none, moderate, high
- Role framing: no role, developer role
- Instruction structure: minimal, detailed
- Format: plain text prompt, JSON-formatted prompt, XML-formatted prompt

### Matrix CSV Fields
- ID
- Tone
- Pressure
- Role framing
- Instruction structure
- Format
- ProblemID (from `problems.csv`)
- Prompt (generated text)

### Source Problem CSV Fields
- ID
- Problem
- Eval

### ID Convention
`PM_<6-digit-sequence>`

Example:
`PM_000127`

## Python Problem Set Design

### Target Mix
- Total: 30-50 tasks (start with 30 if time is limited).
- Difficulty split:
  - Easy: 20%
  - Medium: 50%
  - Hard: 30%

### Skill Coverage Tags
- arrays/strings
- hash maps/sets
- sorting/search
- intervals
- stacks/queues
- recursion/backtracking
- dynamic programming
- graphs/trees
- simulation/state machines
- parsing/format handling

### Problem Quality Rules
- Require reasoning beyond straightforward template copy.
- Include edge cases designed to break naive solutions.
- Prefer constraints that force algorithmic choices.
- Ensure deterministic expected output.
- Keep problem statement concise and unambiguous.

### Originality Safeguards
- Rewrite problem narratives and input/output contracts from scratch.
- Combine concepts not commonly paired in public benchmark items.
- Add custom constraints and corner cases.
- Record "closest known pattern" to avoid accidental clones.

## Acceptance Criteria

### Matrix Acceptance
- `prompt_matrix.csv` generated successfully from `problems.csv`.
- All required matrix fields are present.
- Enumerated values match allowed sets for each framing dimension.
- `ProblemID` values map correctly to `problems.csv` IDs.
- Prompt text is produced for plain text, JSON, and XML formats.

### Problem Set Acceptance
- At least 30 original problems drafted in `problems.csv`.
- Each problem has tests or test outlines reflected in `Eval`.
- No direct benchmark copy detected by manual review.

## Risks and Mitigations
- Risk: Category explosion reduces interpretability.
  - Mitigation: Keep core matrix fixed; treat format as extension.
- Risk: Tasks are too easy or too benchmark-like.
  - Mitigation: Add adversarial edge cases and originality checks.
- Risk: Prompt length confounds results.
  - Mitigation: Use length guidance and length-matched variants.

## Weekly Execution Rhythm
- Monday: Add/refine categories and prompts.
- Tuesday: Draft tasks and tests.
- Wednesday: Internal validation and pruning.
- Thursday: Supervisor progress update.
- Friday: Consolidate and freeze the next revision.

## Immediate Next Actions
1. Create mock `problems.csv` with ID, Problem, Eval.
2. Implement `generate_prompt_matrix.py`.
3. Generate `prompt_matrix.csv` from `problems.csv`.
4. Review sample rows for plain text, JSON, and XML prompt formatting.
