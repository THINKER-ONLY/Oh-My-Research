# Concepts

## Claim-Evidence Ledger

- **Notation**: \(L = \{(c_i, e_i, s_i, q_i)\}\)
- **Definition**: A structured mapping from each substantive claim \(c_i\) to evidence pointer \(e_i\), support status \(s_i\), and limiting qualifiers \(q_i\).
- **Boundary conditions**: Applies to factual, quantitative, comparative, attribution-dependent, and conclusion-bearing claims; a faithful copyedit may keep the mapping internal when no support change occurs.
- **Related concepts**: Evidence Status, Claim-Strength Order, Writing Workflow Gate

## Evidence Status

- **Notation**: \(s \in \{supported, qualified, gap, pending\text{-}verification, not\text{-}applicable\}\)
- **Definition**: The explicit state describing whether and how a claim is supported at the time of writing.
- **Boundary conditions**: Status reflects available artifacts, not linguistic plausibility; `pending-verification` is not interchangeable with `supported`.
- **Related concepts**: Claim-Evidence Ledger, Citation Identity, Evidence Boundary

## Claim-Strength Order

- **Notation**: \(c_a \preceq_e c_b\)
- **Definition**: A partial order in which claim \(c_a\) is no stronger than claim \(c_b\) with respect to evidence type, causal force, scope, certainty, and generality.
- **Boundary conditions**: The order is task- and design-sensitive; descriptive association cannot be promoted to causal effect without additional design support.
- **Related concepts**: Evidence Status, Meaning Atoms, Compression Safety Gate

## Meaning Atoms

- **Notation**: \(A(x) = (p, scope, polarity, comparison, causal, numbers, uncertainty, limits)\)
- **Definition**: The conclusion-relevant semantic fields that must be compared before and after a substantive revision.
- **Boundary conditions**: Stylistic changes may alter surface form but must preserve these atoms unless a disclosed evidence correction is required.
- **Related concepts**: Claim-Strength Order, Compression Safety Gate, Revision Audit

## Compression Safety Gate

- **Notation**: \(safe(x,x') \iff A_f(x)=A_f(x') \land |x'|\leq b\)
- **Definition**: A constrained shortening operation that freezes causal force, scope, quantities, comparison, and conclusion-changing limitations before minimizing length under budget \(b\).
- **Boundary conditions**: If no sentence can satisfy both the word budget and frozen atoms, the gate returns the shortest faithful alternative instead of deleting a material caveat.
- **Related concepts**: Meaning Atoms, Claim-Strength Order, Revision Audit

## Writing Workflow Gate

- **Notation**: \(W = F \rightarrow L \rightarrow S \rightarrow D \rightarrow R \rightarrow A \rightarrow V\)
- **Definition**: The ordered Frame, Ledger, Story, Draft, Revise, Audit, Deliver sequence, with smaller task-specific subsets allowed when they protect the claim.
- **Boundary conditions**: Full ceremony is unnecessary for a faithful copyedit, but ledger and audit gates become mandatory when creating or strengthening substantive claims.
- **Related concepts**: Claim-Evidence Ledger, Progressive Disclosure, Completion Check

## Progressive Disclosure

- **Notation**: \(R(t) \subseteq R_{all}\)
- **Definition**: Loading only the reference module needed for current task type \(t\), while keeping non-negotiable evidence and integrity rules in the core Skill.
- **Boundary conditions**: It may reduce context use but must not hide rules whose omission could cause integrity failure.
- **Related concepts**: Writing Workflow Gate, Completion Check

## Corpus Provenance Record

- **Notation**: \(P(u)=(source, page, kind, status, path, hash, error)\)
- **Definition**: A record binding a normalized URL \(u\) to its source PDF/page, link kind, retrieval outcome, local path, checksum, and failure reason.
- **Boundary conditions**: A successful retrieval proves byte availability and integrity at a point in time; it does not prove source quality or redistribution rights.
- **Related concepts**: License Boundary, Completion Check, Evidence Boundary

## License Boundary

- **Notation**: \(allow(action, source) \in \{true,false,unknown\}\)
- **Definition**: A policy gate separating local research use, metadata indexing, and open redistribution for each source.
- **Boundary conditions**: “Downloadable” does not imply “redistributable”; unknown permission defaults to metadata/link retention rather than bundling the binary or protected text.
- **Related concepts**: Corpus Provenance Record, Evidence Boundary
