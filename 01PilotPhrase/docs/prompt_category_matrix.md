# Prompt Category Matrix (Pilot v1)

## Usage
- Target total categories: 15-20
- Prompts per category: 3-5
- Keep wording changes controlled so framing variables are isolated.

## Columns
- Category ID
- Tone
- Pressure
- Role
- Structure
- Format
- Intended Effect
- Prompt 1
- Prompt 2
- Prompt 3
- Prompt 4 (optional)
- Prompt 5 (optional)
- Notes

## Category Table

| Category ID | Tone | Pressure | Role | Structure | Format | Intended Effect | Prompt 1 | Prompt 2 | Prompt 3 | Prompt 4 | Prompt 5 | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| C01_Neutral_None_NoRole_Minimal | neutral | none | no role | minimal | plain | baseline anchor |  |  |  |  |  |  |
| C02_Neutral_Moderate_NoRole_Minimal | neutral | moderate | no role | minimal | plain | pressure-only effect |  |  |  |  |  |  |
| C03_Neutral_High_NoRole_Minimal | neutral | high | no role | minimal | plain | high-pressure effect |  |  |  |  |  |  |
| C04_Polite_None_NoRole_Explicit | polite | none | no role | explicit | plain | tone + structure effect |  |  |  |  |  |  |
| C05_Polite_Moderate_WithRole_Explicit | polite | moderate | assigned role | explicit | plain | role + polite interaction |  |  |  |  |  |  |
| C06_Polite_High_WithRole_Explicit | polite | high | assigned role | explicit | plain | high-pressure polite interaction |  |  |  |  |  |  |
| C07_Aggressive_None_NoRole_Minimal | aggressive | none | no role | minimal | plain | tone-only aggressive effect |  |  |  |  |  |  |
| C08_Aggressive_Moderate_WithRole_Explicit | aggressive | moderate | assigned role | explicit | plain | role-anchored aggressive effect |  |  |  |  |  |  |
| C09_Aggressive_High_WithRole_Explicit | aggressive | high | assigned role | explicit | plain | maximal framing intensity |  |  |  |  |  |  |
| C10_Neutral_None_WithRole_Explicit | neutral | none | assigned role | explicit | plain | role + structure effect |  |  |  |  |  |  |
| C11_Neutral_Moderate_WithRole_Explicit | neutral | moderate | assigned role | explicit | plain | controlled role/pressure interaction |  |  |  |  |  |  |
| C12_Neutral_High_WithRole_Explicit | neutral | high | assigned role | explicit | plain | high-pressure role interaction |  |  |  |  |  |  |
| C13_Neutral_None_NoRole_Minimal_JSON | neutral | none | no role | minimal | JSON | format sensitivity (JSON) |  |  |  |  |  |  |
| C14_Neutral_None_NoRole_Minimal_XML | neutral | none | no role | minimal | XML | format sensitivity (XML) |  |  |  |  |  |  |
| C15_Aggressive_Moderate_NoRole_Minimal_JSON | aggressive | moderate | no role | minimal | JSON | tone x format effect |  |  |  |  |  |  |
| C16_Polite_Moderate_NoRole_Minimal_XML | polite | moderate | no role | minimal | XML | polite x format effect |  |  |  |  |  |  |

## Completion Checklist
- [ ] 15-20 categories finalized
- [ ] 3-5 prompts per category filled
- [ ] Redundancy/overlap reviewed
- [ ] Length normalization pass completed
- [ ] Pilot subset selected (first 50-100 prompts)
