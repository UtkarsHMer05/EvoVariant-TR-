# Mini Project PPT Material (20 Slides, Updated with Final Metrics)

Project: Evo2 Variant Analysis (Next.js Frontend + Modal Serverless Backend)

This is the final slide script for your presentation.
Each slide section contains:
- Slide content (what to place)
- Visual suggestion (what to show)
- Presenter notes (what to say)

---

## Slide 1 - Title Slide

### Slide content
- Project Title: Evo2-Powered Variant Effect Prediction for Human SNVs
- Student Name(s): [Add names]
- Guide Name: [Add guide]
- Department / Institution: [Add department and college]
- Date: [Add date]

### Visual suggestion
- App homepage screenshot or project thumbnail

### Presenter notes
- This work builds a complete, cloud-deployed variant effect prediction platform.
- It combines genomics data APIs, a foundation model (Evo2), and a user-facing web app.

---

## Slide 2 - Problem Statement

### Slide content
- Single nucleotide variants (SNVs) can be benign or disease-associated.
- Experimental functional assays are expensive, slow, and not scalable for all variants.
- ClinVar is valuable but does not cover all novel variants.
- Need a fast computational method for early prioritization of potentially harmful variants.

### Visual suggestion
- DNA sequence -> variant -> AI scoring -> risk label pipeline graphic

### Presenter notes
- Emphasize real-world bottleneck: too many variants, too little experimental capacity.

---

## Slide 3 - Objectives

### Slide content
- Develop an end-to-end web system for SNV analysis.
- Integrate Evo2 for sequence likelihood-based pathogenicity estimation.
- Provide intuitive interfaces for genome selection, gene search, and sequence exploration.
- Compare Evo2 predictions with known ClinVar labels.
- Return interpretable outputs: delta score, class label, confidence.

### Visual suggestion
- Five-point objective checklist

### Presenter notes
- Clarify this is a decision-support tool, not a final clinical diagnostic engine.

---

## Slide 4 - Motivation

### Slide content
- Genomic data growth is outpacing manual interpretation workflows.
- AI models can capture long-range sequence context missed by classical heuristics.
- Cloud deployment enables practical usage of large models without local GPUs.
- Goal: make advanced genomics modeling accessible through a usable UI.

### Visual suggestion
- Increasing genomics data trend chart + cloud GPU iconography

### Presenter notes
- Motivation is both scientific (model capability) and engineering (real deployment).

---

## Slide 5 - Scope of the Project

### Slide content
Included:
- Human assembly selection and chromosome browsing
- Gene lookup and metadata retrieval
- Sequence window visualization
- SNV analysis through Evo2 backend
- ClinVar vs Evo2 comparison panel

Excluded:
- Indels and structural variants
- Clinical-grade patient decision pathways
- Full prospective clinical validation
- Multigene calibration-specific threshold tuning

### Visual suggestion
- Included vs Excluded table

### Presenter notes
- Scope control is deliberate to keep quality high for the SNV pathway.

---

## Slide 6 - Literature Review Overview

### Slide content
- Variant effect prediction evolved from feature-based models to deep sequence models.
- Clinical resources (ClinVar) provide curated labels but incomplete coverage.
- Modern genomic foundation models can evaluate sequence plausibility directly.
- Literature gap: integration of strong models with production-grade interactive tooling.

### Visual suggestion
- Timeline: traditional variant scoring -> deep models -> foundation models

### Presenter notes
- The project contributes by closing the deployment and usability gap.

---

## Slide 7 - Literature Review: Paper 1

### Slide content
Paper: Findlay et al. (2018), BRCA1 saturation editing
- Method: experimental functional assay of BRCA1 SNVs
- Labels: LOF, INT, FUNC
- Contribution: large, biologically grounded benchmark set
- Limitation: expensive wet-lab pipeline, gene-specific focus

### Visual suggestion
- Citation + dataset summary card (3893 BRCA1 SNVs)

### Presenter notes
- This dataset underpins the benchmark and threshold calibration workflow.

---

## Slide 8 - Literature Review: Paper 2

### Slide content
Paper: Evo2 model work (Arc Institute)
- Method: long-context genomic language modeling
- Use in this project: sequence likelihood scoring for reference vs mutated sequence
- Strength: captures context-dependent sequence patterns
- Limitation: high compute requirement, deployment complexity

### Visual suggestion
- Model concept diagram with long DNA context window

### Presenter notes
- This is why serverless H100 inference is central to the solution.

---

## Slide 9 - Literature Review: Paper 3

### Slide content
Paper/Resource: ClinVar and NCBI variant curation ecosystem
- Method: expert-curated clinical significance records
- Strength: trusted baseline for known variants
- Limitation: missing labels for many variants, possible disagreements across submissions

### Visual suggestion
- Known vs unknown variant coverage diagram

### Presenter notes
- The app uses ClinVar as a reference point, not as a perfect ground truth for all variants.

---

## Slide 10 - Research Gap Identified

### Slide content
Identified gaps:
- Strong models are not always exposed through practical web systems.
- Data discovery and inference are often split across disconnected tools.
- Operational metrics (latency, reliability) are often ignored in academic prototypes.

Project response:
- Unified platform: gene discovery, sequence context, AI scoring, and comparison in one flow.

### Visual suggestion
- Gap-to-solution map

### Presenter notes
- Emphasize end-to-end integration as key contribution.

---

## Slide 11 - Proposed System

### Slide content
- Frontend: Next.js UI for search/browse/analyze/compare
- Backend: Modal FastAPI endpoint for live scoring
- Model: Evo2 sequence scorer
- Data providers: UCSC APIs + NCBI APIs

Request flow:
1. User chooses variant.
2. Backend fetches sequence window.
3. Evo2 scores reference and mutated sequence.
4. Backend returns prediction and confidence.

### Visual suggestion
- High-level block diagram (User, Frontend, Backend, External APIs)

### Presenter notes
- Keep this as the big-picture architecture before deeper methodology.

---

## Slide 12 - System Architecture

### Slide content
Frontend modules:
- Home page, GeneViewer, VariantAnalysis, KnownVariants, ComparisonModal

Backend modules:
- VariantRequest schema
- get_genome_sequence
- analyze_variant
- Evo2Model.analyze_single_variant (webhook)

Infrastructure:
- Modal serverless containers
- H100 GPU runtime
- API gateway endpoint

### Visual suggestion
- Component interaction diagram from project README

### Presenter notes
- Mention sender/receiver chain explicitly: UI -> API adapter -> Modal endpoint -> UCSC + Evo2 -> response.

---

## Slide 13 - Methodology (Detailed)

### Slide content
Variant scoring method:
1. Input variant: (position, alt base, genome, chromosome)
2. Fetch centered 8192 bp sequence window
3. Build:
   - Reference sequence
   - Variant sequence (single-base substitution)
4. Compute Evo2 scores:
   - s_ref = score(reference sequence)
   - s_var = score(variant sequence)
5. Delta:
   - delta = s_var - s_ref

Classification rule:
- If delta < -0.0009178519 -> Likely pathogenic
- Else -> Likely benign

Confidence rule:
- Pathogenic side: |delta - threshold| / 0.0015140239 (capped at 1)
- Benign side: |delta - threshold| / 0.0009016589 (capped at 1)

### Visual suggestion
- Formula box + sequence mutation diagram

### Presenter notes
- Explain that negative delta implies stronger disruption signal in model likelihood space.

---

## Slide 14 - Tools and Technologies

### Slide content
Frontend:
- Next.js 15, React 19, TypeScript, Tailwind, shadcn/ui

Backend:
- Python, FastAPI, Modal, Pydantic

Model stack:
- Evo2, PyTorch, CUDA runtime

Data and metadata:
- UCSC Genome API
- NCBI Clinical Tables
- NCBI E-utilities / ClinVar

Deployment:
- Modal serverless GPU with H100

### Visual suggestion
- Stack logos grouped by layer

### Presenter notes
- Point out cloud-first architecture enables heavy-model inference from a lightweight browser UI.

---

## Slide 15 - Data Collection and Preprocessing

### Slide content
Primary benchmark source:
- Findlay BRCA1 functional dataset (3893 SNVs)

Label processing:
- Merge FUNC and INT -> FUNC/INT
- Binary target for evaluation:
  - LOF = 1
  - FUNC/INT = 0

Columns used:
- chromosome, position (hg19), reference, alt, function score, class

Subset used for endpoint evaluation:
- First 100 valid SNVs (cost-optimized live evaluation run)

### Visual suggestion
- Dataset pipeline table

### Presenter notes
- Mention that evaluation subset choice should be treated as internal benchmark, not final external validation.

---

## Slide 16 - Implementation

### Slide content
Implemented workflow:
- Frontend collects user-selected variant
- API call to Modal webhook
- Backend obtains sequence from UCSC and computes Evo2 delta
- Result rendered with confidence and ClinVar comparison

Engineering highlights:
- Runtime patching for flash-attention compatibility in Modal image
- Container warm-start behavior and scaledown settings
- Error handling and input validation for SNV format

### Visual suggestion
- Code module map (frontend + backend)

### Presenter notes
- Show that this is a production-style engineering implementation, not only notebook experimentation.

---

## Slide 17 - Performance Metrics (Final Updated Values)

### Slide content
Evaluation protocol (new run, no source-code changes):
- 100 BRCA1 variants evaluated via live deployed Modal endpoint
- Success rate: 100/100 (100%)

Binary classification metrics:
- Accuracy: 0.9000 (90.00%)
- Precision: 0.5625 (56.25%)
- Recall: 0.7500 (75.00%)
- F1-score: 0.6429 (64.29%)
- AUROC (from endpoint delta scores): 0.9309

Confusion matrix:
- [[TN, FP], [FN, TP]] = [[81, 7], [3, 9]]

Latency metrics (same run):
- Average latency: 2.7015 s
- Median latency: 2.5999 s
- P95 latency: 2.9770 s
- Total wall time for 100 calls: 270.16 s

Context metric (from original BRCA1 notebook):
- Full benchmark AUROC printed as 0.73

### Visual suggestion
- One metrics table + confusion matrix heatmap + latency boxplot

### Presenter notes
- Call out the precision-recall tradeoff: high recall, moderate precision.
- Mention this run uses a threshold calibrated on a BRCA1 subset, so results are useful but not final external generalization proof.

---

## Slide 18 - Results and Analysis (Final)

### Slide content
What the numbers indicate:
- Model captures LOF variants reasonably well (Recall = 75%).
- False negatives remain low (FN = 3), useful for screening workflows.
- False positives are present (FP = 7), creating precision tradeoff.

Operational interpretation:
- Good for prioritization workflows where missing pathogenic variants is costly.
- Requires downstream filtering/secondary evidence to improve precision.

Score interpretation:
- More negative delta -> stronger pathogenic tendency.
- Confidence scales with distance from threshold and class-specific score spread.

### Visual suggestion
- Confusion matrix + precision-recall discussion box

### Presenter notes
- Mention this is a 100-case cost-constrained run; final benchmark should be expanded for stronger statistical confidence.

---

## Slide 19 - Data Visualization (What to Show)

### Slide content
Visualization set for presentation:
1. BRCA1 delta distribution plot (LOF vs FUNC/INT)
2. Confusion matrix heatmap (500-call run)
3. Latency histogram/boxplot and percentile summary
4. ROC curve using endpoint delta scores
5. Frontend result card and comparison modal screenshots

Where they come from:
- Existing BRCA1 plot: backend notebook/backend plotting path
- New evaluation graphs: generated by evaluation script in this repo

### Visual suggestion
- 2x2 panel: distribution, confusion matrix, ROC, latency

### Presenter notes
- This slide should be mostly visuals with short captions.

---

## Slide 20 - Conclusion and Future Work

### Slide content
Conclusion:
- Built an end-to-end AI variant analysis platform with real cloud deployment.
- Integrated Evo2 inference into an interactive genome exploration experience.
- Demonstrated measurable predictive performance and operational latency behavior.

Future work:
- Evaluate on held-out and multi-gene datasets
- Recalibrate thresholding for improved precision
- Add support for indels and richer variant types
- Add asynchronous batch mode and dashboard monitoring
- Add experiment tracking for model and latency drift

### Visual suggestion
- Summary-to-roadmap timeline

### Presenter notes
- End with practical impact and clear extension plan.

---

# Viva Appendix A - Exact Final Metric Values

- Total evaluated: 100
- Successful calls: 100
- Failed calls: 0
- Accuracy: 0.900000
- Precision: 0.562500
- Recall: 0.750000
- F1-score: 0.642857
- AUROC (endpoint delta): 0.930871
- Confusion matrix: [[81, 7], [3, 9]]
- Average latency: 2.7015 s
- Median latency: 2.5999 s
- P95 latency: 2.9770 s
- Total evaluation wall time: 270.16 s

---

# Viva Appendix B - Theory Talking Points (Short)

1. Evo2 acts as a sequence likelihood model over genomic context.
2. A variant effect score is computed by comparing mutated vs reference likelihood.
3. Delta score is converted into class prediction via calibrated thresholding.
4. Confidence is distance-to-threshold normalized by class-specific variance.
5. This design supports transparent score-based interpretation, not black-box-only labels.

---

# Viva Appendix C - Reproducibility and Data Visibility

After adding the evaluation script, you can view everything at:
- evaluation output CSV: per-variant predictions and latencies
- metrics JSON: final scalar metrics
- PNG plots: confusion matrix, ROC, latency plots
- optional TensorBoard logs: scalar metrics and latency distribution

These artifacts make your slide values auditable and repeatable.
