# AGENTS.md — Brotato Codex

## 项目概述

基于反编译游戏数据构建的 Brotato 网页图鉴（13 种语言）。仓库位于反编译游戏根目录下的 `codex/` 子目录中。

**关键前提**：此仓库必须克隆到 GDRE 反编译后的游戏目录内才能运行数据管线（`main.py` 依赖 `CODEX_DIR.parent` 即反编译根目录作为 `BASE_DIR`）。

## 技术栈

- **数据管线**：Python 3 — 解析 Godot `.tres` 文件，渲染效果文本，生成 `public/data/brotato_data.<lang>.json` + `languages.json` + `public/icons/`
- **前端**：Vue 3 + Element Plus + Vite（另用 chart.js / vue-chartjs），包管理用 pnpm
- **翻译工具**：`translations/` 下是独立的 Vite 应用（端口 5174）

## 常用命令

```bash
# 翻译分析（需反编译数据）
cd translations && python analyze.py

# 翻译修正工具（独立 Vite 应用，端口 5174）
cd translations && pnpm install && pnpm dev

# 前端 UI 文案（修改后需重新运行 main.py 才会写入数据 JSON）
python build_ui_strings.py   # 生成 ui_strings.json

# 数据管线
python main.py

# 主应用开发
pnpm install && pnpm dev    # 端口 3000
pnpm build                  # 输出到 dist/
```

## 两个 Vite 应用

| 应用 | 目录 | 端口 | 用途 |
|------|------|------|------|
| 主图鉴 | 根目录 | 3000 | 按当前语言读取 `public/data/brotato_data.<lang>.json` 渲染 |
| 翻译工具 | `translations/` | 5174 | 手动匹配缺失翻译键，导出 `translations_merged.json` |

两个应用独立 `pnpm install`，互不依赖。

## 数据流

```
GDRE 反编译数据 (.tres, .csv)
  ↓ python translations/analyze.py
translations/merged_analysis.json  (缺失翻译键分析)
  ↓ 网页工具手动匹配
public/data/translations_merged.json  (翻译修正)
  ↓                                   build_ui_strings.py → ui_strings.json (前端文案)
  ↓ python main.py  ←────────────────────────────────┘
public/data/brotato_data.<lang>.json ×13 + languages.json + public/icons/
  ↓ Vue 前端按语言 fetch
浏览器渲染
```

## Python 脚本注意事项

### main.py（~3900 行）

- `BASE_DIR = CODEX_DIR.parent` — 必须在反编译游戏根目录下运行
- 语言列表 `LANGS`（13 种）在 `main.py` 与 `build_ui_strings.py` 中各有一份，**顺序必须一致**；`LANG_META` 输出为 `languages.json`
- 先构建含全部语言的数据，再由 `prune_data_for_lang()` 裁剪为每语言一份 JSON，并把 `ui_strings.json` 中对应语言的文案注入为 `ui` 字段
- 冷却时间：`spawn_cooldown` 已是秒，**不要**除以 60；`structure_stats.cooldown` 和 `weapon_stats.cooldown` 是帧数，需除以 60
- 效果渲染只走 `render_effect_text()`；`_build_effect_args_and_signs()` 是未被调用的旧代码，不要在其上修改
- `text_key = "[EMPTY]"` 的效果会被过滤
- `stat_scaled = "different_item"` 映射为 `tr("ITEM")` 而非 `tr("DIFFERENT_ITEM")`
- 废案武器排除在 `EXCLUDED_WEAPONS` 中（如 `weapon_knuckles`）
- 输出时 `separators=(',', ':')` 生成紧凑 JSON
- 无法渲染的效果写入 `public/data/unrenderable_effects.md`

### build_ui_strings.py

- 所有前端 UI 文案（tab、筛选、资源页 sections、标签翻译等）在此用 `T(...)` 按 `LANGS` 顺序写 13 个值，生成 `ui_strings.json`
- 新增前端文案：在这里加键 → 运行脚本 → 运行 `main.py` → 前端用 `S.<key>` 访问

### translations/analyze.py

- `PROJECT_ROOT = SCRIPT_DIR.parent.parent` — 同样依赖反编译目录结构
- 扫描 `*effect*.tres` 文件，与 CSV 交叉比对找出缺失翻译键

## 前端约定

### 结构

- `src/App.vue`：仅为外壳（头部、Tab、筛选栏、主内容/资源页切换），`onMounted(initCodex)`
- `src/store/codexStore.js`：**所有共享状态、计算属性、渲染函数和数据加载**都在这里，以模块级 `ref`/`computed` 导出；组件直接 import 使用，不用 props/emit 传递全局状态，也不用 Pinia
- `src/components/`：
  - 布局：`AppHeader`、`FilterBar`、`MainContent`（`ItemGrid` + `DetailPanel`）、`ResourcesPanel`
  - 网格：`ItemGrid` → `GridCard`
  - 详情：`DetailPanel` 按 Tab 分派到 `WeaponDetail` / `ItemDetail` / `CharacterDetail`，共用 `DetailHeader`、`TierTabs`、`EffectsList`、`WeaponStatRows`、`PriceSection`、`CurseSection`、`TagBadge`、`AttackSpeedCalculator`
- `src/styles/theme.css`（主题变量、Element Plus 覆盖）+ `src/styles/app.css`（布局），在 `main.js` 全局引入；组件内只放 scoped 局部样式

### 数据与多语言

- `BASE`（`codexStore.js` 顶部）：生产环境从 jsDelivr 镜像 CDN 加载 `public/` 数据，**URL 中带版本 tag（如 `@v2.0.2`），发版时需同步更新**；开发环境用 `BASE_URL`
- 切换语言时 `watch(currentLang)` 重新 fetch `brotato_data.<lang>.json`；`languages.json` 提供下拉菜单列表；默认语言由浏览器 locale 推断
- UI 文案统一通过 `S`（= `rawData.ui`）访问，不要在组件里硬编码文本
- 用户偏好（语言、主题、排序等）以 `brotato_*` 键存 `localStorage`

### UI 细节

- 主题切换通过 `isDark` ref + `watch` 给 `<html>` 和 `<body>` 添加 `light-theme` class
- `html` 和 `body` 必须设置相同背景色，防止宽屏下两侧露出不同底色
- Tab 图标：武器=Aim，道具=Box，角色=User，资源=Collection（`@element-plus/icons-vue`）
- 语言切换：`AppHeader` 中的 el-dropdown，按钮内直接显示当前语言名，不用 `:icon` prop
- 效果行使用两个 flex 子元素（`eff-prefix` + `eff-text`）避免换行
- `<icon>short_key</icon>` 语法由 Python 端生成，前端 `renderEffectText()` 替换为 `<img>` 渲染
- 属性图标前缀（`renderEffectPrefix()`）：效果带 `icon` 字段且能在 `stat_icons` 中解析时显示对应 stat icon；否则显示 `·` 以保持对齐
- 左侧网格：`repeat(auto-fill, minmax(85px, 1fr))` 布局
- 右侧详情面板：独立滚动
- 武器按 family 分组（去掉尾部 `_数字` 后缀合并同族武器），详情面板显示 T1-T4 切换

## CI/CD

`.github/workflows/deploy.yml`：push 到 `main` 时自动构建并部署到 GitHub Pages（数据文件在生产环境走 CDN，见上文 `BASE`）。
