# Metrics

All local benchmark summaries use the repository metric implementation plus
the fixed bootstrap seed 42 with 1,000 replicates where the subgroup contains
both classes. Results include sample size and class counts. Small or
single-class strata are marked INSUFFICIENT_SUPPORT, not converted to zero.

Accuracy, balanced accuracy, precision, recall, specificity, positive-class
F1, macro-F1, micro-F1, weighted-F1, MCC, Brier, NLL, ECE, TP, TN, FP, FN,
AUROC, AUPRC, and probability MAE are available where labels and scores
support them.
