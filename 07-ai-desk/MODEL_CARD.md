# AI Desk / Karta systemu / System card

## PL — przeznaczenie

Lokalny asystent do wyszukiwania w dokumentach fikcyjnej firmy Antillia North. Wspiera polski i angielski. Odbiorcy: pracownicy, redaktorzy bazy wiedzy i administratorzy. Nie służy do porad medycznych, prawnych ani automatycznych decyzji personalnych.

Wyszukiwanie używa gotowego `paraphrase-multilingual-MiniLM-L12-v2`: 384 wymiary, normalizacja L2, cosine similarity. Fragmenty mają do 1000 znaków i nakładają się o 150 znaków. Cztery najlepsze fragmenty z wynikiem ≥ 0.38 trafiają do modelu. Embedding ma ograniczenie tokenów modelu; bardzo długie fragmenty mogą zostać skrócone przy wektoryzacji.

Generacja: lokalny `qwen3.5:4b` przez Ollama, temperature 0.1, maksymalnie 700 tokenów, kontekst 8192. Nazwa nie zastępuje identyfikatora wag: digest instalacji jest zapisywany podczas live evaluation. Nie przeprowadzono treningu LLM. Model nie posiada narzędzi, dostępu do powłoki ani przeglądarki.

Dane: 20 autorskich tematów, każdy w PL i EN. To dokumentacja demonstracyjna, nie prawdziwe zasady firmy Antillia. Testy nie stanowią niezależnego benchmarku. Scenariusze zawierają powtórzenia pytań bezpieczeństwa, co jawnie ogranicza ich różnorodność.

Wyniki: patrz `evaluation/retrieval-results.json`, `evaluation/live-results.json` oraz `evaluation-tests.txt`. Brak pliku oznacza, że danej ewaluacji nie wykonano. Liczba poprawnych retrieval nie jest miarą poprawności odpowiedzi LLM.

## EN — intended use and limitations

Local document assistant for a fictional organisation. SQL permission filtering occurs before retrieval; ordinary users cannot retrieve administrator evidence. Chat ownership is checked for reads, deletion and generation. Stored assistant answers are withheld if their source permissions are later revoked.

Citation validation checks identifiers, not entailment. A valid citation can still accompany an inaccurate interpretation. The interface explicitly asks users to inspect evidence. Prompt instructions reduce injection risk but do not prove resistance to every attack. Permissions and lack of tools form the security boundary.

The threshold is a fixed demonstration heuristic, not a calibrated probability. Retrieval-only evaluation and transport-success checks are reported separately from human assessment. No externally certified performance or benchmark leaderboard position is claimed.

The system runs offline after installation; no paid API is required. The embedding model is Apache-2.0, provided by Sentence Transformers. Source: https://huggingface.co/sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2 . Ollama weights are external to this package and retain their own license. No production compliance certification is implied.

Retrieval update: hybrid ranking adds at most 0.22 for exact title-term overlap to cosine similarity. This addresses short policy headings; scores are ranking scores, not probabilities. The initial pure-embedding run missed 16 of 40 topic prompts before this change; final reports describe the revised system, not an untouched holdout benchmark.

Observed live limitation: four document-injection examples attached valid but semantically imprecise source IDs to facts supported by other retrieved chunks. The system passed forbidden-text checks but does not guarantee per-citation entailment. See evaluation/qualitative-review.md.
