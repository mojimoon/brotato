import os
import re
import json
import shutil
import csv
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent.parent
OUTPUT_DIR = BASE_DIR / "tools" / "web" / "public"
OUTPUT_JSON = OUTPUT_DIR / "brotato_data.json"
OUTPUT_ICONS = OUTPUT_DIR / "icons"

# ====================================================================
# Translation
# ====================================================================
TR = {}

# Global index for reverse lookup: English text -> translation key
TR_BY_EN = {}

def load_translations():
    """Load base + DLC translations"""
    global TR_BY_EN
    translations = {}
    
    def load_csv(path):
        if not path.exists():
            print(f"  WARNING: Translation not found: {path}")
            return
        with open(path, encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                key = row.get('key', '')
                if not key:
                    continue
                # Handle <!MissingKey:N:text> format
                original_key = key
                if key.startswith('<!MissingKey:'):
                    match = re.match(r'<!MissingKey:\d+:(.+)>', key)
                    if match:
                        key = match.group(1)
                    else:
                        continue
                en_text = row.get('en', '')
                translations[key] = {
                    'en': en_text,
                    'zh': row.get('zh', ''),
                }
                # Index by English text for reverse lookup
                if en_text and en_text not in TR_BY_EN:
                    TR_BY_EN[en_text] = key
    
    print("Loading translations...")
    load_csv(BASE_DIR / ".assets" / "resources" / "translations" / "translations.csv")
    load_csv(BASE_DIR / ".assets" / "dlcs" / "dlc_1" / "translations" / "translations.csv")
    print(f"  Loaded {len(translations)} translation keys")
    return translations

def tr(key, lang='en'):
    if key in TR:
        return TR[key].get(lang, key)
    return key

def load_merged_translations():
    """Load manually-fixed translation entries from translations_merged.json.
    
    This file contains en/zh templates for keys that were missing from the
    original translations.csv (identified via the <!MissingKey:N:text> entries).
    Each entry has a 'key' (uppercase), 'status' (matched/manual/skipped), 
    and 'en'/'zh' template strings.
    """
    merged_path = BASE_DIR / "tools" / "web" / "public" / "data" / "translations_merged.json"
    if not merged_path.exists():
        merged_path = BASE_DIR / "translations-fix" / "data" / "translations_merged_2026-06-21.json"
    if not merged_path.exists():
        print("  WARNING: translations_merged.json not found, skipping")
        return 0
    
    with open(merged_path, encoding='utf-8') as f:
        merged = json.load(f)
    
    count = 0
    for entry in merged.get('entries', []):
        if entry.get('status') not in ('matched', 'manual'):
            continue
        key = entry.get('key', '')
        en = entry.get('en', '')
        zh = entry.get('zh', '')
        if not key or not en:
            continue
        key_upper = key.upper()
        if key_upper not in TR:
            TR[key_upper] = {'en': en, 'zh': zh}
            if en and en not in TR_BY_EN:
                TR_BY_EN[en] = key_upper
            count += 1
        else:
            existing = TR[key_upper]
            if not existing.get('en') or existing['en'] == key_upper:
                TR[key_upper] = {'en': en, 'zh': zh}
                if en and en not in TR_BY_EN:
                    TR_BY_EN[en] = key_upper
                count += 1
    
    print(f"  Loaded {count} merged translation entries")
    return count

# ====================================================================
# .tres parser
# ====================================================================
def parse_tres_value(val_str):
    val_str = val_str.strip()
    if val_str == 'true': return True
    if val_str == 'false': return False
    m = re.match(r'^ExtResource\(\s*(\d+)\s*\)$', val_str)
    if m: return {'_ext': int(m.group(1))}
    if val_str == 'null' or val_str == '': return None
    if re.match(r'^-?\d+\.\d+$', val_str): return float(val_str)
    if re.match(r'^-?\d+$', val_str): return int(val_str)
    if val_str.startswith('"') and val_str.endswith('"'): return val_str[1:-1]
    if val_str.startswith('{') and val_str.endswith('}'): return parse_tres_dict(val_str)
    if val_str.startswith('[') and val_str.endswith(']'): return parse_tres_array(val_str[1:-1])
    return val_str

def parse_tres_dict(dict_str):
    result = {}
    content = dict_str[1:-1].strip()
    if not content: return result
    parts = split_by_comma(content)
    for part in parts:
        sep = ':=' if ':=' in part else (':' if ':' in part else ('=' if '=' in part else None))
        if sep:
            key, val = part.split(sep, 1)
            result[key.strip().strip('"')] = parse_tres_value(val.strip())
    return result

def parse_tres_array(arr_str):
    arr_str = arr_str.strip()
    if not arr_str or arr_str == ' ': return []
    parts = split_by_comma(arr_str)
    return [parse_tres_value(p.strip()) for p in parts]

def split_by_comma(content):
    parts = []
    depth = 0
    current = []
    in_string = False
    for ch in content:
        if ch == '"' and (not current or current[-1] != '\\'):
            in_string = not in_string
        if not in_string:
            if ch in '([{': depth += 1
            elif ch in ')]}': depth -= 1
            elif ch == ',' and depth == 0:
                parts.append(''.join(current).strip())
                current = []
                continue
        current.append(ch)
    if current:
        parts.append(''.join(current).strip())
    return parts

def parse_tres_file(filepath):
    with open(filepath, encoding='utf-8') as f:
        content = f.read()
    
    ext_resources = {}
    ext_pattern = re.compile(r'\[ext_resource\s+path="([^"]*)"\s+type="([^"]*)"\s+id=(\d+)\]')
    for m in ext_pattern.finditer(content):
        path = m.group(1)
        if path.startswith('res://'): path = path[6:]
        ext_resources[int(m.group(3))] = {'path': path, 'type': m.group(2)}
    
    res_match = re.search(r'\[resource\]\s*\n(.*)', content, re.DOTALL)
    if not res_match:
        return {'ext_resources': ext_resources, 'data': {}}
    
    res_content = res_match.group(1)
    lines = res_content.split('\n')
    current_key = None
    current_value_lines = []
    data = {}
    
    def flush():
        nonlocal current_key, current_value_lines
        if current_key is not None:
            val_str = ''.join(current_value_lines).strip()
            data[current_key] = parse_tres_value(val_str)
            current_key = None
            current_value_lines = []
    
    for line in lines:
        if '=' in line and current_key is None:
            eq_pos = line.index('=')
            key = line[:eq_pos].strip()
            val_start = line[eq_pos + 1:].strip()
            if (val_start.count('[') > val_start.count(']') or
                val_start.count('{') > val_start.count('}')):
                current_key = key
                current_value_lines = [val_start]
            else:
                data[key] = parse_tres_value(val_start)
        elif current_key is not None:
            current_value_lines.append(line)
            full = ''.join(current_value_lines)
            bracket_balance = 0
            brace_balance = 0
            in_str = False
            for ch in full:
                if ch == '"': in_str = not in_str
                if not in_str:
                    if ch == '[': bracket_balance += 1
                    elif ch == ']': bracket_balance -= 1
                    elif ch == '{': brace_balance += 1
                    elif ch == '}': brace_balance -= 1
            if bracket_balance == 0 and brace_balance == 0:
                flush()
    flush()
    return {'ext_resources': ext_resources, 'data': data}

# ====================================================================
# Data collection helpers
# ====================================================================
TIER_NAMES = {0: 'common', 1: 'uncommon', 2: 'rare', 3: 'legendary'}
WEAPON_TYPE_NAMES = {0: 'melee', 1: 'ranged'}

def find_icon_file(tres_path, parsed_data):
    ext = parsed_data.get('ext_resources', {})
    icon_val = parsed_data.get('data', {}).get('icon')
    if isinstance(icon_val, dict) and '_ext' in icon_val:
        ext_id = icon_val['_ext']
        if ext_id in ext:
            return ext[ext_id]['path']
    parent = tres_path.parent
    for pattern in ['*_icon.png', 'icon.png']:
        matches = list(parent.glob(pattern))
        if matches:
            return str(matches[0].relative_to(BASE_DIR))
    return None

def find_icon_for_dlc(tres_path, parsed_data):
    ext = parsed_data.get('ext_resources', {})
    icon_val = parsed_data.get('data', {}).get('icon')
    if isinstance(icon_val, dict) and '_ext' in icon_val:
        ext_id = icon_val['_ext']
        if ext_id in ext:
            return ext[ext_id]['path']
    parent = tres_path.parent
    for pattern in ['*_icon.png', 'icon.png']:
        matches = list(parent.glob(pattern))
        if matches: return str(matches[0].relative_to(BASE_DIR))
    if (parent.parent / (parent.parent.name + '_icon.png')).exists():
        return str((parent.parent / (parent.parent.name + '_icon.png')).relative_to(BASE_DIR))
    return None

# ====================================================================
# Effect system - comprehensive parsing
# ====================================================================

def parse_weapon_stats(filepath):
    """Parse projectile weapon_stats .tres"""
    if not filepath or not os.path.exists(filepath):
        return None
    parsed = parse_tres_file(filepath)
    data = parsed['data']
    
    stats = {
        'cooldown': data.get('cooldown', 0),
        'damage': data.get('damage', 0),
        'accuracy': data.get('accuracy', 1.0),
        'crit_chance': data.get('crit_chance', 0.03),
        'crit_damage': data.get('crit_damage', 1.5),
        'min_range': data.get('min_range', 0),
        'max_range': data.get('max_range', 150),
        'knockback': data.get('knockback', 0),
        'lifesteal': data.get('lifesteal', 0.0),
        'scaling_stats': data.get('scaling_stats', []),
        'effect_scale': data.get('effect_scale', 1.0),
        'is_healing': data.get('is_healing', False),
    }
    
    if 'nb_projectiles' in data:
        stats.update({
            'nb_projectiles': data.get('nb_projectiles', 1),
            'piercing': data.get('piercing', 0),
            'piercing_dmg_reduction': data.get('piercing_dmg_reduction', 0.5),
            'bounce': data.get('bounce', 0),
            'bounce_dmg_reduction': data.get('bounce_dmg_reduction', 0.5),
            'projectile_speed': data.get('projectile_speed', 3000),
        })
    
    if 'attack_type' in data:
        stats.update({
            'attack_type': data.get('attack_type', 0),
            'deal_dmg_on_return': data.get('deal_dmg_on_return', False),
            'alternate_attack_type': data.get('alternate_attack_type', False),
        })
    
    return stats

def parse_effect_file(filepath):
    """Full effect parsing including all possible fields"""
    if not filepath or not os.path.exists(filepath):
        return None
    parsed = parse_tres_file(filepath)
    data = parsed['data']
    ext = parsed['ext_resources']
    
    result = {
        'key': data.get('key', ''),
        'text_key': data.get('text_key', ''),
        'value': data.get('value', 0),
        'custom_key': data.get('custom_key', ''),
        'storage_method': data.get('storage_method', 0),
        'effect_sign': data.get('effect_sign', 3),
    }
    
    # Collect ALL extra numeric fields (value2, value3, interval, chance, etc.)
    extra_numerics = {}
    for field_name in ['value2', 'value3', 'interval', 'chance', 'max_stacks',
                         'nb_stat_scaled', 'duration_secs', 'scale',
                         'sound_db_mod', 'base_smoke_amount',
                         'for_every_health_percent', 'stat_nb', 'double_chance']:
        if field_name in data:
            extra_numerics[field_name] = data[field_name]
    if extra_numerics:
        result['extra'] = extra_numerics
    
    # Parse custom_args
    custom_args_raw = data.get('custom_args', [])
    if isinstance(custom_args_raw, list) and custom_args_raw:
        custom_args = []
        for ca in custom_args_raw:
            if isinstance(ca, dict) and '_ext' in ca:
                ext_id = ca['_ext']
                if ext_id in ext:
                    ca_path = BASE_DIR / ext[ext_id]['path']
                    if ca_path.exists():
                        ca_parsed = parse_tres_file(ca_path)
                        ca_data = ca_parsed['data']
                        custom_args.append({
                            'arg_index': ca_data.get('arg_index', 0),
                            'arg_sign': ca_data.get('arg_sign', 4),
                            'arg_value': ca_data.get('arg_value', 0),
                            'arg_format': ca_data.get('arg_format', 0),
                            'arg_key': ca_data.get('arg_key', ''),
                        })
        if custom_args:
            result['custom_args'] = custom_args
    
    # Parse boolean fields
    for bool_field in ['auto_target_enemy', 'reset_on_hit', 'perm_stats_only']:
        if bool_field in data:
            result[bool_field] = data[bool_field]
    
    # Parse weapon_stats reference
    weapon_stats_raw = data.get('weapon_stats')
    if isinstance(weapon_stats_raw, dict) and '_ext' in weapon_stats_raw:
        ext_id = weapon_stats_raw['_ext']
        if ext_id in ext:
            ws_path = BASE_DIR / ext[ext_id]['path']
            if ws_path.exists():
                result['weapon_stats'] = parse_weapon_stats(ws_path)
    
    # Parse burning_data reference (BurningEffect)
    burning_data_raw = data.get('burning_data')
    if isinstance(burning_data_raw, dict) and '_ext' in burning_data_raw:
        ext_id = burning_data_raw['_ext']
        if ext_id in ext:
            bd_path = BASE_DIR / ext[ext_id]['path']
            if bd_path.exists():
                bd_parsed = parse_tres_file(bd_path)
                bd_data = bd_parsed['data']
                result['burning_data'] = {
                    'chance': bd_data.get('chance', 0),
                    'damage': bd_data.get('damage', 0),
                    'duration': bd_data.get('duration', 0),
                    'spread': bd_data.get('spread', 0),
                    'scaling_stats': bd_data.get('scaling_stats', []),
                }
    
    # Parse sub_effects (WeaponEffectWithSubEffects)
    sub_effects_raw = data.get('sub_effects')
    if isinstance(sub_effects_raw, list) and sub_effects_raw:
        sub_effects = []
        for se in sub_effects_raw:
            if isinstance(se, dict) and '_ext' in se:
                ext_id = se['_ext']
                if ext_id in ext:
                    se_path = BASE_DIR / ext[ext_id]['path']
                    se_data = parse_effect_file(se_path)
                    if se_data:
                        sub_effects.append(se_data)
        if sub_effects:
            result['sub_effects'] = sub_effects
    
    # Parse weapon_stacked_name/stat_name (WeaponStackEffect)
    for sf in ['weapon_stacked_name', 'weapon_stacked_id', 'stat_displayed_name', 'stat_name', 'stat_displayed']:
        if sf in data:
            result[sf] = data[sf]
    
    # Parse stat_scaled / nb_stat_scaled / increased_stat_name (WeaponGainStatForEveryStatEffect / GainStatForEveryStatEffect)
    for gf in ['stat_scaled', 'nb_stat_scaled', 'increased_stat_name', 'stat']:
        if gf in data:
            result[gf] = data[gf]
    
    # Parse StructureEffect specific: spawn_cooldown
    if 'spawn_cooldown' in data:
        extra_numerics['spawn_cooldown'] = data['spawn_cooldown']
    
    # Parse stats reference (StructureEffect: landmine, turret, garden stats)
    stats_raw = data.get('stats')
    if isinstance(stats_raw, dict) and '_ext' in stats_raw:
        ext_id = stats_raw['_ext']
        if ext_id in ext:
            stats_path = BASE_DIR / ext[ext_id]['path']
            if stats_path.exists():
                ws = parse_weapon_stats(stats_path)
                if ws:
                    result['structure_stats'] = ws
    
    # Parse effects array (StructureEffect: sub-effects for structures)
    effects_raw = data.get('effects')
    if isinstance(effects_raw, list) and effects_raw:
        parsed_effects = []
        for se in effects_raw:
            if isinstance(se, dict) and '_ext' in se:
                ext_id = se['_ext']
                if ext_id in ext:
                    se_path = BASE_DIR / ext[ext_id]['path']
                    se_data = parse_effect_file(se_path)
                    if se_data:
                        parsed_effects.append(se_data)
        if parsed_effects:
            result['structure_effects'] = parsed_effects
    
    # Update extra after spawn_cooldown
    if extra_numerics:
        result['extra'] = extra_numerics
    
    return result

# ====================================================================
# Effect text rendering (preprocessing)
# ====================================================================

# ====================================================================
# Stat name -> display name mapping (from Godot translations)
# ====================================================================
STAT_DISPLAY = {
    'stat_max_hp': '最大生命值',
    'stat_damage': '伤害',
    'stat_percent_damage': '%伤害',
    'stat_armor': '护甲',
    'stat_crit_chance': '%暴击率',
    'stat_luck': '幸运',
    'stat_attack_speed': '%攻击速度',
    'stat_elemental_damage': '元素伤害',
    'stat_hp_regeneration': '生命再生',
    'stat_lifesteal': '%生命窃取',
    'stat_melee_damage': '近战伤害',
    'stat_ranged_damage': '远程伤害',
    'stat_dodge': '%闪避',
    'stat_engineering': '工程学',
    'stat_range': '范围',
    'stat_speed': '%速度',
    'stat_harvesting': '收获',
    'stat_knockback': '击退',
    'stat_xp_gain': '获得%经验',
    'xp_gain': '获得%经验',
    'stat_damage_against_bosses': '%对Boss伤害',
    'damage': '伤害',
    'stat_curse': '诅咒',
    'explosion_size': '爆炸范围',
    'stat_explosion_size': '爆炸范围',
    'explosion_damage': '爆炸伤害',
    'stat_explosion_damage': '爆炸伤害',
}

# Color markers for preprocessed text
GREEN = '<span class="g">'
RED = '<span class="r">'
PURPLE = '<span class="p">'
CLOSE = '</span>'

# English stat display names (override translations that have % prefix)
STAT_DISPLAY_EN = {
    'explosion_size': 'Explosion Size',
    'stat_explosion_size': 'Explosion Size',
    'explosion_damage': 'Explosion Damage',
    'stat_explosion_damage': 'Explosion Damage',
    'stat_percent_damage': '% Damage',
    'stat_attack_speed': '% Attack Speed',
    'stat_crit_chance': '% Crit Chance',
    'stat_dodge': '% Dodge',
    'stat_lifesteal': '% Life Steal',
    'stat_speed': '% Speed',
}

def stat_display_name(stat_key, lang='zh'):
    """Get the display name for a stat key"""
    if lang == 'zh' and stat_key in STAT_DISPLAY:
        return STAT_DISPLAY[stat_key]
    if lang == 'en' and stat_key in STAT_DISPLAY_EN:
        return STAT_DISPLAY_EN[stat_key]
    # Fall back to translation, stripping leading % if present
    translated = tr(stat_key.upper(), lang)
    if translated.startswith('% '):
        translated = translated[2:]
    return translated

def fmt_val(v, lang='zh', add_op=False, add_pct=False):
    """Format a numeric value with optional + prefix and % suffix"""
    s = str(v)
    if add_op and v > 0:
        s = '+' + s
    if add_pct:
        s = s + '%'
    return s

def needs_operator(key):
    """Check if a key needs + operator prefix (from Godot's keys_needing_operator)"""
    return key.lower() in {
        'stat_max_hp', 'stat_damage', 'stat_armor', 'stat_crit_chance', 'stat_luck',
        'stat_attack_speed', 'stat_elemental_damage', 'stat_hp_regeneration', 'stat_lifesteal',
        'stat_melee_damage', 'stat_percent_damage', 'stat_dodge', 'stat_engineering',
        'stat_range', 'stat_ranged_damage', 'stat_speed', 'stat_harvesting',
        'xp_gain', 'weapon_slot', 'items_price', 'weapons_price',
        'number_of_enemies', 'map_size', 'enemy_speed', 'enemy_health', 'enemy_damage',
        'effect_enemy_health', 'effect_enemy_speed', 'effect_knockback',
        'explosion_size', 'stat_explosion_size',
        'explosion_damage', 'stat_explosion_damage',
        'effect_gain_stat_every_killed_enemies', 'effect_damage_against_bosses',
        'stat_damage_against_bosses',
        'effect_pickup_range', 'pickup_range', 'knockback',
        'stat_curse',  # curse always shows +
    }

def needs_percent(key):
    """Check if a key needs % suffix.
    
    In Godot, keys_needing_percent is used for format string arg indices, not for 
    stat display names. Stat display names already include % where needed 
    (e.g., '%伤害' for stat_percent_damage). So we should NOT add % suffix for stat keys.
    
    The % suffix is only needed for non-stat keys where the raw value represents a 
    percentage (e.g., chance-based effects).
    """
    return key.lower() in {
        'effect_burn_chance', 'effect_explode_custom',
        'effect_damage_against_bosses',
        'stat_damage_against_bosses',
        'explosion_size', 'stat_explosion_size',
        'explosion_damage', 'stat_explosion_damage',
        'piercing_damage', 'effect_piercing_damage_short',
    }

def sign_color(eff):
    """Get sign color based on effect_sign and value"""
    sign = eff.get('effect_sign', 3)
    value = eff.get('value', 0)
    if sign == 0: return 'g'  # POSITIVE -> green
    elif sign == 1: return 'r'  # NEGATIVE -> red
    elif sign == 2: return ''  # NEUTRAL -> no color
    elif sign == 3:  # FROM_VALUE
        if value > 0: return 'g'
        elif value < 0: return 'r'
        return ''
    elif sign == 5: return 'p'  # OVERRIDE (curse) -> purple
    return ''

def wrap_color(text, color):
    """Wrap text with color span if color is specified"""
    if not color:
        return str(text)
    return f'<span class="{color}">{text}</span>'

# ====================================================================
# Effect text rendering (preprocessing)
# ====================================================================

def get_effect_format_string(eff):
    """Get the translation format string for an effect.
    
    In Godot's Effect.get_text():
    - key_text = key.to_upper() if text_key is empty else text_key.to_upper()
    - This key_text is used to look up the format string via Text.text()
    """
    text_key = eff.get('text_key', '')
    key = eff.get('key', '')
    
    # The actual key used by Godot for lookup
    actual_lookup = (text_key or key).upper()
    
    # Priority 1: Exact match with EFFECT_ prefix variants
    candidates = []
    if actual_lookup:
        candidates.append(actual_lookup)
        if actual_lookup.startswith('EFFECT_'):
            candidates.append(actual_lookup.replace('EFFECT_', '', 1))
        else:
            candidates.append('EFFECT_' + actual_lookup)
    
    for c in candidates:
        if c and c in TR:
            return c, TR[c]
    
    # Priority 2: text_key might be the English text itself (MissingKey format)
    if text_key and text_key in TR_BY_EN:
        real_key = TR_BY_EN[text_key]
        return real_key, TR[real_key]
    if key and key in TR_BY_EN:
        real_key = TR_BY_EN[key]
        return real_key, TR[real_key]
    
    # Priority 3: Search translations where the key contains the effect key name
    if key:
        key_lower = key.lower()
        for search_key, trans in TR.items():
            en = trans.get('en', '')
            if not en or '{0}' not in en:
                continue
            search_lower = search_key.lower()
            # Prefer exact match of key within search key (e.g., "explode" in "effect_explode_on_overkill")
            if key_lower in search_lower and 'and_burn' not in search_lower:
                return search_key, trans
    
    # Priority 4: Match by key name words
    if key:
        key_words = set(key.lower().replace('_', ' ').split())
        best_match = None
        best_score = 0
        for search_key, trans in TR.items():
            en = trans.get('en', '')
            if not en or '{0}' not in en:
                continue
            en_words = set(en.lower().replace('.', '').replace(',', '').replace('%', '').split())
            score = len(key_words & en_words)
            if score > best_score and score >= len(key_words):
                best_score = score
                best_match = (search_key, trans)
        if best_match and best_score >= 2:
            return best_match
    
    return None, None

def get_sign_color(eff):
    """Determine color based on effect_sign and value"""
    sign = eff.get('effect_sign', 3)
    value = eff.get('value', 0)
    if sign == 0:  # POSITIVE
        return '#5ee65e'  # green
    elif sign == 1:  # NEGATIVE
        return '#ff3333'  # red
    elif sign == 2:  # NEUTRAL
        return None  # no color
    elif sign == 3:  # FROM_VALUE
        if value > 0: return '#5ee65e'
        elif value < 0: return '#ff3333'
        return None
    elif sign == 5:  # OVERRIDE (curse)
        return '#b75cff'  # purple
    return None

def _fmt_extra_val(val):
    """Format an extra numeric value for display"""
    if isinstance(val, float):
        if val == int(val):
            return str(int(val))
        return str(val)
    return str(val)

def build_scaling_text(scaling_stats, lang='zh'):
    """Build scaling stat icon text like '100%<span class="ic" data-ic="ranged_damage"></span>'"""
    parts = []
    for ss in scaling_stats:
        if isinstance(ss, list) and len(ss) >= 2:
            pct = int(ss[1] * 100)
            stat_key = ss[0]  # e.g. "stat_ranged_damage"
            # Extract short key for data-ic: "stat_ranged_damage" -> "ranged_damage"
            ic_key = stat_key.replace('stat_', '', 1) if stat_key.startswith('stat_') else stat_key
            parts.append(f"{pct}%<span class=\"ic\" data-ic=\"{ic_key}\"></span>")
    return '+'.join(parts) if parts else ''


def render_effect_text(eff, lang):
    """Render an effect to human-readable text with color markup.
    
    Color markers: <span class="g">green</span>, <span class="r">red</span>, <span class="p">purple</span>
    These map to: positive/negative/curse colors in the frontend.
    
    The text follows the exact same logic as Godot's Effect.get_text() for each subclass.
    """
    key = eff.get('key', '')
    value = eff.get('value', 0)
    custom_key = eff.get('custom_key', '')
    extra = eff.get('extra', {})
    color = sign_color(eff)
    is_zh = (lang == 'zh')
    text_key = eff.get('text_key', '')
    tk_upper = (text_key or key).upper()
    
    # Define stat_keys early - used by multiple handlers before the generic section
    stat_keys = {
        'stat_max_hp', 'stat_damage', 'stat_percent_damage', 'stat_armor',
        'stat_crit_chance', 'stat_luck', 'stat_attack_speed', 'stat_elemental_damage',
        'stat_hp_regeneration', 'stat_lifesteal', 'stat_melee_damage', 'stat_ranged_damage',
        'stat_dodge', 'stat_engineering', 'stat_range', 'stat_speed',
        'stat_harvesting', 'stat_knockback', 'stat_curse', 'stat_xp_gain',
        'xp_gain', 'explosion_size', 'stat_explosion_size',
        'explosion_damage', 'stat_explosion_damage',
    }
    
    # ====================================================================
    # 1. ExplodingEffect (effect_explode, effect_explode_melee, effect_explode_custom)
    #    get_args() = [str(round(chance * 100.0))]
    # ====================================================================
    if key in ('effect_explode', 'effect_explode_melee', 'effect_explode_custom'):
        chance_val = extra.get('chance', 1.0)
        chance_pct = int(chance_val * 100)
        # For explode effects, color based on chance value since 'value' may be 0
        explode_color = 'g' if chance_val > 0 else color
        chance_str = wrap_color(f'{chance_pct}%', explode_color)
        
        if is_zh:
            if key == 'effect_explode':
                return f'投射物命中时有{chance_str}概率爆炸'
            elif key == 'effect_explode_melee':
                return f'击中时有{chance_str}概率爆炸'
            else:
                return f'有{chance_str}概率命中时爆炸'
        else:
            if key == 'effect_explode':
                return f'Projectiles have a {chance_str} chance to explode on hit'
            elif key == 'effect_explode_melee':
                return f'Hitting an enemy has a {chance_str} chance to make it explode'
            else:
                return f'{chance_str} chance to explode on hit'
    
    # ====================================================================
    # 2. BurningEffect (effect_burning)
    #    get_args() = [str(duration), str(damage), scaling_stats_text]
    # ====================================================================
    if key == 'effect_burning':
        bd = eff.get('burning_data', {})
        if bd:
            duration = bd.get('duration', 0)
            dmg = bd.get('damage', 0)
            scaling = bd.get('scaling_stats', [])
            scaling_text = build_scaling_text(scaling, lang)
            
            d_dur = wrap_color(str(duration), color)
            d_dmg = wrap_color(str(dmg), color)
            d_scaling = wrap_color(scaling_text, color) if scaling_text else ''
            
            spread_info = ''
            bd_spread = bd.get('spread', 0)
            if bd_spread > 0:
                spread_info = '，燃烧会蔓延至附近敌人' if is_zh else ', burning spreads to nearby enemies'
            
            if is_zh:
                return f'造成{d_dur}x{d_dmg}（{d_scaling}）燃烧伤害{spread_info}' if scaling_text else f'造成{d_dur}x{d_dmg}燃烧伤害{spread_info}'
            else:
                return f'Deals {d_dur}x{d_dmg} ({d_scaling}) burning damage{spread_info}' if scaling_text else f'Deals {d_dur}x{d_dmg} burning damage{spread_info}'
        else:
            if is_zh:
                return f'造成{wrap_color(str(value), color)}x{wrap_color(str(value), color)}燃烧伤害'
            return f'Deals {wrap_color(str(value), color)}x{wrap_color(str(value), color)} burning damage'
    
    # ====================================================================
    # 3. GainStatEveryKilledEnemiesEffect (effect_gain_stat_every_killed_enemies)
    #    get_args() = [str(stat_nb), tr(stat.to_upper()), str(value)]
    #    Godot format: "Every {0} enemies killed = +1 {1} (max {2})"
    #    But for weapons, the Chinese localization uses value as the kill count
    #    and stat_nb as the gain amount (usually 1). E.g.:
    #    Ghost Axe T1: value=20, stat_nb=1 -> "每击杀20名敌人便会+1%伤害"
    #    Ghost Axe T2: value=15, stat_nb=1 -> "每击杀15名敌人便会+1%伤害"
    # ====================================================================
    if key == 'effect_gain_stat_every_killed_enemies':
        stat_field = eff.get('stat', 'stat_percent_damage')
        stat_nb = eff.get('stat_nb', 1)
        s_name = stat_display_name(stat_field, lang)
        
        if is_zh:
            # In Chinese, value is the "every N kills" count, stat_nb is the gain
            s_nb = wrap_color(str(value), color)  # value = every X kills
            if stat_nb > 1:
                s_val = wrap_color(str(stat_nb), color)
                return f'每击杀{s_nb}名敌人便会{s_val}{s_name}'
            else:
                return f'每击杀{s_nb}名敌人便会+1{s_name}'
        else:
            s_nb = wrap_color(str(stat_nb), color)
            return f'Every {s_nb} enemies killed = +1 {s_name}'
    
    # ====================================================================
    # 4. SlowInZoneEffect
    #    get_args() = []
    # ====================================================================
    if key == 'effect_slow_in_zone':
        return '使投射物周围的敌人减速' if is_zh else 'Slows enemies around the projectiles'
    
    # ====================================================================
    # 5. CharmEffect / NullCharmEffect
    #    get_args() = [str(value2), str(chance), scaling_text, str(CHARM_DURATION=8)]
    #    value2 = HP threshold, value = chance%
    #    key may be '' or 'effect_charm', text_key = 'EFFECT_CHARM_BELOW_HP_NO_SCALING' etc.
    # ====================================================================
    if (key == 'effect_charm' or key == '' and 'CHARM' in tk_upper):
        val2 = extra.get('value2', 60)  # HP threshold
        chance_val = value  # chance%
        duration_secs = 8  # Utils.CHARM_DURATION (in seconds)
        
        s_hp = wrap_color(str(int(val2)) + '%', color)
        s_chance = wrap_color(str(int(chance_val)) + '%', color)
        s_dur = wrap_color(str(duration_secs), color)
        
        if is_zh:
            return f'击中生命值低于{s_hp}的敌人时，有{s_chance}的几率使其在{s_dur}秒内受到魅惑'
        else:
            return f'Hitting an enemy below {s_hp} health has a {s_chance} chance to charm it for {s_dur} seconds'
    
    # ====================================================================
    # 6. ProjectilesOnHitEffect (effect_projectiles_on_hit, EFFECT_PROJECTILES_ON_HIT)
    #    get_args() = [str(value), str(damage), str(bounce+1), scaling_text]
    # ====================================================================
    if key in ('effect_projectiles_on_hit', 'EFFECT_PROJECTILES_ON_HIT'):
        ws = eff.get('weapon_stats')
        if ws:
            nb = abs(value) if value else ws.get('nb_projectiles', 3)
            dmg = ws.get('damage', 0)
            scaling_text = build_scaling_text(ws.get('scaling_stats', []), lang)
            bounce = ws.get('bounce', 0) + 1
            
            s_nb = wrap_color(str(nb), color)
            s_dmg = wrap_color(str(dmg), color)
            s_scaling = wrap_color(scaling_text, color) if scaling_text else ''
            s_bounce = wrap_color(str(bounce), color)
            
            bounce_text = f'，最多反弹{s_bounce}次' if bounce > 1 else ''
            if is_zh:
                return f'击中敌人时产生{s_nb}投射物，造成{s_dmg}（{s_scaling}）伤害{bounce_text}' if scaling_text else f'击中敌人时产生{s_nb}投射物，造成{s_dmg}伤害{bounce_text}'
            else:
                return f'Hitting an enemy spawns {s_nb} projectiles dealing {s_dmg} ({s_scaling}) damage{bounce_text}' if scaling_text else f'Hitting an enemy spawns {s_nb} projectiles dealing {s_dmg} damage{bounce_text}'
    
    # ====================================================================
    # 7. Slow projectiles on hit (EFFECT_SLOW_PROJECTILES_ON_HIT)
    # ====================================================================
    if key == 'EFFECT_SLOW_PROJECTILES_ON_HIT':
        ws = eff.get('weapon_stats')
        if ws:
            nb = abs(value) if value else 2
            dmg = ws.get('damage', 0)
            scaling_text = build_scaling_text(ws.get('scaling_stats', []), lang)
            
            s_nb = wrap_color(str(nb), color)
            s_dmg = wrap_color(str(dmg), color)
            s_scaling = wrap_color(scaling_text, color) if scaling_text else ''
            
            if is_zh:
                return f'击中敌人时产生{s_nb}投射物，造成{s_dmg}（{s_scaling}）伤害并使周围的敌人减速' if scaling_text else f'击中敌人时产生{s_nb}投射物，造成{s_dmg}伤害并使周围的敌人减速'
            else:
                return f'Hitting an enemy spawns {s_nb} projectiles dealing {s_dmg} ({s_scaling}) damage and slowing enemies around them' if scaling_text else f'Hitting an enemy spawns {s_nb} projectiles dealing {s_dmg} damage and slowing enemies around them'
    
    # ====================================================================
    # 8. Lightning on hit (effect_lightning_on_hit)
    # ====================================================================
    if key == 'effect_lightning_on_hit':
        ws = eff.get('weapon_stats')
        if ws:
            dmg = ws.get('damage', 0)
            scaling_text = build_scaling_text(ws.get('scaling_stats', []), lang)
            bounce = ws.get('bounce', 0) + 1
            
            s_bounce = wrap_color(str(bounce), color)
            s_dmg = wrap_color(str(dmg), color)
            s_scaling = wrap_color(scaling_text, color) if scaling_text else ''
            
            if is_zh:
                return f'击中敌人时产生雷电投射物，反弹{s_bounce}次，造成{s_dmg}（{s_scaling}）伤害' if scaling_text else f'击中敌人时产生雷电投射物，反弹{s_bounce}次，造成{s_dmg}伤害'
            else:
                return f'Hitting an enemy spawns a lightning projectile that bounces {s_bounce} times dealing {s_dmg} ({s_scaling}) damage' if scaling_text else f'Hitting an enemy spawns a lightning projectile that bounces {s_bounce} times dealing {s_dmg} damage'
    
    # ====================================================================
    # 9. WeaponEffectWithSubEffects (modify_every_x_projectile)
    #    get_args() returns the sub_effect args
    # ====================================================================
    if key == 'modify_every_x_projectile':
        sub = eff.get('sub_effects', [])
        if sub and len(sub) > 0:
            sub_eff = sub[0]
            sub_key = sub_eff.get('key', '')
            sub_value = sub_eff.get('value', 0)
            sub_color = sign_color(sub_eff) or color or 'g'
            main_color = color or 'g'
            
            s_every = wrap_color(str(value), main_color)
            s_sub_val = wrap_color(str(sub_value), sub_color)
            s_sub_name = stat_display_name(sub_key, lang)
            
            if sub_key == 'stat_crit_chance':
                # Remove leading % from stat name to avoid double %%
                s_sub_name = s_sub_name.lstrip('%')
                if is_zh:
                    return f'每第{s_every}个投射物有{s_sub_val}%{s_sub_name}'
                else:
                    return f'Every {s_every}th projectile has {s_sub_val}% {s_sub_name}'
            else:
                if is_zh:
                    return f'每第{s_every}个投射物有{s_sub_val}{s_sub_name}'
                else:
                    return f'Every {s_every}th projectile has {s_sub_val} {s_sub_name}'
    
    # ====================================================================
    # 10. WeaponStackEffect (EFFECT_WEAPON_STACK)
    #     get_args() = [str(value), tr(stat_displayed_name), tr(weapon_stacked_name), str(nb*value)]
    # ====================================================================
    if key == 'EFFECT_WEAPON_STACK' and 'weapon_stacked_name' in eff:
        stacked_name = tr(eff['weapon_stacked_name'].upper(), lang)
        stat_key = eff.get('stat_displayed_name', 'stat_damage')
        stat_name = stat_display_name(stat_key, lang)
        
        s_val = wrap_color(fmt_val(value, add_op=needs_operator(stat_key), add_pct=needs_percent(stat_key)), color)
        
        if is_zh:
            return f'每额外持有1个{stacked_name}便会{s_val}{stat_name}'
        else:
            return f'Deals {s_val} {stat_name} for every additional {stacked_name} you have'
    
    # ====================================================================
    # 10b. NullDoubleValueEffect with EFFECT_STAT_ON_EVERY_STEP (登山杖 Hiking Stick)
    #     get_args() = [str(value), tr(key.to_upper()), str(value2)]
    #     Translation: "{0} {1} for every {2} steps you take during a wave"
    #     Chinese: "每在一波袭击中前进{2}步，可获得{0}{1}"
    # ====================================================================
    if tk_upper == 'EFFECT_STAT_ON_EVERY_STEP':
        steps = extra.get('value2', 70)
        s_steps = wrap_color(str(int(steps)), color)
        s_val = wrap_color(fmt_val(value, add_op=needs_operator(key), add_pct=needs_percent(key)), color)
        s_name = stat_display_name(key, lang)
        if is_zh:
            return f'每在一波袭击中前进{s_steps}步，可获得{s_val}{s_name}'
        else:
            return f'{s_val} {s_name} for every {s_steps} steps you take during a wave'
    
    # ====================================================================
    # 11. WeaponSlowOnHitEffect (effect_weapon_slow_on_hit / EFFECT_WEAPON_SLOW_ON_HIT)
    #     get_args() = [str(value), str(1), tr(scaling_stat), str(total_modifier)]
    #     Translation: "每拥有{1}{2}，攻击命中时会使敌人减速{0}[{3}]"
    #     Note: value = slow amount per point of scaling_stat
    # ====================================================================
    if key in ('effect_weapon_slow_on_hit', 'EFFECT_WEAPON_SLOW_ON_HIT'):
        scaling_stat = eff.get('scaling_stat', 'stat_engineering')
        s_slow = wrap_color(fmt_val(value, add_op=False, add_pct=True), color)
        s_per_every = wrap_color('1', color)
        s_stat = stat_display_name(scaling_stat, lang)
        
        if is_zh:
            return f'每拥有{s_per_every}{s_stat}，攻击命中时会使敌人减速{s_slow}'
        else:
            return f'Slows enemies by {s_slow} on hit for every {s_per_every} {s_stat} you have'
    
    # ====================================================================
    # 12. Various weapon-specific effects with text_key
    # ====================================================================
    
    # Consumable heal (砍刀 Chopper) - effect_consumable_heal
    # Needs + operator: "{0} HP recovered from consumables" -> "+1 HP recovered..."
    if key in ('consumable_heal', 'effect_consumable_heal'):
        s_val = wrap_color(fmt_val(value, add_op=True), color)
        return f'使用消耗品恢复{s_val}HP' if is_zh else f'{s_val} HP recovered from consumables'
    
    # Reload when pickup gold (EFFECT_WEAPONS_RELOAD_WHEN_PICKUP_GOLD / reload_when_pickup_gold)
    if key in ('reload_when_pickup_gold', 'effect_reload_when_pickup_gold'):
        return '捡起材料后会重置冷却时间' if is_zh else 'Picking up a material resets the cooldown'
    
    # Reload turrets on shoot
    if key in ('effect_reload_turrets_on_shoot', 'reload_turrets_on_shoot'):
        return '攻击时重置所有攻击型炮塔的冷却时间' if is_zh else 'Reloads all attack turrets when shooting'
    
    # 王者之剑 (Excalibur): effect_additional_weapon_bonus
    # key = stat_armor, text_key = effect_additional_weapon_bonus, value = -2
    # custom_args[0]: arg_index=2, arg_value=ADDITIONAL_WEAPONS (=value * num_weapons)
    # get_args() = [str(value), tr(key)] with custom_arg replacing arg[2]
    # Translation: "{0} {1} for every weapon you have [{2}]"
    # 中文: "每持有1件武器{0}{1} [{2}]"
    if tk_upper == 'EFFECT_ADDITIONAL_WEAPON_BONUS' or (key in stat_keys and eff.get('custom_key', '') == 'additional_weapon_effects'):
        s_val = wrap_color(fmt_val(value, add_op=needs_operator(key), add_pct=needs_percent(key)), color)
        stat_name = stat_display_name(key, lang)
        if is_zh:
            return f'每持有1件武器{s_val}{stat_name}'
        else:
            return f'{s_val} {stat_name} for every weapon you have'
    
    # Lose HP per second (大镰)
    if key in ('effect_lose_hp_per_second', 'lose_hp_per_second'):
        s_val = wrap_color(str(abs(value)), color)
        return f'每秒受到{s_val}伤害（不给予无敌时间）' if is_zh else f'Lose {s_val} HP per second (does not grant invincibility)'
    
    # 琉特琴 (Lute): PercentDamageEffect / WeaponPercentDamageEffect
    # text_key = EFFECT_INCREASE_DAMAGE_RECEIVED
    # get_args() = [str(value), tr(key), str(duration_secs), str(max_stacks*value)]
    # Translation: "Enemies hit take {0} more damage for {2} seconds (max: {3})"
    # value = 10 (%)  max_stacks*value = 30 (%)
    if tk_upper == 'EFFECT_INCREASE_DAMAGE_RECEIVED':
        duration = extra.get('duration_secs', 3)
        max_stacks = extra.get('max_stacks', 3)
        max_val = max_stacks * value
        s_val = wrap_color(fmt_val(value, add_op=False, add_pct=True), color)
        s_dur = wrap_color(str(duration), color)
        s_max = wrap_color(fmt_val(max_val, add_op=False, add_pct=True), color)
        if is_zh:
            return f'敌人会额外承受{s_val}伤害，持续{s_dur}秒（上限：{s_max}）'
        else:
            return f'Enemies hit take {s_val} more damage for {s_dur} seconds (max: {s_max})'
    
    # No hit boost (磁轨炮/钻机)
    # 磁轨炮: PlayerNoHitEffect, EFFECT_NO_HIT_BOOST
    #   get_args() = [str(value), str(interval)]  value=damage, interval=seconds
    #   Translation: "每{1}秒钟造成{0}点基础伤害，直到波次结束\n受到伤害时，加成重置"
    # 钻机 (Drill): uses effect_no_hit_boost with different stat
    if key == 'effect_no_hit_boost':
        interval = extra.get('interval', 5)
        stat_key = eff.get('stat', '')
        # 磁轨炮: no stat field, value is flat base damage
        # 钻机: has stat field (stat_attack_speed), value is stat gain
        if stat_key:
            stat_name = stat_display_name(stat_key, lang)
            s_val = wrap_color(fmt_val(value, add_op=needs_operator(stat_key), add_pct=not stat_name.startswith('%')), color)
            s_int = wrap_color(str(interval), color)
            return f'每{s_int}秒{s_val}{stat_name}，直至敌袭结束' if is_zh else f'Every {s_int}s {s_val} {stat_name} until end of wave'
        else:
            # 磁轨炮: flat base damage
            s_dmg = wrap_color(fmt_val(value, add_op=True), color)
            s_int = wrap_color(str(interval), color)
            if is_zh:
                return f'每{s_int}秒钟造成{s_dmg}点基础伤害，直到波次结束。受到伤害时，加成重置'
            else:
                return f'Deals {s_dmg} Base Damage every {s_int} seconds until the end of the wave\nBonus resets when taking damage'
    
    # Gain stat when hit (大镰 Scythe - 受到攻击时获得伤害加成)
    # key = stat_percent_damage, text_key = effect_on_hit, custom_key = temp_stats_on_hit
    # get_args() = [str(value), tr(displayed_key)]
    # Translation (via effect_on_hit): "{0} {1} on hit until the end of the wave"
    if key == 'effect_gain_stat_when_hit' or (key in stat_keys and eff.get('custom_key', '') == 'temp_stats_on_hit'):
        stat_key = eff.get('stat', key) if eff.get('stat') else key
        stat_name = stat_display_name(stat_key, lang)
        s_val = wrap_color(fmt_val(value, add_op=True, add_pct=not stat_name.startswith('%')), color)
        return f'受到攻击时{s_val}{stat_name}，直至敌袭结束' if is_zh else f'When hit: {s_val} {stat_name} until end of wave'
    
    # 船长的剑 (Captain Sword): WeaponGainStatForEveryStatEffect
    # text_key = EFFECT_WEAPON_DAMAGE_FOR_FREE_WEAPON_SLOTS
    # get_args() = [str(value), tr(key_arg), str(nb_stat_scaled), stat_scaled_text, str(bonus)]
    # Translation: "每有一个空闲的武器栏，将造成{0}{1}[{4}]"
    # value=25 (flat damage), stat_scaled=free_weapon_slots
    # Needs + operator on {0}
    if tk_upper == 'EFFECT_WEAPON_DAMAGE_FOR_FREE_WEAPON_SLOTS' or (key == 'stat_damage' and 'free_weapon_slots' in eff.get('stat_scaled', '')):
        stat_key = key if key.startswith('stat_') else 'stat_damage'
        s_val = wrap_color(fmt_val(value, add_op=True, add_pct=needs_percent(stat_key)), color)
        stat_name = stat_display_name(stat_key, lang)
        return f'每有一个空闲的武器栏，将造成{s_val}{stat_name}' if is_zh else f'Deals {s_val} {stat_name} for every free weapon slot'
    
    # 电锯: current HP as bonus damage
    # key may be 'effect_damage_based_on_current_hp' or 'bonus_current_health_damage'
    if key in ('effect_damage_based_on_current_hp', 'bonus_current_health_damage'):
        s_pct = wrap_color(str(value) + '%', color)
        v2 = extra.get('value2', None)
        if v2 is not None:
            s_boss_pct = wrap_color(str(int(v2)) + '%', color)
        else:
            s_boss_pct = wrap_color(str(int(value / 10)) + '%', color)
        return f'造成敌人当前生命值的{s_pct}以作为奖励伤害（头目和精英怪的{s_boss_pct}）' if is_zh else f'Deals {s_pct} of enemy current HP as bonus damage ({s_boss_pct} for bosses/elites)'
    
    # 磁轨炮: gain damage every N seconds, reset on hit
    # Temp stats per interval (Rail Gun, Drill, etc.)
    # key can be 'effect_temp_stats_per_interval' or a stat key with custom_key='temp_stats_per_interval'
    if key == 'effect_temp_stats_per_interval' or eff.get('custom_key', '') == 'temp_stats_per_interval':
        interval = extra.get('interval', 5)
        s_int = wrap_color(str(interval), color)
        # Determine stat key: use explicit stat field, or the key if it's a stat key, or default
        explicit_stat = eff.get('stat', '')
        if explicit_stat:
            stat_key = explicit_stat
        elif key.startswith('stat_'):
            stat_key = key
        else:
            stat_key = 'stat_damage'
        stat_name = stat_display_name(stat_key, lang)
        s_val = wrap_color(fmt_val(value, add_op=needs_operator(stat_key), add_pct=not stat_name.startswith('%')), color)
        reset = eff.get('reset_on_hit', True)
        if reset:
            return f'每{s_int}秒{s_val}{stat_name}，直到波次结束。受到伤害时，加成重置' if is_zh else f'Every {s_int}s gain {s_val} {stat_name} until end of wave. Resets on taking damage'
        else:
            return f'每{s_int}秒{s_val}{stat_name}，直至敌袭结束' if is_zh else f'Every {s_int}s {s_val} {stat_name} until end of wave'
    
    # 左轮手枪: additional cooldown every X shots
    if key == 'effect_additional_cooldown_every_x_shots':
        pass  # Handled by generic format below
    
    # Piercing on crit (十字弓)
    if key in ('pierce_on_crit', 'effect_pierce_on_crit'):
        s_val = wrap_color(str(value), color)
        return f'暴击时最多能贯通{s_val}次' if is_zh else f'Pierces up to {s_val} time(s) on critical hit'
    
    # Bounce on crit (手里剑)
    if key in ('bounce_on_crit', 'effect_bounce_on_crit'):
        s_val = wrap_color(str(value), color)
        return f'暴击时最多能反弹{s_val}次' if is_zh else f'Bounces up to {s_val} time(s) on critical hit'
    
    # Always crit on burning (勺子)
    if key == 'crit_on_hitting_burning_target':
        return '击中燃烧目标时总是造成暴击' if is_zh else 'Always deals critical hits to burning enemies'
    
    # ====================================================================
    # 13. StructureEffect (landmines, turrets, garden, etc.)
    #     text_key = "effect_landmines", "effect_turret", "effect_garden", etc.
    #     key is usually ""
    #     get_args() = [str(value), str(spawn_cd), str(damage), scaling_stats_names]
    # ====================================================================
    structure_text_keys = {
        'effect_landmines', 'effect_turret', 'effect_turret_flame',
        'effect_turret_laser', 'effect_turret_rocket', 'effect_garden',
    }
    if tk_upper in {k.upper() for k in structure_text_keys} or key in ('effect_spawn_garden', 'effect_spawn_landmine'):
        struct_stats = eff.get('structure_stats', {})
        spawn_cd = extra.get('spawn_cooldown', extra.get('interval', 0))
        # If spawn_cooldown is -1 or 0, use structure_stats cooldown (in frames, divide by 60 for seconds)
        if spawn_cd <= 0 and struct_stats:
            spawn_cd = struct_stats.get('cooldown', spawn_cd)
            # cooldown is in frames (60fps), convert to seconds for display
            spawn_cd = spawn_cd / 60.0
            if spawn_cd == int(spawn_cd):
                spawn_cd = int(spawn_cd)
        if spawn_cd <= 0:
            spawn_cd = 12  # default fallback
        s_val = wrap_color(str(value), color)
        s_cd = wrap_color(str(spawn_cd), color)
        
        dmg = struct_stats.get('damage', value) if struct_stats else value
        scaling = struct_stats.get('scaling_stats', []) if struct_stats else []
        scaling_text = build_scaling_text(scaling, lang)
        s_dmg = wrap_color(str(dmg), color)
        s_scaling = wrap_color(scaling_text, color) if scaling_text else ''
        
        tk_lower = (text_key or key).lower()
        
        if 'landmine' in tk_lower:
            if is_zh:
                return f'地雷每{s_cd}秒生成一次，并对一个区域造成{s_dmg}（{s_scaling}）伤害' if scaling_text else f'地雷每{s_cd}秒生成一次，并对一个区域造成{s_dmg}伤害'
            else:
                return f'Landmines spawn every {s_cd}s and deal {s_dmg} ({s_scaling}) damage in an area' if scaling_text else f'Landmines spawn every {s_cd}s and deal {s_dmg} damage in an area'
        
        elif 'garden' in tk_lower:
            if is_zh:
                return f'生成一个花园，每{s_cd}秒可以结下一种水果'
            else:
                return f'Creates a garden that produces a fruit every {s_cd}s'
        
        elif 'turret' in tk_lower:
            # Check for burning data - may be in top-level burning_data or in structure_effects
            bd = eff.get('burning_data')
            if not bd:
                # Check structure_effects for burning
                struct_effs = eff.get('structure_effects', [])
                for se in struct_effs:
                    if se.get('burning_data'):
                        bd = se['burning_data']
                        break
            
            if bd and ('flame' in tk_lower or 'burn' in tk_lower.lower()):
                bd_dmg = bd.get('damage', 5)
                bd_duration = bd.get('duration', 8)
                bd_scaling = build_scaling_text(bd.get('scaling_stats', []), lang)
                s_bd_dmg = wrap_color(str(bd_dmg), color)
                s_bd_dur = wrap_color(str(bd_duration), color)
                s_bd_scaling = wrap_color(bd_scaling, color) if bd_scaling else ''
                return f'生成1台燃烧炮塔，造成{s_bd_dur}x{s_bd_dmg}（{s_bd_scaling}）燃烧伤害' if is_zh else f'Summons a burning turret dealing {s_bd_dur}x{s_bd_dmg} ({s_bd_scaling}) burning damage'
            
            # Check for specific turret types from structure_stats
            piercing = struct_stats.get('piercing', 0) if struct_stats else 0
            
            if 'laser' in tk_lower:
                return f'生成1台发射贯通弹的炮塔，造成{s_dmg}（{s_scaling}）伤害' if is_zh else f'Summons a turret with piercing projectiles dealing {s_dmg} ({s_scaling}) damage'
            elif 'rocket' in tk_lower:
                return f'生成1台发射爆破弹的炮塔，造成{s_dmg}（{s_scaling}）范围伤害' if is_zh else f'Summons a turret with exploding projectiles dealing {s_dmg} ({s_scaling}) area damage'
            elif 'flame' in tk_lower:
                return f'生成1台燃烧炮塔，造成{s_dmg}（{s_scaling}）燃烧伤害' if is_zh else f'Summons a burning turret dealing {s_dmg} ({s_scaling}) burning damage'
            elif piercing > 0:
                return f'生成1台发射贯通弹的炮塔，造成{s_dmg}（{s_scaling}）伤害' if is_zh else f'Summons a turret with piercing projectiles dealing {s_dmg} ({s_scaling}) damage'
            else:
                return f'生成1台炮塔，造成{s_dmg}（{s_scaling}）伤害' if is_zh else f'Summons a turret dealing {s_dmg} ({s_scaling}) damage'
    
    # 园艺/修枝剪刀 (Pruner): spawn garden
    # TurretEffect with is_spawning=true
    # get_args() returns [str(spawn_cd / 60.0)] where spawn_cd comes from garden_stats.cooldown
    # garden_stats.cooldown = 900 (frames at 60fps) = 15 seconds
    if key == 'effect_spawn_garden':
        struct_stats = eff.get('structure_stats', {})
        if struct_stats:
            cd_frames = struct_stats.get('cooldown', 900)
            interval = cd_frames / 60.0
            if interval == int(interval):
                interval = int(interval)
        else:
            interval = extra.get('interval', 15)
        s_int = wrap_color(str(interval), color)
        return f'生成一个花园，每{s_int}秒可以结下一种水果' if is_zh else f'Creates a garden that produces a fruit every {s_int}s'
    
    # 螺丝刀: spawn landmine
    if key == 'effect_spawn_landmine':
        interval = extra.get('interval', 12)
        s_int = wrap_color(str(interval), color)
        s_dmg = wrap_color(str(value), color)
        scaling_text = '100%[工程学]' if is_zh else '100%[Engineering]'
        return f'地雷每{s_int}秒生成一次，并对一个区域造成{s_dmg}（{scaling_text}）伤害' if is_zh else f'Landmines spawn every {s_int}s and deal {s_dmg} ({scaling_text}) damage in an area'
    
    # 扳手: spawn turrets
    if key == 'effect_spawn_turret':
        ws = eff.get('weapon_stats')
        if ws:
            dmg = ws.get('damage', 10)
            scaling_text = build_scaling_text(ws.get('scaling_stats', []), lang)
            s_dmg = wrap_color(str(dmg), color)
            
            # Check if burning turret
            bd = eff.get('burning_data')
            if bd:
                bd_dmg = bd.get('damage', 5)
                bd_duration = bd.get('duration', 8)
                bd_scaling = build_scaling_text(bd.get('scaling_stats', []), lang)
                s_bd_dmg = wrap_color(str(bd_dmg), color)
                s_bd_dur = wrap_color(str(bd_duration), color)
                return f'生成1台燃烧炮塔，造成{s_bd_dur}x{s_bd_dmg}（{bd_scaling}）燃烧伤害' if is_zh else f'Summons a burning turret dealing {s_bd_dur}x{s_bd_dmg} ({bd_scaling}) burning damage'
            
            # Check for piercing projectile
            if ws.get('piercing', 0) > 0:
                return f'生成1台发射贯通弹的炮塔，造成{s_dmg}（{scaling_text}）伤害' if is_zh else f'Summons a turret with piercing projectiles dealing {s_dmg} ({scaling_text}) damage'
            
            # Check for exploding
            if eff.get('is_exploding', False) or ws.get('exploding', False):
                return f'生成1台发射爆破弹的炮塔，造成{s_dmg}（{scaling_text}）范围伤害' if is_zh else f'Summons a turret with exploding projectiles dealing {s_dmg} ({scaling_text}) area damage'
            
            return f'生成1台炮塔，造成{s_dmg}（{scaling_text}）伤害' if is_zh else f'Summons a turret dealing {s_dmg} ({scaling_text}) damage'
    
    # 砖块: weapon breaks and drops materials on hit
    # key = "break_on_hit", text_key = "effect_break_on_hit", NullDoubleValueEffect
    # value = chance%, value2 = materials
    if key == 'break_on_hit' or key == 'effect_break_on_hit':
        chance_pct = value  # value is the chance %
        s_chance = wrap_color(f'{chance_pct}%', color)
        materials = extra.get('value2', 10)
        # For brick: T1=10, T2=30, T3=75, T4=200 - but we show only the current tier
        s_mats = wrap_color(str(int(materials)) if isinstance(materials, float) else str(materials), color)
        return f'命中时武器有{s_chance}几率损坏并掉落{s_mats}材料' if is_zh else f'Weapon has a {s_chance} chance to break and drop {s_mats} materials on hit'
    
    # 尖牙 (Sharp Tooth): GainStatForEveryStatEffect
    # key = stat_lifesteal, text_key = EFFECT_GAIN_STAT_FOR_EVERY_PERCENT_PLAYER_MISSING_HEALTH
    # nb_stat_scaled = 25, stat_scaled = percent_player_missing_health
    # get_args() = [str(value), tr(key_arg), str(nb_stat_scaled), stat_scaled_text, str(bonus)]
    # Translation: "每损失{2}生命值，有{0}{1}[{4}]"
    if key == 'effect_player_missing_health_damage_bonus' or tk_upper == 'EFFECT_GAIN_STAT_FOR_EVERY_PERCENT_PLAYER_MISSING_HEALTH':
        hp_percent = extra.get('for_every_health_percent', extra.get('nb_stat_scaled', 25))
        s_hp = wrap_color(str(int(hp_percent)) + '%', color)
        stat_name = stat_display_name(key, lang)
        # key is stat_lifesteal, needs + operator
        s_val = wrap_color(fmt_val(value, add_op=True, add_pct=needs_percent(key)), color)
        return f'每损失{s_hp}生命值，有{s_val}{stat_name}' if is_zh else f'For every {s_hp} missing HP, {s_val} {stat_name}'
    
    # 三叉戟: bonus damage against high HP targets
    if key in ('effect_damage_against_high_hp_targets', 'bonus_damage_against_targets_above_hp'):
        hp_threshold = extra.get('value2', 80)
        s_hp = wrap_color(str(hp_threshold) + '%', color)
        stat_key = eff.get('stat', 'stat_percent_damage')
        stat_name = stat_display_name(stat_key, lang) if stat_key else ('%伤害' if is_zh else '% Damage')
        s_val = wrap_color(fmt_val(value, add_op=True, add_pct=not stat_name.startswith('%')), color)
        return f'对生命值超过{s_hp}的目标造成{s_val}{stat_name}' if is_zh else f'Deals {s_val} {stat_name} to enemies above {s_hp} HP'
    
    # 镰刀/镰 (Sickle): bonus damage against low HP targets
    # key = bonus_damage_against_targets_below_hp, text_key = EFFECT_BONUS_DAMAGE_AGAINST_TARGETS_BELOW_HP
    # This is NullDoubleValueEffect: get_args() = [str(value), tr(key), str(value2)]
    # value2 = HP threshold%, value = damage bonus%. Needs + operator.
    if key in ('effect_damage_against_low_hp_targets', 'bonus_damage_against_targets_below_hp'):
        hp_threshold = extra.get('value2', 30)
        s_hp = wrap_color(str(int(hp_threshold)) + '%', color)
        # Determine if this is percent damage or flat damage
        stat_key = eff.get('stat', '')
        if stat_key:
            stat_name = stat_display_name(stat_key, lang)
        else:
            stat_name = '伤害' if is_zh else 'damage'
        # Use + operator for bonus damage (镰刀/Sickle is a positive damage bonus)
        s_val = wrap_color(fmt_val(value, add_op=True, add_pct=not stat_name.startswith('%')), color)
        return f'对生命值低于{s_hp}的目标造成{s_val}{stat_name}' if is_zh else f'Deals {s_val} {stat_name} to enemies below {s_hp} HP'
    
    # 电击枪/鱼叉枪: slow on hit
    if key == 'effect_slow_projectiles_around':
        return '使投射物周围的敌人减速' if is_zh else 'Slows enemies around the projectiles'
    
    # 盗贼匕首/钻机: chance to gain material on crit kill
    if key == 'gold_on_crit_kill':
        s_val = wrap_color(str(value) + '%', color)
        return f'以暴击杀死敌人时有{s_val}概率获得1个材料' if is_zh else f'{s_val} chance to gain 1 material when killing an enemy with a critical hit'
    
    # 斩首剑 (Vorpal Sword): OneShotOnHitEffect
    # text_key = EFFECT_ONE_SHOT_ON_HIT_EFFECT
    # value is the % chance directly (1/2/3 = 1%/2%/3%)
    # Translation: "{0} chance to one shot the target when hitting it"
    if key == 'effect_one_shot_on_hit' or tk_upper == 'EFFECT_ONE_SHOT_ON_HIT_EFFECT':
        # value IS the chance percentage directly (1, 2, or 3)
        s_chance = wrap_color(f'{value}%', color)
        return f'{s_chance}几率在命中目标时直接将其秒杀' if is_zh else f'{s_chance} chance to instantly kill the target on hit'
    
    # 核弹发射器: explode on hit (this is via effect_explode but might be item_exploding)
    if key == 'effect_explode_melee':
        chance_val = extra.get('chance', 1.0)
        chance_pct = int(chance_val * 100)
        s_chance = wrap_color(f'{chance_pct}%', color)
        return f'击中时有{s_chance}概率爆炸' if is_zh else f'Hitting an enemy has a {s_chance} chance to make it explode'
    
    # 粉碎者: explode on projectile hit
    if key == 'effect_explode':
        chance_val = extra.get('chance', 1.0)
        chance_pct = int(chance_val * 100)
        s_chance = wrap_color(f'{chance_pct}%', color)
        return f'投射物命中时有{s_chance}概率爆炸' if is_zh else f'Projectiles have a {s_chance} chance to explode on hit'
    
    # ====================================================================
    # 15. StatGainsModificationEffect (effect_increase_stat_gains / EFFECT_REDUCE_STAT_GAINS)
    #     Godot get_args() = [tr(stat_displayed.to_upper()), str(abs(value))]
    #     Translation: "{0} modifications are increased by {1}" / "{0}的修改增加{1}"
    #     Translation: "{0} modifications are reduced by {1}" / "{0}的修改减少{1}"
    #     NOTE: stat_displayed = "stat_damage" -> "伤害", stat_displayed = "stat_percent_damage" -> "%伤害"
    # ====================================================================
    if key == 'effect_increase_stat_gains' or tk_upper == 'EFFECT_REDUCE_STAT_GAINS' or key == 'effect_reduce_stat_gains':
        stat_displayed = eff.get('stat_displayed', '')
        s_stat = stat_display_name(stat_displayed, lang) if stat_displayed else stat_display_name(key, lang)
        s_stat_colored = wrap_color(s_stat, color)
        s_val = wrap_color(str(abs(value)), color)
        
        if key == 'effect_increase_stat_gains' or tk_upper == 'EFFECT_INCREASE_STAT_GAINS':
            if is_zh:
                return f'{s_stat_colored}的修改增加{s_val}%'
            else:
                return f'{s_stat_colored} modifications are increased by {s_val}%'
        else:
            if is_zh:
                return f'{s_stat_colored}的修改减少{s_val}%'
            else:
                return f'{s_stat_colored} modifications are reduced by {s_val}%'
    
    # ====================================================================
    # 16. ItemExplodingEffect (explode_on_overkill) - DLC Ogre character
    #     Godot get_args() = [str(chance*100), str(total_damage), scaling_text, str(value)]
    #     Translation: "Enemies taking double their max health as damage explode for {1} ({2}) damage"
    # ====================================================================
    if key == 'explode_on_overkill' or tk_upper == 'EFFECT_EXPLODE_ON_OVERKILL':
        # Look up the DLC translation
        fmt_key, fmt_trans = get_effect_format_string(eff)
        if not fmt_trans:
            # Fallback: try the EFFECT_EXPLODE_ON_OVERKILL key directly
            if 'EFFECT_EXPLODE_ON_OVERKILL' in TR:
                fmt_trans = TR['EFFECT_EXPLODE_ON_OVERKILL']
        
        if fmt_trans:
            fmt = fmt_trans.get(lang, '') or fmt_trans.get('en', '')
            if fmt:
                # args: [0]=chance%, [1]=damage, [2]=scaling_text, [3]=value
                ws = eff.get('weapon_stats') or eff.get('structure_stats', {})
                if ws:
                    dmg = ws.get('damage', 0)
                    scaling_text = build_scaling_text(ws.get('scaling_stats', []), lang)
                else:
                    dmg = eff.get('value', 0)
                    scaling_text = ''
                
                s_chance = wrap_color(str(int(abs(value))), color)
                s_dmg = wrap_color(str(dmg), color)
                s_scaling = wrap_color(scaling_text, color) if scaling_text else ''
                
                result = fmt
                result = result.replace('{0}', s_chance)
                result = result.replace('{1}', s_dmg)
                result = result.replace('{2}', s_scaling)
                result = result.replace('{3}', wrap_color(str(abs(value)), color))
                return result
        
        # Hardcoded fallback
        ws = eff.get('weapon_stats') or eff.get('structure_stats', {})
        dmg = ws.get('damage', 0) if ws else value
        s_dmg = wrap_color(str(dmg), color)
        if is_zh:
            return f'敌人受到双倍于其最大生命值的伤害时会爆炸，造成{s_dmg}伤害'
        else:
            return f'Enemies taking double their max health as damage explode for {s_dmg} damage'
    
    # ====================================================================
    # Generic stat-based effects (the most common type)
    # Base Effect: get_args() = [str(value), tr(displayed_key.to_upper())]
    # stat_* keys are allowed to use hardcoded formatting since they are
    # well-known common patterns.
    # ====================================================================
    
    # (Hardcoded non-stat effect text removed - must use translations)
    if key in stat_keys and (text_key == 'effect_unique_weapon_bonus' or custom_key == 'unique_weapon_effects'):
        # Look up the EFFECT_UNIQUE_WEAPON_BONUS translation
        fmt_key, fmt_trans = get_effect_format_string(eff)
        if not fmt_trans and 'EFFECT_UNIQUE_WEAPON_BONUS' in TR:
            fmt_trans = TR['EFFECT_UNIQUE_WEAPON_BONUS']
        
        if fmt_trans:
            fmt = fmt_trans.get(lang, '') or fmt_trans.get('en', '')
            stat_name = stat_display_name(key, lang)
            s_val = wrap_color(fmt_val(value, add_op=needs_operator(key), add_pct=needs_percent(key)), color)
            # Format: {0}=value, {1}=stat_name, {2}=total (skip for static display)
            result = fmt
            result = result.replace('{0}', s_val)
            result = result.replace('{1}', stat_name)
            # Remove [{2}] bracket since we don't know weapon count
            result = re.sub(r'\s*\[\s*\{2\}\s*\]\s*', '', result)
            result = re.sub(r'\s*\{2\}\s*', '', result)
            result = result.strip()
            return result
        # No translation found - fall through to generic handler
    
    # Handle stat effects with special text_keys - must use translations, no guessing
    # These fall through to the text-key-based handler below if they have translations
    # (stat_* keys with simple "+X stat_name" are handled by the generic stat handler)
    
    # ====================================================================
    # TEXT-KEY-BASED FORMAT STRING RENDERING
    # For effects with text_key that have CSV translations, use the
    # format string. This must run BEFORE the generic stat_key handler,
    # otherwise effects like Baby Elephant (EFFECT_DEAL_DMG_WHEN_PICKUP_GOLD)
    # would be rendered as simple stat bonuses ("+25 Luck").
    # ====================================================================
    if text_key and key in stat_keys:
        fmt_key, fmt_trans = get_effect_format_string(eff)
        if fmt_trans:
            fmt = fmt_trans.get(lang, '') or fmt_trans.get('en', '')
            if fmt and '{' in fmt:
                args = [''] * 10
                ck = custom_key or ''
                extra = extra
                
                # --- Determine arg mapping based on text_key / custom_key ---
                damage_tks = {'EFFECT_DEAL_DMG_WHEN_PICKUP_GOLD', 'EFFECT_DEAL_DMG_WHEN_DEATH',
                    'EFFECT_DEAL_DMG_WHEN_DODGE', 'EFFECT_DEAL_DMG_WHEN_HEAL'}
                gain_every_tks = {'EFFECT_GAIN_STAT_FOR_EVERY_STAT', 'EFFECT_GAIN_STAT_FOR_EVERY_PERM_STAT',
                    'EFFECT_GAIN_STAT_FOR_EVERY_DIFFERENT_STAT', 'EFFECT_GAIN_STAT_FOR_EVERY_ENEMY',
                    'EFFECT_GAIN_STAT_FOR_EVERY_BURNING_ENEMY', 'EFFECT_GAIN_STAT_FOR_EVERY_TREE',
                    'EFFECT_GAIN_STAT_FOR_DUPLICATE_ITEMS'}
                
                if tk_upper in damage_tks or 'dmg_when' in ck or 'dmg_on' in ck:
                    # Damage trigger effects: {0}=chance%, {1}=1 (base dmg), {2}=scaling
                    chance_val = extra.get('chance', value)
                    args[0] = wrap_color(f'{int(chance_val)}%', color)
                    args[1] = wrap_color('1', color)
                    # Build scaling text using data-ic format
                    scaling_ic = build_scaling_text([[key, value / 100.0 if value else 0]], lang) if value else ''
                    args[2] = wrap_color(scaling_ic, color) if scaling_ic else ''
                
                elif tk_upper in gain_every_tks:
                    # GainStatForEveryStatEffect: {0}=value, {1}=stat, {2}=nb_scaled, {3}=scaled_stat, {4}=total
                    args[0] = wrap_color(fmt_val(value, add_op=needs_operator(key), add_pct=needs_percent(key)), color)
                    args[1] = stat_display_name(key, lang)
                    nb = extra.get('nb_stat_scaled', eff.get('stat_nb', eff.get('nb_stat_scaled', 0)))
                    if nb:
                        args[2] = wrap_color(str(int(nb)) if isinstance(nb, float) and nb == int(nb) else str(nb), color)
                    scaled_s = eff.get('stat_scaled', eff.get('stat', key))
                    if scaled_s:
                        args[3] = stat_display_name(scaled_s, lang)
                    # {4} = total bonus, skip since we don't know the real total
                
                elif tk_upper == 'EFFECT_GAIN_STATS_ON_REROLL' or ck == 'gain_stats_on_reroll':
                    # {2}=chance/value2, {0}=value, {1}=stat_name
                    args[0] = wrap_color(fmt_val(value, add_op=needs_operator(key), add_pct=needs_percent(key)), color)
                    args[1] = stat_display_name(key, lang)
                    v2 = extra.get('value2', extra.get('chance', 0))
                    args[2] = wrap_color(f'{int(v2)}%' if v2 <= 100 else f'{int(v2)}%', color) if v2 else ''
                
                elif tk_upper == 'EFFECT_STAT_ON_LEVEL_UP' or ck == 'stats_on_level_up':
                    args[0] = wrap_color(fmt_val(value, add_op=needs_operator(key), add_pct=needs_percent(key)), color)
                    args[1] = stat_display_name(key, lang)
                
                elif tk_upper == 'EFFECT_TEMP_STATS_PER_INTERVAL' or ck == 'temp_stats_per_interval':
                    args[0] = wrap_color(fmt_val(value, add_op=needs_operator(key), add_pct=needs_percent(key)), color)
                    args[1] = stat_display_name(key, lang)
                    iv = extra.get('interval', 5)
                    args[2] = wrap_color(str(int(iv)) if isinstance(iv, float) and iv == int(iv) else str(iv), color)
                
                elif tk_upper == 'EFFECT_DECAYING_STAT_ON_CONSUMABLE' or ck == 'decaying_stats_on_consumable':
                    args[0] = wrap_color(fmt_val(value, add_op=needs_operator(key), add_pct=needs_percent(key)), color)
                    args[1] = stat_display_name(key, lang)
                    dur = extra.get('value2', extra.get('duration_secs', 2))
                    args[2] = wrap_color(str(int(dur)) if isinstance(dur, float) and dur == int(dur) else str(dur), color)
                
                elif tk_upper == 'EFFECT_DECAYING_STAT_ON_HIT' or ck == 'decaying_stats_on_hit':
                    args[0] = wrap_color(fmt_val(value, add_op=needs_operator(key), add_pct=needs_percent(key)), color)
                    args[1] = stat_display_name(key, lang)
                    dur = extra.get('value2', extra.get('duration_secs', 0))
                    args[2] = wrap_color(str(int(dur)) if isinstance(dur, float) and dur == int(dur) else str(dur), color)
                
                elif tk_upper in ('EFFECT_TIER_IV_WEAPON_BONUS', 'EFFECT_TIER_I_WEAPON_BONUS') or ck in ('tier_iv_weapon_effects', 'tier_i_weapon_effects'):
                    args[0] = wrap_color(fmt_val(value, add_op=needs_operator(key), add_pct=needs_percent(key)), color)
                    args[1] = stat_display_name(key, lang)
                
                elif tk_upper == 'EFFECT_WEAPON_SCALING_STATS' or ck == 'weapon_scaling_stats':
                    args[0] = wrap_color(fmt_val(value, add_op=needs_operator(key), add_pct=needs_percent(key)), color)
                    args[1] = stat_display_name(key, lang)
                
                elif tk_upper == 'EFFECT_ENEMY_PERCENT_DAMAGE_TAKEN_ONCE':
                    args[0] = wrap_color(f'{value}%', color)
                    dur = extra.get('duration_secs', 3)
                    args[1] = wrap_color(str(int(dur)), color)
                    args[2] = stat_display_name(key, lang)
                
                elif tk_upper in ('EFFECT_TEMP_CONSUMABLE_STAT_WHILE_MAX', ) or ck == 'temp_consumable_stats_while_max':
                    args[0] = wrap_color(fmt_val(value, add_op=needs_operator(key), add_pct=needs_percent(key)), color)
                    args[1] = stat_display_name(key, lang)
                
                elif tk_upper == 'EFFECT_CONSUMABLE_STAT_WHILE_MAX' or ck == 'consumable_stats_while_max':
                    args[0] = wrap_color(fmt_val(value, add_op=needs_operator(key), add_pct=needs_percent(key)), color)
                    args[1] = stat_display_name(key, lang)
                
                elif tk_upper == 'EFFECT_CONSUMABLE_STAT_WHILE_MAX_LIMITED':
                    args[0] = wrap_color(fmt_val(value, add_op=needs_operator(key), add_pct=needs_percent(key)), color)
                    args[1] = stat_display_name(key, lang)
                    max_val = extra.get('max_stacks', 3)
                    args[2] = wrap_color(str(int(max_val)), color)
                
                elif tk_upper == 'EFFECT_STAT_ON_FRUIT' or ck == 'stats_on_fruit':
                    args[0] = wrap_color(fmt_val(value, add_op=needs_operator(key), add_pct=needs_percent(key)), color)
                    args[1] = stat_display_name(key, lang)
                    v2 = extra.get('value2', extra.get('chance', 0))
                    args[2] = wrap_color(f'{int(v2)}%', color) if v2 else ''
                
                elif tk_upper == 'EFFECT_TEMP_STAT_ON_DODGE' or ck == 'temp_stats_on_dodge':
                    args[0] = wrap_color(fmt_val(value, add_op=needs_operator(key), add_pct=needs_percent(key)), color)
                    args[1] = stat_display_name(key, lang)
                
                elif tk_upper == 'EFFECT_GAIN_STAT_WHEN_ATTACK_KILLED_ENEMIES' or ck == 'gain_stat_when_attack_killed_enemies':
                    args[0] = wrap_color(fmt_val(value, add_op=needs_operator(key), add_pct=needs_percent(key)), color)
                    args[1] = stat_display_name(key, lang)
                    kc = extra.get('stat_nb', extra.get('nb_stat_scaled', 2))
                    args[2] = wrap_color(str(int(kc)), color) if kc else ''
                
                elif tk_upper == 'EFFECT_GAIN_STAT_FOR_KILLED_ENEMIES_WHILE_BURNING' or ck == 'gain_stat_for_killed_enemies_while_burning':
                    kc = extra.get('stat_nb', extra.get('nb_stat_scaled', 5))
                    s_val_ck = wrap_color(fmt_val(value, add_op=needs_operator(key), add_pct=needs_percent(key)), color)
                    s_name_ck = stat_display_name(key, lang)
                    max_v = extra.get('max_stacks', 0)
                    args[0] = wrap_color(str(int(kc)), color) if kc else ''
                    args[1] = s_name_ck
                    args[2] = s_val_ck
                    args[3] = wrap_color(str(int(max_v)), color) if max_v else ''
                
                elif tk_upper == 'EFFECT_GAIN_STAT_FOR_EQUIPPED_ITEM_WITH_STAT':
                    args[0] = wrap_color(fmt_val(value, add_op=needs_operator(key), add_pct=needs_percent(key)), color)
                    args[1] = stat_display_name(key, lang)
                    scaled_s = eff.get('stat_scaled', eff.get('stat', key))
                    if scaled_s:
                        args[3] = stat_display_name(scaled_s, lang)
                
                else:
                    # Generic: {0}=value, {1}=stat_name, {2}+=extra fields in order
                    args[0] = wrap_color(fmt_val(value, add_op=needs_operator(key), add_pct=needs_percent(key)), color)
                    args[1] = stat_display_name(key, lang)
                    fmt_slots = sorted([int(m.group(1)) for m in re.finditer(r'\{(\d+)\}', fmt) if int(m.group(1)) > 1])
                    extra_fields = []
                    for fn in ['value2', 'interval', 'chance', 'nb_stat_scaled', 'duration_secs', 'max_stacks', 'scale']:
                        if fn in extra:
                            vv = extra[fn]
                            if fn == 'chance':
                                extra_fields.append(f'{int(vv)}%' if isinstance(vv, float) and vv <= 1 else f'{int(vv)}%')
                            elif fn == 'interval':
                                extra_fields.append(str(int(vv)) if isinstance(vv, float) and vv == int(vv) else str(vv))
                            else:
                                extra_fields.append(str(int(vv)) if isinstance(vv, float) and vv == int(vv) else str(vv))
                    for i, fv in enumerate(extra_fields):
                        if i < len(fmt_slots):
                            args[fmt_slots[i]] = wrap_color(fv, color)
                
                # Apply custom_args remapping
                for ca in eff.get('custom_args', []):
                    idx = ca.get('arg_index', 0)
                    av = ca.get('arg_value', 4)
                    while len(args) <= idx:
                        args.append('')
                    if av == 0:  # VALUE
                        args[idx] = str(value)
                    elif av == 1:  # ABS_VALUE
                        args[idx] = str(abs(value))
                
                # Fill format string
                result = fmt
                for i in range(len(args)):
                    if args[i]:
                        result = result.replace('{' + str(i) + '}', str(args[i]))
                result = re.sub(r'\s*\{\d+\}\s*', ' ', result)
                result = re.sub(r'[（(]\s*[）)]', '', result)
                result = re.sub(r'\[\s*\]', '', result)
                result = re.sub(r'\s+', ' ', result).strip()
                if result:
                    return result
    
    if key in stat_keys:
        # Special handling for XP Gain
        if key == 'xp_gain':
            s_val = wrap_color(fmt_val(value, add_op=needs_operator(key), add_pct=False), color)
            return f'{s_val}%经验获得' if is_zh else f'{s_val} XP Gain'
        
        s_val = wrap_color(fmt_val(value, add_op=needs_operator(key), add_pct=needs_percent(key)), color)
        s_name = stat_display_name(key, lang)
        
        # Special handling for negative values on speed (长矛)
        if key == 'stat_speed' and value < 0:
            return f'{s_val}{s_name}'
        
        return f'{s_val}{s_name}' if is_zh else f'{s_val} {s_name}'
    
    # For effects with custom_key = "starting_weapon" (character starting weapon effects)
    if custom_key == 'starting_weapon':
        s_val = wrap_color(fmt_val(value, add_op=needs_operator(key), add_pct=needs_percent(key)), color)
        displayed_key = key[:-2] if len(key) > 2 else key
        s_name = stat_display_name(displayed_key, lang)
        return f'{s_val}{s_name}' if is_zh else f'{s_val} {s_name}'
    
    # ====================================================================
    # Character/Item-specific effects
    # All text must come from translations (CSV + merged). No guessing.
    # If no translation found, fall through to the generic handler.
    # ====================================================================
    
    # Effects that are now handled by translation templates via the generic
    # handler below. Previously these had hardcoded text, but now they rely
    # on translations_merged.json providing the correct templates.
    # The keys below are handled by the generic handler (L2147+).
    
    # (All hardcoded text blocks removed - translations must come from TR)
    
    # ====================================================================
    # Pet / Projectile / Structure effects with weapon_stats
    # These effects have translation format strings that reference weapon_stats data
    # (damage, scaling_text, cooldown, etc.) which need to be extracted and filled in.
    # ====================================================================
    
    pet_text_keys = {
        'EFFECT_PET_RATZILLA', 'EFFECT_PET_LOOTWORM', 'EFFECT_PET_BLAZEMANDER',
        'EFFECT_PET_BONK_DOG', 'EFFECT_PET_BOT_O_MINE', 'EFFECT_PET_CATLING_GUN',
        'EFFECT_PET_DOC_MOTH', 'EFFECT_PET_SCAPEGOAT', 'EFFECT_PET_JELLYSHIELD',
        'EFFECT_ALIEN_EYES', 'EFFECT_TURRET_HEALING', 'EFFECT_BUILDER_TURRET',
        'EFFECT_BUILDER_TURRET_ALT', 'EFFECT_BUILDER_TURRET_UPGRADE',
        'EFFECT_TYLER', 'EFFECT_EXPLODE_AND_BURN_ON_CONSUMABLE',
    }
    
    if tk_upper in {k.upper() for k in pet_text_keys} or key in ('alien_eyes',):
        # Look up translation ONLY by exact text_key match (not fuzzy search)
        fmt_key = None
        fmt_trans = None
        for candidate in [tk_upper, 'EFFECT_' + tk_upper.replace('EFFECT_', '', 1)]:
            if candidate in TR:
                fmt_key = candidate
                fmt_trans = TR[candidate]
                break
        if not fmt_trans:
            # Try without EFFECT_ prefix
            candidate = tk_upper.replace('EFFECT_', '', 1)
            if candidate in TR:
                fmt_key = candidate
                fmt_trans = TR[candidate]
        
        if fmt_trans:
            fmt = fmt_trans.get(lang, '') or fmt_trans.get('en', '')
            if fmt:
                ws = eff.get('weapon_stats') or eff.get('structure_stats', {})
                bd = eff.get('burning_data', {})
                
                args = [''] * 15
                args[0] = wrap_color(str(value), color)  # {0} = value by default
                
                # --- Handle effects that don't need weapon_stats first ---
                # Lootworm pattern: {0}=double_chance% (no weapon_stats needed)
                if tk_upper == 'EFFECT_PET_LOOTWORM':
                    dc = extra.get('double_chance', 0)
                    if dc:
                        pct = int(dc * 100) if dc <= 1 else int(dc)
                        args[0] = wrap_color(f'{pct}%', color)
                    else:
                        args[0] = wrap_color(str(int(value * 10)) + '%', color)
                
                # Extract weapon/structure stats
                # Most effects: {0}=damage or nb, {1}=scaling_text
                elif ws:
                    dmg = ws.get('damage', 0)
                    scaling_text = build_scaling_text(ws.get('scaling_stats', []), lang)
                    cooldown = ws.get('cooldown', 0)
                    # cooldown is in frames (60fps), convert to seconds
                    if cooldown:
                        cd_sec = cooldown / 60.0
                        if cd_sec == int(cd_sec):
                            cd_sec = int(cd_sec)
                        else:
                            cd_sec = round(cd_sec, 1)
                            if cd_sec == int(cd_sec):
                                cd_sec = int(cd_sec)
                    else:
                        cd_sec = 0
                    
                    # Ratzilla pattern: {0}=damage, {1}=scaling_text
                    if tk_upper == 'EFFECT_PET_RATZILLA' or tk_upper == 'EFFECT_PET_CATLING_GUN':
                        args[0] = wrap_color(str(dmg), color) if dmg else wrap_color(str(value), color)
                        args[1] = wrap_color(scaling_text, color) if scaling_text else ''
                    
                    # Bonk Dog: {0}=pet_dmg, {1}=pet_scaling, {2}=cooldown, {3}=dash_dmg, {4}=dash_scaling
                    elif tk_upper == 'EFFECT_PET_BONK_DOG':
                        args[0] = wrap_color(str(dmg), color) if dmg else wrap_color(str(value), color)
                        args[1] = wrap_color(scaling_text, color) if scaling_text else ''
                        args[2] = wrap_color(str(cd_sec), color) if cd_sec else ''
                        # Check structure_effects for dash weapon stats
                        struct_effs = eff.get('structure_effects', [])
                        if struct_effs:
                            for se in struct_effs:
                                se_ws = se.get('weapon_stats') or se.get('structure_stats', {})
                                if se_ws:
                                    dash_dmg = se_ws.get('damage', 0)
                                    dash_scaling = build_scaling_text(se_ws.get('scaling_stats', []), lang)
                                    args[3] = wrap_color(str(dash_dmg), color) if dash_dmg else ''
                                    args[4] = wrap_color(dash_scaling, color) if dash_scaling else ''
                                    break
                    
                    # Bot-O-Mine: {0}=bullet_dmg, {1}=bullet_scaling, {2}=cd, {3}=mine_dmg, {4}=mine_scaling
                    elif tk_upper == 'EFFECT_PET_BOT_O_MINE':
                        args[0] = wrap_color(str(dmg), color) if dmg else wrap_color(str(value), color)
                        args[1] = wrap_color(scaling_text, color) if scaling_text else ''
                        args[2] = wrap_color(str(cd_sec), color) if cd_sec else ''
                        # Check structure_effects for landmine stats
                        struct_effs = eff.get('structure_effects', [])
                        if struct_effs:
                            for se in struct_effs:
                                se_ws = se.get('structure_stats') or se.get('weapon_stats', {})
                                if se_ws:
                                    mine_dmg = se_ws.get('damage', 0)
                                    mine_scaling = build_scaling_text(se_ws.get('scaling_stats', []), lang)
                                    args[3] = wrap_color(str(mine_dmg), color) if mine_dmg else ''
                                    args[4] = wrap_color(mine_scaling, color) if mine_scaling else ''
                                    break
                    
                    # Blazemander: {0}=pet_dmg, {1}=pet_scaling, {2}=burn_duration, {3}=burn_dmg, {4}=burn_scaling, {5}=cooldown, {6}=proj_dmg, {7}=proj_scaling
                    elif tk_upper == 'EFFECT_PET_BLAZEMANDER':
                        args[0] = wrap_color(str(dmg), color) if dmg else wrap_color(str(value), color)
                        args[1] = wrap_color(scaling_text, color) if scaling_text else ''
                        if bd:
                            args[2] = wrap_color(str(bd.get('duration', 0)), color)
                            args[3] = wrap_color(str(bd.get('damage', 0)), color)
                            bd_scaling = build_scaling_text(bd.get('scaling_stats', []), lang)
                            args[4] = wrap_color(bd_scaling, color) if bd_scaling else ''
                        args[5] = wrap_color(str(cd_sec), color) if cd_sec else ''
                        # Check structure_effects for projectile weapon_stats
                        struct_effs = eff.get('structure_effects', [])
                        if struct_effs:
                            for se in struct_effs:
                                se_ws = se.get('weapon_stats') or se.get('structure_stats', {})
                                if se_ws:
                                    proj_dmg = se_ws.get('damage', 0)
                                    proj_scaling = build_scaling_text(se_ws.get('scaling_stats', []), lang)
                                    args[6] = wrap_color(str(proj_dmg), color) if proj_dmg else ''
                                    args[7] = wrap_color(proj_scaling, color) if proj_scaling else ''
                                    break
                    
                    # Alien Eyes: {0}=nb, {1}=dmg, {3}=scaling, {4}=cooldown
                    elif tk_upper == 'EFFECT_ALIEN_EYES':
                        args[0] = wrap_color(str(value), color)
                        args[1] = wrap_color(str(dmg), color) if dmg else ''
                        args[3] = wrap_color(scaling_text, color) if scaling_text else ''
                        args[4] = wrap_color(str(cd_sec), color) if cd_sec else ''
                    
                    # Builder Turret: {4}=structure_range
                    elif 'BUILDER_TURRET' in tk_upper:
                        args[0] = wrap_color(str(dmg), color) if dmg else wrap_color(str(value), color)
                        args[1] = wrap_color(scaling_text, color) if scaling_text else ''
                        args[4] = tr('STRUCTURE_RANGE', lang)
                    
                    # Turret Healing
                    elif tk_upper == 'EFFECT_TURRET_HEALING':
                        args[0] = wrap_color(str(dmg) if dmg else str(value), color)
                        args[1] = wrap_color(scaling_text, color) if scaling_text else ''
                    
                    # Tyler: {0}=damage, {1}=scaling, {2}=nb_projectiles
                    elif tk_upper == 'EFFECT_TYLER':
                        nb = ws.get('nb_projectiles', 1)
                        args[0] = wrap_color(str(dmg), color) if dmg else wrap_color(str(value), color)
                        args[1] = wrap_color(scaling_text, color) if scaling_text else ''
                        args[2] = wrap_color(str(nb), color) if nb > 1 else ''
                    
                    # Chef: explode_on_consumable with burning
                    elif tk_upper == 'EFFECT_EXPLODE_AND_BURN_ON_CONSUMABLE':
                        if bd:
                            args[0] = wrap_color(str(int(value * 100)) + '%', color)  # scale%
                            bd_dmg = bd.get('damage', 0)
                            bd_dur = bd.get('duration', 0)
                            bd_scaling = build_scaling_text(bd.get('scaling_stats', []), lang)
                            # Build burning damage text: duration x damage (scaling)
                            args[1] = wrap_color(f'{bd_dur}x{bd_dmg}（{bd_scaling}）', color) if bd_scaling else wrap_color(f'{bd_dur}x{bd_dmg}', color)
                    else:
                        # Generic pet: {0}=value, {1}=scaling or stat
                        pass
                
                # Apply custom_args remapping
                for ca in eff.get('custom_args', []):
                    idx = ca.get('arg_index', 0)
                    av = ca.get('arg_value', 4)
                    ak = ca.get('arg_key', '')
                    while len(args) <= idx:
                        args.append('')
                    if av == 0:  # VALUE
                        args[idx] = str(value)
                    elif av == 1:  # ABS_VALUE
                        args[idx] = str(abs(value))
                    elif av == 2:  # KEY
                        key_to_tr = ak if ak else key
                        args[idx] = tr(key_to_tr.upper(), lang)
                
                # Apply format
                result = fmt
                for i in range(len(args)):
                    result = result.replace('{' + str(i) + '}', str(args[i]) if args[i] else '')
                # Cleanup
                result = re.sub(r'\s*\{\d+\}\s*', ' ', result)
                result = re.sub(r'\s+', ' ', result).strip()
                result = re.sub(r'[（(]\s*[）)]', '', result)
                result = re.sub(r'\[\s*\]', '', result)
                result = re.sub(r'\s+', ' ', result).strip()
                if result:
                    return result
    
    # Generic: Try format string from translations
    # For non-stat effects like pickup_range, knockback: apply operator/percent
    # based on the format_key (text_key or key), as Godot does in text.gd
    needs_op_key = tk_upper.lower() if tk_upper else key.lower()
    needs_pct_key = tk_upper.lower() if tk_upper else key.lower()
    fmt_key, fmt_trans = get_effect_format_string(eff)
    if fmt_trans:
        fmt = fmt_trans.get(lang, '') or fmt_trans.get('en', '')
        
        # Auto-prepend {0} if the key needs an operator but the template has no {0}
        # (mirrors text.gd L211-219: keys_needing_operator keys get {0} auto-prepended)
        lookup_key_lower = (text_key or key).lower()
        if '{0}' not in fmt and (needs_operator(lookup_key_lower) or key in stat_keys):
            # Prepend {0} without space if template starts with %, else with space
            if fmt.startswith('%'):
                fmt = '{0}' + fmt
            else:
                fmt = '{0} ' + fmt
        
        if fmt and '{' not in fmt:
            # Template has no placeholders even after auto-prepend - return as-is
            return fmt
        if fmt and '{' in fmt:
            # Build args array
            args = [''] * 10
            
            # For arg {0}: format value with operator/percent based on the FORMAT KEY
            # Godot uses keys_needing_operator / keys_needing_percent on the format key
            fmt_key_lower = (fmt_key or '').lower()
            
            # Non-stat keys that need % display in format strings
            needs_pct_keys = {
                'effect_instant_gold_attracting', 'effect_piercing_damage',
                'effect_piercing_damage_short',
            }
            # Non-stat keys that need operator (+) in format strings
            needs_op_keys = {
                'effect_item_box_gold',
            }
            
            needs_op = (fmt_key_lower in needs_op_keys
                        or any(fmt_key_lower.startswith(prefix) for prefix in [
                'effect_pickup_range', 'effect_knockback',
            ]) or needs_operator(lookup_key_lower) or (key in stat_keys and needs_operator(key)))
            needs_pct = (fmt_key_lower in needs_pct_keys
                         or fmt_key_lower.startswith('effect_pickup_range')
                         or (key in stat_keys and needs_percent(key)))
            args[0] = wrap_color(fmt_val(value, add_op=needs_op, add_pct=needs_pct), color)
            
            # {1} = tr(key.to_upper()) by default (from effect.gd get_args)
            # stat_display_name falls back to tr(key.upper()) for non-stat keys
            args[1] = stat_display_name(key, lang) if key else ''
            
            # Override {1} with damage if we have weapon/structure stats and key is not a stat/item key
            ws = eff.get('weapon_stats') or eff.get('structure_stats', {})
            if ws:
                format_slots = sorted([int(m.group(1)) for m in re.finditer(r'\{(\d+)\}', fmt)])
                ws_dmg = ws.get('damage', 0)
                ws_scaling = build_scaling_text(ws.get('scaling_stats', []), lang)
                # If format has {1} and we have weapon/structure stats with damage,
                # and the key is not a stat key (stat keys use {1} for stat name)
                if 1 in format_slots and ws_dmg and key not in stat_keys:
                    args[1] = wrap_color(str(ws_dmg), color)
            
            # For effects with 'chance' in extra, {0} is often the chance percentage
            # rather than the raw value (e.g., explode_on_hit, burn_chance)
            if 'chance' in extra and extra['chance']:
                chance_pct = int(extra['chance'] * 100) if extra['chance'] <= 1 else int(extra['chance'])
                args[0] = wrap_color(f'{chance_pct}%', color)
            
            # If format has {2} and we have scaling_stats, assign scaling to {2}
            if ws and ws_scaling:
                format_slots_asc = sorted([int(m.group(1)) for m in re.finditer(r'\{(\d+)\}', fmt)])
                if 2 in format_slots_asc:
                    args[2] = wrap_color(ws_scaling, color)
            
            # Collect extra fields in order, assign to format slots > 1
            extra_fields_list = []
            for fn in ['value2', 'interval', 'nb_stat_scaled']:
                if fn in extra:
                    extra_fields_list.append(wrap_color(str(extra[fn]), color))
            if 'chance' in extra:
                extra_fields_list.append(wrap_color(str(int(extra['chance'] * 100)) + '%', color))
            if 'duration_secs' in extra:
                extra_fields_list.append(wrap_color(str(extra['duration_secs']), color))
            if 'max_stacks' in extra:
                extra_fields_list.append(wrap_color(str(extra['max_stacks']), color))
            
            # Map extra fields to format slots > 1 in ascending order
            format_slots_asc = sorted([int(m.group(1)) for m in re.finditer(r'\{(\d+)\}', fmt)])
            extra_slots = [s for s in format_slots_asc if s > 1]
            for i, fv in enumerate(extra_fields_list):
                if i < len(extra_slots):
                    args[extra_slots[i]] = fv
            
            # Apply custom_args remapping
            for ca in eff.get('custom_args', []):
                idx = ca.get('arg_index', 0)
                arg_value_type = ca.get('arg_value', 4)
                arg_key = ca.get('arg_key', '')
                while len(args) <= idx:
                    args.append('')
                if arg_value_type == 0:  # VALUE
                    args[idx] = str(value)
                elif arg_value_type == 1:  # ABS_VALUE
                    args[idx] = str(abs(value))
                elif arg_value_type == 2:  # KEY
                    key_to_tr = arg_key if arg_key else key
                    args[idx] = tr(key_to_tr.upper(), lang)
            
            result = fmt
            for i in range(len(args)):
                result = result.replace('{' + str(i) + '}', str(args[i]) if args[i] else '')
            result = re.sub(r'\s*\{\d+\}\s*', ' ', result)
            result = re.sub(r'\s+', ' ', result).strip()
            result = re.sub(r'[（(]\s*[）)]', '', result)
            result = re.sub(r'\[\s*\]', '', result)
            result = re.sub(r'\s+', ' ', result).strip()
            if result:
                return result
    
    # Fallback for completely unknown effects
    s_val = wrap_color(str(value), color)
    s_key = tr(key.upper(), lang) if key else ''
    return f'{s_val} {s_key}' if lang == 'en' else f'{s_val}{s_key}'

def render_effect_text_en(eff):
    return render_effect_text(eff, 'en')

def render_effect_text_zh(eff):
    return render_effect_text(eff, 'zh')

# ====================================================================
# Set bonuses
# ====================================================================

SET_EFFECTS_MANUAL = {
    # key: name_key -> {en_desc, zh_desc} for each tier
    'WEAPON_CLASS_BLADE': {
        'name_en': 'Blade',
        'name_zh': '利器',
        'effects': [
            {'en': '+1 Melee Damage, +1% Lifesteal', 'zh': '+1 近战伤害，+1% 生命窃取'},
            {'en': '+2 Melee Damage, +2% Lifesteal', 'zh': '+2 近战伤害，+2% 生命窃取'},
            {'en': '+3 Melee Damage, +3% Lifesteal', 'zh': '+3 近战伤害，+3% 生命窃取'},
            {'en': '+4 Melee Damage, +4% Lifesteal', 'zh': '+4 近战伤害，+4% 生命窃取'},
            {'en': '+5 Melee Damage, +5% Lifesteal', 'zh': '+5 近战伤害，+5% 生命窃取'},
        ]
    },
    'WEAPON_CLASS_BLUNT': {
        'name_en': 'Blunt',
        'name_zh': '钝器',
        'effects': [
            {'en': '+1 Armor, +0 Max HP, -2% Speed', 'zh': '+1 护甲，-2% 速度'},
            {'en': '+1 Armor, +3 Max HP, -4% Speed', 'zh': '+1 护甲，+3 最大生命值，-4% 速度'},
            {'en': '+2 Armor, +3 Max HP, -6% Speed', 'zh': '+2 护甲，+3 最大生命值，-6% 速度'},
            {'en': '+2 Armor, +6 Max HP, -8% Speed', 'zh': '+2 护甲，+6 最大生命值，-8% 速度'},
            {'en': '+3 Armor, +6 Max HP, -10% Speed', 'zh': '+3 护甲，+6 最大生命值，-10% 速度'},
        ]
    },
    'WEAPON_CLASS_ELEMENTAL': {
        'name_en': 'Elemental',
        'name_zh': '元素',
        'effects': [
            {'en': '+1 Elemental Damage', 'zh': '+1 元素伤害'},
            {'en': '+2 Elemental Damage', 'zh': '+2 元素伤害'},
            {'en': '+3 Elemental Damage', 'zh': '+3 元素伤害'},
            {'en': '+4 Elemental Damage', 'zh': '+4 元素伤害'},
            {'en': '+5 Elemental Damage', 'zh': '+5 元素伤害'},
        ]
    },
    'WEAPON_CLASS_ETHEREAL': {
        'name_en': 'Ethereal',
        'name_zh': '虚灵',
        'effects': [
            {'en': '+6% Dodge, -1 Armor', 'zh': '+6% 闪避，-1 护甲'},
            {'en': '+12% Dodge, -2 Armor', 'zh': '+12% 闪避，-2 护甲'},
            {'en': '+18% Dodge, -3 Armor', 'zh': '+18% 闪避，-3 护甲'},
            {'en': '+24% Dodge, -4 Armor', 'zh': '+24% 闪避，-4 护甲'},
            {'en': '+30% Dodge, -5 Armor', 'zh': '+30% 闪避，-5 护甲'},
        ]
    },
    'WEAPON_CLASS_EXPLOSIVE': {
        'name_en': 'Explosive',
        'name_zh': '爆炸',
        'effects': [
            {'en': '+5% Explosive Size', 'zh': '+5% 爆炸范围'},
            {'en': '+10% Explosive Size', 'zh': '+10% 爆炸范围'},
            {'en': '+15% Explosive Size', 'zh': '+15% 爆炸范围'},
            {'en': '+20% Explosive Size', 'zh': '+20% 爆炸范围'},
            {'en': '+25% Explosive Size', 'zh': '+25% 爆炸范围'},
        ]
    },
    'WEAPON_CLASS_GUN': {
        'name_en': 'Gun',
        'name_zh': '枪械',
        'effects': [
            {'en': '+10 Range', 'zh': '+10 范围'},
            {'en': '+20 Range', 'zh': '+20 范围'},
            {'en': '+30 Range', 'zh': '+30 范围'},
            {'en': '+40 Range', 'zh': '+40 范围'},
            {'en': '+50 Range', 'zh': '+50 范围'},
        ]
    },
    'WEAPON_CLASS_HEAVY': {
        'name_en': 'Heavy',
        'name_zh': '重型',
        'effects': [
            {'en': '+5% Damage', 'zh': '+5% 伤害'},
            {'en': '+10% Damage', 'zh': '+10% 伤害'},
            {'en': '+15% Damage', 'zh': '+15% 伤害'},
            {'en': '+20% Damage', 'zh': '+20% 伤害'},
            {'en': '+25% Damage', 'zh': '+25% 伤害'},
        ]
    },
    'WEAPON_CLASS_LEGENDARY': {
        'name_en': 'Legendary',
        'name_zh': '传奇',
        'effects': [
            {'en': '-20 Max HP', 'zh': '-20 最大生命值'},
            {'en': '-40 Max HP', 'zh': '-40 最大生命值'},
            {'en': '-60 Max HP', 'zh': '-60 最大生命值'},
            {'en': '-80 Max HP', 'zh': '-80 最大生命值'},
            {'en': '-100 Max HP', 'zh': '-100 最大生命值'},
        ]
    },
    'WEAPON_CLASS_MEDICAL': {
        'name_en': 'Medical',
        'name_zh': '医疗',
        'effects': [
            {'en': '+1 HP Regeneration', 'zh': '+1 生命再生'},
            {'en': '+2 HP Regeneration', 'zh': '+2 生命再生'},
            {'en': '+3 HP Regeneration', 'zh': '+3 生命再生'},
            {'en': '+4 HP Regeneration', 'zh': '+4 生命再生'},
            {'en': '+5 HP Regeneration', 'zh': '+5 生命再生'},
        ]
    },
    'WEAPON_CLASS_MEDIEVAL': {
        'name_en': 'Medieval',
        'name_zh': '中世纪',
        'effects': [
            {'en': '+1 Armor, +0% Dodge', 'zh': '+1 护甲'},
            {'en': '+1 Armor, +3% Dodge', 'zh': '+1 护甲，+3% 闪避'},
            {'en': '+2 Armor, +3% Dodge', 'zh': '+2 护甲，+3% 闪避'},
            {'en': '+2 Armor, +6% Dodge', 'zh': '+2 护甲，+6% 闪避'},
            {'en': '+3 Armor, +6% Dodge', 'zh': '+3 护甲，+6% 闪避'},
        ]
    },
    'WEAPON_CLASS_MUSIC': {
        'name_en': 'Music',
        'name_zh': '音乐',
        'effects': [
            {'en': '+5 Luck', 'zh': '+5 幸运'},
            {'en': '+10 Luck', 'zh': '+10 幸运'},
            {'en': '+15 Luck', 'zh': '+15 幸运'},
            {'en': '+20 Luck', 'zh': '+20 幸运'},
            {'en': '+25 Luck', 'zh': '+25 幸运'},
        ]
    },
    'WEAPON_CLASS_NAVAL': {
        'name_en': 'Naval',
        'name_zh': '海军',
        'effects': [
            {'en': '+1 Curse', 'zh': '+1 诅咒'},
            {'en': '+2 Curse', 'zh': '+2 诅咒'},
            {'en': '+3 Curse', 'zh': '+3 诅咒'},
            {'en': '+4 Curse', 'zh': '+4 诅咒'},
            {'en': '+5 Curse', 'zh': '+5 诅咒'},
        ]
    },
    'WEAPON_CLASS_PRECISE': {
        'name_en': 'Precise',
        'name_zh': '精准',
        'effects': [
            {'en': '+3% Crit Chance', 'zh': '+3% 暴击率'},
            {'en': '+6% Crit Chance', 'zh': '+6% 暴击率'},
            {'en': '+9% Crit Chance', 'zh': '+9% 暴击率'},
            {'en': '+12% Crit Chance', 'zh': '+12% 暴击率'},
            {'en': '+15% Crit Chance', 'zh': '+15% 暴击率'},
        ]
    },
    'WEAPON_CLASS_PRIMITIVE': {
        'name_en': 'Primitive',
        'name_zh': '原始',
        'effects': [
            {'en': '+3 Max HP', 'zh': '+3 最大生命值'},
            {'en': '+6 Max HP', 'zh': '+6 最大生命值'},
            {'en': '+9 Max HP', 'zh': '+9 最大生命值'},
            {'en': '+12 Max HP', 'zh': '+12 最大生命值'},
            {'en': '+15 Max HP', 'zh': '+15 最大生命值'},
        ]
    },
    'WEAPON_CLASS_SUPPORT': {
        'name_en': 'Support',
        'name_zh': '辅助',
        'effects': [
            {'en': '+5 Harvesting', 'zh': '+5 收获'},
            {'en': '+10 Harvesting', 'zh': '+10 收获'},
            {'en': '+15 Harvesting', 'zh': '+15 收获'},
            {'en': '+20 Harvesting', 'zh': '+20 收获'},
            {'en': '+25 Harvesting', 'zh': '+25 收获'},
        ]
    },
    'WEAPON_CLASS_TOOL': {
        'name_en': 'Tool',
        'name_zh': '工具',
        'effects': [
            {'en': '+1 Engineering', 'zh': '+1 工程学'},
            {'en': '+2 Engineering', 'zh': '+2 工程学'},
            {'en': '+3 Engineering', 'zh': '+3 工程学'},
            {'en': '+4 Engineering', 'zh': '+4 工程学'},
            {'en': '+5 Engineering', 'zh': '+5 工程学'},
        ]
    },
    'WEAPON_CLASS_UNARMED': {
        'name_en': 'Unarmed',
        'name_zh': '徒手',
        'effects': [
            {'en': '+3% Dodge', 'zh': '+3% 闪避'},
            {'en': '+6% Dodge', 'zh': '+6% 闪避'},
            {'en': '+9% Dodge', 'zh': '+9% 闪避'},
            {'en': '+12% Dodge', 'zh': '+12% 闪避'},
            {'en': '+15% Dodge', 'zh': '+15% 闪避'},
        ]
    },
}

def build_sets_data():
    """Build set bonuses from game data + manual fallback"""
    sets_data = {}
    
    for set_dir in [BASE_DIR / "items" / "sets", BASE_DIR / "dlcs" / "dlc_1" / "sets"]:
        if not set_dir.exists():
            continue
        for set_file in set_dir.rglob("*_set_data.tres"):
            if 'appearance' in set_file.name.lower():
                continue
            parsed = parse_tres_file(set_file)
            data = parsed['data']
            ext = parsed['ext_resources']
            name_key = data.get('name', '')
            if not name_key:
                continue
            
            bonuses_raw = data.get('set_bonuses', [])
            bonuses = []
            if isinstance(bonuses_raw, list):
                for tier_bonus in bonuses_raw:
                    tier_effects = []
                    if isinstance(tier_bonus, list):
                        for eff in tier_bonus:
                            if isinstance(eff, dict) and '_ext' in eff:
                                ext_id = eff['_ext']
                                if ext_id in ext:
                                    eff_path = BASE_DIR / ext[ext_id]['path']
                                    eff_data = parse_effect_file(eff_path)
                                    if eff_data:
                                        tier_effects.append(eff_data)
                    if tier_effects:
                        bonuses.append(tier_effects)
            
            if bonuses:
                # Pre-render effect texts for set bonuses
                rendered_bonuses = []
                for tier_effects in bonuses:
                    rendered_tier = []
                    for eff_data in tier_effects:
                        eff_data['text_en'] = render_effect_text_en(eff_data)
                        eff_data['text_zh'] = render_effect_text_zh(eff_data)
                        rendered_tier.append(eff_data)
                    rendered_bonuses.append(rendered_tier)
                sets_data[name_key] = rendered_bonuses
    
    # Apply manual overrides
    for key, manual in SET_EFFECTS_MANUAL.items():
        if key not in sets_data or not sets_data[key]:
            sets_data[key] = {
                '_manual': True,
                'name_en': manual['name_en'],
                'name_zh': manual['name_zh'],
                'tiers': manual['effects'],
            }
    
    return sets_data

# ====================================================================
# Collectors
# ====================================================================

def get_effects(parsed):
    ext = parsed['ext_resources']
    data = parsed['data']
    effects_raw = data.get('effects', [])
    effects = []
    if isinstance(effects_raw, list):
        for eff in effects_raw:
            if isinstance(eff, dict) and '_ext' in eff:
                ext_id = eff['_ext']
                if ext_id in ext:
                    eff_path = BASE_DIR / ext[ext_id]['path']
                    eff_data = parse_effect_file(eff_path)
                    if eff_data:
                        # Pre-render effect text
                        eff_data['text_en'] = render_effect_text_en(eff_data)
                        eff_data['text_zh'] = render_effect_text_zh(eff_data)
                        effects.append(eff_data)
    return effects

def get_sets_for_weapon(parsed):
    ext = parsed['ext_resources']
    data = parsed['data']
    sets_raw = data.get('sets', [])
    result = []
    if isinstance(sets_raw, list):
        for s in sets_raw:
            if isinstance(s, dict) and '_ext' in s:
                ext_id = s['_ext']
                if ext_id in ext:
                    sets_path = ext[ext_id]['path']
                    full_path = BASE_DIR / sets_path
                    if full_path.exists():
                        set_parsed = parse_tres_file(full_path)
                        set_name = set_parsed['data'].get('name', '')
                        result.append(set_name)
    return result

def get_upgrades_into(parsed):
    ext = parsed['ext_resources']
    data = parsed['data']
    upgrades_raw = data.get('upgrades_into')
    if isinstance(upgrades_raw, dict) and '_ext' in upgrades_raw:
        ext_id = upgrades_raw['_ext']
        if ext_id in ext:
            upgrade_path = BASE_DIR / ext[ext_id]['path']
            if upgrade_path.exists():
                upgrade_parsed = parse_tres_file(upgrade_path)
                return upgrade_parsed['data'].get('my_id', None)
    return None

def extract_stats_from_tres(tres_path, parsed):
    ext = parsed['ext_resources']
    data = parsed['data']
    stats_val = data.get('stats')
    if isinstance(stats_val, dict) and '_ext' in stats_val:
        ext_id = stats_val['_ext']
        if ext_id in ext:
            stats_path = BASE_DIR / ext[ext_id]['path']
            return parse_weapon_stats(stats_path)
    return None

def get_starting_weapon_ids(parsed):
    ext = parsed['ext_resources']
    data = parsed['data']
    weapons_raw = data.get('starting_weapons', [])
    result = []
    if isinstance(weapons_raw, list):
        for w in weapons_raw:
            if isinstance(w, dict) and '_ext' in w:
                ext_id = w['_ext']
                if ext_id in ext:
                    w_path = BASE_DIR / ext[ext_id]['path']
                    if w_path.exists():
                        w_parsed = parse_tres_file(w_path)
                        my_id = w_parsed['data'].get('my_id', '')
                        if my_id:
                            result.append(my_id)
    return result

# Weapons to exclude (废案)
EXCLUDED_WEAPONS = {
    'weapon_knuckles',  # 黄铜指虎 (not 烈焰黄铜指虎 flaming_brass_knuckles)
}

def collect_weapons(search_dir, dlc=0):
    weapons = []
    for data_file in search_dir.rglob('*_data*.tres'):
        if 'stats' in data_file.name or 'effect' in data_file.name.lower():
            continue
        if 'appearance' in data_file.name.lower():
            continue
        # Skip burning data files (torch etc.)
        if 'burning' in data_file.name.lower():
            continue
        
        relative = data_file.relative_to(BASE_DIR)
        print(f"  Parsing weapon: {relative}")
        
        parsed = parse_tres_file(data_file)
        data = parsed['data']
        
        if 'weapon_id' not in data:
            continue
        
        my_id = data.get('my_id', '')
        
        # Skip excluded weapons (废案)
        if my_id in EXCLUDED_WEAPONS:
            print(f"    SKIPPING (excluded): {my_id}")
            continue
        
        name_key = data.get('name', '')
        icon = find_icon_for_dlc(data_file, parsed) if dlc else find_icon_file(data_file, parsed)
        
        effects = get_effects(parsed)
        
        weapon = {
            'id': my_id,
            'name_key': name_key,
            'name_en': tr(name_key, 'en'),
            'name_zh': tr(name_key, 'zh'),
            'tier': data.get('tier', 0),
            'tier_name': TIER_NAMES.get(data.get('tier', 0), 'common'),
            'value': data.get('value', 0),
            'type': WEAPON_TYPE_NAMES.get(data.get('type', 0), 'melee'),
            'weapon_id': data.get('weapon_id', ''),
            'sets': get_sets_for_weapon(parsed),
            'icon': icon,
            'dlc': dlc,
            'effects': effects,
            'stats': extract_stats_from_tres(data_file, parsed),
            'upgrades_into': get_upgrades_into(parsed),
            'unlocked_by_default': data.get('unlocked_by_default', False),
            'is_cursed': data.get('is_cursed', False),
        }
        weapons.append(weapon)
    
    return weapons

def _parse_item_file(data_file, dlc, parsed=None):
    """Parse a single item .tres file and return item dict or None if invalid."""
    if parsed is None:
        parsed = parse_tres_file(data_file)
    data = parsed['data']
    my_id = data.get('my_id', '')
    if not my_id.startswith('item_'):
        return None
    relative = data_file.relative_to(BASE_DIR)
    if 'appearance' in data_file.name.lower():
        return None
    if 'character' in str(relative).lower():
        return None
    # Validate directory name matches item id
    if data_file.parent.name != my_id.replace('item_', ''):
        parent_name = data_file.parent.name
        if parent_name not in my_id:
            return None
    
    print(f"  Parsing item: {relative}")
    
    name_key = data.get('name', '')
    icon = find_icon_for_dlc(data_file, parsed) if dlc else find_icon_file(data_file, parsed)
    
    # All items (including pets) use their own icons from items/ directory
    # The stray robot (Wandering Bot) already has its icon at items/all/wandering_bot/
    # Other pets previously used entities/units/pet/ icons which was incorrect
    tags = data.get('tags', [])
    
    effects = get_effects(parsed)
    
    return {
        'id': my_id,
        'name_key': name_key,
        'name_en': tr(name_key, 'en'),
        'name_zh': tr(name_key, 'zh'),
        'tier': data.get('tier', 0),
        'tier_name': TIER_NAMES.get(data.get('tier', 0), 'common'),
        'value': data.get('value', 0),
        'max_nb': data.get('max_nb', -1),
        'tags': tags,
        'icon': icon,
        'dlc': dlc,
        'effects': effects,
        'unlocked_by_default': data.get('unlocked_by_default', False),
        'is_cursed': data.get('is_cursed', False),
    }

def collect_items(search_dir, dlc=0):
    items = []
    seen_ids = set()
    
    # First pass: standard *_data.tres files
    for data_file in search_dir.rglob('*_data.tres'):
        item = _parse_item_file(data_file, dlc)
        if item:
            items.append(item)
            seen_ids.add(item['id'])
    
    # Second pass: items where the main file is {dirname}.tres (not _data.tres)
    for data_file in search_dir.rglob('*.tres'):
        if data_file.name.endswith('_data.tres'):
            continue  # already handled above
        # Only consider files where name == parent_dir.tres (e.g. scapegoat/scapegoat.tres)
        if data_file.name != data_file.parent.name + '.tres':
            continue
        parsed = parse_tres_file(data_file)
        my_id = parsed['data'].get('my_id', '')
        if not my_id.startswith('item_'):
            continue
        if my_id in seen_ids:
            continue
        item = _parse_item_file(data_file, dlc, parsed=parsed)
        if item:
            items.append(item)
            seen_ids.add(item['id'])
    
    return items

def collect_characters(search_dir, dlc=0):
    characters = []
    for data_file in search_dir.rglob('*_data.tres'):
        relative = data_file.relative_to(BASE_DIR)
        parsed = parse_tres_file(data_file)
        data = parsed['data']
        my_id = data.get('my_id', '')
        if not my_id.startswith('character_'):
            continue
        if 'appearance' in data_file.name.lower() or 'effect' in data_file.name.lower():
            continue
        
        print(f"  Parsing character: {relative}")
        
        name_key = data.get('name', '')
        icon = find_icon_for_dlc(data_file, parsed) if dlc else find_icon_file(data_file, parsed)
        
        effects = get_effects(parsed)
        
        character = {
            'id': my_id,
            'name_key': name_key,
            'name_en': tr(name_key, 'en'),
            'name_zh': tr(name_key, 'zh'),
            'tier': data.get('tier', 0),
            'tier_name': TIER_NAMES.get(data.get('tier', 0), 'common'),
            'value': data.get('value', 0),
            'wanted_tags': data.get('wanted_tags', []),
            'banned_item_groups': data.get('banned_item_groups', []),
            'banned_items': data.get('banned_items', []),
            'banned_upgrades': data.get('banned_upgrades', []),
            'starting_weapons': get_starting_weapon_ids(parsed),
            'icon': icon,
            'dlc': dlc,
            'effects': effects,
            'unlocked_by_default': data.get('unlocked_by_default', False),
            'max_nb': data.get('max_nb', -1),
            'tags': data.get('tags', []),
        }
        characters.append(character)
    
    return characters

# ====================================================================
# Icon copy
# ====================================================================
def copy_icons(all_data_entries, output_icons_dir):
    copied = set()
    for entry in all_data_entries:
        icon = entry.get('icon')
        if not icon: continue
        src = BASE_DIR / icon
        if not src.exists():
            print(f"  WARNING: Icon not found: {src}")
            continue
        if icon in copied: continue
        copied.add(icon)
        dst = output_icons_dir / icon
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
    print(f"  Copied {len(copied)} icon files")

def collect_stat_icons():
    mapping = {}
    for stat_file in (BASE_DIR / "items" / "upgrades").rglob("stat_*.tres"):
        parsed = parse_tres_file(stat_file)
        data = parsed['data']
        ext = parsed['ext_resources']
        stat_name = data.get('stat_name', '')
        small_icon_val = data.get('small_icon')
        if stat_name and isinstance(small_icon_val, dict) and '_ext' in small_icon_val:
            ext_id = small_icon_val['_ext']
            if ext_id in ext:
                mapping[stat_name] = ext[ext_id]['path']
    
    dlc_stats_dir = BASE_DIR / "dlcs" / "dlc_1" / "stats"
    if dlc_stats_dir.exists():
        for stat_file in dlc_stats_dir.glob("*.tres"):
            parsed = parse_tres_file(stat_file)
            data = parsed['data']
            ext = parsed['ext_resources']
            stat_name = data.get('stat_name', '')
            small_icon_val = data.get('small_icon')
            if stat_name and isinstance(small_icon_val, dict) and '_ext' in small_icon_val:
                ext_id = small_icon_val['_ext']
                if ext_id in ext:
                    mapping[stat_name] = ext[ext_id]['path']
    
    # Also scan DLC upgrades directory for stat definitions (e.g. stat_curse)
    dlc_upgrades_dir = BASE_DIR / "dlcs" / "dlc_1" / "upgrades"
    if dlc_upgrades_dir.exists():
        for stat_file in dlc_upgrades_dir.rglob("stat_*.tres"):
            parsed = parse_tres_file(stat_file)
            data = parsed['data']
            ext = parsed['ext_resources']
            stat_name = data.get('stat_name', '')
            small_icon_val = data.get('small_icon')
            if stat_name and isinstance(small_icon_val, dict) and '_ext' in small_icon_val:
                ext_id = small_icon_val['_ext']
                if ext_id in ext:
                    mapping[stat_name] = ext[ext_id]['path']
    return mapping

def get_relevant_translations():
    relevant = {}
    # Collect all effect text_keys used in weapons
    effect_keys = set()
    for data_file in BASE_DIR.glob("weapons/**/*.tres"):
        parsed = parse_tres_file(data_file)
        data = parsed['data']
        tk = data.get('text_key', '') or data.get('key', '')
        if tk:
            effect_keys.add(tk.upper())
            effect_keys.add(tk)
    for data_file in BASE_DIR.glob("dlcs/**/*.tres"):
        parsed = parse_tres_file(data_file)
        data = parsed['data']
        tk = data.get('text_key', '') or data.get('key', '')
        if tk:
            effect_keys.add(tk.upper())
            effect_keys.add(tk)
    
    for key, trans in TR.items():
        if (key.upper() in effect_keys or
            any(key.startswith(p) for p in [
                'EFFECT_', 'STAT_', 'ITEM_', 'WEAPON_', 'CHARACTER_',
                'TIER_', 'CATEGORY_', 'WEAPON_CLASS_', 'SET_',
                'INFO_', 'MELEE', 'RANGED', 'KNOCKBACK', 'LIFESTEAL',
                'BOUNCE', 'PIERCING', 'CRITICAL', 'COOLDOWN', 'DAMAGE_',
                'RANGE_', 'ALTERNATES_', 'DEALS_DAMAGE_ON_RETURN',
                'ADDITIONAL_COOLDOWN', 'effect_', 'effect',
            ])):
            if 'en' in trans and len(trans['en']) < 300:
                relevant[key] = trans
    return relevant

def clean_arrays_for_json(obj):
    if isinstance(obj, list):
        return [clean_arrays_for_json(v) for v in obj]
    if isinstance(obj, dict):
        return {k: clean_arrays_for_json(v) for k, v in obj.items()}
    return obj

# ====================================================================
# Main
# ====================================================================
def main():
    global TR
    TR = load_translations()
    load_merged_translations()
    
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_ICONS.mkdir(parents=True, exist_ok=True)
    
    print("\n=== Collecting Base Game Weapons ===")
    base_weapons = (
        collect_weapons(BASE_DIR / "weapons" / "melee", dlc=0) +
        collect_weapons(BASE_DIR / "weapons" / "ranged", dlc=0)
    )
    print(f"  Found {len(base_weapons)} base weapons")
    
    print("\n=== Collecting DLC Weapons ===")
    dlc_weapons = []
    dlc_weapons_dir = BASE_DIR / "dlcs" / "dlc_1" / "weapons"
    if dlc_weapons_dir.exists():
        dlc_weapons = (
            collect_weapons(dlc_weapons_dir / "melee", dlc=1) +
            collect_weapons(dlc_weapons_dir / "ranged", dlc=1)
        )
    print(f"  Found {len(dlc_weapons)} DLC weapons")
    
    print("\n=== Collecting Base Game Items ===")
    base_items = collect_items(BASE_DIR / "items" / "all", dlc=0)
    print(f"  Found {len(base_items)} base items")
    
    print("\n=== Collecting DLC Items ===")
    dlc_items = []
    dlc_items_dir = BASE_DIR / "dlcs" / "dlc_1" / "items"
    if dlc_items_dir.exists():
        dlc_items = collect_items(dlc_items_dir, dlc=1)
    print(f"  Found {len(dlc_items)} DLC items")
    
    print("\n=== Collecting Base Game Characters ===")
    base_characters = collect_characters(BASE_DIR / "items" / "characters", dlc=0)
    print(f"  Found {len(base_characters)} base characters")
    
    print("\n=== Collecting DLC Characters ===")
    dlc_characters = []
    dlc_chars_dir = BASE_DIR / "dlcs" / "dlc_1" / "characters"
    if dlc_chars_dir.exists():
        dlc_characters = collect_characters(dlc_chars_dir, dlc=1)
    print(f"  Found {len(dlc_characters)} DLC characters")
    
    all_weapons = base_weapons + dlc_weapons
    all_items = base_items + dlc_items
    all_characters = base_characters + dlc_characters
    
    sort_key = lambda x: (x['tier'], x['name_en'])
    all_weapons.sort(key=sort_key)
    all_items.sort(key=sort_key)
    all_characters.sort(key=sort_key)
    
    translations = get_relevant_translations()
    print(f"  Extracted {len(translations)} relevant translation entries")
    
    stat_icons = collect_stat_icons()
    print(f"  Extracted {len(stat_icons)} stat icon mappings")
    
    all_sets = build_sets_data()
    print(f"  Extracted {len(all_sets)} sets with bonuses")
    
    # Verify effect text coverage
    weapons_with_effects = [w for w in all_weapons if w['effects']]
    effects_with_text = []
    effects_without_text = []
    for w in weapons_with_effects:
        for e in w['effects']:
            entry = {
                'weapon': f"{w['name_en']} (T{w['tier']+1}) [{w['id']}]",
                'key': e['key'],
                'text_key': e.get('text_key', ''),
                'value': e['value'],
                'sign': e['effect_sign'],
                'extra': e.get('extra', {}),
                'text_en': e.get('text_en', ''),
                'text_zh': e.get('text_zh', ''),
            }
            if e.get('text_en'):
                effects_with_text.append(entry)
            else:
                effects_without_text.append(entry)
    
    print(f"\n=== Effect Text Coverage ===")
    print(f"  With text: {len(effects_with_text)}")
    print(f"  Without text: {len(effects_without_text)}")
    if effects_without_text:
        print(f"  Missing translations:")
        for e in effects_without_text:
            print(f"    [{e['weapon']}] key={e['key']} text_key={e['text_key']} value={e['value']} sign={e['sign']} extra={e['extra']}")
    
    data = {
        'weapons': all_weapons,
        'items': all_items,
        'characters': all_characters,
        'translations': translations,
        'stat_icons': stat_icons,
        'sets': all_sets,
        'meta': {
            'weapon_count': len(all_weapons),
            'item_count': len(all_items),
            'character_count': len(all_characters),
            'base_weapon_count': len(base_weapons),
            'dlc_weapon_count': len(dlc_weapons),
            'base_item_count': len(base_items),
            'dlc_item_count': len(dlc_items),
            'base_character_count': len(base_characters),
            'dlc_character_count': len(dlc_characters),
            'effects_with_text': len(effects_with_text),
            'effects_without_text': len(effects_without_text),
        }
    }
    
    data = clean_arrays_for_json(data)
    
    print(f"\n=== Writing JSON ===")
    with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"  Written to {OUTPUT_JSON}")
    
    print(f"\n=== Copying Icons ===")
    all_entries = all_weapons + all_items + all_characters
    copy_icons(all_entries, OUTPUT_ICONS)
    
    for stat_name, icon_path in stat_icons.items():
        src = BASE_DIR / icon_path
        if src.exists():
            dst = OUTPUT_ICONS / icon_path
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
    print(f"  Copied stat icons: {len(stat_icons)} files")
    
    print(f"\n=== Summary ===")
    print(f"  Total weapons: {len(all_weapons)} (base: {len(base_weapons)}, dlc: {len(dlc_weapons)})")
    print(f"  Total items: {len(all_items)} (base: {len(base_items)}, dlc: {len(dlc_items)})")
    print(f"  Total characters: {len(all_characters)} (base: {len(base_characters)}, dlc: {len(dlc_characters)})")
    print(f"  JSON size: {OUTPUT_JSON.stat().st_size / 1024:.1f} KB")
    
    # Output report table
    print(f"\n=== Effect Text Report ===")
    print(f"{'Weapon':<30} {'Key':<35} {'Val':<6} {'EN Text':<80}")
    print("-" * 155)
    for e in effects_with_text[:5] + effects_without_text:
        print(f"{e['weapon']:<30} {e['key']:<35} {e['value']:<6} {e['text_en'][:80]}")
    
    # Output missing effects as table
    if effects_without_text:
        print(f"\n=== Missing Effect Texts ({len(effects_without_text)}) ===")
        for e in effects_without_text:
            print(f"  {e['weapon']}: key={e['key']}, text_key={e['text_key']}, val={e['value']}, sign={e['sign']}, extra={e['extra']}")

if __name__ == '__main__':
    main()
