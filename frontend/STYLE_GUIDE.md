# InvisionU Visual Style Guide

Визуальный стиль извлечён из прототипа (`prototype-frontend/`), который копирует типографию, цветовую гамму и компоненты официального сайта inVision University.

---

## Типографика

### Шрифт

| Свойство | Значение |
|----------|----------|
| Семейство | **Raleway**, Arial, sans-serif |
| Подключение | Google Fonts: `Raleway:wght@400;500;600;700;800` |

### Начертания (font-weight)

| Вес | Использование |
|-----|---------------|
| 400 | Не используется напрямую в прототипе, подключён как резерв |
| 500 | Базовый текст (`body`) |
| 600 | Подключён как резерв |
| 700 | Навигация, кнопки, подписи, мета-текст, chips, pills, badges |
| 800 | Заголовки, бренд, eyebrow-лейблы, значения метрик, имена в строках |

### Размеры текста

| Элемент | Размер |
|---------|--------|
| Body (базовый) | `clamp(1rem, 0.94rem + 0.18vw, 1.125rem)` (16–18px) |
| H1 (главный заголовок) | `clamp(2rem, 1.65rem + 1.8vw, 3.2rem)` (32–51px) |
| H2 (секция) | `clamp(1.8rem, 1.5rem + 1vw, 2.6rem)` (29–42px) |
| H3 (карточка/панель) | `1.12rem` (~18px) |
| Panel title | `1.22rem` (~20px) |
| Summary card value | `1.9rem` (~30px) |
| Queue summary value | `1.16rem` (~19px) |
| Eyebrow / label | `0.76rem` (~12px), uppercase, `letter-spacing: 0.12em` |
| Nav links | `0.98rem` (~16px) |
| Кнопки | `0.96rem` (~15px), small: `0.9rem` |
| Мета/подпись | `0.82rem` (~13px) |
| Pill/tag мелкий | `0.74rem` (~12px) |
| Timeline tag | `0.72rem` (~12px) |

### Letter-spacing

| Контекст | Значение |
|----------|----------|
| Заголовки (h1, h2, h3, brand) | `-0.03em` ... `-0.04em` (сжатый) |
| Eyebrow / uppercase-лейблы | `+0.10em` ... `+0.12em` (разреженный) |

### Line-height

| Контекст | Значение |
|----------|----------|
| Body | `1.4` |
| H3 / card headings | `1.1` |

---

## Цветовая палитра

### Основные цвета бренда

| Токен | Hex | Описание |
|-------|-----|----------|
| `--brand-ink` | `#141414` | Основной тёмный (текст, тёмные карточки, кнопки) |
| `--brand-paper` | `#ffffff` | Основной светлый (фон, текст на тёмных поверхностях) |
| `--brand-lime` | `#c1f11d` | Акцент 1 — зелёно-лаймовый (CTA hover, активные состояния, accent cards) |
| `--brand-blue` | `#3dedf1` | Акцент 2 — циан/бирюзовый (recommend-бейджи, timeline-теги) |
| `--brand-coral` | `#ff8e70` | Акцент 3 — коралловый (manual review, предупреждения) |
| `--brand-purple` | `#b4b0ef` | Акцент 4 — лавандовый (определён, но не используется в текущем прототипе) |

### Текстовые оттенки

| Токен | Значение | Использование |
|-------|----------|---------------|
| `--brand-muted` | `rgba(20, 20, 20, 0.62)` | Вторичный текст, подписи, мета |
| `--brand-muted-strong` | `rgba(20, 20, 20, 0.76)` | Усиленный мета-текст |

### Линии и разделители

| Токен | Значение |
|-------|----------|
| `--brand-line` | `rgba(20, 20, 20, 0.09)` |
| Border карточек | `rgba(20, 20, 20, 0.06)` |
| Border таблиц | `rgba(20, 20, 20, 0.07)` |
| Border chips/inputs | `rgba(20, 20, 20, 0.1)` |

### Поверхности

| Токен | Значение | Использование |
|-------|----------|---------------|
| `--surface-soft` | `rgba(255, 255, 255, 0.88)` | Фон карточек |
| `--surface-strong` | `rgba(255, 255, 255, 0.96)` | Определён как альтернатива |
| Topbar | `rgba(255, 255, 255, 0.78)` + `backdrop-filter: blur(18px)` | Стеклянная навигация |
| Ghost button | `rgba(255, 255, 255, 0.72)` | Полупрозрачная кнопка |
| Chips/input | `rgba(255, 255, 255, 0.78)` – `0.82` | Интерактивные элементы |

### Тени

| Токен | Значение |
|-------|----------|
| `--surface-shadow` | `0 18px 50px rgba(20, 20, 20, 0.07)` |
| Brand mark glow | `0 0 0 5px rgba(193, 241, 29, 0.18)` |

### Семантические цвета для бейджей

| Семантика | Background | Text |
|-----------|-----------|------|
| Strong / Lime | `rgba(193, 241, 29, 0.28)` | `#415005` |
| Recommend / Blue | `rgba(61, 237, 241, 0.18)` | `#0a6a6d` |
| Manual / Coral | `rgba(255, 142, 112, 0.18)` | `#ac472e` |

### Фон страницы (gradient)

```css
background:
  radial-gradient(circle at top left, rgba(193, 241, 29, 0.18), transparent 25%),
  radial-gradient(circle at 100% 0, rgba(61, 237, 241, 0.1), transparent 20%),
  linear-gradient(180deg, #fbfdf6 0%, #ffffff 16%, #f4f7ef 100%);
```

Светлый тёплый фон с едва заметными цветными бликами lime (сверху-слева) и cyan (сверху-справа).

### Lime gradient (accent cards)

```css
background: linear-gradient(180deg, #c1f11d, #defb75);
```

### Brand mark gradient

```css
background: linear-gradient(135deg, var(--brand-lime), var(--brand-blue));
```

---

## Скругления (border-radius)

| Токен | Значение | Использование |
|-------|----------|---------------|
| `--radius-xl` | `1.9rem` | — |
| `--radius-lg` | `1.45rem` | Карточки, панели |
| `--radius-md` | `1.05rem` | Факты, decision items |
| `--radius-sm` | `0.9rem` | — |
| `--radius-pill` | `999px` | Кнопки, chips, pills, badges, meta-items |
| Table inner items | `1rem` | List items, callouts, inputs |
| Queue table | `1rem` | Обёртка таблицы |
| Document row | `0.95rem` | Строки документов |

---

## Компоненты

### Button

Три варианта:

| Вариант | Фон | Текст | Border | Hover |
|---------|-----|-------|--------|-------|
| **Default** | transparent | `--brand-ink` | `1px solid --brand-ink` | `translateY(-1px)` |
| **Dark** (`--dark`) | `--brand-ink` | `--brand-paper` | `--brand-ink` | bg → `--brand-lime`, text → ink |
| **Ghost** (`--ghost`) | `rgba(255,255,255,0.72)` | `--brand-ink` | `--brand-ink` | `translateY(-1px)` |

Общие свойства: `border-radius: 999px`, `font-weight: 700`, `min-width: 10.5rem`, `padding: 0.9rem 1.2rem`.
Small: `min-width: 0`, `padding: 0.72rem 0.95rem`, `font-size: 0.9rem`.

### Card / Panel

Общий стиль для `summary-card`, `ops-panel`, `workspace-panel`, `detail-card`, `rail-card`, `shortlist-card`, `committee-card`, `system-card`:

- `border: 1px solid rgba(20, 20, 20, 0.06)`
- `border-radius: var(--radius-lg)` (1.45rem)
- `background: var(--surface-soft)` (rgba(255,255,255,0.88))
- `box-shadow: var(--surface-shadow)`

Модификаторы:
- `--dark`: bg `--brand-ink`, text `--brand-paper`
- `--lime`: bg `linear-gradient(180deg, #c1f11d, #defb75)`

### Chip / Filter Pill / Sort Chip

- `border-radius: 999px`
- `padding: 0.65rem 0.95rem`
- `border: 1px solid rgba(20, 20, 20, 0.1)`
- `background: rgba(255, 255, 255, 0.78)`
- `font-weight: 700`
- Активное состояние (`is-active`): bg `--brand-ink`, text `--brand-paper`

### Badge / Tag Pill

- `border-radius: 999px`
- `font-weight: 700`
- Badge: `padding: 0.5rem 0.8rem`, `font-size: 0.78rem`
- Tag pill: `padding: 0.34rem 0.6rem`, `font-size: 0.74rem`
- Три цветовые схемы: lime, blue, coral (см. семантические цвета)

### Eyebrow Label

Используется для категорий и секций:
- `font-size: 0.76rem`
- `font-weight: 800`
- `letter-spacing: 0.12em`
- `text-transform: uppercase`
- `color: var(--brand-muted)`

### Search Input

- `padding: 0.92rem 1rem`
- `border: 1px solid rgba(20, 20, 20, 0.1)`
- `border-radius: 1rem`
- `background: rgba(255, 255, 255, 0.82)`
- Label: `font-size: 0.82rem`, `font-weight: 700`

### Queue Table Row

- `padding: 0.95rem 1rem`
- `border-bottom: 1px solid rgba(20, 20, 20, 0.05)`
- Hover/active: `background: linear-gradient(180deg, #ffffff, #fbffeb)`
- Имя: `font-size: 0.95rem`, `font-weight: 800`
- Мета-текст: `font-size: 0.82rem`, `color: var(--brand-muted)`

### Topbar

- Sticky, `z-index: 60`
- `backdrop-filter: blur(18px)`
- `background: rgba(255, 255, 255, 0.78)`
- `border-bottom: 1px solid rgba(20, 20, 20, 0.06)`
- Высота: `min-height: 4.8rem`

### Nav Link Hover

Подчёркивание снизу с анимацией:
- `height: 2px`, `background: var(--brand-lime)`
- `transform: scaleX(0)` → `scaleX(1)`, `transition: 0.35s ease`

---

## Сетка и контейнер

| Свойство | Значение |
|----------|----------|
| Max-width контейнера | `92rem` (1472px) |
| Padding контейнера | `2rem` inline (desktop), `1rem` (mobile <760px) |
| Grid gap (стандартный) | `1rem` |
| Summary strip | 5 колонок |
| Ops board | `1.2fr 0.9fr 0.9fr` (3 колонки) |
| Workspace | `0.95fr 1.25fr 0.8fr` (3 колонки: queue / detail / rail) |
| Workspace meta | 4 колонки |

---

## Переходы и анимации

| Элемент | Свойство | Значение |
|---------|----------|----------|
| Кнопки | transform, bg, color, border | `0.3s ease` |
| Nav underline | transform (scaleX) | `0.35s ease` |
| Queue row hover | background-color | `0.25s ease` |

---

## Brand Mark (логотип)

Круглая точка:
- `width: 1rem`, `height: 1rem`
- `border-radius: 50%`
- `background: linear-gradient(135deg, --brand-lime, --brand-blue)`
- `box-shadow: 0 0 0 5px rgba(193, 241, 29, 0.18)`

Текст бренда: `font-weight: 800`, `letter-spacing: -0.03em`, `white-space: nowrap`.
