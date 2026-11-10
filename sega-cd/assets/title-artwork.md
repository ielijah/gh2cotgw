# Title artwork, 10 November 2026

Both masters were generated with the built-in imagegen tool. No external font is required.

* `title-brush-source.png`: reference `analysis/title-original.png`; prompt requested the exact two lines `СЕРЫЙ ВОЛК` / `И БЕЛАЯ ЛАНЬ`, rough thick calligraphic brushwork, tapered angular strokes, readable Cyrillic, flat white with thin indigo outline on black, 16-bit pixel art, no additional text.
* `title-subtitle-source.png`: prompt requested the exact one-line `ТАЙНАЯ ИСТОРИЯ ЮАНЬ`, readable angular square uppercase lettering, open counters and separate letters, medium weight, solid yellow on black, no additional text, no gradients or shadows, readable at 176×14 pixels.

Reproduce the indexed assets from the project root:

```powershell
& sega-cd/tools/render_title_brush.ps1
& sega-cd/tools/render_title_subtitle.ps1
.runtime/python/python.exe -X utf8 sega-cd/tools/render_title_labels.py
```

The last script draws native Cyrillic prompt glyphs and keeps the original START pixels. Its palette indices are copied row by row from START, including both dark bands. The М glyph is horizontally symmetric. All graphic tiles, pointers and blink rectangles are checked by `tools/verify.py`.

Emulator evidence: `analysis/qa-title-brush.png`, cold boot using the trial CUE, then START successfully opens the main menu. Both distributed CUE packages contain the rebuilt ISO. Biography card frame and glyph-pool fix is documented in `analysis/catalog-card-fix-20261110.json`.
