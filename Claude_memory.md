# Полное руководство по системе памяти в Claude Code

## 1. Уровни памяти (по приоритету)

Claude Code имеет многоуровневую архитектуру. Все найденные файлы **конкатенируются** в контекст (не переопределяют друг друга), от корня системы вниз к рабочей директории.

| Уровень | Путь | Scope |
|---------|------|-------|
| **Enterprise (managed policy)** | macOS: `/Library/Application Support/ClaudeCode/CLAUDE.md`<br/>Linux/WSL: `/etc/claude-code/CLAUDE.md`<br/>Windows: `C:\ProgramData\ClaudeCode\CLAUDE.md` | Все пользователи организации, не переопределяется |
| **User** | `~/.claude/CLAUDE.md` | Все ваши проекты — личные предпочтения |
| **Project** | `./CLAUDE.md` или `./.claude/CLAUDE.md` | Команда, коммитится в git |
| **Project local** | `./CLAUDE.local.md` | Только локально, должен быть в `.gitignore` |
| **Subdirectory** | `./src/api/CLAUDE.md` | Загружается **лениво** при работе с файлами в этой папке |

На одном уровне `CLAUDE.md` грузится **раньше** `CLAUDE.local.md`.

## 2. Механизм поиска

При запуске Claude Code идёт **вверх по дереву** от рабочей директории до корня (`/`), собирая каждый встреченный `CLAUDE.md`/`CLAUDE.local.md`. Поддиректорные `CLAUDE.md` подгружаются **только при чтении файлов внутри них** — это лениво.

```
/home/user/proj/src/api/  ← cwd
    ↑ ищет CLAUDE.md в каждом уровне
/home/user/proj/      ← project CLAUDE.md
/home/user/            ← обычно пусто
/                       ← корень
+ ~/.claude/CLAUDE.md   ← user
+ enterprise policy      ← если есть
```

## 3. Импорты `@path/to/file`

```markdown
See @README.md for overview
Personal rules: @~/.claude/my-rules.md
Standards: @docs/style-guide.md
```

**Правила:**
- **Относительные пути** — относительно файла с импортом, не cwd
- **`@~/...`** — раскрывается в home directory
- **Глубина рекурсии** — максимум **5 уровней**, циклы блокируются
- **НЕ работает** внутри code blocks (` ``` `), inline code (`` ` ``), HTML-комментариев
- **Первый импорт извне проекта** — Claude Code попросит подтверждение

## 4. Команды

| Команда | Назначение |
|---------|-----------|
| `/memory` | Открыть интерактивный список всех загруженных memory-файлов и редактировать их |
| `/init` | Анализирует кодовую базу и генерирует стартовый CLAUDE.md |
| `# заметка` | Префикс `#` в начале сообщения — быстрая запись в auto memory |
| `/clear` | Очищает историю разговора, **сохраняет** CLAUDE.md (он переоткрывается из диска) |
| `/compact` | Сжимает историю; CLAUDE.md перечитывается заново, вложенные subdir-файлы — нет (подгрузятся при следующем чтении файлов в них) |

## 5. Что писать в CLAUDE.md

```markdown
## Build & Test
- Build: `npm run build`
- Test: `npm test` (всегда перед commit)
- Lint: `npm run lint`

## Code Style
- 2-space indent, max 100 chars/line
- API handlers → `src/api/handlers/`
- DB models → `src/db/models/`

## Workflow
- Branch: `feature/name`, `fix/issue-N`
- Commit: `type: description` (feat/fix/refactor/docs)
- Always squash merge to main
```

**Принцип**: конкретность вместо расплывчатости. «Используй prettier» лучше чем «форматируй красиво».

## 6. Best practices

- **Размер** — целиться в **<200 строк** на файл, жёсткий рекомендуемый предел ~25KB. Каждая строка тратит токены **в каждом** промпте.
- **Структура** — markdown-заголовки и буллеты, Claude лучше следует структурированному тексту
- **Пересмотр** — если Claude повторяет ошибку дважды, добавьте правило; если правило не работает — переформулируйте
- **Конфликты** — если разные CLAUDE.md дают противоречивые инструкции, поведение непредсказуемо
- **`/clear`** в долгих сессиях — освобождает контекст, CLAUDE.md остаётся

## 7. Auto Memory (персистент между сессиями)

Хранится **локально на машине** в `~/.claude/projects/<project>/memory/`:
- `MEMORY.md` — индекс, **первые 200 строк или 25KB** загружаются на старте
- Прочие `.md` (`debugging.md`, `patterns.md`, …) — **по требованию**

**Особенности:**
- Привязка к проекту: внутри git repo — по identifier репо (все worktrees = одна память); вне git — по корню директории
- **Не шарится** между машинами и не коммитится
- Plain markdown — можно редактировать/удалять руками
- Управление через `/memory` (toggle) или setting `autoMemoryEnabled: false`

## 8. Подводные камни

- **CLAUDE.md грузится в КАЖДЫЙ запрос** — большой файл = постоянный налог на токены и фокус
- **Импорты разворачиваются полностью** при загрузке — следите за общим размером
- **Lazy subdir loading**: после `/compact` вложенные `CLAUDE.md` нужно «перетриггерить» обращением к файлам в них
- **Молчаливые failures**: несуществующие импорты пропускаются без явной ошибки
- **`CLAUDE.local.md` в .gitignore** — иначе утечёт личное в repo

## 9. Settings.json (memory-related)

```json
{
  "autoMemoryEnabled": true,
  "autoMemoryDirectory": "~/custom-memory",
  "claudeMdExcludes": [
    "**/legacy/CLAUDE.md"
  ]
}
```

Уровни settings (последний побеждает): managed policy → user → project → local → CLI flag.

## 10. Память vs Skills vs Hooks vs Slash Commands

| | **Memory (CLAUDE.md)** | **Skill** | **Hook** | **Slash** |
|---|---|---|---|---|
| Когда грузится | Каждый запрос | По триггеру/описанию | На событие | По вводу `/name` |
| Гарантия выполнения | Best effort | Best effort | **Гарантирована** | Manual |
| Стоимость контекста | Высокая (постоянно) | Низкая (on-demand) | Нулевая | — |
| Назначение | Always-on правила и факты | Workflow / справочник | Детерминированная автоматизация | Запуск skill |

**Правило**: всё, что должно быть **всегда** в голове у Claude → CLAUDE.md. Многошаговая процедура или большой reference → Skill. Должно срабатывать **всегда детерминированно** → Hook.

## 11. Поток в реальной сессии

1. Старт `claude` → грузятся system prompt → auto memory (200 строк) → env info → все CLAUDE.md от `/` до cwd → skills descriptions
2. Чтение файла в `src/api/` → подгружается `src/api/CLAUDE.md`
3. `# remember: build = pnpm build` → запись в `MEMORY.md`
4. `/compact` → история сжимается, CLAUDE.md перечитывается с диска свежим
5. `/clear` → история стирается, CLAUDE.md остаётся в новом промпте
