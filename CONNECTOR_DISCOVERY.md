# Webflow Connector — Connector Discovery

**Дата discovery:** 2026-08-20
**Статус:** Ярусы 1-3 пройдены (свежее чтение официальной документации developers.webflow.com, 2026-08-20). §7 (решение по объёму) — Влад уже явно заявил объём в первом сообщении по задаче #2203 ("максимальный функционал, полный максимум") → исключение Шага 5 применяется, переспрашивать не требуется. Берём Ярус 1 + Ярус 2 + Ярус 3.

---

## 1. Целевой сервис и источники

Webflow — визуальный no-code/low-code билдер сайтов с собственным хостингом и встроенной CMS. В отличие от MuleSoft/Tray, у Webflow **один согласованный REST API** — Data API v2 (v1 deprecated), с открытой OpenAPI 3.1 спецификацией и полным llms.txt-индексом — можно было систематически обойти все разделы, а не собирать по памяти.

Источники (прочитаны 2026-08-20):
- `developers.webflow.com/data/reference/rest-introduction`, `/structure-1` — общая архитектура ресурсов
- `developers.webflow.com/data/reference/authentication`, `/authentication/site-token`, `/oauth-app`, `/authentication/workspace-token` — три модели токенов
- `developers.webflow.com/data/reference/scopes` — полная таблица site-level и workspace-level scope'ов
- `developers.webflow.com/data/reference/rate-limits`, `/error-handling`, `/versioning`
- `developers.webflow.com/llms.txt` и `developers.webflow.com/data/v2.0.0/llms.txt` — полный индекс разделов Data API v2 (Sites, Pages & Components, CMS, Assets, Custom Code, Ecommerce, Webhooks, Comments, Site Configuration, Enterprise)
- `help.webflow.com/hc/en-us/articles/33961356296723-Intro-to-Webflow-s-APIs`

## 2. Модель авторизации — критичное архитектурное решение

Webflow предлагает **три типа токена**, и выбор не тривиален:

| Тип | Как получить | Область действия | Когда использовать |
|---|---|---|---|
| **Site Token** | Владелец/админ сайта генерирует вручную в Site Settings → Apps & integrations → API access — без внешнего OAuth-редиректа | Один конкретный сайт | Внутренние инструменты, single-site интеграции, полный контроль у пользователя |
| **Workspace Token** | Аналогично, но на уровне Workspace | Read-only доступ ко ВСЕМ сайтам воркспейса | Мониторинг/аудит нескольких сайтов разом |
| **OAuth Data Client App** | Полноценный OAuth 2.0 authorization code flow, приложение должно быть зарегистрировано как Webflow App | Multi-tenant, произвольные сайты произвольных пользователей | Публичные Marketplace-приложения Webflow, встраивание для чужих конечных пользователей |

**Решение: Site Token как основной BYOK-механизм** — тот же паттерн, что уже использован в WordPress Hub (Application Password), MuleSoft/n8n/Power Automate/UiPath (Connected App / API key). Пользователь генерирует токен сам за 30 секунд, без стороннего approval-процесса — никакой курицы-и-яйца, как у Zapier.

**Опционально Workspace Token** — как второй, дополнительный режим подключения для read-only кросс-сайтовой аналитики/аудита (не заменяет Site Token, а расширяет).

**⚠️ ГРАНИЦА ЯРУСА, подтверждено таблицей scopes:** `custom_code:read` / `custom_code:write` (управление кастомным JS/CSS сайта и отдельных страниц) — единственная пара ресурсов, доступная **только через OAuth Data Client App**, Site Token её не даёт. Это осознанно выносится в Custom Code раздел с пометкой "недоступно в этом заходе без полноценной OAuth-регистрации приложения в Webflow Marketplace" — аналог границы Platform/Embedded API у Tray.io.

## 3. Карта возможностей (по scope-группам API, направление на каждую)

| Группа ресурсов | Возможность | Ingress/Egress/Both | Комментарий |
|---|---|---|---|
| **Sites** | List sites, get site, publish site | Both | Базовый уровень — какие сайты видит токен, деплой на прод |
| **Pages** | List pages, get page metadata, get/update page content (static text on a page) | Both | Работа со страницами сайта вне CMS |
| **Components** | List components, get component, get/update component content/properties | Both | Переиспользуемые визуальные блоки Webflow (Components feature) |
| **CMS — Collections** | List/get collections, create/delete collection, list/create/delete collection fields | Both | Схема контентной модели сайта |
| **CMS — Collection Items** | List/get/create/update/delete items (staged), list/get live items, publish items | Both | Основная рабочая лошадка — реальный контент (посты блога, товары, кейсы) |
| **Assets** | List/get assets, upload asset, create/list asset folders | Both | Медиатека сайта |
| **Custom Fonts** | List custom fonts, upload font | Both | Шрифты, загруженные в проект |
| **Forms** | List forms, list form submissions | Ingress | Заявки с форм сайта — прямая интеграция с Sales Strategy Hub/CRM |
| **Comments** | List comment threads, list comments, moderate/reply | Both | Комментарии в Webflow Editor (contributor workflow) |
| **Custom Code** | Get/apply/remove custom code (site-level, page-level) | Both | ⚠️ Только OAuth Data Client — Site Token недостаточно, см. §2 |
| **Ecommerce** | List/get products+SKUs, create/update product, list/get/update orders, inventory, ecommerce settings | Both | Полноценный WooCommerce-аналог для сайтов с Webflow Ecommerce |
| **Webhooks** | Create/list/get/delete webhook, ~14 типов событий (site_publish, form_submission, collection_item_created/changed/deleted, ecommerce_order_created и др.) | Both | Событийная интеграция вместо поллинга |
| **Site Configuration** | 301 redirects (CRUD), robots.txt override, well-known files | Both | SEO/техническая конфигурация сайта |
| **Users** (Webflow Memberships) | List/get/update users сайта с включённым Memberships | Both | Управление доступом к закрытому контенту сайта |
| **Site Activity** | Get site activity log | Ingress | История изменений на сайте |
| **Workspace (Enterprise)** | List workspaces, workspace members, audit logs | Ingress | Административный уровень организации — Enterprise-only |
| **Authorized User / Token Introspect** | Get info about the current token/user | Ingress | Диагностика подключения |

## 4. Классификация по типу функционала (Шаг 1 стандарта)

- **Ingress (сильный)**: Forms submissions, Site Activity, Webhooks (входящие события), Comments (чтение), Audit Logs, token introspect — то, что коннектор в первую очередь должен уметь *принимать/показывать*.
- **Egress (сильный)**: publish site, create/update/delete CMS items, publish CMS items to live, upload asset, create redirect, update Ecommerce order status, reply to comment, create webhook — реальные операции с последствиями на живом сайте.
- **Both**: Collections/Fields (создать схему = запись, прочитать = чтение), Users/Memberships, Custom Code.

## 5. Ярус 1 — Ключевые функции (P0-кандидаты)

Ближайший аналог "подключить сайт + управлять контентом + видеть заявки", по образцу WordPress Hub (`connect_site`/`list_posts`/`create_post`) и уже существующих BYOK-коннекторов:

1. `connect_webflow` / `disconnect_webflow` — Site Token (+ опционально Workspace Token режим)
2. `list_sites` / `get_site` — какие сайты видит токен
3. `publish_site` — задеплоить черновик на прод
4. `list_collections` / `get_collection` — схема CMS сайта
5. `list_collection_items` / `get_collection_item` — контент
6. `create_collection_item` / `update_collection_item` / `delete_collection_item`
7. `publish_collection_items` — вывести staged-изменения в live (Webflow CMS двухфазный: staged → live)
8. `list_forms` / `list_form_submissions` — входящие заявки с сайта
9. `list_pages` / `get_page_content`
10. `upload_asset` / `list_assets`

## 6. Ярус 2 — Полное покрытие

| Возможность | Статус | Причина/триггер |
|---|---|---|
| Sites: list/get/publish | included | Ярус 1 |
| Pages: list/get, get/update content | included | Естественное расширение — тот же HTTP-клиент, WordPress Hub имеет прямой аналог (`update_post`) |
| Components: list/get, get/update content+properties | included | Прямое расширение Pages — тот же паттерн вызовов |
| CMS Collections: list/get/create/delete, fields CRUD | included | Полное покрытие схемы — нужно для настройки новых типов контента без захода в UI |
| CMS Items: полный CRUD + staged/live различие + publish | included | Ярус 1 расширенный до полноты (bulk create, live variant отдельным полем) |
| Assets: list/get/upload, folders | included | Естественное расширение Ярус 1 |
| Custom Fonts: list/upload | included | Малая добавка поверх Assets-клиента |
| Forms: list forms/submissions | included | Ярус 1 |
| Comments: list threads/comments, moderate, reply | included | Прямой аналог `list_comments`/`reply_to_comment` из WordPress Hub/YouTube Studio Hub — уже устоявшийся паттерн в портфеле |
| Custom Code: get/apply/remove | included, но **функционально заблокировано без OAuth App** | Реализуем код клиента и функции сейчас; они будут явно возвращать точную ошибку "требуется OAuth Data Client App, Site Token не поддерживает custom_code scope" до тех пор, пока Imperal не зарегистрирует OAuth-приложение в Webflow Marketplace отдельно (это отдельный организационный шаг вне кода) |
| Ecommerce: Products/SKUs CRUD, Orders list/get/update/fulfill/refund, Inventory, Settings | included | Полноценный аналог WooCommerce-блока WordPress Hub — большая, но полностью документированная поверхность |
| Webhooks: create/list/get/delete, все ~14 событий | included | Событийная интеграция — заменяет поллинг там, где нужен realtime (аналог создания webhook в WordPress Hub) |
| Site Configuration: 301 redirects CRUD, robots.txt, well-known files | included | Прямой аналог Rank Math redirects/robots.txt блока WordPress Hub — уже знакомый паттерн |
| Users/Memberships: list/get/update | included | Управление доступом к gated-контенту — явная бизнес-ценность для сайтов с платным контентом |
| Site Activity: get activity log | included | Read-only диагностика, дешёвая добавка |
| Token introspect / authorized user | included | Диагностика подключения — аналог `check_access` в других коннекторах |
| Workspace-level (list workspaces, members, audit logs) | included, только при Workspace Token | Отдельный опциональный режим подключения — не блокирует Site Token путь |
| Custom Code OAuth App registration сама по себе | not applicable (в этом заходе) | Это отдельная организационная задача (регистрация Imperal как публичного Webflow App в их Marketplace, отдельное ревью Webflow) — вне рамок написания кода коннектора; фиксируется отдельным пунктом на будущее |

## 7. Ярус 3 — Функции на нашей стороне (value-add)

Аналогично `audit_folder`/`audit_cloudhub_environment`/`audit_estate` в UiPath/MuleSoft/Blue Prism — агрегирующие и bulk-обёртки, которых нет как готового эндпоинта у самого Webflow:

- **`audit_site`** — единый отчёт по сайту: список коллекций + количество items в каждой + последняя публикация сайта + количество непрочитанных form submissions + активные webhooks + custom code статус (blocked/active) одним вызовом, вместо ручного обхода 6+ разных эндпоинтов.
- **`bulk_publish_collection_items`** — публикация нескольких items одним вызовом (Webflow API поддерживает batch, но с явными лимитами на размер батча — обёртка разбивает на страницы автоматически).
- **`bulk_create_collection_items`** — массовое наполнение коллекции (например, публикация партии статей из Article Writer / Content Strategy Hub напрямую в Webflow CMS Blog Collection).
- **`find_stale_collection_items`** — находит items, которые остаются в staged (не опубликованы в live) дольше N дней — контент создан, но забыт неопубликованным.
- **`sync_content_to_webflow`** — принимает готовую статью (по формату, совместимому с Article Writer `export_article_text`) и создаёт/обновляет CMS item по маппингу полей — прямой мост между Article Writer и Webflow Blog Collection, аналог того, как WordPress Hub уже принимает контент от Content Strategy Hub.
- **preview-стиль подтверждение перед `delete_collection_item`/`delete_collection`** — у Webflow нет собственного soft-delete/trash для CMS items (в отличие от WordPress), поэтому явный preview слой обязателен для защиты от необратимых действий.

## 8. Решение по объёму этого захода

Влад уже явно заявил объём в первом сообщении по задаче ("максимальный функционал, полный максимум") → правило #2134 п.5 не требует повторного вопроса. Берём:

**Ярус 1 + Ярус 2 + Ярус 3 целиком**, с одной явной оговоркой: раздел Custom Code (2 функции: get/update) будет реализован полностью в коде и схемах, но будет **сразу и честно сообщать пользователю**, что требует OAuth Data Client App вместо Site Token — сама по себе OAuth-регистрация Imperal как Webflow-приложения не является кодовой задачей этого коннектора и выходит за рамки написания кода.

Итоговая оценка объёма: ~55-65 функций (сопоставимо по масштабу с WordPress Hub, самым крупным коннектором портфеля) — оправдано тем, что Webflow Data API v2 действительно один согласованный API без фрагментации (в отличие от MuleSoft/Automation Anywhere), поэтому полное покрытие реалистично за один заход.
