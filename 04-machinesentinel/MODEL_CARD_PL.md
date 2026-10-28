# MachineSentinel — karta modelu

Zastosowanie: edukacja, badania i demonstracja portfolio.

Dane: AI4I 2020; https://archive.ics.uci.edu/dataset/601/ai4i+2020+predictive+maintenance+dataset

Podział 70/15/15, seed 42. Przetwarzanie dopasowano na danych treningowych. Wybór modelu i progów wyłącznie na walidacji. Wyniki testowe, błędy i czas treningu: reports/report.html, metrics.json oraz artifacts/config.json.

Ograniczenia: Dane syntetyczne. Model może przeoczyć awarie; wynik anomalii nie jest prawdopodobieństwem awarii. Nie stosować do sterowania bezpieczeństwem.

Odtworzenie: train.ps1; ocena zapisanych wag: evaluate.ps1.
