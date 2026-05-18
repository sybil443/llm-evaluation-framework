# Failure Analysis Workflow

## Goal
Review failed cases systematically and turn them into actionable follow-up work.

## Why failure analysis matters
Overall metrics can show that a system underperforms, but they usually do not explain why. Failure analysis helps identify:
- repeated failure patterns
- likely causes
- which issues matter most
- which fixes should be prioritized

## Workflow
1. Identify failed or weak examples
2. Group failures by type
3. Review representative examples
4. Record observed behavior
5. Record expected behavior
6. Write suspected cause
7. Suggest next action or experiment

## Example failure categories
Possible categories include:
- formatting errors
- missing content
- wrong classification
- low-quality generation
- weak retrieval
- hallucination
- category-specific weakness

## Per-example review template
Each reviewed failure should capture:
- example ID
- input
- observed output
- expected output
- failure category
- suspected cause
- suggested fix

## Outputs
The workflow should produce:
- a categorized list of failures
- representative examples per category
- short notes on likely causes
- a prioritized set of next actions

## Design notes
- Failure categories should be simple enough to apply consistently
- Examples should be easy to trace back to the original dataset
- The workflow should favor actionability, not just description
- A small number of clear failure groups is better than an overcomplicated taxonomy

## Future extensions
- connect failures to slices
- add counts per failure type
- add severity ranking
- include links to example outputs or reports