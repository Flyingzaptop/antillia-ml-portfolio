# Antillia — ML Portfolio

Семь самостоятельных локальных исследовательских проектов: шесть ML-систем и AI-ассистент. Интерфейсы PL/EN, польский по умолчанию. Исходники, данные, сохранённые веса и отчёты находятся внутри каждой папки.

## После git clone

Выполните `restore-assets.ps1`, чтобы загрузить сохранённые модели и данные из релиза. Затем запустите `setup.ps1` внутри нужного проекта. Готовые самостоятельные ZIP доступны в релизе. Презентационные страницы: [index.html](index.html), [инструкция](CASE_STUDIES.md).

## Открыть на этом компьютере

В PowerShell из папки Portfolio:

```powershell
.\start.ps1
# Один проект:
.\start.ps1 -Project 03-terravision
# Остановить запущенные общим launcher серверы:
.\stop.ps1
```

Общий launcher не завершает неизвестные процессы и не занимает уже занятые порты. Для AI Desk должен работать локальный Ollama с моделью `qwen3.5:4b` (на этом компьютере она подготовлена). Если Ollama не запущен, откройте приложение Ollama либо выполните `ollama serve` в отдельном терминале. Общий launcher не останавливает Ollama.

| Проект | Локальный адрес | Исходники и инструкция | Архив |
|---|---|---|---|
| DemandCast | http://127.0.0.1:8101 | [README](01-demandcast/README.md) | [ZIP](https://github.com/Flyingzaptop/antillia-ml-portfolio/releases/download/v1.0.0/01-demandcast.zip) |
| IntentRoute | http://127.0.0.1:8102 | [README](02-intentroute/README.md) | [ZIP](https://github.com/Flyingzaptop/antillia-ml-portfolio/releases/download/v1.0.0/02-intentroute.zip) |
| TerraVision | http://127.0.0.1:8103 | [README](03-terravision/README.md) | [ZIP](https://github.com/Flyingzaptop/antillia-ml-portfolio/releases/download/v1.0.0/03-terravision.zip) |
| MachineSentinel | http://127.0.0.1:8104 | [README](04-machinesentinel/README.md) | [ZIP](https://github.com/Flyingzaptop/antillia-ml-portfolio/releases/download/v1.0.0/04-machinesentinel.zip) |
| BasketWise | http://127.0.0.1:8105 | [README](05-basketwise/README.md) | [ZIP](https://github.com/Flyingzaptop/antillia-ml-portfolio/releases/download/v1.0.0/05-basketwise.zip) |
| ReviewPulse | http://127.0.0.1:8106 | [README](06-reviewpulse/README.md) | [ZIP](https://github.com/Flyingzaptop/antillia-ml-portfolio/releases/download/v1.0.0/06-reviewpulse.zip) |
| AI Desk | http://127.0.0.1:8107 | [README](07-ai-desk/README.md) | [ZIP](https://github.com/Flyingzaptop/antillia-ml-portfolio/releases/download/v1.0.0/07-ai-desk.zip) |

## Перенос на другой компьютер

Windows, Python 3.12 и Node.js 24. Распакуйте нужный ZIP. Внутри его единственной папки:

```powershell
.\setup.ps1
.\run.ps1
# При необходимости: .\run.ps1 -Port 8201
```

Остановка отдельного сервера: Ctrl+C. Архивы независимы: соседние проекты и общий launcher им не нужны. `.venv` и `node_modules` в архивы не включены; они устанавливаются из фиксированных зависимостей. Первоначальная установка требует сети. После подготовки сохранённые модели работают локально без платных API.

Для AI Desk на новом компьютере также установите Ollama и один раз загрузите `ollama pull qwen3.5:4b`. Веса языковой модели принадлежат общей службе Ollama и не дублируются в ZIP. Готовый encoder поиска включён. После setup случайные пароли трёх ролей находятся в `demo-credentials.json`; этот файл, секреты и живая БД не входят в архив. Setup создаёт новую демонстрационную базу из 20 тем в PL/EN.

## Проверки и результаты

- [Итоговый статус](FINAL_STATUS.json): чистые установки, проверки архивов и состояние поставки.
- [Подробные доказательства переноса](reports/packaging/summary.json).
- В каждой папке `reports/` находятся метрики, model cards/отчёты, тесты, аудит зависимостей и снимки интерфейса.
- Сценарии ассистента: [live-results.json](07-ai-desk/evaluation/live-results.json), [содержательный разбор](07-ai-desk/evaluation/qualitative-review.md).
- `verify.ps1` запускает backend-тесты всех проектов. Скрипты `evaluate.ps1` внутри ML-проектов пересчитывают сохранённые результаты. `train.ps1` переобучает и перезаписывает артефакты — сначала сохраните исходную папку.

## Измеренные ограничения

1. **DemandCast:** сезонный baseline выиграл у boosting и GRU. Тестовый MAE 66,01 проката/час; исторический эксперимент одного города, не прогноз текущего спроса.
2. **IntentRoute:** macro-F1 90,74% на английском BANKING77. Польская контрольная выборка содержит всего 12 авторских примеров; accuracy 66,67%. Это не полноценный польский benchmark.
3. **TerraVision:** accuracy 96,57%, macro-F1 96,45% на EuroSAT. Перенос на новые регионы не доказан. Grad-CAM не устанавливает причинность.
4. **MachineSentinel:** PR-AUC 0,2665; при выбранном пороге recall 29,41%, precision 24,59%. Модель пропускает значительную часть отказов; данные синтетические, применять как систему промышленной безопасности нельзя.
5. **BasketWise:** NDCG@10 0,0990 против 0,0442 у популярности. Кандидаты ограничены 1600 товарами train-каталога; рост продаж не измерялся.
6. **ReviewPulse:** macro-F1 91,78%, PR-AUC 96,28% на английском тесте. Только положительный/отрицательный классы; нет нейтрального. Польская диагностика — 16 авторских примеров.
7. **AI Desk:** 70/70 завершённых live-потоков, 67/70 проверок retrieval. Три общих польских вопроса вызвали отказ за недостатком уверенного поиска. В четырёх adversarial-примерах отмечены неточные привязки отдельных утверждений к конкретной цитате, хотя нужные факты были среди найденных фрагментов. Проверка существования ID не доказывает смысловую поддержку каждого утверждения. История сохраняется, но предыдущие реплики не передаются LLM; поиск выполняется заново для каждого вопроса. SSE выдаётся после проверки цитат, а не непосредственно во время генерации.

Это завершённые локальные демонстраторы с измеренными границами, а не сертифицированные production-системы. Публичное размещение, внешний аудит, нагрузочные испытания и физические устройства iOS/Android не входят в проверенную поставку. Адаптивность проверена в браузере на 390/768/1440 px; reduced motion проверен по CSS, без эмуляции настройки ОС. Сканирование зависимостей фиксирует известные уязвимости на момент проверки и не гарантирует отсутствие будущих.
