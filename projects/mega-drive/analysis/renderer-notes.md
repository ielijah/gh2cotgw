# Renderer changes, v0.3

Original routines: `5E16` text interpreter, `5CF8` glyph conversion, `5BF2` cyclic glyph allocation, `3E5E` generic tile upload, `5B2A` text pool reset.

The v0.1 approach assigned Cyrillic letters to fixed slots inside a ring still used by speech bubbles. This caused two independent problems: overwritten glyph shapes and sharing bitmaps whose foreground/background colours differed.

The intermediate v0.2 cache still allowed long-lived HUD text to be evicted by later output. Version 0.3 puts persistent text in a permanent bank: all 66 Russian glyphs, Latin capitals, digits, punctuation and Roman-numeral forms fit the original 192-tile allocation after deduplicating 8×8 halves. A glyph's halves need not be consecutive. The `5C10` preload and `5CF8` static lookup are replaced accordingly; no extra VRAM region is claimed.

Both faces come from the user-provided reference ROM, SHA-256 `593ab1fef1f30ac3bf13a75be211f4536a765f24404fb1bfb92cdad81084161d`, at offsets `46244` and `46844`. Five missing uppercase forms per face are derived from its own glyphs. Cyrillic preserves case. Static Latin lowercase is folded to capitals, and rare punctuation/ordinal variants are consolidated by the explicit `ALIASES` table in `tools/import_font.py`. Latin grades A–E retain their identities.

Only dynamic, coloured text uses the original ring. A RAM tag table at `FFD000..FFD7FF` associates physical tile pairs with a glyph identity. `FFD800` records the current face. These areas lie below the original `FFE000` stack guard; no original absolute references to this interval were found in the inspected code. Indirect access and long-session behaviour still need broader testing.

- Zero tag: free/unknown contents.
- Dynamic tag: `8000 | ((foreground << 4 | background) << 7) | (glyph_index + 1)`.
- A generic upload clears tags for every intersected physical pair. Pool resets and face changes clear the tag table.
- Static glyph pixels use indices 0/F, and their palette is carried by the tilemap, as for the original Latin font. Dynamic glyphs retain both actual pixel colours in the cache key.
- A new dynamic glyph keeps its pending key in the unused word at `-44(a6)` of the original glyph frame; the output-upload hook records the key after the original allocator path finishes.

ROM additions: code at `100400..100Exx`; compressed replacement buttons at `102000` and `102200`; normal 1bpp font at `103000`, alternate at `103500`; permanent 4bpp bank at `104000..1057FF`; Latin map at `105800`, Cyrillic map at `105B00`; relocated scenario strings at `106000`, `106040`, `106080`. Encoding is A0..DF for А..я, 1C for Ё, 7F for ё. The main dispatcher handles these before the original control/Shift-JIS checks. The glyph-index transfer is widened to a word.

The scenario selector reuses the stock 20×10 frame preset, moves left, and highlights 18 columns. Its original `9760` routine used a 64-byte local buffer, insufficient for two rows of 18 tile words (72 bytes). The frame grows to 80 bytes, the buffer moves down, and the MOVEM restore displacement changes with it. This prevents the stack corruption exposed by the full scenario title.

Graphics routine `33F0` decodes KOEI streams. Control words are little endian; flag bytes select literals and back-references. The Python port is in `tools/graphics_codec.py`. Replacement buttons use valid literal-only streams and retain dimensions 4×2 tiles. The original pointer table at `A663C` is updated for resource IDs B9 and BA.

Verification includes both ROM hashes, exact IPS replay, checksums, field padding and printf specifiers, relocated pointers, reconstruction of all 66 glyphs from permanent tiles, compressed-image dimensions, actual 68000 tests, emulator captures, pixel equality after reversing scenario selection, and an unchanged Price HUD across menus. This does not establish correctness for every game screen or long sessions.


## 0.3.2: старшие биты индекса символа

В штатной инструкции 005E7C `MOVE.B D4,D0` старшие 24 бита D0 не очищались: оригинальный рендерер позднее брал только младший байт. После расширения индексов для Ё/ё новый код использовал более широкий индекс. Это позволяло остаточным битам влиять на выбор глифа; на игровой карте возникала лишняя буква и исчезали цифры стоимости приказа.

Исправление: `2004` (`MOVE.L D4,D0`) вместо `1004`. D4 уже нормализован исходным вычислением индекса ASCII или нашим кириллическим диспетчером. Вызовы специальных индексов Ё/ё передают D4 напрямую. Нативные тесты глифов и сравнение области x72..111, y40..55 с оригинальным ROM проходят; сравнение выполняется на кадре 15200 после открытия хозяйственного меню.

Главное меню загружает ресурсы FD, FE, B3, B4, B5, B6, B7, F6 из списка 047F22. Дополнительно переведены варианты B1, B2, B8. Новые потоки расположены в 108000..1095FF, по 0x200 на ресурс, общий размер ROM 0x10A000. Глифы кнопок берутся из импортированного шрифта без изменения масштаба; индекс E — белые буквы, F — тень, 9 — фон.
