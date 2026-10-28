# ReviewPulse — model card / karta modelu

## EN
Purpose: binary sentiment classification for product, movie and restaurant reviews. Intended for local demonstration and supervised exploration. Not suitable for automatic high-stakes decisions. Multilingual frozen MiniLM embeddings plus trained MLP are compared with a TF-IDF logistic-regression baseline. Hyperparameters and model selection use validation macro F1 only. Evaluation on held-out test; detailed metrics, per-class scores, confusion matrix and real error examples are in [report](reports/report.html). An explicit uncertain flag uses a validation-derived score threshold; scores are not calibrated probabilities. Out-of-domain detection is not guaranteed.

The separate author-written Polish control set is small, not representative and not an official benchmark. Data leakage from pretrained encoder pretraining cannot be ruled out. Hardware, training duration, library versions and fixed seed are recorded in `artifacts/training.json`. Dataset/model sources and licenses: [LICENSES](LICENSES.md).

## PL
Zastosowanie: binarna analiza sentymentu opinii o produktach, filmach i restauracjach. Lokalna demonstracja i analiza pod nadzorem człowieka. Model nie służy do samodzielnych decyzji o dużych konsekwencjach. Zamrożony wielojęzyczny MiniLM z wyuczonym MLP porównano z TF-IDF i regresją logistyczną. Wybór modelu i hiperparametrów wykorzystuje wyłącznie walidację. Test pozostaje odłożony. Szczegóły w [raporcie](reports/report.html).

Wyniki pewności nie są skalibrowane. Próg niepewności pochodzi z walidacji, ale nie gwarantuje wykrywania tekstów spoza domeny. Mały autorski zestaw polski jest wyłącznie diagnostyczny. Nie stanowi reprezentatywnego benchmarku ani certyfikacji. Brak gwarancji poprawności dla sarkazmu, nietypowego języka i nowych domen. Brak klasy neutralnej.

## Input window / Okno wejściowe
The encoder truncates input to 128 tokens. Maximum API text length is 2000 characters; content beyond the token window is not analyzed by MiniLM. Encoder analizuje pierwsze 128 tokenów, nawet jeśli zaakceptowany tekst jest dłuższy.
