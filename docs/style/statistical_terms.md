# Statistical Terminology Glossary

**Status:** Initial seed. Authoritative source for statistical / machine-learning terminology used in this project's prose, agent-generated reports, and wiki documentation. Extend per the amendment process at the bottom of this file.

**Why this exists.** Large language models commonly conflate technical statistical terms with their colloquial cousins (probability vs likelihood, accuracy vs precision, statistical bias vs algorithmic bias, statistical risk vs insured peril). When the project's pipeline produces an intake report, data report, or wiki page, the prose should use the precise term. This file is the single source of truth for what "precise" means here. Contributors and downstream consumers (including future agent-prompt injection) read from this file.

**What this file is NOT.** This is not a domain dictionary for property-and-casualty (P&C) insurance — for those terms see `docs/wiki/claims-model-starter/Glossary.md` "Domain terms" section. This is not an exhaustive statistics textbook. It is a curated list of terms whose precise meaning the project actively cares about because they are commonly conflated, and a process for adding more.

---

## How to use this file

**As a contributor writing prose** (commit messages, planning docs, wiki pages, code comments): if you reach for one of the terms in this glossary, use the definition here. If you find yourself using one of the "Common confusion" alternatives synonymously, stop and pick the precise term.

**As a reviewer**: when reviewing LLM-generated artifacts (intake reports, data reports, drafted wiki content), scan for the terms in this glossary and flag any usage that matches the "Common confusion" column rather than the "Definition" column.

**As an agent-prompt author** (future work): inject this file (or a curated subset) into agent system prompts so generated text uses the precise term. That integration is **not yet wired** as of Session 61 — it is filed as a follow-up in `BACKLOG.md`.

---

## Probability and inference

| Term | Definition | Common confusion |
|------|-----------|-----------------|
| **Probability** | The chance of an event occurring, expressed as a number in [0, 1]. Frequentist interpretation: long-run relative frequency. Bayesian interpretation: degree of belief. Both interpretations agree on the calculus; they disagree on what the number *means*. | Often used as a synonym for "likelihood" in casual speech. In this project, use **probability** when referring to P(event) — the chance of an outcome. |
| **Likelihood** | In statistical inference, the likelihood function `L(θ \| data)` measures how well a parameter value θ explains the observed data. It is a function of θ with the data held fixed. It is **not** a probability over events; it does not integrate to 1 over θ. | "Likelihood of rain" in everyday speech means probability. In this project, "likelihood" has the precise technical meaning above. If you mean P(event), say **probability**. |
| **Odds** | The ratio `p / (1 − p)` where `p` is a probability. Used in logistic regression's link function and in betting / actuarial contexts. | "3-to-1 odds" means odds = 3, which is probability = 0.75 — not 0.33. Conversion: `p = odds / (1 + odds)`. |
| **Confidence interval** | A frequentist interval estimator with the property that, under repeated sampling, X% of constructed intervals contain the true parameter value. The probability statement is about the *procedure*, not about the specific interval. | The interval `[a, b]` does NOT have a 95% probability of containing the parameter — the parameter is fixed; the interval is random. The "95% probability of containing the parameter" interpretation describes a Bayesian **credible interval**, not a confidence interval. |
| **Credible interval** | A Bayesian interval estimator with the property that, given the data and prior, X% of the posterior probability mass falls inside the interval. The probability statement is about the parameter (treating it as a random variable). | Often used interchangeably with confidence interval; the two have different formal meanings even when they numerically coincide. |
| **p-value** | `P(data at least as extreme as observed \| H₀ is true)`. The probability of seeing data this surprising (or more) under the null hypothesis. | The p-value is **not** the probability that H₀ is true, the probability that H₁ is true, or the probability that the result was due to chance. See [American Statistical Association statement on p-values](https://www.tandfonline.com/doi/full/10.1080/00031305.2016.1154108). |
| **Statistical significance** | A claim that the observed data would be unlikely under H₀ — i.e., p-value below a pre-chosen threshold (commonly 0.05). Says nothing about effect size. | Not the same as **practical significance** (the effect is large enough to matter). A study can be statistically significant with a tiny effect, or practically significant without reaching statistical significance. |
| **Bayes' theorem** | `P(A \| B) = P(B \| A) · P(A) / P(B)`. The relationship between a prior, a likelihood, and a posterior. | Not a method or a model — it is an identity. "Bayesian inference" is the practice of *applying* it with explicit priors and posteriors. |

---

## Hypothesis testing and error types

| Term | Definition | Common confusion |
|------|-----------|-----------------|
| **Null hypothesis (H₀)** | The hypothesis of "no effect" or "no difference" that a frequentist test attempts to reject. | Failing to reject H₀ does not mean H₀ is true — it means the data did not provide enough evidence to reject it. |
| **Type I error** | Rejecting H₀ when it is true. False-positive rate. The chosen significance level α (e.g., 0.05) is the rate at which Type I errors are tolerated. | Sometimes confused with "false-positive rate" in classification (TP / (FP + TN)) — they are conceptually related but the contexts (testing vs classification) differ. |
| **Type II error** | Failing to reject H₀ when H₁ is true. False-negative rate β. **Power** of a test is `1 − β`. | "Underpowered" means the test has high β — it would miss real effects. Power depends on effect size, sample size, and α. |
| **Multiple comparisons** | When many hypotheses are tested simultaneously, the family-wise probability of at least one Type I error grows. Corrections (Bonferroni, Holm, Benjamini-Hochberg) control this. | A single significant p-value among 20 independent tests at α = 0.05 is **expected by chance** under H₀ for all 20. |

---

## Classification metrics

For a binary classifier with confusion matrix entries TP, FP, TN, FN:

| Term | Definition | Common confusion |
|------|-----------|-----------------|
| **Accuracy** | `(TP + TN) / (TP + FP + TN + FN)`. Fraction of predictions that are correct. | Misleading on imbalanced classes — a classifier that always predicts the majority class can have high accuracy and zero useful behavior. |
| **Precision** | `TP / (TP + FP)`. Of the items predicted positive, what fraction are actually positive. Also called "positive predictive value." | Not the same as **accuracy**. Not the same as the colloquial / measurement-science use of "precision" (= low variance of repeated measurements). |
| **Recall** | `TP / (TP + FN)`. Of the items that are actually positive, what fraction did the classifier find. Also called **sensitivity** or **true-positive rate (TPR)**. | "Sensitivity" and "recall" are the same quantity; they are used in different traditions (medical statistics vs information retrieval). |
| **Specificity** | `TN / (TN + FP)`. Of the items that are actually negative, what fraction did the classifier correctly reject. Also called **true-negative rate (TNR)**. | The "opposite" of recall in a sense, but for the negative class. `1 − specificity` is the false-positive rate (FPR). |
| **F1 score** | Harmonic mean of precision and recall: `2·P·R / (P + R)`. Single number summarizing precision/recall trade-off, weighting them equally. | Not a probability. Not interpretable in isolation — always report the underlying precision and recall. |
| **ROC AUC** | Area under the receiver-operating-characteristic curve (TPR vs FPR across thresholds). Probability that a randomly chosen positive ranks above a randomly chosen negative. | Insensitive to class imbalance — a useful property in some contexts and a misleading one in others. For heavily imbalanced problems, prefer **PR AUC**. |
| **PR AUC** | Area under the precision-recall curve. More informative than ROC AUC when the positive class is rare, because precision degrades visibly as the model encounters more negatives. | Not directly comparable to ROC AUC — different scales, different baselines. |
| **Calibration** | The property that a model's predicted probabilities match observed event frequencies. A well-calibrated model that predicts 0.7 is right about 70% of the time across all "0.7 predictions." | A model can be highly **discriminative** (separates classes well, high AUC) but poorly calibrated (predicted probabilities are systematically off). Discrimination ≠ calibration. |
| **Discrimination** | The model's ability to rank positives above negatives. Measured by AUC and similar rank-based metrics. | See above — discrimination and calibration are independent properties; both should be measured. |

---

## Model evaluation and generalization

| Term | Definition | Common confusion |
|------|-----------|-----------------|
| **Overfitting** | The model fits noise specific to the training data, so performance on held-out data is materially worse than on training data. | Not the same as "high training error" (that's underfitting) and not the same as "high test error" alone (a model can be underfit AND have high test error). The diagnostic is the **gap** between train and test performance. |
| **Underfitting** | The model is too simple to capture the signal. Both training and test error are high. | Adding capacity (more features, more parameters) can reduce underfitting but risk overfitting; the bias-variance trade-off frames this. |
| **Training set / validation set / test set** | Three disjoint subsets of the data: **training** fits parameters; **validation** selects hyperparameters and tunes; **test** estimates final generalization performance and is used **once**. | Reusing the test set for tuning leaks information and produces optimistic generalization estimates. The "test set" must be held back to the very end. |
| **Cross-validation** | A resampling procedure (commonly k-fold) used in place of a single train/validation split when data is scarce. Each example is used for both training and validation across folds, but never both within a single fold. | Cross-validation does **not** replace a held-out test set for final evaluation. It is a tool for hyperparameter selection, not for unbiased generalization estimation when the same data is also used for tuning. |
| **Class imbalance** | A classification problem where one class is much rarer than another (e.g., 1% positives). | Imbalance is a property of the data, not the model. It changes which metrics are informative (PR AUC over ROC AUC, recall over accuracy) and which sampling / loss-weighting strategies are useful. |
| **Data leakage** | Information from outside the training set (e.g., features computed using future data, the target itself, or test-set statistics) influences the model, producing inflated apparent performance that does not generalize. | Most subtle in time-series and grouped data: standard random splits leak future information into the past. |

---

## Bias, variance, and fairness

| Term | Definition | Common confusion |
|------|-----------|-----------------|
| **Bias (statistical)** | The systematic error of an estimator: `E[θ̂] − θ`. An estimator is **unbiased** if its expected value equals the true parameter. | Entirely distinct from "bias" in the algorithmic-fairness sense (next row). The same English word covers two unrelated technical concepts. Disambiguate explicitly when both could apply. |
| **Variance (in bias-variance trade-off)** | The expected squared deviation of an estimator (or a model's prediction) from its mean across resamples of the data. High-variance models are sensitive to small changes in training data. | Not the same as **variance of a feature distribution** (a basic descriptive statistic), though both use the formula `E[(X − E[X])²]`. Context disambiguates. |
| **Bias-variance trade-off** | The decomposition of expected prediction error into squared bias + variance + irreducible noise. Reducing one often increases the other; total error is minimized at an intermediate complexity. | Often invoked in handwavy ways. The decomposition is precise for squared-error loss; the analogue for other losses is conceptually similar but mathematically different. |
| **Bias (algorithmic / fairness)** | Systematic differences in model performance, error rates, or selection rates across protected demographic groups (e.g., race, sex, age). Measured by metrics like demographic parity, equalized odds, or calibration-within-groups. | Has nothing to do with statistical bias in the estimator sense. A statistically unbiased estimator can produce algorithmically biased decisions, and vice versa. When discussing fairness, always say "algorithmic bias" or "demographic disparity" to avoid collision with the statistical sense. |
| **Fairness metric** | A quantitative measure of disparity. Different fairness metrics (demographic parity, equalized odds, predictive parity, calibration) are mutually incompatible in general — a model cannot satisfy all of them simultaneously when base rates differ across groups (Chouldechova 2017; Kleinberg, Mullainathan, Raghavan 2016). | "Fair" is not a single property. Specify which fairness metric and why it was chosen for the use case. |

---

## Insurance-specific clarifications

These terms have a specific meaning in property-and-casualty (P&C) claims modeling that may differ from their generic statistical / colloquial use.

| Term | Definition | Common confusion |
|------|-----------|-----------------|
| **Risk (statistical sense)** | Expected loss; a probability-weighted outcome. In decision theory, the expected value of a loss function under the data-generating distribution. | Used in this sense when discussing model risk, prediction risk, or empirical risk minimization. |
| **Risk (insurance / peril sense)** | A covered hazard or the insured exposure to it (e.g., "auto liability risk," "wind risk"). What the policy protects against. | When writing for a mixed audience, disambiguate ("model risk" vs "covered risk") on first use. |
| **Frequency (claims modeling)** | The expected number of claims per exposure unit per period (e.g., claims per car-year). | Not the same as "frequency" in statistics (count of observations), though related. |
| **Severity (claims modeling)** | The expected cost per claim (conditional on a claim occurring). | Not the same as "severity" in clinical / safety contexts. |
| **Pure premium** | Expected loss per exposure unit. Decomposed as `frequency × severity`. The actuarial estimate before loadings (expenses, profit, contingency). | Not the same as the **gross** or **office** premium charged to the policyholder. |
| **Loss ratio** | `incurred losses / earned premium`. A core profitability metric. | Not the same as a model's loss function. Context disambiguates. |
| **Hazard ratio** | In survival / duration models (Cox proportional hazards), the ratio of hazard rates between two groups. Relevant for time-to-event modeling such as subrogation recovery time, claim closure duration, or fraud-investigation latency. | Not a probability and not an odds ratio. A hazard ratio of 2 means the instantaneous event rate is twice as high — it does not directly translate to "twice as likely." |
| **Subrogation** | The process of recovering costs from an at-fault third party after paying a claim. The recovery success rate is a frequent modeling target. | See `docs/wiki/claims-model-starter/Glossary.md` "Domain terms" for the broader definition. |

---

## Amendment process

This file is meant to grow. Add a term whenever:

1. **An LLM-generated artifact uses a term incorrectly.** During review of an intake report, data report, or generated wiki page, if a statistical term is conflated with a near-synonym, add the term here and cite the conflation in the "Common confusion" column.
2. **A contributor or stakeholder is observed conflating two terms in conversation.** If a meeting or PR discussion surfaces a recurring conflation, add it.
3. **The pipeline gains a new modeling capability that uses unfamiliar terminology.** If the project starts using survival analysis, causal inference, time-series methods, or another sub-field, seed entries for the most common conflations in that area.

### How to add or amend a term

1. **Pick the right section.** If none fits, add a new `## Section name` heading. Sections group thematically related terms; alphabetical order within a section is not required (related terms cluster).
2. **Write the row in the standard format:**

   ```markdown
   | **Term name** | Precise definition. Cite an authoritative source as a markdown link if the definition is contested or non-obvious. | The conflation this term is meant to head off. Name the wrong synonym explicitly. |
   ```

3. **Authoritative sources** in priority order: peer-reviewed textbooks (Casella & Berger, Hastie/Tibshirani/Friedman, Murphy), professional society statements (American Statistical Association, NIST, NAIC, Society of Actuaries), then standards bodies (ISO 5725 for accuracy/precision in measurement). Wikipedia is acceptable for terms whose definition is uncontested. Avoid blog posts and tutorials.
4. **Decide whether the term needs to surface in the wiki.** See "Wiki integration" below.
5. **Open a PR.** Single-purpose PRs are preferred — "Add `<term>` to statistical_terms.md" — so review focuses on definition correctness rather than batched changes.
6. **Reviewer responsibilities:** verify the cited source supports the definition; verify that the "Common confusion" entry actually represents a conflation that has been observed (not a hypothetical); verify that the term is not already covered in another section.

### How to remove or rewrite a term

Removal is rare — terms here have been added because a real conflation surfaced. If a term is being rewritten because the original definition was wrong, add a one-line note in the corresponding `CHANGELOG.md` entry under the Session that landed the rewrite (e.g., "Statistical glossary: corrected definition of `calibration` to distinguish it from discrimination").

---

## Wiki integration

The wiki at `docs/wiki/claims-model-starter/Glossary.md` has a `## Statistical terms` section that serves as a **curated subset** of this file — the terms most likely to appear in user-facing wiki content (Pipeline-Overview, Data-Guide, Worked-Examples, Schema-Reference). The wiki section opens with a one-line cross-link pointing here.

### When to update the wiki Glossary alongside this file

| Scenario | Wiki action |
|----------|-------------|
| Adding a term that already appears (or will soon appear) in user-facing wiki prose. | Add a row to the wiki `## Statistical terms` table mirroring this file's entry. |
| Adding a term that is purely contributor-facing (e.g., applies to commit messages and planning docs but not user-visible content). | Do not touch the wiki. This file is sufficient. |
| Renaming or rewriting a term that appears in the wiki. | Update both files in the same commit. |
| Removing a term. | Remove from both if present in the wiki; update the wiki section's cross-link if it referenced the removed term. |

### Cross-link format (canonical)

The wiki `## Statistical terms` section opens with:

```markdown
## Statistical terms

> **Curated subset.** See [`docs/style/statistical_terms.md`](../../style/statistical_terms.md) for the full glossary, authoritative sources, and amendment process.
```

When a wiki term diverges in wording from this file (typically because the wiki entry needs more conversational phrasing), keep the technical definition aligned and tag the wiki entry with a marker showing which `docs/style/statistical_terms.md` row is authoritative.

### Sync check at session close

Sessions that touch either file should grep the other for the affected term to confirm they agree:

```bash
grep -in "<term>" docs/style/statistical_terms.md docs/wiki/claims-model-starter/Glossary.md
```

If the two files disagree on a definition, this file (`docs/style/statistical_terms.md`) wins. The wiki gets updated to match.

---

## Future integrations (not yet wired)

- **Agent system-prompt injection.** The intake, data, and website agents will eventually load this glossary (or a curated subset) into their system prompts so generated reports use the precise terminology natively. Filed in `BACKLOG.md` as a follow-up to this file's initial seed. Until then, glossary discipline is enforced at review time, not at generation time.
- **Lint / CI check.** A future tooling pass could grep generated artifacts (reports, wiki pages) for "Common confusion" terms and flag them for human review. Not currently implemented.

---

## Provenance

This file was seeded in Session 61 (2026-04-19) from operator request "develop an initial Statistical terminology glossary and include instructions on amending it and using it with the wiki documentation." The initial term set was chosen to cover the highest-frequency conflations in (a) frequentist-vs-Bayesian inference, (b) classification metrics, (c) bias/variance/fairness, and (d) P&C-specific risk language. Subsequent sessions extend per the amendment process above.
