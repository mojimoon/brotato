# Brotato 图鉴

[English](README.md) | [中文](README.zh.md) | [在线图鉴](https://mojimoon.github.io/brotato/)

基于反编译游戏数据构建的 [Brotato](https://store.steampowered.com/app/1942280/Brotato/)（土豆兄弟）网页图鉴。

## 技术栈

- **数据管线**：Python 3 — 解析 Godot `.tres` 资源文件，翻译效果文本，生成 JSON + 图标资源
- **前端**：Vue 3 + Element Plus + Vite（使用 `pnpm`）
- **样式**：Scoped CSS，支持深色/浅色主题切换

## 配置与使用

### 前置条件

- [GDRE Tools](https://github.com/GDRETools/gdsdecomp/releases) 用于反编译游戏

### 工作流程

```bash
# 1. 用 GDRE 反编译游戏到一个目录，如 D:\brotato\decompiled
#    目录下应包含：.assets/、weapons/、items/、dlcs/、effects/ 等

# 2. 克隆本仓库到反编译目录下
cd D:\brotato\decompiled
git clone https://github.com/mojimoon/brotato codex

# 3. 预分析缺失的翻译键
cd codex/translations
python analyze.py
#    输出：codex/translations/merged_analysis.json

# 4. 启动翻译补全网页工具
pnpm install
pnpm dev
#    打开 http://localhost:3000

# 5. 在网页工具中：加载 merged_analysis.json，逐条匹配翻译，导出
#    导出文件位于：codex/public/data/translations_merged.json

# 6. 生成完整的游戏数据
cd D:\brotato\decompiled
cd codex
python main.py
#    输出：codex/public/data/brotato_data.json
#          codex/public/icons/

# 7. 构建图鉴网站
pnpm install
pnpm build
#    输出：codex/dist/
```

### 项目结构

```
root/
├── .assets/                  # 游戏资源（翻译 CSV、图片等）
├── weapons/                  # 基础武器（melee/、ranged/）
├── items/                    # 基础道具 + 角色
├── effects/                  # Effect 子类实现
├── dlcs/dlc_1/               # DLC1 数据
└── codex/                    # 本仓库
    ├── main.py               # 数据管线：.tres → JSON + 图标
    ├── public/data/
    │   ├── brotato_data.json        # 生成的游戏数据
    │   └── translations_merged.json # 手动翻译修正
    ├── src/App.vue           # Vue 前端
    └── translations/         # 翻译修正工具链
        ├── analyze.py        # 扫描缺失翻译键
        └── web/              # 手动翻译匹配的 Vue 应用
```

## 工作原理

### 数据管线（`main.py`）

1. 从 `.assets/resources/translations/translations.csv`（基础游戏）和 `dlcs/dlc_1/translations/translations.csv`（DLC）加载翻译
2. 可选加载 `translations_merged.json` 中的手动修正条目
3. 用自定义解析器（非 Godot 运行时）解析所有武器、道具、角色 `.tres` 文件
4. 通过复刻 Godot 的 `Effect.get_text()` → `Text.text()` 流程渲染效果文本：
   - 确定翻译 key（`text_key` 或 `key`，大写）
   - 通过各效果子类的 `get_args()` 构建参数
   - 应用 `custom_args` 覆盖（值、符号、格式）
   - 按规则添加运算符（+）、百分比（%）、颜色标签
5. 复制所有引用的图标文件到 `public/icons/`

### 翻译修正工具链（`translations/`）

1. `analyze.py` 扫描所有 `.tres` 效果文件，提取翻译键，与 CSV 交叉比对，输出 `merged_analysis.json` — 按分类列出缺失键及候选字符串
2. 网页工具（`pnpm dev`）让你可视化匹配缺失键到翻译，并导出 `translations_merged.json`
3. `main.py` 读取该文件填补空缺

## 技术要点

### 冷却时间

- `extra.spawn_cooldown` — 已经是秒，不要除以 60
- `structure_stats.cooldown` — 帧数（60fps），需要除以 60
- `weapon_stats.cooldown` — 帧数（60fps），需要除以 60

### 效果渲染

- 存在两条代码路径：`_build_effect_args_and_signs()`（旧）和 `render_effect_text()`（当前使用）。修改渲染逻辑时两处都需同步。
- `text_key = "[EMPTY]"` 的效果会被完全过滤，不加入 JSON
- `stat_scaled = "different_item"` 映射为 `tr("ITEM")`（而非 `tr("DIFFERENT_ITEM")`）
- `spawn_cooldown = -1` 是哨兵值，表示"使用 stats 文件中的冷却时间"
- 图标语法：`<icon>short_key</icon>`（如 `<icon>ranged_damage</icon>`）— Python 端生成，Vue 端渲染为 `<img>`
- 属性图标前缀：`key` 以 `stat_` 开头的效果行前显示对应 stat icon；其他效果行前显示 `・` 以保持对齐

### 前端

- 左侧网格：`repeat(auto-fill, minmax(90px, 1fr))` 布局
- 右侧详情面板：独立滚动
- 效果行使用两个 flex 子元素（`eff-prefix` + `eff-text`）避免换行
- 主题切换：`isDark` ref + `watch` 给 `<html>` 和 `<body>` 添加 `light-theme` class
- Tab 图标：武器=Aim，道具=Box，角色=User（@element-plus/icons-vue）
- 语言切换：el-dropdown，按钮内直接写文字（`{{ isZh ? '中' : 'EN' }}`），不用 `:icon` prop
- `html` 和 `body` 必须设置相同背景色，防止宽屏下两侧露出不同底色
