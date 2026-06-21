# Brotato 图鉴

基于反编译游戏数据构建的 [Brotato](https://store.steampowered.com/app/1942280/Brotato/)（土豆兄弟）网页图鉴。

## 技术栈

- **数据管线**：Python 3（`main.py`）— 解析 Godot `.tres` 资源文件，翻译效果文本，生成 JSON + 图标资源
- **前端**：Vue 3 + Element Plus + Vite
- **样式**：Scoped CSS，支持深色/浅色主题切换

## 项目结构

```
codex/
├── main.py                  # 数据管线：.tres → JSON + 图标
├── public/
│   ├── data/
│   │   ├── brotato_data.json      # 生成的游戏数据（武器、道具、角色）
│   │   └── translations_merged.json  # 手动翻译修正
│   └── icons/               # 复制的游戏图标
├── src/
│   └── App.vue              # 单文件 Vue 应用
├── index.html
├── package.json
└── translations/            # 翻译修正工具（独立子项目）
```

## 使用方法

### 1. 生成数据

需要将反编译的游戏文件放在项目根目录的 `../.assets/` 下。

```bash
python main.py
```

解析所有武器、道具、角色的 `.tres` 文件，渲染带翻译的效果文本，输出：
- `public/data/brotato_data.json` — 主数据文件
- `public/icons/` — 游戏图标

### 2. 启动开发服务器

```bash
pnpm install
pnpm run dev
```

默认打开 `http://localhost:3000`。

### 3. 构建生产版本

```bash
pnpm run build
```

输出到 `dist/`。`vite.config.js` 中 `base: './'` 使用相对路径，兼容 GitHub Pages 部署。

## 翻译修正

游戏 `translations.csv` 中缺失的效果文本，可通过 `translations_merged.json` 手动补充。数据管线会加载其中状态为 `matched` 或 `manual` 的条目来填补空缺。

翻译分析与修正工具链见 `translations/` 目录。

## 注意事项

- 数据管线使用自定义解析器读取 `.tres` 文件（非 Godot 引擎）— 复杂的嵌套结构（如 `ExtResource()` 引用）通过路径解析。
- 效果文本渲染复刻了 Godot 的 `Effect.get_text()` → `Text.text()` 流程，包括运算符（+）、百分比（%）和颜色格式化。
- 部分效果有特殊翻译处理（如 `GainStatForEveryStatEffect` 中 `stat_scaled = "different_item"` 显示为"道具"）。
- 建筑效果中 `spawn_cooldown = -1` 是哨兵值，表示"使用 stats 文件中的冷却时间"。
- 效果文本中 `text_key = "[EMPTY]"` 的条目会被完全剔除，不出现在生成的 JSON 中。
- 图标语法使用 `<icon>ranged_damage</icon>` 格式（非 HTML span），前端渲染时替换为 `<img>` 标签。
- 每行效果文本前会添加属性图标（stat_* 类型）或 `・` 占位符以保持对齐。
