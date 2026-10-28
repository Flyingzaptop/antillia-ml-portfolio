# MachineSentinel — model card

## Intended use
Educational research and interactive portfolio demonstration.

## Data
AI4I 2020; https://archive.ics.uci.edu/dataset/601/ai4i+2020+predictive+maintenance+dataset

## Evaluation
See reports/report.html and metrics.json for measured held-out results; artifacts/config.json records seed 42, selection criterion, training time and thresholds. Train/validation/test proportions are 70/15/15. Preprocessing is fitted on training data only. Model selection never uses test scores.

## Limitations
Synthetic data; low recall means failures may be missed. Anomaly score is not failure probability. Not intended for safety-critical control or production diagnosis.

## Reproduction
Run train.ps1 to retrain; evaluate.ps1 evaluates saved weights and frozen test split. CPU inference is deterministic within float32 tolerance.
