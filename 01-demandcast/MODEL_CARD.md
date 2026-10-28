# DemandCast — Model card PL / EN

## Cel / Purpose
Prognozowanie popytu / Demand forecasting

## Dane / Data
UCI Bike Sharing, CC BY 4.0
https://doi.org/10.24432/C5W894

## Protokół / Protocol
168 godzin historii i znany kalendarz. Podział czasowy 70/15/15; horyzont 24 h. Przyszła pogoda wykluczona. / 168 historical hours and known calendar. Chronological 70/15/15 split; 24-hour horizon; no future weather.

## Model
Selected on validation: seasonal

## Ograniczenia / Limitations
Baseline sezonowy wygrał na walidacji. GRU była trenowana, ale uzyskała gorsze wyniki. Dane historyczne jednego miasta nie potwierdzają uogólnienia. / Seasonal baseline won validation. The trained GRU performed worse. One historical city does not establish generalization.

## Wyniki / Results
Measured results: reports/results-flat.csv and reports/experiment-report.pdf. Reproduce with evaluate.ps1. Training provenance and split manifests are in artifacts/.
