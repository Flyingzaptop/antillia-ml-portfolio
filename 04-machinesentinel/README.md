# MachineSentinel

Самостоятельная локальная демонстрация машинного обучения.

## Запуск

PowerShell из этой папки: `./setup.ps1`, затем `./run.ps1`. Python 3.12 и Node.js 22.12+ обязательны. Setup требует Интернет, обычный запуск — нет. Frontend и API доступны на http://127.0.0.1:8104. Альтернативный порт: `./run.ps1 -Port 9000`. Остановка: Ctrl+C.

Обучение: `./train.ps1`. Проверка весов на сохранённой тестовой выборке: `./evaluate.ps1`. Тесты: `./.venv/Scripts/python.exe -m pytest tests -q`. По умолчанию используется CPU. Для повторного обучения на GPU установите совместимые PyTorch/torchvision из официального CUDA-индекса PyTorch вместо CPU-пакетов. Обучение не запускается при старте приложения.

## Данные и модель

Источник: AI4I 2020; https://archive.ics.uci.edu/dataset/601/ai4i+2020+predictive+maintenance+dataset. Полный исходный архив находится в data/source.zip. Список выборок: artifacts/splits.json. Конфигурация, выбор модели по validation и checksum источника: artifacts/config.json. Веса в artifacts. Результаты: reports/metrics.json, metrics.csv, report.html. Все метрики вычислены, не заданы вручную.

API: /docs, /openapi.json, /api/v1/health, /api/v1/metrics, /api/v1/examples, /api/v1/predict. Файлы обрабатываются в памяти, имена не используются как пути. Логи запросов содержат случайный request ID без содержимого загрузок. Сервис привязан к localhost; аутентификация для публичного учебного inference не предусмотрена.

## Ограничения

Synthetic data; low recall means failures may be missed. Anomaly score is not failure probability. Not intended for safety-critical control or production diagnosis.

Inference использует только локальные файлы. Не загружайте pickle/weights из недоверенных источников. reports/environment.txt фиксирует фактическую среду эксперимента. requirements.txt — закреплённые зависимости установки; повторяемость допускает различия float32 до 1e-5.

Обучение выполнено на PyTorch 2.5.1; финальный CPU runtime обновлён для безопасности. Проверка метрик после обновления сохраняется в reports/reproducibility.json.
