# AGENTS.md — Brotato Codex

## 项目概述

基于反编译游戏数据构建的 Brotato 网页图鉴。仓库位于反编译游戏根目录下的 `codex/` 子目录中。

**关键前提**：此仓库必须克隆到 GDRE 反编译后的游戏目录内才能运行数据管线（`main.py` 依赖 `CODEX_DIR.parent` 即反编译根目录作为 `BASE_DIR`）。

## 技术栈

- **数据管线**：Python 3 — 解析 Godot `.tres` 文件，渲染效果文本，生成 `public/data/brotato_data.json` + `public/icons/`
- **前端**：Vue 3 + Element Plus + Vite，包管理用 pnpm
- **翻译工具**：`translations/` 下是独立的 Vite 应用（端口 5174）

## 常用命令

```bash
# 翻译分析（需反编译数据）
cd translations && python analyze.py

# 翻译修正工具（独立 Vite 应用，端口 5174）
cd translations && pnpm install && pnpm dev

# 数据管线
python main.py

# 主应用开发
pnpm install && pnpm dev    # 端口 3000
pnpm build                  # 输出到 dist/
```

## 两个 Vite 应用

| 应用 | 目录 | 端口 | 用途 |
|------|------|------|------|
| 主图鉴 | 根目录 | 3000 | 读取 `public/data/brotato_data.json` 渲染 |
| 翻译工具 | `translations/` | 5174 | 手动匹配缺失翻译键，导出 `translations_merged.json` |

两个应用独立 `pnpm install`，互不依赖。

## 数据流

```
GDRE 反编译数据 (.tres, .csv)
  ↓ python analyze.py
translations/merged_analysis.json  (缺失翻译键分析)
  ↓ 网页工具手动匹配
public/data/translations_merged.json  (翻译修正)
  ↓ python main.py
public/data/brotato_data.json + public/icons/  (最终数据)
  ↓ Vue 前端读取
浏览器渲染
```

## Python 脚本注意事项

### main.py（~3180 行）

- `BASE_DIR = CODEX_DIR.parent` — 必须在反编译游戏根目录下运行
- 冷却时间：`spawn_cooldown` 已是秒，**不要**除以 60；`structure_stats.cooldown` 和 `weapon_stats.cooldown` 是帧数，需除以 60
- 效果渲染有两条代码路径：`_build_effect_args_and_signs()`（旧）和 `render_effect_text()`（当前使用）。**修改渲染逻辑时两处都需同步**
- `text_key = "[EMPTY]"` 的效果会被过滤
- `stat_scaled = "different_item"` 映射为 `tr("ITEM")` 而非 `tr("DIFFERENT_ITEM")`
- 废案武器排除在 `EXCLUDED_WEAPONS` 中（如 `weapon_knuckles`）
- 输出时 `separators=(',', ':')` 生成紧凑 JSON

### translations/analyze.py

- `PROJECT_ROOT = SCRIPT_DIR.parent.parent` — 同样依赖反编译目录结构
- 扫描 `*effect*.tres` 文件，与 CSV 交叉比对找出缺失翻译键

## 前端约定（App.vue，单文件组件）

- 单文件组件，无子组件（`src/components/` 为空）
- 所有 UI 逻辑、状态、样式都在 `src/App.vue` 中
- 主题切换通过 `isDark` ref + `watch` 给 `<html>` 和 `<body>` 添加 `light-theme` class
- `html` 和 `body` 必须设置相同背景色，防止宽屏下两侧露出不同底色
- Tab 图标：武器=Aim，道具=Box，角色=User（`@element-plus/icons-vue`）
- 语言切换：el-dropdown，按钮内直接写文字（`{{ isZh ? '中' : 'EN' }}`），不用 `:icon` prop
- 效果行使用两个 flex 子元素（`eff-prefix` + `eff-text`）避免换行
- `<icon>short_key</icon>` 语法由 Python 端生成，Vue 端替换为 `<img>` 渲染
- 属性图标前缀：`key` 以 `stat_` 开头的效果行前显示对应 stat icon；其他效果行前显示 `・` 以保持对齐
- 左侧网格：`repeat(auto-fill, minmax(90px, 1fr))` 布局
- 右侧详情面板：独立滚动
- 武器按 family 分组（去掉尾部 `_数字` 后缀合并同族武器），详情面板显示 T1-T4 切换

## CI/CD

`.github/workflows/deploy.yml`：push 到 `main` 时自动构建并部署到 GitHub Pages。

