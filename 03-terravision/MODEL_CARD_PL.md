# TerraVision — karta modelu

Zastosowanie: edukacja, badania i demonstracja portfolio.

Dane: EuroSAT RGB, Sentinel-2; https://zenodo.org/records/7711810

Podział 70/15/15, seed 42. Przetwarzanie dopasowano na danych treningowych. Wybór modelu i progów wyłącznie na walidacji. Wyniki testowe, błędy i czas treningu: reports/report.html, metrics.json oraz artifacts/config.json.

Ograniczenia: Losowy podział nie dowodzi skuteczności w nowych regionach. Obrazy spoza domeny mogą być błędnie rozpoznane z dużą pewnością. Grad-CAM nie wskazuje przyczyn.

Odtworzenie: train.ps1; ocena zapisanych wag: evaluate.ps1.
