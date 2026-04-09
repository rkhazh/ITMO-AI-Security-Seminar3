# Security Assessment: LiteLLM v1.81.9-stable

Воспроизводимое исследование безопасности проекта [LiteLLM](https://github.com/BerriAI/litellm) версии v1.81.9-stable с использованием инструментов статического анализа и аудита зависимостей.

## Объект анализа

| Параметр | Значение |
|----------|----------|
| Проект | LiteLLM — unified interface для 100+ LLM-провайдеров |
| Версия | v1.81.9-stable |
| Commit | `a09d3e9162ebd7b436a68e92c2b9b6c070fa72d8` |
| Дата анализа | 2026-04-09 |

## Инструменты

| Инструмент | Версия | Назначение | Результат |
|------------|--------|-----------|-----------|
| [Bandit](https://github.com/pycqa/bandit) | 1.9.4 | SAST для Python (паттерн-матчинг) | 356 findings, 10 релевантных после триажа |
| [Semgrep](https://github.com/semgrep/semgrep) | 1.157.0 | Семантический SAST (taint tracking, OWASP) | 9 findings, 8 релевантных |
| [pip-audit](https://pypi.org/project/pip-audit/) | 2.9.0 | Аудит зависимостей (CVE/GHSA) | 15 уязвимостей в 5 пакетах |
| [skillscan-security](https://anonymous.4open.science/r/skillscan/) | — | Сканер AI agent skills | Неприменим к данному типу проекта |

## Ключевые результаты

- **4 подтвержденные проблемы**: `exec()` в custom guardrails (обходимый sandbox), wildcard CORS, 10 CVE в aiohttp, JWT decode без верификации подписи
- **8 потенциальных проблем**: SQL через f-string, XML без defusedxml, MD5, HTTP без timeout, CVE в cryptography/orjson/pyjwt/Pillow
- **~340 ложных срабатываний** отфильтровано при триаже

Полный отчет: [`report.md`](report.md)

## Структура репозитория

```
.
├── report.md                          # Итоговый отчет
├── artifacts/
│   ├── metadata.txt                   # Метаданные сканирования (OS, Python, версии)
│   ├── bandit/
│   │   ├── bandit_full.json           # Полный JSON-вывод Bandit
│   │   ├── bandit_summary.txt         # Human-readable summary
│   │   └── bandit_stderr.log          # stderr
│   ├── semgrep/
│   │   ├── semgrep_full.json          # Полный JSON-вывод Semgrep
│   │   ├── semgrep_summary.txt        # Human-readable summary
│   │   └── semgrep_stderr.log         # stderr
│   ├── pip-audit/
│   │   ├── osv_results.json           # Результаты запроса OSV API
│   │   ├── pip_audit_stderr.log       # stderr оригинального запуска
│   │   └── ...                        # Промежуточные артефакты
│   └── skillscan/
│       └── applicability_analysis.txt # Анализ неприменимости
└── skillscan/                         # Исходный код skillscan-security
```

## Воспроизведение

```bash
# 1. Клонировать исходный код LiteLLM
git clone --depth 1 --branch v1.81.9-stable https://github.com/BerriAI/litellm.git litellm-v1.81.9

# 2. Создать окружение и установить инструменты
python3 -m venv venv-security
source venv-security/bin/activate
pip install bandit semgrep pip-audit

# 3. Bandit
bandit -r litellm-v1.81.9/litellm/ -f json -o artifacts/bandit/bandit_full.json
bandit -r litellm-v1.81.9/litellm/ -f txt -o artifacts/bandit/bandit_summary.txt

# 4. Semgrep
semgrep --config p/python --config p/security-audit --config p/owasp-top-ten \
  litellm-v1.81.9/litellm/ --json -o artifacts/semgrep/semgrep_full.json

# 5. pip-audit (требует Python <=3.13 для полного resolution)
pip-audit -r litellm-v1.81.9/requirements.txt --format json
```

> **Примечание:** pip-audit не разрешает зависимости на Python 3.14 из-за `redisvl==0.4.1` и `ddtrace==2.19.0`. В данном исследовании использован прямой запрос к [OSV API](https://api.osv.dev/) как альтернатива.
