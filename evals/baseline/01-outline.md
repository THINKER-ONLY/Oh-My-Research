# Baseline Output: Story-First Outline

Model: `gpt-5.6-terra`, reasoning `high`, no research-writing Skill.

## Raw Output

## Working title

Evidence Ledgers for More Grounded LLM-Assisted ML Paper Drafting: A Pilot Study

## Conference-paper outline

1. **Abstract**
   - Problem: LLM-assisted drafting can introduce claims without traceable support.
   - Method: evidence-ledger workflow linking each substantive claim to a source, result, or explicit uncertainty.
   - Pilot result: unsupported claims fell from 7 to 2 across 12 drafts.
   - Scope: preliminary within-pilot evidence; controlled replication remains necessary.

2. **Introduction**
   - Motivate unsupported claims as a practical reliability risk in ML writing.
   - Define the evidence-ledger workflow.
   - State pilot finding and research question.
   - Contributions:
     - A concrete, auditable drafting workflow for claim-evidence traceability.
     - A pilot evaluation suggesting fewer unsupported claims.
     - An error taxonomy and evaluation protocol for future controlled studies.

3. **Related Work**
   - LLMs for scientific writing and scholarly assistance.
   - Citation/attribution verification and hallucination mitigation.
   - Provenance, traceability, and structured human-in-the-loop workflows.

4. **Evidence-Ledger Workflow**
   - Ledger schema: claim, evidence pointer, evidence type, confidence/status, reviewer decision.
   - Drafting procedure: extract claims, attach evidence, flag unsupported claims, revise or qualify.
   - Roles of the LLM and human reviewer.
   - Design principles: provenance, uncertainty preservation, auditability.

5. **Pilot Study**
   - Dataset: 12 drafts.
   - Comparison: unsupported-claim counts before versus after workflow use.
   - Annotation protocol and operational definition of “unsupported claim.”
   - Results: 7 unsupported claims before; 2 after.
   - Qualitative examples of claims removed, qualified, or supported.

6. **Interpretation and Limitations**
   - The pilot is consistent with the workflow reducing unsupported claims.
   - No statistical test, model/version control, randomized control condition, or external replication.
   - Counts should not be interpreted as a causal or generalizable effect estimate.

7. **Future Evaluation**
   - Preregistered multi-model, multi-domain controlled study.
   - Fixed prompts/models and blinded claim annotation.
   - Report effect sizes, uncertainty intervals, and inter-annotator agreement.
   - Test writing quality, effort, coverage, and false reassurance alongside unsupported claims.

8. **Conclusion**
   - Evidence ledgers offer a practical mechanism for making LLM-assisted drafting more auditable.
   - Initial pilot evidence motivates, but does not settle, broader efficacy claims.

## Opening paragraph of the introduction

Large language models can accelerate ML paper drafting, but their fluency can also obscure whether a technical claim is actually supported by the underlying evidence. This creates a traceability problem: authors and reviewers must distinguish claims grounded in results or sources from claims that are plausible yet unverified. We study whether an evidence-ledger workflow—requiring substantive draft claims to be linked to supporting evidence or explicitly marked as uncertain—can reduce unsupported claims in LLM-assisted writing. In a 12-draft pilot, the number of unsupported claims identified in our drafts decreased from seven before the workflow to two after its use. Although this preliminary result does not establish causality or generalize across models and settings, it motivates evidence ledgers as a concrete, auditable intervention for improving the epistemic discipline of LLM-assisted scientific drafting.

## Observed Baseline Gaps

- No separate evidence ledger or unresolved-evidence list was delivered.
- “An error taxonomy and evaluation protocol” was promoted to a contribution even though neither was present in the notes.
- The outline correctly retained the supplied limitations; this is a positive control, not a failure.
