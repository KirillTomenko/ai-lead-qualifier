# Сценарий GIF-демо

> Сюда вставь свой сценарий — пришли его в чат, и я оформлю этот файл полностью.

## Как вставить GIF в README

1. Запиши демо по сценарию (OBS / Loom / gifcap.dev / ScreenToGif)
2. Сохрани файл: `docs/demo.gif` (рекомендуемый размер: до 5 МБ)
3. Открой `README.md`, найди блок `GIF_PLACEHOLDER_START`
4. Замени весь блок `<!-- ... -->` и строку с `> 📹` на:

```markdown
![Demo](docs/demo.gif)
```

## Инструменты для записи

| Инструмент | Платформа | Ссылка |
|---|---|---|
| ScreenToGif | Windows | https://www.screentogif.com |
| gifcap | Browser | https://gifcap.dev |
| OBS + FFmpeg | Все | конвертация через `ffmpeg -i demo.mp4 -vf fps=10 docs/demo.gif` |
