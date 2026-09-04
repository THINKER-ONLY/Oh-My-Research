# Forward Output: Story-First Outline

Skill: research-writing

## Raw Output

### Proposed title

**Traceable Claims in LLM-Assisted Paper Writing: An Evidence-Ledger Method and a 12-Draft Pilot**

### Eight-section outline

1. **Introduction**
   - Establish the central problem: fluent LLM-assisted prose can contain claims that are not linked to supporting sources or results.
   - Present the paper's insight: make evidence traceability part of drafting through a claim-level ledger, rather than treating verification only as a final review step.
   - State two bounded contributions: the evidence-ledger method and a preliminary 12-draft observation in which the recorded unsupported-claim count fell from 7 to 2.
   - Make clear at first mention that the pilot does not establish causality or generalizability.

2. **Related Work and Positioning**
   - Organize verified literature around LLM-assisted scholarly writing, factual or citation reliability, and provenance or claim-traceability systems.
   - Position the ledger as a workflow mechanism that connects each manuscript claim to a source or result.
   - Add only citations that have been checked against the specific nearby claim; the supplied notes provide no sources for this section.

3. **Problem Formulation and Design Requirements**
   - Define the unit being tracked: a manuscript claim, its supporting source or result, and whether that support is sufficient.
   - Specify the operational meaning of “unsupported claim” before reporting the pilot result.
   - Derive the method's requirements: visible evidence links, explicit unresolved gaps, preserved qualifiers, and a verification point before a claim enters the manuscript as fact.

4. **The Evidence-Ledger Method**
   - Describe the ledger structure and identify which fields were actually used; at minimum, report the claim, evidence pointer, and support status.
   - Explain where the ledger enters the drafting workflow: claim creation, evidence linking, review of unresolved entries, and manuscript revision.
   - Include a compact worked example using a non-result claim, while avoiding any implication that unreported fields or automation were part of the pilot.

5. **Pilot Study Design**
   - Report the 12-draft scope and the use of a single model version.
   - Explain how the 7 and 2 counts were obtained: comparison conditions or sequence, counting unit, draft selection, prompts, topics, model identifier, and adjudication procedure. Mark any unavailable detail as a reproducibility gap.
   - State that no significance test and no controlled replication were conducted.

6. **Pilot Results**
   - Report the descriptive observation exactly: across the 12-draft pilot, the recorded number of unsupported claims fell from 7 to 2.
   - Avoid a percentage reduction, significance language, or an attribution of the change to the ledger unless the missing denominator and study design support it.
   - Use a small table or figure only after clarifying what each count represents.

7. **Discussion, Limitations, and Threats to Validity**
   - Interpret the pilot narrowly: the observation suggests that claim-level traceability merits controlled evaluation.
   - Discuss the supplied limitations together with the conclusion they constrain: one model version, no significance test, and no controlled replication.
   - Address additional validity questions exposed by the study description, including the definition and adjudication of unsupported claims, without implying that controls were performed.

8. **Conclusion and Evaluation Agenda**
   - Restate the supported contribution: an evidence-ledger approach for linking claims to sources or results, accompanied by a preliminary 12-draft observation.
   - Conclude that the pilot motivates, but does not replace, a controlled evaluation.
   - Specify the next test: a controlled replication across multiple model versions with a predefined annotation protocol and an appropriate statistical analysis.

### Opening paragraph of the introduction

LLM-assisted paper drafting poses a basic integrity problem: fluent prose can make a claim appear settled even when it is not linked to a supporting source or result. We propose an evidence ledger that keeps this link explicit for each claim throughout drafting. In an initial pilot spanning 12 drafts, the recorded number of unsupported claims fell from 7 to 2. This observation is preliminary: the pilot used one model version, included no significance test, and has not been replicated under controlled conditions. We therefore present the result as motivation for rigorous evaluation, not as evidence that the ledger caused the change or will generalize beyond the pilot.

*Evidence boundary: The notes do not specify what the 7 and 2 counts aggregate, how drafts were compared, or how unsupported claims were adjudicated. Those details should be supplied before submission; until then, the raw-count wording above is the strongest defensible formulation.*
