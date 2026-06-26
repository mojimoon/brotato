#!/usr/bin/env python3
"""
分析 Brotato 反编译源码中 effect tres 文件的键值，对照 translations.csv
找出缺失的翻译键，分类输出 JSON 供前端填写。

用法:
    python analyze.py
"""

import csv
import json
import os
import re
import sys
from collections import defaultdict
from pathlib import Path

# ============================================================================
# 配置 — paths relative to this script's location
# ============================================================================
SCRIPT_DIR = Path(__file__).resolve().parent          # codex/translations/
PROJECT_ROOT = SCRIPT_DIR.parent.parent               # decompiled game root
BASE_CSV = PROJECT_ROOT / ".assets" / "resources" / "translations" / "translations.csv"
DLC_CSV = PROJECT_ROOT / ".assets" / "dlcs" / "dlc_1" / "translations" / "translations.csv"

OUTPUT_DIR = SCRIPT_DIR           # merged_analysis.json goes here

# 语言列（en 和 zh 是必须的，其余作为参考）
LANG_COLS = ["en", "fr", "zh", "ja", "ko", "zh_TW", "ru", "pl", "es", "pt", "de", "tr", "it"]

# ============================================================================
# CSV 解析
# ============================================================================

def parse_csv(path: Path) -> dict:
    """解析 translations.csv，返回 {KEY_UPPER: {key, en, zh, ...}}"""
    result = {}
    with open(path, encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            raw_key = row.get("key", "").strip()
            if not raw_key:
                continue
            entry = {"key": raw_key}
            for col in LANG_COLS:
                entry[col] = (row.get(col) or "").strip()
            # 以大写键存储（effect.gd 第117行: key.to_upper()）
            result[raw_key.upper()] = entry
    return result


def parse_missing_keys(csv_data: dict) -> list:
    """提取 CSV 中 <!MissingKey:N:text> 格式的条目，返回 [{n, text, en, zh}]"""
    missing = []
    for key_upper, entry in csv_data.items():
        if key_upper.startswith("<!MISSINGKEY:"):
            # 格式: <!MissingKey:N:english_text>
            m = re.match(r"<!MissingKey:(\d+):(.+)>$", entry["key"], re.DOTALL)
            if m:
                missing.append({
                    "n": int(m.group(1)),
                    "text": m.group(2),
                    "en": entry["en"],
                    "zh": entry["zh"],
                    "raw_key": entry["key"],
                })
    return missing


# ============================================================================
# Effect TRES 解析
# ============================================================================

# 匹配 [resource] 段之后的 key/text_key/value 行
_RE_KEY = re.compile(r'^key\s*=\s*"(.*)"\s*$', re.MULTILINE)
_RE_TEXT_KEY = re.compile(r'^text_key\s*=\s*"(.*)"\s*$', re.MULTILINE)
_RE_VALUE = re.compile(r'^value\s*=\s*(-?\d+)\s*$', re.MULTILINE)
_RE_EFFECT_SIGN = re.compile(r'^effect_sign\s*=\s*(\d+)\s*$', re.MULTILINE)
_RE_SCRIPT = re.compile(r'\[ext_resource\s+path="res://([^"]+)"\s+type="Script"', re.MULTILINE)

# 匹配 .gd 文件中的 text_key 赋值
_RE_GD_TEXT_KEY = re.compile(r'\.text_key\s*=\s*"([^"]+)"', re.MULTILINE)


def parse_effect_tres(path: Path) -> dict | None:
    """解析单个 effect tres 文件，提取 key/text_key/value 等"""
    try:
        text = path.read_text(encoding="utf-8")
    except Exception:
        try:
            text = path.read_text(encoding="latin-1")
        except Exception:
            return None

    m_key = _RE_KEY.search(text)
    m_text = _RE_TEXT_KEY.search(text)
    m_val = _RE_VALUE.search(text)
    m_sign = _RE_EFFECT_SIGN.search(text)

    key = m_key.group(1) if m_key else ""
    text_key = m_text.group(1) if m_text else ""
    value = int(m_val.group(1)) if m_val else 0
    effect_sign = int(m_sign.group(1)) if m_sign else 3

    # 脚本路径（帮助判断 effect 类型）
    scripts = _RE_SCRIPT.findall(text)
    script = scripts[0] if scripts else ""

    # 两个都为空则跳过（无显示文本的纯内部 effect）
    if not key and not text_key:
        return None

    # 最终键：text_key 优先，否则 key，转大写
    final_key_raw = text_key if text_key.strip() else key
    final_key = final_key_raw.strip().upper()

    if not final_key:
        return None

    return {
        "key": key,
        "text_key": text_key,
        "final_key": final_key,
        "value": value,
        "effect_sign": effect_sign,
        "script": script,
        "filename": path.name,
    }


def collect_effects(search_root: Path, base_root: Path, exclude_dirs: list = None) -> list:
    """收集目录下所有 *effect*.tres 文件的信息，可排除指定子目录"""
    exclude_set = set(exclude_dirs or [])
    results = []
    for tres_path in sorted(search_root.rglob("*effect*.tres")):
        # 检查是否在排除目录中
        parts = tres_path.relative_to(search_root).parts
        if parts and parts[0] in exclude_set:
            continue
        info = parse_effect_tres(tres_path)
        if info is None:
            continue
        # 相对路径
        try:
            rel_path = str(tres_path.relative_to(base_root)).replace("\\", "/")
        except ValueError:
            rel_path = str(tres_path).replace("\\", "/")
        info["path"] = rel_path
        results.append(info)
    return results


def parse_gd_text_keys(path: Path) -> list:
    """解析 .gd 文件中的 text_key 赋值，返回 [{final_key, key, text_key, ...}]"""
    try:
        text = path.read_text(encoding="utf-8")
    except Exception:
        try:
            text = path.read_text(encoding="latin-1")
        except Exception:
            return []

    results = []
    for match in _RE_GD_TEXT_KEY.finditer(text):
        text_key = match.group(1)
        final_key = text_key.strip().upper()
        if final_key:
            results.append({
                "key": "",
                "text_key": text_key,
                "final_key": final_key,
                "value": 0,
                "effect_sign": 3,
                "script": "",
                "filename": path.name,
            })
    return results


def collect_gd_text_keys(search_root: Path, base_root: Path, label: str) -> list:
    """收集指定目录下所有 .gd 文件中的 text_key 赋值"""
    results = []
    for gd_path in sorted(search_root.rglob("*.gd")):
        # 只处理 dlc_1_data.gd
        if gd_path.name != "dlc_1_data.gd":
            continue
        keys = parse_gd_text_keys(gd_path)
        for info in keys:
            try:
                rel_path = str(gd_path.relative_to(base_root)).replace("\\", "/")
            except ValueError:
                rel_path = str(gd_path).replace("\\", "/")
            info["path"] = rel_path
            info["source"] = label
            results.append(info)
    return results


# ============================================================================
# 分类与上下文
# ============================================================================

def classify_key(key: str) -> str:
    """将键分类为 stat_*, effect_*, 其他"""
    k = key.lower()
    if k.startswith("stat_"):
        return "stat"
    elif k.startswith("effect_"):
        return "effect"
    else:
        return "other"


def infer_source_name(rel_path: str) -> str:
    """从路径推断物品/武器/角色名（跳过纯数字等级目录）"""
    parts = rel_path.split("/")
    # 例如: items/all/adrenaline/adrenaline_effect_0.tres -> adrenaline
    # weapons/melee/cactus_mace/1/cactus_mace_effect_1.tres -> cactus_mace
    # items/characters/well/well_effect_1.tres -> well
    # 取倒数第二级目录名，如果为纯数字则往上找
    for i in range(len(parts) - 2, -1, -1):
        name = parts[i]
        if name and not name.isdigit():
            return name
    return ""


def infer_category(rel_path: str) -> str:
    """从路径推断大类：item/weapon/character/other"""
    parts = rel_path.lower()
    if "/items/" in parts or "/consumables/" in parts:
        return "item"
    elif "/weapons/" in parts:
        return "weapon"
    elif "/characters/" in parts or "/entities/units/" in parts:
        return "character"
    elif "/sets/" in parts:
        return "set"
    elif "/effect_behaviors/" in parts:
        return "behavior"
    elif "/difficulties/" in parts:
        return "difficulty"
    elif "/upgrades/" in parts:
        return "upgrade"
    else:
        return "other"


# ============================================================================
# 主分析逻辑（合并 base + dlc1）
# ============================================================================

def collect_effects_for_source(label: str, search_root: Path, base_root: Path,
                                exclude_dirs: list = None) -> list:
    """收集某来源的所有 effect tres，并给每条加 source 标签"""
    effects = collect_effects(search_root, base_root, exclude_dirs=exclude_dirs)
    for eff in effects:
        eff["source"] = label
    return effects


def merge_and_analyze(base_effects: list, dlc_effects: list,
                      base_csv: dict, dlc_csv: dict,
                      base_missing_keys: list, dlc_missing_keys: list) -> dict:
    """
    合并 base + dlc1 的 effect tres，对照两个 CSV 找出缺失键。
    每个缺失键带 sources 标签 (["base"] / ["dlc1"] / ["base", "dlc1"])。
    候选池合并，用 "B_{n}" / "D_{n}" 区分来源。
    """
    all_effects = base_effects + dlc_effects
    print(f"[合并] 总 effect tres: {len(all_effects)} (base={len(base_effects)}, dlc={len(dlc_effects)})")

    # 按最终键分组
    key_map: dict[str, dict] = {}

    for eff in all_effects:
        fk = eff["final_key"]
        if fk not in key_map:
            key_map[fk] = {
                "final_key": fk,
                "key": eff["key"],
                "text_key": eff["text_key"],
                "category": classify_key(fk),
                "contexts": [],
                "sources": set(),
            }
        ctx = {
            "path": eff["path"],
            "value": eff["value"],
            "source_name": infer_source_name(eff["path"]),
            "source_type": infer_category(eff["path"]),
            "script": eff["script"],
            "source": eff["source"],
        }
        key_map[fk]["contexts"].append(ctx)
        key_map[fk]["sources"].add(eff["source"])

    # 合并 CSV (base + dlc1)
    merged_csv = {}
    merged_csv.update(base_csv)
    merged_csv.update(dlc_csv)

    known = []
    missing = []

    for fk, info in key_map.items():
        all_ctx = info["contexts"]
        source_names = sorted(set(c["source_name"] for c in all_ctx if c["source_name"]))
        source_types = sorted(set(c["source_type"] for c in all_ctx))
        sample_ctx = all_ctx[:10]
        sources = sorted(info["sources"])

        entry = {
            "final_key": fk,
            "key": info["key"],
            "text_key": info["text_key"],
            "category": info["category"],
            "source_names": source_names,
            "source_types": source_types,
            "occurrence_count": len(all_ctx),
            "sample_contexts": sample_ctx,
            "sources": sources,
        }

        if fk in merged_csv:
            csv_entry = merged_csv[fk]
            entry["csv_en"] = csv_entry["en"]
            entry["csv_zh"] = csv_entry["zh"]
            entry["status"] = "known"
            known.append(entry)
        else:
            entry["csv_en"] = ""
            entry["csv_zh"] = ""
            entry["status"] = "missing"
            missing.append(entry)

    # 合并候选池：base 用 "B_{n}"，dlc1 用 "D_{n}"
    merged_candidates = []
    seen_texts = {}  # en -> id，去重
    for mk in base_missing_keys:
        cid = f"B_{mk['n']}"
        merged_candidates.append({
            "id": cid,
            "source": "base",
            "n": mk["n"],
            "en": mk["en"],
            "zh": mk["zh"],
        })
    for mk in dlc_missing_keys:
        cid = f"D_{mk['n']}"
        merged_candidates.append({
            "id": cid,
            "source": "dlc1",
            "n": mk["n"],
            "en": mk["en"],
            "zh": mk["zh"],
        })

    stats = {
        "total_effects": len(all_effects),
        "unique_keys": len(key_map),
        "known_count": len(known),
        "missing_count": len(missing),
        "by_category": {
            "stat": len([m for m in missing if m["category"] == "stat"]),
            "effect": len([m for m in missing if m["category"] == "effect"]),
            "other": len([m for m in missing if m["category"] == "other"]),
        },
        "by_source": {
            "base_only": len([m for m in missing if m["sources"] == ["base"]]),
            "dlc1_only": len([m for m in missing if m["sources"] == ["dlc1"]]),
            "both": len([m for m in missing if m["sources"] == ["base", "dlc1"]]),
        },
    }

    cat_order = {"stat": 0, "effect": 1, "other": 2}
    missing.sort(key=lambda x: (cat_order.get(x["category"], 3), x["final_key"]))
    known.sort(key=lambda x: x["final_key"])

    result = {
        "label": "merged",
        "stats": stats,
        "missing_keys": missing,
        "known_keys": known,
        "csv_missing_keys": merged_candidates,
    }

    print(f"[合并] 唯一键: {stats['unique_keys']}, 已知: {stats['known_count']}, "
          f"缺失: {stats['missing_count']} "
          f"(stat={stats['by_category']['stat']}, "
          f"effect={stats['by_category']['effect']}, "
          f"other={stats['by_category']['other']})")
    print(f"[合并] 缺失键来源: base_only={stats['by_source']['base_only']}, "
          f"dlc1_only={stats['by_source']['dlc1_only']}, "
          f"both={stats['by_source']['both']}")
    print(f"[合并] 候选池: {len(merged_candidates)} "
          f"(base={len(base_missing_keys)}, dlc1={len(dlc_missing_keys)})")

    return result


def main():
    print("=" * 60)
    print("Brotato translations.csv 缺失键分析 (合并 base + dlc1)")
    print("=" * 60)

    # 解析 CSV
    print("\n解析 CSV...")
    base_csv = parse_csv(BASE_CSV)
    dlc_csv = parse_csv(DLC_CSV)
    base_missing = parse_missing_keys(base_csv)
    dlc_missing = parse_missing_keys(dlc_csv)
    print(f"基础 CSV: {len(base_csv)} 条 ({len(base_missing)} 个 MissingKey)")
    print(f"DLC1 CSV: {len(dlc_csv)} 条 ({len(dlc_missing)} 个 MissingKey)")

    # 收集 effect tres
    print("\n收集 effect tres...")
    base_effects = collect_effects_for_source(
        "base", PROJECT_ROOT, PROJECT_ROOT, exclude_dirs=["dlcs"])
    print(f"基础游戏: {len(base_effects)} 个 effect tres")

    dlc_root = PROJECT_ROOT / "dlcs" / "dlc_1"
    dlc_effects = collect_effects_for_source("dlc1", dlc_root, dlc_root)
    print(f"DLC1: {len(dlc_effects)} 个 effect tres")

    # 收集 dlc_1_data.gd 中 curse_item() 使用的 text_key
    print("\n收集 dlc_1_data.gd 中的 text_key...")
    dlc_gd_text_keys = collect_gd_text_keys(dlc_root, dlc_root, "dlc1")
    print(f"DLC1 .gd 文件: {len(dlc_gd_text_keys)} 个 text_key")
    dlc_effects.extend(dlc_gd_text_keys)

    # 合并分析
    print("\n合并分析...")
    merged_result = merge_and_analyze(
        base_effects, dlc_effects,
        base_csv, dlc_csv,
        base_missing, dlc_missing,
    )

    # 输出 JSON
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    merged_path = OUTPUT_DIR / "merged_analysis.json"

    with open(merged_path, "w", encoding="utf-8") as f:
        json.dump(merged_result, f, ensure_ascii=False, indent=2)
    print(f"\n合并分析结果 -> {merged_path}")

    # 打印缺失键样本
    print("\n" + "=" * 60)
    print(f"缺失键样本 (共 {len(merged_result['missing_keys'])} 个, 前 20):")
    print("=" * 60)
    for entry in merged_result["missing_keys"][:20]:
        src_str = "+".join(s.upper() for s in entry["sources"])
        print(f"  [{entry['category']:6s}] [{src_str:9s}] {entry['final_key']:45s} "
              f"(出现 {entry['occurrence_count']} 次, "
              f"来源: {', '.join(entry['source_names'][:3])})")

    print("\n完成!")


if __name__ == "__main__":
    main()
