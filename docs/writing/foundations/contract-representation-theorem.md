# Contract Representation Theorem

## Thesis

We now have the same structural pattern three times:

1. the bare threshold contract with quotient `M_k`,
2. the protected-witness contract with quotient `Q_(k,p)`,
3. the unique-minimal causal class, which factors into `Q_(k,p)` through a witness-faithful translation.

That repetition is not an accident. It suggests the next theorem is a contract-level representation result.

The right version, stated honestly, is:

> Every admissible contract admits a canonical quotient. The remaining work is to define “admissible” so that the theorem is true, useful, and broad enough to contain causal identification beyond the unique-minimal class.

This note makes that template explicit.

## What This Note Is

This is not a claim that the fully general causal theorem is already proved.

It is a cleaned-up meta-theorem template:

- precise enough to organize the results already on disk,
- honest about which hypotheses make the theorem go through,
- sharp enough to point directly at the next object `Q_(k,𝒜)`.

## 1. Raw Material

Let `X` be a raw associative state space with product `*`.

Examples:

- words over `{N, F}`,
- words over `{N, T} union {W_lambda}`,
- causal linearizations translated into one of those alphabets.

The whole program lives on the same backbone:

- there is a raw compositional world,
- there is a contract specifying what must be preserved,
- there is a coarsest quotient that keeps that promise.

## 2. Candidate Definition of Admissible Contract

We need a definition that is weak enough to include the contracts we care about, but strong enough to force a canonical quotient.

### Definition 1. Contract

A contract `C` on `X` consists of:

1. an admissible set of test contexts `Ctx_C subseteq X x X`,
2. an observable map `Obs_C : X -> O_C`,
3. a notion of soundness: a summary is contract-sound if it preserves `Obs_C` under every admissible test context.

Given `(l, r) in Ctx_C`, the contextual observable of `x` is

`Obs_C(l * x * r)`.

### Definition 2. Contextual equivalence

Define

`x ~_C y`

iff for every admissible test context `(l, r) in Ctx_C`,

`Obs_C(l * x * r) = Obs_C(l * y * r)`.

This is the natural “indistinguishable under the contract” relation.

### Definition 3. Admissible contract

Call `C` admissible if:

1. `~_C` is a two-sided congruence on `X`,
2. `~_C` has finite index,
3. there exists a finite separator radius `srad(C)` such that any two inequivalent classes are separated by some admissible context of total size at most `srad(C)`.

This definition is deliberately operational. It says the contract is:

- compositional,
- finitely representable,
- locally testable in bounded radius.

## 3. Canonical Quotient Theorem

### Theorem 1. Contract representation theorem

Let `C` be an admissible contract on an associative raw space `X`.

Then:

1. the quotient

   `Q_C = X / ~_C`

   is a well-defined associative quotient monoid;

2. `Obs_C` factors through the quotient map

   `rho_C : X -> Q_C`;

3. every contract-sound associative summary factors uniquely through `Q_C`;

4. `Q_C` is unique up to isomorphism among contract-sound associative quotients;

5. the contract has bounded local distinguishability with radius `srad(C)`.

### Proof

Parts 1 and 2 are immediate from the definition of `~_C` as a two-sided congruence.

For Part 3, let `h : X -> S` be any associative contract-sound summary. If `x ~_C y`, then every admissible context gives the same contract observable on `x` and `y`. Since `h` is sound, `h(x)` and `h(y)` cannot differ on any contract-relevant behavior. Therefore `h` is constant on `~_C`-classes and factors through the quotient.

Part 4 follows from the universal property of quotienting by the maximal sound indistinguishability relation.

Part 5 is exactly the separator-radius hypothesis.

QED.

## 4. Why This Theorem Is Not Vacuous

At first glance Theorem 1 looks formal. But that is exactly the point.

The hard work is not the quotient construction after the equivalence relation is known. The hard work is:

1. finding the right contract,
2. proving finite index,
3. proving bounded separators,
4. computing the resulting quotient exactly.

That is where the real mathematics lives.

The theorem tells us what success looks like once those pieces are in place.

## 5. Instantiations Already on Disk

### Bare threshold contract

For the threshold language:

- raw space is the event-word monoid,
- contract observable is threshold feasibility,
- the canonical quotient is `M_k`,
- the one-sided quotient is `R_k`,
- the separator radius is `k`.

### Protected-witness contract

For named witness preservation:

- raw space is the witness-colored word monoid,
- contract observable records witness survival,
- the canonical quotient is `Q_(k,p)`,
- the exact class count is `sum_(d=0)^k (d + 2)^p`,
- the symmetric orbit quotient is `binom(k + p + 2, p + 1) - 1`.

### Unique-minimal causal class

For the narrow causal regime already proved:

- raw space is the class of prefix-witness linearizations,
- the contract observable is witness-preserving causal soundness,
- the factorization note proves a translation into the protected-witness contract,
- so the causal problem factors through `Q_(k,p)`.

This is not yet a new canonical quotient theorem for all causal queries. It is a certified instance of the general template.

## 6. Translation Principle

The factorization theorem suggests a general corollary.

### Corollary 1. Contract-preserving translation

Suppose `P` is a problem on raw space `X_P` and `C` is an admissible contract on raw space `X_C`.

If there exists a translation

`L : X_P -> X_C`

such that the problem observable on `P` equals the contract observable on `C` after translation, then the problem factors through `Q_C`.

This is exactly the move used in the unique-minimal causal note.

It is also the right template for future causal classes:

- first find the translation,
- then inherit the quotient.

## 7. Where the Full Causal Theorem Still Breaks

The universal-looking sentence

> causality lives in the smallest state that keeps the answer identifiable

is currently proved only on the unique-minimal witness-faithful class.

To make it universal, one of two things must happen:

1. the broader causal contracts must still fit the admissible-contract template with finite quotient and bounded separators,
2. or we must discover that different identification regimes require qualitatively different contracts and therefore different quotient geometries.

That is why the next object matters.

## 8. The Next Quotient: `Q_(k,𝒜)`

Let `𝒜` be the hypergraph of admissible minimal adjustment families.

Once minimal adjustment sets are no longer unique, the correct observable is no longer just:

- which witness variable survives,

but rather:

- which admissible witness family survives.

That points naturally to a new contract:

`C_(k,𝒜)`.

If `C_(k,𝒜)` is admissible in the sense above, then its quotient

`Q_(k,𝒜)`

will be the next canonical object.

This is where the geometry may genuinely change:

- the state may stop looking like a coordinate vector,
- the separator structure may depend on hypergraph overlap,
- the right symmetry group may act on families rather than variables.

That is the next real depth.

## 9. The Honest Universal Sentence

The strongest universal sentence we can currently justify is:

> In every regime so far formalized, the semantic contract determines the canonical memory quotient.

The strongest causal sentence we can currently justify is:

> In the unique-minimal witness-faithful regime, causality does not live in the answer. It lives in the smallest state that keeps the answer identifiable.

That sentence is narrower than the dream, but much more durable.

## 10. Takeaways

1. We now have a clean candidate definition of admissible contract.
2. Under that definition, the canonical quotient theorem is straightforward and unifies the results already obtained.
3. The hard mathematics is pushed to finite index, exact quotient identification, and separator bounds.
4. The unique-minimal causal theorem is the first real causal instantiation of the template.
5. The next object to test is the adjustment-family quotient `Q_(k,𝒜)`.
