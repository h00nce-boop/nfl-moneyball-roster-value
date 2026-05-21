# Methodology Notes

## Project Goal

This project uses public NFL data to evaluate roster value through a Moneyball-style lens: which teams and players generate the most production relative to contract cost?

## V1: Baseline Surplus Value

The original model compares production rank to cost rank.

For players:

`player_surplus_gap = cost_rank_position - production_rank_position`

A positive gap means the player produced better than his cost rank. A negative gap means the player was expensive relative to his production rank.

## V2: Confidence Workflow

V2 adds confidence and data-quality flags.

The goal is to avoid over-interpreting players with missing contract data or very small samples.

Important fields:

- has_contract_match
- has_missing_contract
- contract_confidence
- meets_sample_threshold
- sample_confidence
- overall_confidence

The diagnostic file preserves flagged and excluded players for auditability.

## V3: Contract Context

V3 adds draft-capital and estimated contract-stage context.

This helps separate general cheapness from structurally underpriced production, especially rookie-contract and pre-extension players.

Important fields:

- draft_capital_bucket
- years_since_drafted
- estimated_contract_stage
- is_likely_rookie_contract
- surplus_context

## Current Limitations

- Public contract data may be incomplete.
- Draft matching depends on player IDs in public datasets.
- Contract stage is estimated, not a full cap-accounting model.
- Offensive skill-position production is easier to measure than offensive line or defensive value.
- The model does not yet include injuries, snap counts, scheme, or opponent strength.