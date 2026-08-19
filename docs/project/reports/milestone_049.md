# Milestone 049: Official Evo 2 Parity Requirements

## Question
What are the exact requirements for Evo 2 scoring parity with the original EvoVariant project, before GPU integration?

## Answer

Based on the protocol (`research/protocol/protocol.yaml`) and original project requirements:

### Sequence Format
- **Context window**: 8,192 bp (frozen at M41)
- **Reference assembly**: GRCh38 (assembly38)
- **Strand**: Both forward and reverse-complement scoring required
- **Input format**: Single FASTA sequence string (no headers, no newlines)

### Scoring Semantics
- **Forward strand**: Score the reference sequence and alternate (mutated) sequence
- **Reverse strand**: Reverse-complement both the reference and alternate sequences, then score
- **Score output**: Log-odds or log-likelihood score (model determines scale)
- **Delta**: score_alternate - score_reference (positive = variant more likely)

### GPU Requirements
- **Framework**: PyTorch
- **Model**: Evo 2 (70M or larger)
- **Precision**: bfloat16 for efficiency
- **Batching**: Process variants in batches of 64-256 sequences
- **Memory**: Minimum 24GB VRAM for 70M model, 80GB for larger models

### Parity Checklist
- [x] 8,192bp context window (M41, M42)
- [x] Forward + reverse-complement scoring (M45)
- [x] Reference allele validation (M34, M44)
- [x] Deterministic sequence cache (M46)
- [x] Model-agnostic scorer interface (M47)
- [x] Fake scorer for testing (M48)
- [ ] Modal GPU orchestration setup (M51-M59)
- [ ] Official Evo 2 smoke test (M55)
- [ ] Real Evo 2 scoring integration (M56-M60)
