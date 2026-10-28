# BasketWise — Model card PL / EN

## Cel / Purpose
Rekomendacje produktów / Product recommendations

## Dane / Data
UCI Online Retail, CC BY 4.0
https://doi.org/10.24432/C5BW33

## Protokół / Protocol
Chronologiczny podział dni 70/15/15. Katalog tylko z train. Pełny ranking 1600 produktów; popularity, item-item i SVD. / Chronological day split 70/15/15. Train-only catalog. Full ranking of 1600 products; popularity, item-item and SVD.

## Model
Selected on validation: factorization

## Ograniczenia / Limitations
Ocena ograniczona do znanych produktów nowych dla użytkownika; osobne wyniki cold start. Nie zmierzono wzrostu konwersji. / Evaluation covers known-catalog, new-to-user items, with separate cold start. Conversion uplift was not measured.

## Wyniki / Results
Measured results: reports/results-flat.csv and reports/experiment-report.pdf. Reproduce with evaluate.ps1. Training provenance and split manifests are in artifacts/.
