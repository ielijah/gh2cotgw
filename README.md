# Genghis Khan II — переводы для двух платформ

- [Mega Drive / Genesis](mega-drive/README.md) — релиз русского перевода 1.0.0. Исходники перевода, шрифты, инструменты и проверки находятся в `mega-drive/`.
- [Sega CD / Mega-CD](sega-cd/README.md) — экспериментальный перевод японской версии с русской озвучкой. Исходники, графика и инструменты находятся в `sega-cd/`. Исправлена загрузка CD-дорожек; проверены разговор в гареме, возвращение на карту и CD-аудио. Перевод ещё не является готовым релизом.

## Структура

Каждый проект содержит собственные `tools/`, `translation/`, `assets/`, `analysis/` и README. Оригинальный ROM Mega Drive хранится локально в `mega-drive/rom/`, диск Sega CD — в `sega-cd/disc/`. Результаты сборки находятся в `build/` соответствующего проекта. ROM, образы и локальные релизные пакеты исключены из Git. Все аудиодорожки текущей русской сборки и CUE опубликованы в [sega-cd/dub](sega-cd/dub/README.md).

Скрытая папка `.runtime/` — общее локальное окружение Python и эмулятора, также исключённое из Git. При переносе проекта она остаётся в корне, чтобы не нарушать пути установленных окружений. Импорт шрифтов и терминологии Sega CD использует соседний каталог `mega-drive/`.

## Сборка из корня репозитория (PowerShell)

```powershell
& ./.runtime/python/python.exe -X utf8 mega-drive/tools/build.py
& ./.runtime/python/python.exe -X utf8 mega-drive/tools/verify.py
& ./.runtime/python/python.exe -X utf8 sega-cd/tools/build.py
& ./.runtime/python/python.exe -X utf8 sega-cd/tools/verify.py
```

Для сборки требуются собственные оригиналы игр; подробности приведены в README каждого проекта. Команды в README Mega Drive выполняются из `mega-drive/`, команды в README Sega CD — из корня репозитория.
