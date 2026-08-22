# Pricing History — Webflow Connector

Обязательный журнал: каждое выставление или изменение цен на функции этого
приложения фиксируется здесь — что изменилось, почему, и на основании
чего. Не переписывать прошлые записи — только дописывать новые сверху.

---

## 2026-08-22 — первичный прайсинг (per_action, revenue_split_dev=95)

**Порядок соблюдён:** пост-аудит чист, `deploy_app` выполнен ДО прайсинга,
и только ПОСЛЕ этого — прайсинг, ДО `submit_for_review` (канонический
порядок из `PRICING_POLICY.md` §1).

**Карта цен — фиксированная платформенная шкала {0, 8, 16, 20, 40, 60}**
построена по `action_type` + семантике имени для всех функций манифеста
(зеркалирует `tool-prices.json`):

| Цена | Категория | Примеры |
|---|---|---|
| 0 | connect/disconnect/список подключений | `connect_webflow`, `connect_webflow_workspace`, `disconnect_webflow`, `list_connections` |
| 8 | read (list/get) | `list_sites`, `get_site`, `list_pages`, `get_page`, `list_collections`, `get_collection_item` |
| 16 | write простой (create/update/delete одной сущности) | `create_collection`, `update_page_metadata`, `delete_product`, `update_sku` |
| 20 | write с реальным операционным эффектом в проде пользователя | `publish_site`, `publish_collection_items`, `fulfill_order`, `refund_order` |

**Процесс:** приложение было `live`, поэтому потребовался `suspend_app`
перед `update_pricing` (платформенное правило: пока приложение
обслуживает пользователей "мид-флайт", менять цену нельзя). Первый вызов
`update_pricing` вернул ошибку `'connect_webflow'/'connect_webflow_workspace'/
'disconnect_webflow'/'list_connections' unexpectedly still priced` —
расхождение ТОЛЬКО по `free_tools` (0-цены), платные функции сохранились с
первого раза. Немедленный повторный вызов с ИДЕНТИЧНЫМ payload прошёл без
ошибки, цена подтверждена сохранённой. Задокументировано как отдельный
воспроизводимый баг платформы (тот же паттерн пойман в этот день также на
Salesforce/Klaviyo/HubSpot/MuleSoft Connector): задача #2275 (Imperal
Cloud tracker).

После этого: `deploy_app` (21/22, commit fac647ad) → `submit_for_review`
→ статус `pending_review`.
