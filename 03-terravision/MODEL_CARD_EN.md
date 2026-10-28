# TerraVision — model card

## Intended use
Educational research and interactive portfolio demonstration.

## Data
EuroSAT RGB, Sentinel-2; https://zenodo.org/records/7711810

## Evaluation
See reports/report.html and metrics.json for measured held-out results; artifacts/config.json records seed 42, selection criterion, training time and thresholds. Train/validation/test proportions are 70/15/15. Preprocessing is fitted on training data only. Model selection never uses test scores.

## Limitations
Random stratified hash-deduplicated split is not a geographic holdout. RGB only; no multispectral bands. Grad-CAM is associative, not causal. Out-of-domain images may yield confident wrong classes.

## Reproduction
Run train.ps1 to retrain; evaluate.ps1 evaluates saved weights and frozen test split. CPU inference is deterministic within float32 tolerance.
