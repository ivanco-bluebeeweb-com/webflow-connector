# Webflow Connector — Preparation

**Статус:** Фаза 1 (Discovery + архитектурные решения) завершена. Влад
заявил объём релиза уже в первом сообщении по задаче 2026-08-20 —
«максимальный функционал, полный максимум» (Ярус 1+2+3). Переходим к
реализации.

**Владелец продукта:** vlad@bluebeeweb.com
**Дата подготовки:** 2026-08-20, v0.1
**Vikunja task:** #2203 (BBW Imperal Apps), [App Development].

**Почему сейчас:** Webflow — ведущая no-code платформа для маркетинговых
сайтов/лендингов с собственным хостингом и CMS. Прямое пересечение с
контентно-SEO вертикалью Imperal (Content Strategy Hub, Media Studio,
Article Writer, SEO Audit Engine, Page Speed Insights) — реальные клиенты
агентства работают на Webflow, а не только на WordPress. Коннектор закрывает
для Webflow ту же нишу «публикация и управление сайтом», которую WordPress
Hub закрывает для WP-стека.

---

## 1. Паспорт приложения

**Название в Marketplace (display_name): «Webflow»**. Внутренний
app_id/папка: `webflow-connector`.

**Webflow Connector** — коннектор к Webflow Data API v2. BYOK:
пользователь подключает свой(и) сайт(ы) собственным Site Token
(сгенерированным в Site Settings → Apps & integrations), опционально
Workspace Token для read-only кросс-сайтовой аналитики. Imperal ничего не
хостит и не проксирует, кроме самого запроса.

## 2. Проблема в человеческих словах

> Когда **маркетолог/владелец агентства** ведёт сайт на Webflow, ему
> приходится **вручную заходить в Webflow Designer/Editor, чтобы
> опубликовать сгенерированную статью в CMS, проверить статус форм,
> перенести кастомный код или обработать заказ**, из-за чего теряется
> время на переключение контекста и нет единой точки, где видно и сайт на
> Webflow, и остальной SEO/контент-конвейер Imperal одновременно.

## 3. Пользователи, роли и права

- **Владелец агентства/маркетолог** — подключает Site Token, публикует
  контент из Content Strategy Hub/Article Writer напрямую в CMS Collection,
  следит за формами и заказами, управляет редиректами/robots.txt.
- **SEO-специалист** — читает пейджи/коллекции для аудита, находит
  неопубликованные (staged) items, управляет 301-редиректами.
- **Val (Imperal Cloud)** — получатель эскалаций по платформенным багам
  (тот же паттерн, что и остальные коннекторы).

## 4. Сценарии и точки решения человека

Основной сценарий:

```text
триггер: готова статья в Article Writer
  → действие человека: просит Webbee опубликовать в Webflow CMS
  → действие приложения: create_collection_item (staged) → показывает draft
  → review/approval человека: подтверждает публикацию
  → действие приложения: publish_collection_item (live)
  → результат: статья видна на живом сайте
```

- happy path: item создан staged → опубликован live → доступен по URL.
- missing/error path: неверный collection_id / несуществующее обязательное
  поле схемы коллекции → честная ошибка с именем недостающего поля.
- blocked state: `custom_code` операции — честно сообщают о недоступности
  без OAuth Data Client App (см. §6/§7).
- recovery path: `delete_collection_item` требует явного preview (Webflow
  не имеет soft-delete/trash для CMS, в отличие от WordPress).

## 5. Ценность и измеримый результат

- Публикация контента без выхода из Imperal panel — экономия переключений
  контекста.
- Единый список форм/заявок и заказов Ecommerce на равне с остальными
  каналами лидов (потенциальный мост к Sales Strategy Hub).
- Метрики успеха: доля статей, опубликованных через коннектор вместо
  ручного Designer; число обнаруженных staged-и-забытых items;
  время от готовой статьи до live-публикации.

## 6. Границы: делает / не делает

**Входит в P0 (Ярус 1):** подключение через Site Token, список
сайтов/публикация, список/CRUD коллекций и items (staged+live), список
форм и submissions, список/загрузка assets, список webhooks +
create/delete.

**Не входит / явная граница:**
- `custom_code:read`/`custom_code:write` — реализованы в схемах и клиенте,
  но каждый вызов явно и честно отвечает, что требует OAuth Data Client
  App (не Site Token) — сама OAuth-регистрация Imperal как Webflow-app
  выходит за рамки написания кода этого коннектора.
- Полноценный Designer/Browser API (визуальное редактирование канвы) —
  отдельный продукт Webflow (JS SDK внутри Designer), архитектурно не
  REST-совместим с моделью «агент вызывает функцию» — вне охвата.
- Enterprise Audit Logs / Workspace Management — доступны только на
  Enterprise-плане и Workspace Token; включены как опциональный Ярус 2
  раздел, деградирующий в честную ошибку на не-Enterprise токене.
- Destructive-операции (delete site page/collection/item, delete asset) —
  обязательный preview-паттерн перед выполнением.

## 7. Данные, конфиденциальность и интеграции

- Хранится: только сам Site Token / Workspace Token (через `ctx.secrets`,
  зашифрованно, тот же паттерн, что WordPress Hub/MuleSoft/n8n).
- Источник данных: сайты/коллекции/формы/заказы — всё остаётся в самом
  Webflow, коннектор ничего не зеркалирует локально, кроме
  read-through-запросов.
- Retention: нет собственного хранилища контента — только секрет токена.
- Tenant isolation: секрет скопирован per-user через штатный `ctx.secrets`.
- Все интеграции статус `available` — Webflow Data API v2 полностью
  документирован и стабилен (см. `CONNECTOR_DISCOVERY.md`), кроме
  `custom_code:*` = `blocked` (OAuth-only, вне охвата этого захода).
- **Обязательный подшаг выполнен:** `CONNECTOR_DISCOVERY.md` построен
  2026-08-20 по методологии `CONNECTOR_DISCOVERY_STANDARD.md`, три яруса
  зафиксированы, объём выбран Владом заранее.

## 8. P0 — минимальный законченный полезный путь

- Главный use case: подключить сайт → опубликовать статью в CMS Collection
  → опубликовать сайт целиком.
- Сущности: connection (Site Token), Site, Collection, CollectionItem.
- Server-side safety gates: preview перед delete_collection_item/
  delete_collection/publish_site (публикация сайта — необратимое действие
  с реальными последствиями для живых посетителей).
- Исключено из P0: custom code, Designer API, Enterprise Audit Logs.
- Acceptance: пользователь может подключить сайт, увидеть список
  коллекций, создать/опубликовать item, увидеть его в списке published.

## 9. UX-карта Imperal panel

- Точка входа: сайдбар «Webflow» → форма подключения (Site Token, опц.
  Workspace Token) с помощью-панелью, где взять токен.
- Первый экран после подключения: список подключённых сайтов + быстрый
  переход к коллекциям выбранного сайта.
- Primary next action: «Опубликовать в CMS» / «Посмотреть формы».
- Empty state: «Сайтов не найдено — проверь права токена».
- Blocked state (custom_code): явное сообщение с ссылкой на
  `developers.webflow.com/data/reference/oauth-app`.
- App settings: единственная secondary-кнопка внизу сайдбара, список
  подключений + disconnect, по `UI_INTERFACE_STANDARD.md`.

## 10. Safety, approvals и audit trail

- Webbee может сама: читать сайты/коллекции/items/форм/заказов, создавать
  staged CMS items (не live).
- Только предложить + explicit confirmation: publish_site,
  publish_collection_items, delete_* (нет undo/trash в Webflow CMS).
- Named human approval не требуется (не финансовый/юридический процесс) —
  но публикация сайта затрагивает живых посетителей, поэтому всегда через
  подтверждение, не автоматически.
- Fail closed: если токен не имеет нужного scope — честная ошибка с
  именем недостающего scope, не тихий пропуск.

## 11. Discovery и проверка гипотезы

Discovery выполнен как систематический обход официальной документации
(`CONNECTOR_DISCOVERY.md`), а не интервью — паттерн, принятый для всех
инфраструктурных коннекторов портфеля (MuleSoft/UiPath/Automation
Anywhere/Blue Prism). Живой пилот — собственные проекты агентства на
Webflow, если такие появятся после релиза.

## 12. План воплощения и live-критерии

| Срез | Статус |
|---|---|
| Discovery (`CONNECTOR_DISCOVERY.md`) | `designed` |
| Preparation (этот файл) | `designed` |
| Код (app/schemas/client/handlers/panels) | `planned` → далее по ходу сессии |
| Локальные тесты / `imperal validate` | `planned` |
| Deploy | `planned` |
| Сквозной пост-аудит (Часть C стандарта) | `planned` |
| Сценарийное тестирование (`SCENARIO_TESTS.md`) | `planned` |
| Прайсинг (`update_pricing` до `submit_for_review`) | `planned` |
| Submit for review | `planned` |

### Куда развивать дальше и почему

| Priority | Срез | Entry condition |
|---|---|---|
| P1 | OAuth Data Client App регистрация → разблокировать `custom_code:*` | Реальный запрос клиента на управление кастомным кодом через чат, а не через Designer |
| P2 | Прямой мост Content Strategy Hub → `sync_content_to_webflow` как штатная функция самого Content Strategy Hub (не только Webflow Connector) | После того как ≥1 реальный сайт агентства работает на Webflow и используется конвейер публикации |
| P3 | Enterprise Workspace Audit Logs / multi-site Workspace Token режим | Клиент на Enterprise-плане Webflow с несколькими сайтами в одном workspace |

## 13. Decision log

| # | Вопрос | Решение | Обоснование |
|---|---|---|---|
| 1 | BYOK или центральный брокер? | **BYOK** | Тот же паттерн, что WordPress Hub/MuleSoft/n8n — пользователь управляет своим Webflow-аккаунтом. |
| 2 | Какой токен по умолчанию? | **Site Token** (Workspace Token — опциональный второй режим) | Генерируется мгновенно самим пользователем, без approval-процесса, аналог WP Application Password. |
| 3 | Custom Code раздел? | Реализован в схемах/клиенте, но с честным blocked-статусом без OAuth App | Единственная пара scope'ов, недоступная Site Token — задокументированная граница, не тихий пропуск. |
| 4 | Объём релиза? | **«Максимум» = Ярус 1+2+3** | Влад заявил в первом сообщении задачи. |
| 5 | Ecommerce/Enterprise разделы? | Включены в Ярус 2 с честной деградацией на не-подходящем плане/токене | Часть официального API, но не у каждого сайта есть Ecommerce/Enterprise — ошибка должна быть понятной, не крашем. |

## 14. Live verification log

_Заполняется по ходу Части C цикла воплощения (deploy → install → manual
panel flow)._
