# Causal Contract Refinement for Tropical Memory

## Thesis

The strongest mathematically defensible next step is not the raw claim that the bare tropical frontier `W[0..k]` recovers minimal adjustment sets. The stronger and more important result is sharper:

> `L2` is canonical for the **bare threshold contract**, but causal identification is a **strictly richer contract**. Therefore bare `L2` cannot, in general, recover minimal adjustment-set identity. Any successful causal theorem must pass through a witness-refined quotient.

This note turns that sentence into a concrete theorem package and a revised experimental program.

## Source Basis

This note relies on the following local artifacts:

- `/Users/jackg/dreams/papers/paper_i_tropical_algebra.pdf`
- `/Users/jackg/dreams/papers/paper_03_validity_mirage_compression.pdf`
- `/Users/jackg/Downloads/research_findings_conversation_synthesis.md`
- `/Users/jackg/Downloads/miragekit_selective_memory_proof_and_how_we_got_here.md`

From those sources we treat the following as already established background:

- Raw `L2 = (W[0..k], d_total)` with tropical composition
- The capping quotient `L2 -> L2'`
- The exact two-sided bare quotient `M_k = (d_hat, m)`
- The exact one-sided quotient `R_k`
- The quotient ladder `raw L2 -> L2' -> M_k -> R_k`

The new work in this note is the causal refinement:

1. a no-go theorem for bare-`L2` recovery of minimal adjustment sets
2. a permutation-invariance theorem explaining why predecessor identities are invisible to the bare frontier
3. an exact witness-refined quotient statement that turns the repair into mathematics
4. a revised causal program in which colored witnesses, not bare feasibility alone, become the correct target

## 1. Preliminaries

Let `k >= 1` be the prefix requirement. A raw tropical summary is

`L2 = (W[0..k], d_total)`

with composition

`W_(A⊗B)[j] = max(W_A[j], W_B[max(0, j - d_A)])`.

The bare feasibility predicate is

`feasible(W, d_total) = 1` iff `W[k] > -inf`.

The synthesis note already identifies the exact bare quotients:

- `L2' = (W[0..k], min(d_total, k))`
- `M_k = (d_hat, m)` where `m = max { j <= k : W[j] > -inf }`
- `R_k = {accept} union {need = 0, 1, ..., k}`

The key point is that these objects are exact for the **bare threshold language**: they answer questions of the form "is there enough predecessor capacity for a feasible pivot?" They do not yet answer questions of the form "which named confounder made the effect identifiable?"

## 2. The Quotient Ladder We Can Already Trust

The synthesis note already gives the correct structural spine:

`raw L2 -> L2' -> M_k -> R_k`

Interpretation:

- `raw L2` remembers the whole frontier plus uncapped predecessor count
- `L2'` forgets predecessor surplus above `k`
- `M_k` forgets all numeric detail except capped predecessor capacity `d_hat` and the live frontier endpoint `m`
- `R_k` forgets even the two-sided context and keeps only suffix residual demand

This matters because it tells us something very strong:

> Canonicality is not absolute. It is always canonical **for a contract**.

For the bare threshold contract, `M_k` and `R_k` are exact. Once the semantic promise changes, the quotient must change too.

## 3. Main New Result: No Bare Decoder for Minimal Adjustment Sets

### Theorem 1. Bare `L2` cannot universally recover minimal adjustment sets

Fix any decoding rule

`D : bare-L2-state -> candidate adjustment set`.

There is no such rule that is correct for every identifiable DAG linearization, even in the smallest nontrivial causal class.

### Proof

Take `k = 1` and compare the following two DAGs:

1. Confounded graph `G_conf`

`C -> T`, `C -> Y`, `T -> Y`

Its unique minimal adjustment set is `{C}`.

2. Clean graph `G_clean`

`U -> T`, `T -> Y`

Its unique minimal adjustment set is the empty set.

Now linearize both graphs using the same temporal profile and the same focal weights:

- first event: one non-focal predecessor
- second event: treatment `T` as the dominant focal pivot with weight `100`
- third event: outcome `Y` as a later focal event with weight `50`

So the event sequences are:

- `L_conf = [C, T, Y]`
- `L_clean = [U, T, Y]`

At the level of bare tropical summaries, the first event in each sequence contributes the same non-focal context, and the focal events contribute the same focal contexts. The composition law sees only:

- how many non-focal events occurred before each focal event
- what the focal weights are

It does **not** see whether the predecessor was a confounder (`C -> Y`) or merely a parent of treatment (`U -> T`).

Therefore

`L2(L_conf) = L2(L_clean)`.

But the causal answers differ:

- `Adj(G_conf, T, Y) = {{C}}`
- `Adj(G_clean, T, Y) = {empty}`

So no decoder from the bare `L2` state can be correct on both.

QED.

### Corollary 1. The original exact-bijection target is too strong for bare `L2`

An experiment asking for

`bare-L2 frontier == minimal adjustment set identity`

cannot hold as a universal law, because the mapping fails on a three-node witness pair.

This does **not** kill the program. It corrects the target:

- bare `L2` can still encode threshold feasibility, predecessor capacity, and destruction boundaries
- but named confounder identity requires a strictly finer contract

## 4. Why This Failure Is Structural, Not an Artifact

### Theorem 2. Bare `L2` is invariant under predecessor relabeling inside non-focal intervals

Consider two linearized event streams with:

- the same focal events in the same order
- the same focal weights
- the same number of non-focal events between consecutive focal events

but possibly different identities or causal roles for those non-focal events.

Then the two streams have identical bare `L2` traces.

### Proof

Every non-focal event contributes the same elementary context:

- `W = [-inf, ..., -inf]`
- `d_total = 1`

So any block of `r` consecutive non-focal events composes to a context determined only by the count `r`, not by the identities of those events.

Every focal event contributes a context determined only by its weight.

The tropical recurrence

`W_(A⊗B)[j] = max(W_A[j], W_B[max(0, j - d_A)])`

depends on the left block only through `d_A`, and on the right block only through the right frontier values. Thus within each interval between focal events, the only non-focal information preserved by bare `L2` is the count of predecessor capacity. Renaming or permuting the individual non-focal events leaves the trace unchanged.

QED.

### Corollary 2. Exact identity recovery is impossible without witness coordinates

Minimal adjustment sets are identity-level objects. Bare `L2` is count-level.

So any identity-sensitive causal contract must refine the state space beyond bare `L2`.

## 5. The Over-Recovery Problem

The theorem above explains a second issue in the proposed MIRAGE-CAUSAL extraction rule.

Suppose we have a mixed graph

`C -> T`, `C -> Y`, `U -> T`, `T -> Y`

with topological order `[C, U, T, Y]`.

The unique minimal adjustment set is `{C}`. But the full pre-pivot non-focal prefix is `{C, U}`.

Because bare `L2` sees only predecessor capacity, any witness extraction rule that marks "all pre-pivot non-focals that help make `W[k]` live" cannot distinguish:

- the confounder `C`, which is causally necessary
- the irrelevant predecessor `U`, which is not

So the natural failure mode is not random error. It is **systematic over-recovery**: the tropical side returns the entire structurally helpful prefix, while causal identification asks for the minimal adjustment subset.

This is the causal analogue of the validity mirage:

- surface feasibility survives
- the finer semantic object has already been lost

## 6. The Exact Repair: Lift the Contract

The repair is conceptually simple:

> Move from a bare feasibility contract to a witness-preserving causal contract.

Let `Lambda` be a set of named candidate witnesses, for example the variables in a known or hypothesized adjustment set. Then the summary must remember not only whether there exists enough predecessor mass, but whether each `lambda in Lambda` survives in a way that still supports the contract.

The natural refined state is a colored witness quotient of the form

`Q_(k,Lambda) = (d_hat, m, {m_lambda}_{lambda in Lambda})`

where:

- `d_hat` is capped predecessor capacity
- `m` is the live endpoint of the bare frontier
- `m_lambda` records the deepest live slot at which witness `lambda` still participates, or `bot` if it has been lost

The new selective-memory note sharpens this from an intuition into an exact quotient theorem.

### Theorem 3. Protected-witness quotient

Fix `|Lambda| = p`. For the witness-preserving threshold contract, the exact summary object is

`Q_(k,p) = { (d, (m_lambda)_(lambda in Lambda)) : 0 <= d <= k, m_lambda in {bot, 0, 1, ..., d} }`

with coordinatewise shift-and-max composition:

`(d, m) * (d', n) = ( min(k, d + d'), m vee min(k, d + n) )`

where `vee` and `min` are taken coordinatewise over witness labels.

Its exact class count is

`|Q_(k,p)| = sum_(d=0)^k (d + 2)^p`.

### Proof sketch

Sufficiency follows because every future witness query depends only on:

- how much predecessor capacity remains on the left
- the deepest live slot already achieved by each protected witness
- the rightward shift of witness depths under concatenation

Exactness follows by coordinate separation. If two states differ on some witness coordinate `lambda`, prepend enough `N` symbols to push the larger `m_lambda` to threshold `k`; the smaller one still fails. If the witness coordinates agree but the predecessor capacities differ, append a fresh witness focal event after exactly the separating number of `N` symbols. So unequal states are context-separable.

This refined object does exactly what bare `L2` cannot do:

- it distinguishes `C` from `U`
- it supports witness survival queries
- it makes the causal test about provenance, not just about capacity

### Corollary 3. The provenance tax is exact for protected witnesses

From the class count,

`|Q_(k,p)| ~ k^(p+1) / (p + 1)`.

So every additional protected witness raises the polynomial degree of the required state space by exactly one.

This is not a nuisance constant. It is a degree-raising law:

> Protecting identity is a polynomial tax on memory.

### Corollary 4. The causal bridge must pass through `Q_(k,p)`, not bare `L2`

If a linearization is witness-faithful in the sense that each protected candidate confounder is represented by a named witness coordinate, then the correct contract state for the causal experiment is not `M_k` and not bare `L2`. It is a quotient of `Q_(k,p)` adapted to the witness semantics of that linearization.

That is the mathematically clean repair to the original exact-bijection dream.

## 7. Revision Symmetry and Multiple Valid Adjustment Sets

There is one more twist that matters for causal work: sometimes multiple witness identities are semantically interchangeable.

If the contract does not care which of `p` witnesses survives, but only the multiset of surviving witness depths, then we may quotient by the symmetric group on witness labels.

The selective-memory note gives the exact orbit count:

`|Q_(k,p)^sym| = binom(k + p + 2, p + 1) - 1`.

This matters because many causal graphs admit multiple minimal adjustment sets. In such cases the right contract may not be:

- preserve this exact variable name

but rather:

- preserve some member of this admissible witness family

So the deepest structural sentence becomes:

> Memory is quotient size divided by allowed revision symmetry.

For the causal program, that suggests a second-generation experiment:

- exact-name witness tracking when the minimal set is unique
- orbit-level witness tracking when several minimal adjustment sets are semantically equivalent

## 8. What Is Proved, and What Is Still Open

### Established by the current note plus earlier sources

1. `raw L2 -> L2' -> M_k -> R_k` is the correct bare quotient ladder.
2. Bare `L2` cannot universally recover minimal adjustment-set identity.
3. The reason is structural invariance, not parameter tuning.
4. The exact protected-witness quotient is `Q_(k,p)` with class count `sum_(d=0)^k (d + 2)^p`.
5. The provenance tax is exact at the protected-witness level.
6. Any causal theorem worth proving must refine the contract with witness identity or witness symmetry.

### Open but now sharply posed

1. The exact causal bridge theorem from graph-theoretic adjustment sets to witness-faithful linearizations.
2. Which classes of DAG linearizations preserve identifiability in the exact `Q_(k,p)` sense.
3. How to quotient further when several minimal adjustment sets are symmetry-equivalent.
4. Whether the full causal contract has a terminal quotient strictly between `Q_(k,p)` and the graph itself.

This is a much better research position than the original conjecture, because the remaining unknowns are now exact.

## 9. Revised MIRAGE-CAUSAL Program

The experiment should now be split into three honest tests.

### Test A. Bare feasibility test

Ask whether bare `L2` tracks:

- existence of enough predecessor capacity
- minimal adjustment **size** or residual demand
- identifiability destruction boundaries under compression

Do **not** ask it to recover variable identity.

### Test B. Colored witness fidelity test

Give each candidate confounder a witness coordinate and test whether the surviving witness set matches a ground-truth minimal adjustment set.

This is the correct place to ask for a high exact-match rate.

### Test C. Causal mirage boundary

Compress below the witness-preserving quotient size and measure:

- frontier still feasible
- answer still coherent
- witness set broken
- identifiability lost

That is the genuinely causal version of the validity mirage.

### Test D. Symmetry-aware causal retention

For DAGs with multiple minimal adjustment sets, score two targets:

- exact witness-name retention
- orbit retention modulo admissible adjustment-set symmetry

This separates genuine semantic loss from harmless witness substitution.

## 10. Research Meaning

The correction is not minor. It changes the program from:

> "Maybe bare tropical feasibility already knows the causal skeleton."

to:

> "Bare tropical feasibility knows the capacity skeleton; causal identification requires a provenance contract on top of it."

That is a stronger theory, not a weaker one.

It says:

- the quotient ladder from the tropical papers was real
- the causal bridge was aiming one contract too low
- the next theorem is a witness theorem, not a bare feasibility theorem
- the state explosion is not an accident; it is the exact price of provenance

If that next step works, the result will be much harder to dismiss because it will rest on the right semantic object.

## 11. Takeaways

1. The exact quotient results already proved in the tropical program remain intact.
2. The bare frontier cannot, in principle, recover minimal adjustment-set identity.
3. The right causal object is a witness-refined quotient with exact class count `sum_(d=0)^k (d + 2)^p`.
4. Provenance has an exact polynomial tax, and symmetry reduces that tax when revision is semantically allowed.
5. The experiment should be rewritten around witness survival and causal mirage, not bare set equality.

## Verification Artifact

The companion script

`scripts/referee/causal_contract_counterexamples.py`

constructs the toy DAGs from Theorem 1, computes their minimal adjustment sets by brute force, computes the corresponding bare `L2` summaries, and verifies the collision directly.
