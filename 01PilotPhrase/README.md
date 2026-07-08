# 01PilotPhrase: LLM Framing & Reasoning Pilot Study

This project investigates the impact of various framing factors—such as tone, pressure, and role-playing—on the performance of Large Language Models (LLMs) in Python coding tasks. It includes a pipeline for generating complex prompt matrices, a set of original coding problems (including Vietnamese school math problems), and evaluation scripts.

## Project Structure

### Core Scripts
- **`generate_prompt_matrix.py`**: The primary engine for expanding framing dimensions (Tone, Pressure, Role, Structure, Format) into a full `prompt_matrix.csv`. It combines these factors with problem descriptions from `data/problems.csv`.
- **`generate_dataset.py`**: An automated generator that parses Vietnamese math problems from Markdown, uses an LLM to generate English translations and canonical Python solutions, and saves them in a verified JSON format.
- **`generate_prompt_templates.py`**: Creates high-quality structured prompt templates with placeholders. It defines the "Narrative Tone of Voice" and "Persona" mappings used for detailed instructions.
- **`evaluate_mbpp.py`**: An evaluation runner that takes tasks (in MBPP format), queries an LLM, extracts Python code, and executes it against test assertions. It supports resuming, dry runs, and custom API endpoints.
- **`verify_all.py`**: A utility script to validate the integrity and correctness of generated datasets and solutions.
- **`align_problems.py`**: Helps in mapping and aligning problem IDs across different versions or formats of the problem sets.
- **`parse_and_convert.py`**: Utility for converting between different data formats (e.g., Markdown to JSON/CSV).

### Directories
- **`data/`**: Contains the source and generated CSV files.
  - `problems.csv`: The base set of coding tasks.
  - `prompt_matrix*.csv`: Various versions of the expanded prompt matrix used for experiments.
- **`docs/`**: Project documentation and research planning.
  - `PLAN.md`: Strategic roadmap and deliverable definitions.
  - `progress_tracker.md`: Weekly status and milestone checklist.
  - `evaluation_protocol.md`: Detailed rules for how models are tested and scored.
- **`problems/`**: Source problem sets in structured formats.
  - `VNSchoolMathProblems.*.json`: Versions of the Vietnamese math problem dataset.
  - `VNSchoolMathProblems2026/`: Scripts and raw markdown for fetching new exam problems.
- **`checkpoints/`**: Stores results from evaluation runs (`.jsonl` files). Organized by date and model name.
- **`logs/`**: contains execution logs and detailed failure reports.
  - `generation_failures/`: Specific traces for tasks where LLM generation or verification failed.
- **`refs_problems/`**: Reference datasets used for comparison or as baselines (e.g., MBPP).

## Workflow
1. **Define Problems**: Draft problems in `data/problems.csv` or `problems/`.
2. **Generate Matrix**: Run `python3 generate_prompt_matrix.py` to create the experimental prompts.
3. **Run Evaluation**: Use `python3 evaluate_mbpp.py` pointing to the desired dataset and model.
4. **Analyze Results**: Review the outputs in `checkpoints/` and logs in `logs/`.

## Setup
The project uses a `.env` file for API configuration (API_BASE, API_KEY, MODEL). See `.env.example` for the required fields.
