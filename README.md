# Brotato Codex

A web-based database/encyclopedia for the game [Brotato](https://store.steampowered.com/app/1942280/Brotato/), built from decompiled game data.

## Tech Stack

- **Data pipeline**: Python 3 (`main.py`) — parses Godot `.tres` resource files, translates effect text, generates JSON + icon assets
- **Frontend**: Vue 3 + Element Plus + Vite
- **Styling**: Scoped CSS with dark/light theme toggle

## Project Structure

```
codex/
├── main.py                  # Data pipeline: .tres → JSON + icons
├── public/
│   ├── data/
│   │   ├── brotato_data.json      # Generated game data (weapons, items, characters)
│   │   └── translations_merged.json  # Manual translation fixes
│   └── icons/               # Copied game icons
├── src/
│   └── App.vue              # Single-file Vue app
├── index.html
├── package.json
└── translations/            # Translation fix tool (separate sub-project)
```

## Usage

### 1. Generate Data

Requires the decompiled Brotato game files at `../.assets/` (relative to the project root).

```bash
python main.py
```

This parses all weapon, item, and character `.tres` files, renders effect text with translations, and writes:
- `public/data/brotato_data.json` — the main data file
- `public/icons/` — all game icons

### 2. Run Dev Server

```bash
pnpm install
pnpm run dev
```

Opens at `http://localhost:3000`.

### 3. Build for Production

```bash
pnpm run build
```

Output goes to `dist/`. The `base: './'` in `vite.config.js` ensures relative paths for GitHub Pages.

## Translation Fixes

Effect texts that are missing from the game's `translations.csv` can be manually added via `translations_merged.json`. The pipeline loads entries with status `matched` or `manual` from this file to fill in gaps.

See `translations/` for the translation analysis and fixing toolchain.

## Notes

- The pipeline reads `.tres` files using a custom parser (not Godot) — complex nested structures like `ExtResource()` references are resolved by path.
- Effect text rendering replicates Godot's `Effect.get_text()` → `Text.text()` pipeline, including operator (+), percent (%), and color formatting.
- Some effects (e.g., `GainStatForEveryStatEffect` with `stat_scaled = "different_item"`) have special-case translations that the pipeline handles explicitly.
- `spawn_cooldown = -1` in structure effects is a sentinel meaning "use the stats file's cooldown" — the pipeline treats it accordingly.
