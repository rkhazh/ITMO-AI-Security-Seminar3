# Отчет по безопасности LiteLLM v1.81.9-stable

## Статус выполнения

Исследование проведено 2026-04-09. Запущены 4 инструмента: Bandit (успешно), Semgrep (успешно), pip-audit/OSV (успешно с ограничениями), skillscan-security (неприменим). Все артефакты сохранены в `artifacts/`.

---

## 1. Executive Summary

Проведен tool-based security assessment проекта LiteLLM v1.81.9-stable (commit `a09d3e91`) с использованием Bandit, Semgrep, pip-audit (с прямым запросом к OSV API) и skillscan-security.

Всего обнаружено **356 Bandit-предупреждений**, **9 Semgrep-находок** и **15 уязвимостей в зависимостях** (CVE/GHSA). После ручного триажа:

- **Подтвержденных проблем**: 4 (использование `exec()` для пользовательского кода guardrails, wildcard CORS `*`, уязвимости в aiohttp 3.13.3 с 10 CVE, JWT decode без верификации подписи)
- **Потенциальных проблем**: 6 (SQL-запросы через string formatting, XML parsing без defusedxml, MD5 для хеширования, HTTP-запросы без timeout, binding на 0.0.0.0, уязвимости в cryptography/Pillow/orjson/pyjwt)
- **Ложных срабатываний / шума**: ~340 (B110 try/except/pass, B101 assert, B105 tokenizer-строки, B311 random для не-security целей)
- **Неприменимых**: skillscan-security не подходит для данного типа проекта

Главные риски: выполнение произвольного кода через `exec()` в guardrails, множественные уязвимости в aiohttp (CRLF injection, header leaks, DoS), wildcard CORS в proxy-сервере. Главное ограничение: инструменты не покрывают runtime-логику авторизации, multi-tenant isolation, SSRF, prompt injection и обход guardrails.

---

## 2. Scope и допущения


| Параметр                 | Значение                                         |
| ------------------------ | ------------------------------------------------ |
| Проект                   | LiteLLM                                          |
| Версия                   | v1.81.9-stable                                   |
| Commit                   | `a09d3e9162ebd7b436a68e92c2b9b6c070fa72d8`       |
| Дата анализа             | 2026-04-09                                       |
| ОС                       | macOS Darwin 25.3.0 arm64                        |
| Python                   | 3.14.2                                           |
| Анализируемая директория | `litellm-v1.81.9/litellm/` (исходный код пакета) |


**Что входило в анализ:**

- Статический анализ Python-кода пакета `litellm/`
- Анализ прямых зависимостей из `requirements.txt` (68 пакетов)
- Оценка применимости skillscan-security

**Что НЕ входило:**

- Тестовый код (`tests/`)
- Docker-конфигурации
- Frontend/UI код
- Runtime-тестирование
- Анализ транзитивных зависимостей
- Пентест/DAST
- Ручной code review бизнес-логики

**Покрытие инструментами:**

- Bandit: паттерн-матчинг уязвимостей Python (без taint analysis)
- Semgrep: семантический анализ с taint tracking, OWASP Top 10
- pip-audit/OSV: известные CVE в зависимостях
- skillscan-security: неприменим (см. раздел 4.4)

---

## 3. Методология

### 3.1 Подготовка

```bash
git clone --depth 1 --branch v1.81.9-stable https://github.com/BerriAI/litellm.git litellm-v1.81.9
python3 -m venv venv-security
source venv-security/bin/activate
pip install bandit semgrep pip-audit
```

### 3.2 Bandit

```bash
bandit -r litellm-v1.81.9/litellm/ -f json -o artifacts/bandit/bandit_full.json
bandit -r litellm-v1.81.9/litellm/ -f txt -o artifacts/bandit/bandit_summary.txt
```

### 3.3 Semgrep

```bash
semgrep --config p/python --config p/security-audit --config p/owasp-top-ten \
  litellm-v1.81.9/litellm/ --json -o artifacts/semgrep/semgrep_full.json
semgrep --config p/python --config p/security-audit --config p/owasp-top-ten \
  litellm-v1.81.9/litellm/ --text -o artifacts/semgrep/semgrep_summary.txt
```

### 3.4 pip-audit

Прямой запуск `pip-audit -r requirements.txt` завершился ошибкой из-за несовместимости пакета `redisvl==0.4.1` с Python 3.14. Альтернативно: выполнен прямой запрос к OSV API (api.osv.dev) для каждого из 68 пинированных пакетов.

```bash
# Оригинальная команда (неудачная):
pip-audit -r litellm-v1.81.9/requirements.txt --format json --output artifacts/pip-audit/pip_audit_full.json
# Причина: redisvl==0.4.1 не поддерживает Python 3.14, ddtrace==2.19.0 не собирается

# Альтернатива: прямой запрос OSV API
# Скрипт: для каждого пакета из requirements.txt POST на https://api.osv.dev/v1/query
```

### 3.5 skillscan-security

Проведен анализ исходного кода инструмента из `/Users/bitcoin/ITMO/AI Security/skillscan/`. Инструмент не запускался по причинам, описанным в разделе 4.4.

### 3.6 Triage-процесс

Для каждого finding:

1. Проверка, относится ли finding к коду LiteLLM (не к vendor/test файлам)
2. Чтение исходного кода в контексте finding
3. Оценка exploitability с учетом архитектуры LiteLLM (proxy/gateway)
4. Классификация: confirmed / potential / false positive / not applicable

---

## 4. Результаты по инструментам

### 4.1 Bandit

**Версия:** 1.9.4
**Применимость:** Полная. Bandit эффективен для Python-проектов.
**Команда:** `bandit -r litellm-v1.81.9/litellm/ -f json`

#### Summary


| Severity  | Count   |
| --------- | ------- |
| HIGH      | 2       |
| MEDIUM    | 26      |
| LOW       | 328     |
| **Total** | **356** |


#### Релевантные findings


| #   | Test ID | Severity | Confidence | File                                                                                                                                      | Line                    | Описание                                                  | Статус                                             |
| --- | ------- | -------- | ---------- | ----------------------------------------------------------------------------------------------------------------------------------------- | ----------------------- | --------------------------------------------------------- | -------------------------------------------------- |
| 1   | B102    | MEDIUM   | HIGH       | `proxy/guardrails/guardrail_endpoints.py`                                                                                                 | 1415                    | `exec()` для выполнения пользовательского кода guardrails | **Confirmed**                                      |
| 2   | B102    | MEDIUM   | HIGH       | `proxy/guardrails/guardrail_hooks/custom_code/custom_code_guardrail.py`                                                                   | 153                     | `exec()` для компиляции custom guardrail code             | **Confirmed**                                      |
| 3   | B324    | HIGH     | HIGH       | `proxy/spend_tracking/spend_tracking_utils.py`                                                                                            | 136, 140                | MD5 для хеширования response objects                      | **Potential**                                      |
| 4   | B608    | MEDIUM   | LOW        | `proxy/management_endpoints/user_agent_analytics_endpoints.py`                                                                            | 121, 212, 314, 434, 548 | SQL-запросы через f-string formatting (5 мест)            | **Potential**                                      |
| 5   | B608    | MEDIUM   | LOW        | `proxy/utils.py`                                                                                                                          | 2173, 2625              | SQL-запросы через f-string formatting                     | **Potential**                                      |
| 6   | B608    | MEDIUM   | LOW        | `integrations/focus/database.py`                                                                                                          | 61                      | SQL-запрос через f-string (с параметризованным limit)     | **Potential**                                      |
| 7   | B314    | MEDIUM   | HIGH       | `litellm_core_utils/prompt_templates/factory.py`                                                                                          | 2360                    | XML parsing через `ET.fromstring()` без defusedxml        | **Potential**                                      |
| 8   | B104    | MEDIUM   | MEDIUM     | `proxy/proxy_cli.py:315`, `constants.py:315`, `llms/custom_httpx/http_handler.py:810,891,1180`                                            | —                       | Binding на `0.0.0.0`                                      | **Not applicable** (ожидаемое поведение для proxy) |
| 9   | B113    | MEDIUM   | LOW        | `proxy/client/teams.py:62,119,140`, `proxy/client/users.py:20,30,41,50`, `proxy/guardrails/guardrail_hooks/hiddenlayer/hiddenlayer.py:43` | —                       | HTTP-запросы без timeout                                  | **Potential**                                      |
| 10  | B615    | MEDIUM   | HIGH       | `llms/petals/completion/handler.py`                                                                                                       | 100                     | HuggingFace Hub download без revision pinning             | **Potential**                                      |


#### Ложные срабатывания / шум (340 findings)


| Test ID   | Count | Причина                                                                                    |
| --------- | ----- | ------------------------------------------------------------------------------------------ |
| B110      | 144   | `try/except/pass` — паттерн для опциональных зависимостей, допустим в gateway-проекте      |
| B105      | 53    | «Hardcoded passwords» — это LLM-токенизаторные строки (`<s>`, `</s>`, `<|begin_of_text|>`) |
| B101      | 51    | `assert` — используется в non-production контексте                                         |
| B311      | 31    | `random` — для request ID, sampling, не для security                                       |
| B112      | 15    | `try/except/continue` — аналогично B110                                                    |
| B106      | 11    | Hardcoded password args — false positive, это default parameter names                      |
| B404      | 8     | Import subprocess — информационный, не vulnerability                                       |
| B603/B607 | 13    | Subprocess calls — для prisma CLI и внутренних утилит, контролируемый ввод                 |


### 4.2 Semgrep

**Версия:** 1.157.0
**Применимость:** Полная. Semgrep с наборами правил p/python, p/security-audit, p/owasp-top-ten.
**Команда:** `semgrep --config p/python --config p/security-audit --config p/owasp-top-ten litellm-v1.81.9/litellm/`

#### Summary


| Severity  | Count |
| --------- | ----- |
| ERROR     | 3     |
| WARNING   | 6     |
| **Total** | **9** |


#### Все findings


| #   | Rule ID                           | Severity | File                                                                    | Line | Описание                                                     | Статус                                                                            |
| --- | --------------------------------- | -------- | ----------------------------------------------------------------------- | ---- | ------------------------------------------------------------ | --------------------------------------------------------------------------------- |
| 1   | `exec-detected`                   | WARNING  | `proxy/guardrails/guardrail_endpoints.py`                               | 1415 | Использование `exec()` для выполнения пользовательского кода | **Confirmed**                                                                     |
| 2   | `exec-detected`                   | WARNING  | `proxy/guardrails/guardrail_hooks/custom_code/custom_code_guardrail.py` | 153  | `exec()` для compile custom code                             | **Confirmed**                                                                     |
| 3   | `unverified-jwt-decode`           | ERROR    | `proxy/management_endpoints/ui_sso.py`                                  | 194  | JWT decode с `verify_signature=False`                        | **Confirmed** (с оговоркой — см. ниже)                                            |
| 4   | `unverified-jwt-decode`           | ERROR    | `proxy/management_endpoints/ui_sso.py`                                  | 2570 | JWT decode с `verify_signature=False`                        | **Confirmed** (с оговоркой)                                                       |
| 5   | `use-defused-xml`                 | ERROR    | `litellm_core_utils/prompt_templates/factory.py`                        | 7    | Import `xml.etree.ElementTree` вместо `defusedxml`           | **Potential**                                                                     |
| 6   | `wildcard-cors`                   | WARNING  | `proxy/proxy_server.py`                                                 | 1214 | CORS `allow_origins=["*"]`                                   | **Confirmed**                                                                     |
| 7   | `insecure-hash-algorithm-md5`     | WARNING  | `proxy/spend_tracking/spend_tracking_utils.py`                          | 136  | MD5 hash                                                     | **Potential**                                                                     |
| 8   | `insecure-hash-algorithm-md5`     | WARNING  | `proxy/spend_tracking/spend_tracking_utils.py`                          | 140  | MD5 hash (fallback)                                          | **Potential**                                                                     |
| 9   | `directly-returned-format-string` | WARNING  | `proxy/pass_through_endpoints/common_utils.py`                          | 15   | Format string в возвращаемом значении                        | **False positive** (это не Flask route, а utility function для извлечения header) |


#### Оговорка по JWT (findings #3, #4)

Код в `ui_sso.py:194` выполняет `jwt.decode(access_token_str, options={"verify_signature": False})`. Комментарий в коде (строка 2568-2569) указывает: "signature is already verified by fastapi_sso". Это означает, что верификация подписи выполнена на предыдущем этапе SSO-обработки. Статус: **confirmed как code smell** — лучшая практика требует повторной верификации или явного документирования причины, но при корректной работе fastapi_sso это не эксплуатируемая уязвимость.

#### Корреляция Semgrep и Bandit


| Finding               | Bandit              | Semgrep                                 |
| --------------------- | ------------------- | --------------------------------------- |
| `exec()` в guardrails | B102 (2 места)      | `exec-detected` (2 места)               |
| MD5 hash              | B324 (2 места)      | `insecure-hash-algorithm-md5` (2 места) |
| XML parsing           | B314 (1 место)      | `use-defused-xml` (1 место)             |
| JWT unverified        | —                   | `unverified-jwt-decode` (2 места)       |
| CORS wildcard         | —                   | `wildcard-cors` (1 место)               |
| SQL injection         | B608 (8 мест)       | —                                       |
| HTTP no timeout       | B113 (8 мест)       | —                                       |
| Subprocess calls      | B603/B607 (13 мест) | —                                       |


**Уникальные для Semgrep:** JWT decode без верификации (2), CORS wildcard (1)
**Уникальные для Bandit:** SQL f-string formatting (8), HTTP requests без timeout (8), subprocess calls (13)
**Пересечение:** exec() (2), MD5 (2), XML parsing (1)

### 4.3 pip-audit / OSV API

**Версия pip-audit:** 2.9.0
**Применимость:** Частичная. Прямой запуск pip-audit невозможен из-за несовместимости `redisvl==0.4.1` и `ddtrace==2.19.0` с Python 3.14. Альтернативно использован прямой запрос к OSV API.

**Файл зависимостей:** `requirements.txt` (68 пинированных пакетов)

#### Команда (оригинальная, неудачная)

```bash
pip-audit -r litellm-v1.81.9/requirements.txt --format json --output artifacts/pip-audit/pip_audit_full.json
# EXIT CODE: 1
# Причина: redisvl==0.4.1 — нет совместимой версии для Python 3.14
#           ddtrace==2.19.0 — не собирается wheel на Python 3.14
```

**Stderr сохранен:** `artifacts/pip-audit/pip_audit_stderr.log`

#### Альтернативная команда (OSV API)

```python
# Для каждого пакета из requirements.txt:
requests.post('https://api.osv.dev/v1/query', json={
    "package": {"name": pkg, "ecosystem": "PyPI"}, "version": ver
})
```

#### Findings (15 уязвимостей в 5 пакетах)


| #   | Package      | Version | Advisory            | CVE            | Severity | Fix Version | Relevance для LiteLLM                                                                                           | Статус                            |
| --- | ------------ | ------- | ------------------- | -------------- | -------- | ----------- | --------------------------------------------------------------------------------------------------------------- | --------------------------------- |
| 1   | aiohttp      | 3.13.3  | GHSA-2vrm-gr82-f7m5 | CVE-2026-34514 | —        | 3.13.4      | **Высокая** — CRLF injection через multipart content-type. LiteLLM активно использует aiohttp для HTTP-запросов | **Confirmed**                     |
| 2   | aiohttp      | 3.13.3  | GHSA-3wq7-rqq7-wx6j | CVE-2026-34517 | —        | 3.13.4      | **Средняя** — Memory DoS через multipart. Актуально при обработке multimodal-запросов                           | **Confirmed**                     |
| 3   | aiohttp      | 3.13.3  | GHSA-63hf-3vf5-4wqf | CVE-2026-34520 | —        | 3.13.4      | **Высокая** — null bytes в response headers, header injection                                                   | **Confirmed**                     |
| 4   | aiohttp      | 3.13.3  | GHSA-966j-vmvw-g2g9 | CVE-2026-34518 | —        | 3.13.4      | **Высокая** — утечка Cookie и Proxy-Authorization на cross-origin redirect. Критично для proxy                  | **Confirmed**                     |
| 5   | aiohttp      | 3.13.3  | GHSA-c427-h43c-vf67 | CVE-2026-34525 | —        | 3.13.4      | **Средняя** — duplicate Host headers, request smuggling вектор                                                  | **Confirmed**                     |
| 6   | aiohttp      | 3.13.3  | GHSA-hcc4-c3v8-rx92 | CVE-2026-34513 | —        | 3.13.4      | **Средняя** — DoS через unbounded DNS cache                                                                     | **Confirmed**                     |
| 7   | aiohttp      | 3.13.3  | GHSA-m5qp-6w8w-w647 | CVE-2026-34516 | —        | 3.13.4      | **Средняя** — Multipart header size bypass                                                                      | **Confirmed**                     |
| 8   | aiohttp      | 3.13.3  | GHSA-mwh4-6h8g-pg8w | CVE-2026-34519 | —        | 3.13.4      | **Высокая** — HTTP response splitting через \r в reason phrase                                                  | **Confirmed**                     |
| 9   | aiohttp      | 3.13.3  | GHSA-p998-jp59-783m | CVE-2026-34515 | —        | 3.13.4      | **Низкая** — UNC SSRF на Windows. LiteLLM обычно на Linux                                                       | **Not applicable** (Windows only) |
| 10  | aiohttp      | 3.13.3  | GHSA-w2fm-2cpv-w7v5 | CVE-2026-22815 | —        | 3.13.4      | **Средняя** — unlimited trailer headers, memory DoS                                                             | **Confirmed**                     |
| 11  | cryptography | 44.0.1  | GHSA-m959-cc7f-wv43 | CVE-2026-34073 | —        | 46.0.6      | **Средняя** — incomplete DNS name constraint. Зависит от использования X.509                                    | **Potential**                     |
| 12  | cryptography | 44.0.1  | GHSA-r6ph-v2qm-q3c2 | CVE-2026-26007 | —        | 46.0.5      | **Низкая** — subgroup attack на SECT curves. Специфичный вектор                                                 | **Potential**                     |
| 13  | Pillow       | 11.0.0  | GHSA-cfh3-3jmp-rvhc | CVE-2026-25990 | —        | 12.1.1      | **Низкая** — out-of-bounds write при PSD. LiteLLM обрабатывает изображения ограниченно                          | **Potential**                     |
| 14  | orjson       | 3.11.2  | GHSA-hx9q-6w63-j58v | CVE-2025-67221 | —        | 3.11.6      | **Средняя** — бесконечная рекурсия на глубоко вложенном JSON. DoS-вектор для proxy                              | **Potential**                     |
| 15  | pyjwt        | 2.10.1  | GHSA-752w-5fwx-jx9f | CVE-2026-32597 | —        | 2.12.0      | **Средняя** — unknown `crit` header extensions принимаются. Зависит от JWT-конфигурации                         | **Potential**                     |


### 4.4 skillscan-security

**Версия:** из репозитория [https://anonymous.4open.science/r/skillscan/](https://anonymous.4open.science/r/skillscan/)
**Применимость:** **Неприменим** к LiteLLM.

#### Причины неприменимости

1. **Несовпадение формата входных данных.** skillscan ожидает предварительно скраулленные данные о skills из маркетплейсов (skills.rest, skillsmp.com) в формате JSON (`all_skills_data.json` с ID навыков и метаданными). LiteLLM — не skill, а инфраструктурный Python-проект.
2. **Отсутствие необходимой CLI-зависимости.** Ядро сканирования — внешний бинарник `skill-security-scan`, который не входит в состав репозитория skillscan и требует отдельной установки. Этот инструмент предназначен для сканирования отдельных skill-пакетов, не произвольных Python-кодовых баз.
3. **Несоответствие проверяемых угроз.** Правила skillscan (обнаружение data exfiltration, privilege escalation в контексте skills, prompt injection в описаниях навыков) ориентированы на оценку недоверенных сторонних skill-пакетов, а не на аудит инфраструктуры LLM-proxy.
4. **MCP-компоненты LiteLLM.** LiteLLM включает MCP-серверную функциональность (`mcp==1.25.0`), но выступает КАК MCP-сервер, а не как skill/plugin для агента. skillscan сканирует skills ДЛЯ агентов, а не агентскую инфраструктуру.

#### Вывод

skillscan-security не дает security-value для аудита LiteLLM. Это не неудача инструмента — это корректное несоответствие threat model. Артефакт: `artifacts/skillscan/applicability_analysis.txt`.

---

## 5. Консолидированный список findings

### Confirmed


| ID   | Заголовок                                                      | Источник                            | Категория                       | Severity   | Confidence | Affected Component            | File/Package                                                                                                                | Evidence                                                                                                                 | Почему важно                                                                                                                                                                                   | Условия эксплуатации                                                                                          | Remediation                                                                                        | Статус                                                           |
| ---- | -------------------------------------------------------------- | ----------------------------------- | ------------------------------- | ---------- | ---------- | ----------------------------- | --------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------- |
| F-01 | Выполнение произвольного кода через exec() в custom guardrails | Bandit B102 + Semgrep exec-detected | Guardrails / Policy Enforcement | **High**   | High       | Custom code guardrail system  | `proxy/guardrails/guardrail_endpoints.py:1415`, `proxy/guardrails/guardrail_hooks/custom_code/custom_code_guardrail.py:153` | `exec(compile(request.custom_code, "<guardrail>", "exec"), exec_globals)` с попыткой sandbox через пустые `__builtins__` | LiteLLM принимает пользовательский Python-код для guardrails и выполняет его. Sandbox через `__builtins__ = {}` легко обходится (через `().__class__.__bases__[0].__subclasses__()` и аналоги) | Необходим доступ к API создания/тестирования guardrails (предположительно admin-доступ)                       | Использовать AST-based whitelist вместо exec(), или sandboxed execution через subprocess/контейнер | **Confirmed**                                                    |
| F-02 | Wildcard CORS в proxy-сервере                                  | Semgrep wildcard-cors               | Аутентификация и авторизация    | **Medium** | High       | FastAPI CORS middleware       | `proxy/proxy_server.py:1214` (переменная `origins` на строке 1032)                                                          | `origins = ["*"]`, `allow_credentials=True`                                                                              | Позволяет любому origin выполнять запросы к proxy. В сочетании с `allow_credentials=True` это нарушение best practices (хотя браузеры блокируют wildcard + credentials)                        | Эксплуатируется при наличии браузерного доступа к proxy                                                       | Настроить allow_origins через конфигурацию, ограничить доверенными доменами                        | **Confirmed**                                                    |
| F-03 | 10 уязвимостей в aiohttp 3.13.3                                | pip-audit/OSV                       | Supply chain / зависимости      | **High**   | High       | HTTP-клиент (core dependency) | `aiohttp==3.13.3`                                                                                                           | CVE-2026-34514/17/18/19/20/25, CVE-2026-34513/16, CVE-2026-22815                                                         | LiteLLM активно использует aiohttp для всех HTTP-запросов к LLM-провайдерам. Уязвимости включают CRLF injection, header leaks на redirect, response splitting, DoS                             | Зависит от конкретного CVE: некоторые требуют контроля над ответами сервера, другие — над входящими запросами | Обновить `aiohttp>=3.13.4`                                                                         | **Confirmed**                                                    |
| F-04 | JWT decode без верификации подписи                             | Semgrep unverified-jwt-decode       | Аутентификация и авторизация    | **Medium** | Medium     | SSO authentication flow       | `proxy/management_endpoints/ui_sso.py:194`, `proxy/management_endpoints/ui_sso.py:2570`                                     | `jwt.decode(token, options={"verify_signature": False})`                                                                 | JWT декодируется без проверки подписи. Код комментирует, что верификация выполнена ранее (fastapi_sso), но это создает хрупкую зависимость от порядка вызовов                                  | Если SSO flow изменится и verify будет пропущен на предыдущем этапе, подделка JWT становится тривиальной      | Добавить проверку подписи или явный assertion, что token уже верифицирован                         | **Confirmed** (code smell, не эксплуатируемо при корректном SSO) |


### Potential


| ID   | Заголовок                           | Источник                                | Категория                     | Severity   | Confidence | File/Package                                                                                                                                        | Evidence                                                                | Условия                                                                                                                                                                                                                    | Remediation                                       | Статус        |
| ---- | ----------------------------------- | --------------------------------------- | ----------------------------- | ---------- | ---------- | --------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------- | ------------- |
| F-05 | SQL-запросы через string formatting | Bandit B608                             | Изоляция данных               | **Medium** | Low        | `proxy/management_endpoints/user_agent_analytics_endpoints.py:121,212,314,434,548`, `proxy/utils.py:2173,2625`, `integrations/focus/database.py:61` | f-string SQL-запросы с подстановкой значений                            | Зависит от того, контролирует ли пользователь подставляемые значения. В `user_agent_analytics_endpoints.py` `MAX_TAGS` — константа. В `database.py` limit проходит int-валидацию. Требует ручной проверки каждого callsite | Использовать параметризованные запросы            | **Potential** |
| F-06 | XML parsing без defusedxml          | Bandit B314 + Semgrep use-defused-xml   | Guardrails                    | **Medium** | Medium     | `litellm_core_utils/prompt_templates/factory.py:2360`                                                                                               | `ET.fromstring(xml_content)`                                            | XML-содержимое приходит из ответов LLM (tool calling в XML-формате для Claude). Атакующий, контролирующий ответ LLM, может вставить XXE payload                                                                            | Заменить на `defusedxml.ElementTree.fromstring()` | **Potential** |
| F-07 | MD5 для хеширования                 | Bandit B324 + Semgrep insecure-hash-md5 | Защита данных                 | **Low**    | High       | `proxy/spend_tracking/spend_tracking_utils.py:136,140`                                                                                              | `hashlib.md5(json_str.encode()).hexdigest()`                            | Используется для генерации ID spend logs, не для security-целей. Коллизии MD5 могут привести к перезаписи spend-записей                                                                                                    | Заменить на SHA-256                               | **Potential** |
| F-08 | HTTP-запросы без timeout            | Bandit B113                             | Guardrails / Availability     | **Low**    | Low        | `proxy/client/teams.py:62,119,140`, `proxy/client/users.py:20,30,41,50`, `proxy/guardrails/guardrail_hooks/hiddenlayer/hiddenlayer.py:43`           | `requests.get(url)` / `requests.post(url)` без параметра timeout        | Потенциальный DoS при зависании внешнего сервиса                                                                                                                                                                           | Добавить timeout=30 или аналогичный               | **Potential** |
| F-09 | Уязвимости в cryptography 44.0.1    | pip-audit/OSV                           | Supply chain                  | **Medium** | Medium     | `cryptography==44.0.1`                                                                                                                              | CVE-2026-34073 (DNS name constraints), CVE-2026-26007 (subgroup attack) | Зависит от использования X.509 сертификатов и SECT curves в LiteLLM                                                                                                                                                        | Обновить до `cryptography>=46.0.6`                | **Potential** |
| F-10 | Уязвимость в orjson 3.11.2          | pip-audit/OSV                           | Supply chain                  | **Medium** | Medium     | `orjson==3.11.2`                                                                                                                                    | CVE-2025-67221 — бесконечная рекурсия на глубоко вложенном JSON         | LiteLLM использует orjson для сериализации embedding-ответов. Специально сконструированный ответ LLM-провайдера может вызвать DoS                                                                                          | Обновить до `orjson>=3.11.6`                      | **Potential** |
| F-11 | Уязвимость в pyjwt 2.10.1           | pip-audit/OSV                           | Supply chain / Аутентификация | **Medium** | Medium     | `pyjwt==2.10.1`                                                                                                                                     | CVE-2026-32597 — принятие unknown `crit` header extensions              | Может позволить обход JWT-валидации при определенных конфигурациях                                                                                                                                                         | Обновить до `pyjwt>=2.12.0`                       | **Potential** |
| F-12 | Уязвимость в Pillow 11.0.0          | pip-audit/OSV                           | Supply chain                  | **Low**    | Low        | `Pillow==11.0.0`                                                                                                                                    | CVE-2026-25990 — out-of-bounds write при загрузке PSD                   | LiteLLM использует Pillow для обработки изображений, но PSD-файлы маловероятны в штатном workflow                                                                                                                          | Обновить до `Pillow>=12.1.1`                      | **Potential** |


### False Positive / Not Applicable (резюме)


| Категория               | Count | Источник         | Причина отклонения                                           |
| ----------------------- | ----- | ---------------- | ------------------------------------------------------------ |
| try/except/pass         | 144   | Bandit B110      | Паттерн для опциональных импортов, допустим                  |
| try/except/continue     | 15    | Bandit B112      | Аналогично B110                                              |
| Hardcoded «passwords»   | 53    | Bandit B105      | LLM-tokenizer строки: `<s>`, `</s>`, `<|begin_of_text|>`     |
| assert usage            | 51    | Bandit B101      | Не в production-critical paths                               |
| random                  | 31    | Bandit B311      | Используется для request IDs, log sampling — не security     |
| Hardcoded password args | 11    | Bandit B106      | Default parameter names, не фактические пароли               |
| Import subprocess       | 8     | Bandit B404      | Информационный, не vulnerability                             |
| Subprocess calls        | 13    | Bandit B603/B607 | Вызовы prisma CLI и внутренних утилит с контролируемым input |
| Binding 0.0.0.0         | 5     | Bandit B104      | Ожидаемое поведение proxy-сервера                            |
| Format string return    | 1     | Semgrep          | Utility function, не Flask route                             |
| SSRF на Windows         | 1     | pip-audit/OSV    | aiohttp CVE-2026-34515, применим только к Windows            |


---

## 6. Неприменимость и ограничения

### 6.1 Что НЕ может быть доказано использованными инструментами


| Риск                        | Покрытие | Комментарий                                                                                                                            |
| --------------------------- | -------- | -------------------------------------------------------------------------------------------------------------------------------------- |
| Runtime authorization logic | Нет      | Bandit/Semgrep не анализируют runtime-поведение. RBAC, team-based access control, API key scoping требуют динамического тестирования   |
| Multi-tenant isolation      | Нет      | Изоляция данных между tenants, утечки ключей между командами — бизнес-логика, не покрываемая SAST                                      |
| SSRF через LLM-запросы      | Нет      | LiteLLM как proxy может быть использован для SSRF к внутренним сервисам. Это архитектурный risk, не детектируемый статическим анализом |
| Prompt injection в runtime  | Нет      | Обход guardrails, jailbreak через prompt — семантическая атака, не покрываемая SAST                                                    |
| Логические баги gateway     | Нет      | Rate limiting bypass, request smuggling через LiteLLM, model access control — требуют пентеста                                         |
| Реальные обходы guardrails  | Нет      | Custom code guardrails выполняются через exec() (F-01), но реальная проверка обхода требует runtime-тестирования                       |
| Timing attacks на JWT       | Нет      | Статический анализ не оценивает timing side-channels                                                                                   |
| Secret management в runtime | Частично | Bandit нашел B105/B106, но фактическое хранение секретов (env vars, vault, database) — за пределами SAST                               |


### 6.2 skillscan-security

skillscan-security не дал security-value для этой задачи. Инструмент предназначен для оценки untrusted AI agent skills из маркетплейсов, а не для аудита инфраструктурного кода LLM-proxy. Подробный анализ неприменимости в разделе 4.4.

### 6.3 pip-audit

pip-audit не смог выполнить полный resolution зависимостей из-за несовместимости `redisvl==0.4.1` и `ddtrace==2.19.0` с Python 3.14. Были использованы прямые запросы к OSV API как альтернатива, но транзитивные зависимости не проанализированы.

---

## 7. Приоритеты исправления

### Quick Wins (низкие усилия, высокий эффект)

1. **Обновить aiohttp до >=3.13.4** — закрывает 10 CVE, включая CRLF injection и header leaks. Одно изменение в `requirements.txt`.
2. **Обновить orjson до >=3.11.6** — закрывает DoS через рекурсивный JSON. Одно изменение.
3. **Обновить pyjwt до >=2.12.0** — закрывает CVE-2026-32597. Важно в контексте SSO/JWT-based auth.
4. **Добавить timeout к HTTP-запросам** в `proxy/client/teams.py`, `proxy/client/users.py`, `proxy/guardrails/guardrail_hooks/hiddenlayer/hiddenlayer.py`.

### Structural Fixes (требуют архитектурных решений)

1. **Пересмотреть exec() в custom guardrails** (F-01). Текущий sandbox (`__builtins__ = {}`) недостаточен. Варианты:
  - AST-based whitelist с ограниченным набором операций
  - Выполнение в subprocess с ограничениями (seccomp/AppArmor)
  - Использование `llm-sandbox` (уже в зависимостях) для изолированного выполнения
2. **Настроить CORS** (F-02). Заменить `origins = ["*"]` на конфигурируемый список доверенных origins. Учесть, что wildcard + credentials не работает в браузерах, но это нарушение принципа least privilege.
3. **Заменить XML parsing** на defusedxml (F-06). Низкий приоритет, так как XML приходит из ответов LLM, но cost of fix минимален.

### Dependency Remediation

1. **Обновить cryptography до >=46.0.6** — два CVE, но exploitability зависит от использования X.509.
2. **Обновить Pillow до >=12.1.1** — OOB write, но вектор через PSD маловероятен.
3. **Провести полный аудит транзитивных зависимостей** на совместимой версии Python (3.12/3.13).

---

## 8. Приложения

### 8.1 Команды запуска

```bash
# Клонирование
git clone --depth 1 --branch v1.81.9-stable https://github.com/BerriAI/litellm.git litellm-v1.81.9

# Окружение
python3 -m venv venv-security
source venv-security/bin/activate
pip install bandit semgrep pip-audit

# Bandit
bandit -r litellm-v1.81.9/litellm/ -f json -o artifacts/bandit/bandit_full.json
bandit -r litellm-v1.81.9/litellm/ -f txt -o artifacts/bandit/bandit_summary.txt

# Semgrep
semgrep --config p/python --config p/security-audit --config p/owasp-top-ten \
  litellm-v1.81.9/litellm/ --json -o artifacts/semgrep/semgrep_full.json
semgrep --config p/python --config p/security-audit --config p/owasp-top-ten \
  litellm-v1.81.9/litellm/ --text -o artifacts/semgrep/semgrep_summary.txt

# pip-audit (неудачная попытка)
pip-audit -r litellm-v1.81.9/requirements.txt --format json --output artifacts/pip-audit/pip_audit_full.json
# EXIT CODE: 1 (redisvl==0.4.1 not found for Python 3.14)

# pip-audit альтернатива (OSV API)
# Python-скрипт: POST https://api.osv.dev/v1/query для каждого пакета
```

### 8.2 Версии инструментов


| Инструмент         | Версия                                                                                                                |
| ------------------ | --------------------------------------------------------------------------------------------------------------------- |
| Python             | 3.14.2                                                                                                                |
| Bandit             | 1.9.4                                                                                                                 |
| Semgrep            | 1.157.0                                                                                                               |
| pip-audit          | 2.9.0                                                                                                                 |
| skillscan-security | из [https://anonymous.4open.science/r/skillscan/](https://anonymous.4open.science/r/skillscan/) (без версионирования) |


### 8.3 Артефакты


| Файл                                             | Описание                                |
| ------------------------------------------------ | --------------------------------------- |
| `artifacts/metadata.txt`                         | Метаданные сканирования                 |
| `artifacts/bandit/bandit_full.json`              | Полный JSON-вывод Bandit (356 findings) |
| `artifacts/bandit/bandit_summary.txt`            | Human-readable summary Bandit           |
| `artifacts/bandit/bandit_stderr.log`             | stderr Bandit                           |
| `artifacts/semgrep/semgrep_full.json`            | Полный JSON-вывод Semgrep (9 findings)  |
| `artifacts/semgrep/semgrep_summary.txt`          | Human-readable summary Semgrep          |
| `artifacts/semgrep/semgrep_stderr.log`           | stderr Semgrep                          |
| `artifacts/pip-audit/pip_audit_stderr.log`       | stderr оригинального pip-audit          |
| `artifacts/pip-audit/osv_results.json`           | Результаты OSV API (15 vulnerabilities) |
| `artifacts/pip-audit/requirements_filtered.txt`  | Отфильтрованный requirements.txt        |
| `artifacts/skillscan/applicability_analysis.txt` | Анализ неприменимости skillscan         |


### 8.4 Файлы зависимостей


| Файл                                     | Назначение                                                     |
| ---------------------------------------- | -------------------------------------------------------------- |
| `requirements.txt`                       | Основной файл зависимостей (68 пакетов, проанализирован)       |
| `pyproject.toml`                         | Конфигурация проекта (не содержит дополнительных зависимостей) |
| `docker/build_from_pip/requirements.txt` | Docker-сборка (не анализировался)                              |
| `.circleci/requirements.txt`             | CI/CD зависимости (не анализировались)                         |


---

## Сырые результаты, требующие дальнейшей ручной проверки

### 1. SQL injection через f-string (F-05)

Требуется ручная проверка 8 мест в коде, где SQL-запросы формируются через f-string. Для каждого необходимо проверить:

- Контролирует ли пользователь подставляемые значения
- Есть ли валидация на уровне endpoint (Pydantic models, type hints)
- Возможен ли path от HTTP request до SQL-запроса

Файлы для проверки:

- `proxy/management_endpoints/user_agent_analytics_endpoints.py` (строки 121, 212, 314, 434, 548) — используется `MAX_TAGS` (константа) и параметры с Prisma query. Вероятно **low risk**, но требует подтверждения.
- `proxy/utils.py` (строки 2173, 2625) — требует проверки источников данных
- `integrations/focus/database.py` (строка 61) — limit проходит `int()` валидацию, **low risk**

### 2. exec() sandbox bypass (F-01)

Текущий «sandbox»:

```python
exec_globals = get_custom_code_primitives().copy()
exec_globals["__builtins__"] = {}
exec(compile(request.custom_code, "<guardrail>", "exec"), exec_globals)
```

Этот подход известен как обходимый. PoC-идея (не тестировалась на данной версии):

```python
# Через subclasses
().__class__.__bases__[0].__subclasses__()
# Найти os._wrap_close или аналог для exec shell commands
```

Необходимо проверить, какие именно примитивы возвращает `get_custom_code_primitives()` и не содержат ли они дополнительных путей к escape.

### 3. JWT без верификации (F-04)

Код полагается на то, что `fastapi_sso` уже проверил подпись. Если SSO-конфигурация изменится или будет добавлен альтернативный SSO-провайдер без такой гарантии, это создаст критическую уязвимость. Рекомендуется ручной review всего SSO flow.

### 4. aiohttp credential leaks (F-03, CVE-2026-34518)

Наиболее опасная из aiohttp-уязвимостей для LiteLLM: Cookie и Proxy-Authorization headers утекают при cross-origin redirect. Если LLM-провайдер возвращает redirect на третий сервер, credentials могут быть раскрыты. Требуется проверка, использует ли LiteLLM cookies или Proxy-Authorization при запросах к провайдерам.