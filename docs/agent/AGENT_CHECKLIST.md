# Agent Checklist

Before changing code:
- [ ] Read control docs.
- [ ] Verify branch/HEAD.
- [ ] Preserve user changes.
- [ ] Know phase gate.
- [ ] Know whether task may spend money.

Before model integration:
- [ ] Official source verified.
- [ ] License recorded.
- [ ] Checkpoint/revision recorded.
- [ ] Hardware requirement recorded.
- [ ] Preprocessing documented.
- [ ] Tiny smoke passed.

Before training:
- [ ] Split manifests frozen.
- [ ] Leakage tests pass.
- [ ] Objective predeclared.
- [ ] Test set inaccessible to selection code.
- [ ] Seed logged.

Before HPO:
- [ ] Features cached.
- [ ] Search space saved.
- [ ] Trial budget bounded.
- [ ] No test metric in objective.

Before final test:
- [ ] Config frozen.
- [ ] Model frozen.
- [ ] Ensemble frozen.
- [ ] Calibration frozen.
- [ ] Protocol hash verified.

Before UI:
- [ ] Data comes from registry/API.
- [ ] No hard-coded experiment metrics.
- [ ] Research-only wording.
- [ ] Evidence stage visible.

Before phase PASS:
- [ ] Tests pass.
- [ ] Docs updated.
- [ ] Evidence paths recorded.
- [ ] Cost recorded.
- [ ] Commit created.
