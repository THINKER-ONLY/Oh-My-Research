# Core Algorithms

## 1. Claim admissibility

For claim \(c\), evidence record \(e\), and evidence-status function \(S(c,e)\), define an admissibility predicate:

\[
admit(c,e) =
\begin{cases}
true, & S(c,e) \in \{supported, qualified\} \land strength(c) \preceq strength(e) \\
false, & S(c,e) \in \{gap, pending\text{-}verification\}
\end{cases}
\]

When `admit` is false, the workflow narrows the claim, attributes it to a verified source, labels it as interpretation/proposal, or emits an explicit gap. It never fills the record with a plausible citation or result.

## 2. Revision invariant

Represent conclusion-relevant meaning as:

\[
A(x) = (p,s,pol,cmp,causal,n,u,l)
\]

where \(p\) is proposition, \(s\) scope, \(pol\) polarity, \(cmp\) comparison, \(causal\) causal force, \(n\) numbers/units, \(u\) uncertainty, and \(l\) conclusion-changing limitations.

A faithful revision \(x'\) must satisfy:

\[
A(x') = A(x)
\]

unless a source-backed correction is required and disclosed. Surface syntax is unconstrained.

## 3. Compression objective

For word budget \(b\), minimize length subject to frozen semantic atoms:

\[
x^* = \arg\min_{x'} |x'|
\quad \text{s.t.} \quad
|x'| \leq b \land A_f(x') = A_f(x)
\]

where \(A_f\) contains causal force, scope, numbers, comparison, uncertainty, and material limitations. If no feasible \(x'\) exists, return the shortest faithful alternative and expose the budget conflict.

## 4. Corpus provenance invariant

For every candidate URL \(u\), the manifest must contain one retrieval record:

\[
candidate(u) \Rightarrow \exists! r(u)
\]

For every successful record:

\[
success(r) \Rightarrow exists(path_r) \land SHA256(path_r)=hash_r
\]

Restricted-source policy is evaluated before network retrieval, and PDF candidates must begin with the PDF magic signature before atomic placement.

## Pseudocode

```text
PROCEDURE WRITE_WITH_EVIDENCE(task, materials):
    brief <- FRAME(task, materials)
    ledger <- BUILD_LEDGER(brief.intended_claims, materials)
    for claim in ledger:
        if not ADMISSIBLE(claim):
            claim <- NARROW_ATTRIBUTE_OR_MARK_GAP(claim)
    story <- ORDER_AS_PROBLEM_GAP_INSIGHT_CONTRIBUTION(ledger)
    draft <- DRAFT_SECTIONWISE(story, ledger)
    revised <- REVISE_STRUCTURE_THEN_SENTENCES(draft)
    if MEANING_ATOMS(revised) != MEANING_ATOMS(draft):
        revised <- RESTORE_OR_DISCLOSE_DIFFERENCES(revised, draft)
    audit <- AUDIT_CLAIMS_CITATIONS_NUMBERS_LIMITS(revised, ledger)
    return DELIVER(revised, ledger, audit)

PROCEDURE COMPRESS(text, budget):
    frozen <- FREEZE_MATERIAL_ATOMS(text)
    candidate <- CUT_REPETITION_THEN_LOW_VALUE_CONTEXT(text, budget)
    differences <- COMPARE(frozen, MATERIAL_ATOMS(candidate))
    if differences is empty:
        return candidate
    return SHORTEST_FAITHFUL_ALTERNATIVE(text, differences)

PROCEDURE ARCHIVE_CORPUS(pdfs, prior_manifest, budgets):
    links <- EXTRACT_ANNOTATIONS_AND_VISIBLE_URLS_WITH_PAGES(pdfs)
    candidates, blocked <- NORMALIZE_CLASSIFY_AND_FILTER(links)
    for candidate in candidates:
        if LICENSE_BOUNDARY_DENIES(candidate):
            RECORD_LICENSE_RESTRICTED(candidate)
        else if VERIFIED_PRIOR_SUCCESS_EXISTS(candidate, prior_manifest):
            REUSE_PRIOR_RECORD(candidate)
        else:
            result <- STREAM_RETRY_VALIDATE_HASH(candidate, budgets)
            RECORD(result)
    WRITE_JSON_AND_CSV_MANIFESTS(links, candidates, blocked, results)
```

## Step-by-step binding

1. `research-writing/SKILL.md` owns admissibility, workflow order, and completion checks.
2. `references/evidence-and-integrity.md` defines evidence, citation, causal, and numerical audits.
3. `references/revision-and-style.md` defines meaning atoms and compression order.
4. `scripts/corpus.py` implements extraction, normalization, filtering, downloading, hashing, resumption, manifests, and verification.
5. `evals/comparison.md` applies the fixed rubric to preserved raw outputs.

## Complexity

- Ledger construction is \(O(C + E)\) for \(C\) claim records and \(E\) indexed evidence items, excluding external retrieval.
- Semantic comparison is \(O(A)\) for a fixed-size set of meaning atoms; natural-language extraction of those atoms remains a judgment step outside the stub.
- PDF inventory is \(O(P + L)\), where \(P\) is extracted page text volume and \(L\) is the number of discovered links.
- Download hashing is \(O(B)\) time for \(B\) transferred bytes and uses bounded streaming memory.
- Fixed-rubric evaluation is \(O(KD)\) for \(K\) cases and \(D\) rubric dimensions.
