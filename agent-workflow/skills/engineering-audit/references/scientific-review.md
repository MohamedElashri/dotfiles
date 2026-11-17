# Scientific review considerations

## Physics Analysis Review

Use for HEP, LHCb, ROOT, RooFit, zfit, histograms, ntuples, fitting, selections, efficiencies, plots, systematics, or statistical workflows.

Check:

- Dataset/sample provenance: year, polarity, trigger/stripping line, data-vs-MC separation, tree/branch names, duplicates, file ordering, friend alignment, event IDs, and local-path dependence.
- Selection logic: cut direction, units, boolean masks, object alignment, hidden preselections, blinding, sideband/signal definitions, trigger overlaps, and agreement with notes/thesis text.
- Weights/normalization: denominator/numerator definitions, per-event vs per-candidate weights, negative weights, missing branches, uncertainty propagation, `sumw2`, and year/PID/tracking/trigger factors.
- ROOT/histograms: ownership/lifetimes, overflow/underflow, binning, variable ranges, output names, metadata, and overwrite behavior.
- Fits/statistics: observable/range, binned vs unbinned, extended likelihood, fixed/constrained/floated parameters, normalization range, fit/Hesse/Minos status, pulls, toys, correlations, coverage, and uncertainty interpretation.
- ML in analysis: sample leakage, truth-only features, preprocessing split, threshold choice, overtraining checks, calibration, and inference/training mismatch.
- Reproducibility: input lists, versions, seeds, config separation, deterministic outputs, plot labels, clean-checkout runability, and traceable final numbers.

Ask for missing physics definitions when they determine correctness.
