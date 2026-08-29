# Webflow Connector — UI component plan

Источники: `Docs/session-notes/UI_COMPONENT_VOCABULARY.md`, `UI_INTERFACE_STANDARD.md`,
`concepts/panels.md`. Основано на `POST_CONNECT_EXPERIENCE.md` этого приложения и
существующем `panels.py` (сайдбар без карточек, "App settings" последней кнопкой).

## 1. Компоненты

| Экран | Примитивы | Почему именно эти |
|---|---|---|
| Sidebar (left) | `ui.Column`(align="start") + `ui.Text`(workspace) + `ui.Divider` + navigation `ui.ListItem`(Sites/CMS Collections/Forms/E-commerce) + `ui.Button`("App settings") | Уже закреплено в существующем `panels.py` — plain Stack без Card, App settings последним элементом. |
| Site List (center, `center_overlay=True`) | `ui.DataTable`(name, domain, last published, status Badge published/draft) | Табличный обзор сайтов workspace. |
| CMS Collection List (site detail) | Back-button + `ui.DataTable`(collection name, items count; sortable) | Обзор коллекций CMS внутри сайта. |
| Collection Items Viewer | Back-button + `ui.Stats`(items count/draft/published) + `ui.DataTable`(колонки = поля коллекции, динамически; sortable, editable=True на текстовых/toggle полях) | CMS item — это буквально запись со схемой полей, `DataTable` с editable-колонками закрывает быстрое редактирование прямо из списка. |
| Item Detail (полное редактирование) | Back-button + `ui.Form`(action="update_item") + динамические `ui.Input`/`ui.TextArea`/`ui.Select`/`ui.Toggle` по типу поля схемы + `ui.FileUpload`(image/file поля) + `ui.Button`("Publish") | Форма собирается по схеме коллекции — каждый тип поля Webflow сопоставлен с ближайшим примитивом SDK. |
| Publish Dialog | `ui.Dialog`(title="Опубликовать сайт?", content=`ui.MultiSelect`(target domains), confirm_label="Опубликовать") | Публикация — видимое всем пользователям действие, требует явного подтверждения выбора доменов. |
| Form Submissions Viewer | `ui.DataTable`(submitted_at, form name, fields — динамические колон
... [244 chars elided from this argument for history replay -- the tool received the FULL value] ...
я списка заказов e-commerce (если включён). |
| Order Detail (e-commerce) | Back-button + `ui.KeyValue`(customer/shipping/payment) + `ui.DataTable`(line items, read-only) + `ui.Row`(Button "Fulfill", "Refund") | Стандартный набор для детали заказа. |
| App Settings | `ui.Accordion`([Connections+Disconnect, Default Site Select, Webhooks CRUD]) | Централизованные настройки по стандарту (уже частично реализовано в `panels_settings.py`). |

## 2. User flow (валидно по panel lifecycle)

1. **SESSION INIT** → существующий `__panel__webflow_sidebar` рендерит workspace
   + разделы; `auto_action` открывает Site List для первого сайта или список сайтов.
2. Site List → клик → `ui.Call(site_id=...)` → CMS Collection List на том же
   center handler.
3. Collection List → клик на коллекцию → Collection Items Viewer (DataTable
   с editable-колонками для быстрых правок без открытия формы).
4. Клик на строку (не editable-ячейку) → `ui.Call(item_id=...)` → Item Detail —
   полная форма по схеме коллекции → "Publish" → `Dialog`(выбор доменов) →
   `ui.Call` → `publish_site` → `refresh_panels`.
5. Из сайдбара → Forms/E-commerce — каждый открывает свой раздел на том же
   center handler с новым `view` параметром.
6. "App settings" (нижняя кнопка сайдбара, уже существует) → `panels_settings.py`;
   "Disconnect" там же — единственное деструктивное действие, обёрнуто в `Dialog`.

## 3. Экраны/карточки (конкретно)

- **Screen: Site List** — DataTable(name/domain/last published/status).
- **Screen: CMS Collection List** — DataTable(collection/items count).
- **Screen: Collection Items Viewer** — Stats(3) + DataTable(dynamic columns, editable).
- **Screen: Item Detail** — Form(dynamic fields по схеме) + Button(Publish).
- **Screen: Form Submissions** — DataTable(submitted_at/form/dynamic fields).
- **Screen: Order List / Order Detail** (e-commerce) — DataTable / KeyValue+DataTable+Row.
- **Screen: App Settings** — Accordion(Connections, Default Site, Webhooks).
