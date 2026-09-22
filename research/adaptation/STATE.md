# Adaptation State

Study: POSTHOC-FOUNDATION-ADAPTATION-001
Protocol SHA-256: 07c93b4657e84a4ddfbdc2df1af0f467f80959e0534a67840b4bf2b2b04a2c2c
Current stage: PROTOCOL_FROZEN
Evidence stage: PRELIMINARY_PLANNING

state_machine_stage: PROTOCOL_FROZEN
completed:
  - BRANCH_HYGIENE
  - DATA_IDENTITIES_VERIFIED
  - PROTOCOL_FROZEN_PENDING_HASH
pending:
  - ENV_READY
  - DATA_READY
  - CADUCEUS_SMOKE_PASS
  - CADUCEUS_FROZEN_DONE
  - CADUCEUS_PARTIAL_DONE
  - CADUCEUS_FULL_DONE
  - CADUCEUS_HPO_DONE
  - CADUCEUS_FINAL_TRAINED
  - CADUCEUS_HOLDOUT_DONE
  - NT_SMOKE_PASS
  - NT_FROZEN_DONE
  - NT_PEFT_DONE
  - CALIBRATION_DONE
  - ABSTENTION_DONE
  - ENSEMBLE_DONE
  - ABLATIONS_DONE
  - CONTEXT_DONE
  - LEARNING_CURVES_DONE
  - STATISTICS_DONE
  - FIGURES_DONE
  - JUDGE_NOTEBOOK_DONE
  - REPORT_DONE
  - VALIDATED
  - COMPLETE
holdout:
  validation_manifest_access: identity_and_hash_verification_only
  validation_evaluation: false
  validation_labels_used_for_selection: false
  locked_test_accessed: false
  selection_closed: false
resources:
  paid_compute_budget_usd: 0
  paid_purchases: prohibited
  colab_status: live_T4_connected
provenance:
  branch: research/posthoc-foundation-adaptation
  head: dd36ad72572bd8aa8bf9f0a7a589075c1fe65f70
  train_manifest_sha256: 32bf517ec8bc401d29f611e83a8c8c81eafc0d1f19886d2650a3bf441df044e1
  validation_manifest_sha256: b31d884860fcf07b6f7f453c3ef148886913f381965318e9c1da341d1eaf3c8b
  locked_manifest_sha256: 9f9e052d21f4a6a32f595cb20f48cb81e033c0481942820d04f9b67d410a16cb
  protocol_sha256: 07c93b4657e84a4ddfbdc2df1af0f467f80959e0534a67840b4bf2b2b04a2c2c
