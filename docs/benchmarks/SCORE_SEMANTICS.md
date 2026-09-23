# Score semantics

The immutable primary result uses the frozen isotonic calibrated probability,
with higher_is_more_pathogenic and threshold 0.50. The registered raw Evo2
evidence is alternate_minus_reference_log_likelihood; it is not silently
reoriented in post-processing. Comparator scales are retained in their source
semantics. No locked label, locked score, or frozen threshold is optimized by
the expansion analyses.

MSA = NOT_DEFINED_IN_PROJECT.
