# Broader live-policy validation

The original ten-question development and ten-question held-out benchmarks met
all five targets. This is still a small POC sample. It does not establish that
90% of future staff questions can be automatically answered.

## Automated preparation completed

Eight additional analyst-authored scenarios cover early arrival, occupancy,
privacy, charge/media escalation, pending holds, accessibility details, animal
control and amenity availability. The same frozen retrieval/generation pipeline
produces draft answers, source excerpts and the three reference-free judge scores.
These are supplemental probes, not an independent hotel-staff benchmark.

See `outputs/supplemental_live_results.json`,
`outputs/supplemental_live_summary.json`, and **outputs/staff_review.csv**.
Every probe should retain MANUAL LOOKUP, a null contextual-recall score and a null
four-metric composite until an independent reference is available. A high score
on the other three dimensions must not silently promote it to AUTO ANSWER.

## Prerequisite: a human policy reviewer

Ask a hotel policy owner or experienced staff member to open `staff_review.csv`
in Excel. The reviewer must check current source policies and the relevant live
property profile, including conditions and exceptions. The system's generated
draft is not ground truth. No rows are marked approved by the automated workflow.

For each row, fill:

| Field | Required action |
| --- | --- |
| `review_status` | `approved` only after checking the policy; otherwise `needs_changes` or `rejected` |
| `reviewer` | Reviewer name or identifiable staff ID |
| `reviewed_date` | Date as YYYY-MM-DD |
| `expected_answer` | Independently verified answer, including necessary conditions and exclusions |
| `relevant_context` | Verified source passage(s) and document/section; separate multiple passages using `<>` |
| `unsupported_claims` | Any unsupported detail in the generated draft |
| `missing_conditions` | Missing fees, exceptions, approval requirements or property details |
| `notes` | Corrections or decisions, including whether manual escalation remains necessary |

Do not approve an unsupported question merely because the answer politely abstains.
Verify whether the appropriate outcome is a supported answer, clarification request,
or manual escalation. Keep the original question, draft, sources, case ID and
`index_snapshot_sha256` intact for traceability.

## Collect representative real staff questions

The eight prepared scenarios are only a starting point. Collect at least **30–50
additional de-identified staff questions** as a proposed POC review batch, spanning
properties, rate plans, fees, refunds, accessibility, conflicting information and
unknown requests. This sample size is a practical next step, not a statistical
guarantee of reliability. Do not include guest names, reservation IDs or payment
details. Keep this review batch out of retrieval tuning while assessing it.

Record whether each question was actually resolved without manual policy lookup,
whether the sources support every material claim, and why staff intervened. Report
coverage on the entire batch, including errors, abstentions and escalations. Do not
count a safe abstention as a confidently resolved guest query. A policy owner must
approve the acceptance decision; four LLM scores alone are insufficient sign-off.

## Optional: promote fully approved reference questions

After staff approval, on the complete local project:

```bash
python3 scripts/approve_reviewed_references.py --reviewed-csv outputs/staff_review.csv
```

This command rejects missing reviewer/date/answer/context, stale index snapshots,
and duplicate questions. It preserves the original catalog before adding any
staff-approved judge-only references. The human approval fields are provenance,
not cryptographic proof of review; run the command only after actual review.

An exact approved question can then receive all four live scores. Its verified
answer is supplied only to the judge, never to the generator or embedding index.
Promotion does not establish broader paraphrase coverage. New wordings without an
independent reference still route to manual lookup.

Rebuild/redeploy the backend after a catalog update. Notebook cell 138 regenerates
the baseline development catalog; rerunning it can replace the expanded catalog.
Preserve reviewed files and re-review if the index/policies change. Do not rerun the
benchmark notebook as part of a routine deployment-only rebuild.

## Completion evidence

Return the reviewed worksheet, real staff-question outcomes, and policy-owner
decision. Until then the report must say **supplemental automation checks complete;
human and representative live validation pending**, rather than claiming 100%
operational validation.
