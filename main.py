import os
import re
import json
import shutil
import csv
from pathlib import Path

CODEX_DIR = Path(__file__).resolve().parent            # codex/
BASE_DIR = CODEX_DIR.parent                           # decompiled game root
OUTPUT_DIR = CODEX_DIR / "public"
OUTPUT_JSON = OUTPUT_DIR / "data" / "brotato_data.json"
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
    merged_path = CODEX_DIR / "data" / "translations_merged.json"
    if not merged_path.exists():
        merged_path = CODEX_DIR / "public" / "data" / "translations_merged.json"
    if not merged_path.exists():
        merged_path = CODEX_DIR / "translations" / "translations_merged.json"
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
    
    # Calculate animation cooldown based on weapon type
    recoil_duration = data.get('recoil_duration', 0.1)
    max_range = data.get('max_range', 150)
    stats['recoil_duration'] = recoil_duration
    
    if 'attack_type' in data:  # Melee weapon
        # Melee animation: atk_duration/2 + back_duration + recoil_duration
        # At base attack speed (atk_spd=0):
        # atk_duration = BASE_ATK_DURATION + range_factor * 0.15
        # back_duration = BASE_ATK_DURATION
        BASE_ATK_DURATION = 0.2
        range_factor = max(0.0, max_range / 70.0)
        atk_duration = BASE_ATK_DURATION + range_factor * 0.15
        back_duration = BASE_ATK_DURATION
        stats['animation_cooldown'] = atk_duration / 2 + back_duration + recoil_duration
    elif 'nb_projectiles' in data:  # Ranged weapon
        # Ranged animation: recoil_duration * 2
        stats['animation_cooldown'] = recoil_duration * 2
    else:
        stats['animation_cooldown'] = 0
    
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
    
    # Extract set_id for ClassBonusEffect (weapon class bonus)
    if 'set_id' in data:
        result['set_id'] = data['set_id']
    
    # Extract top-level cooldown (e.g., alien_eyes has cooldown=3 separate from weapon_stats)
    if 'cooldown' in data:
        result['effect_cooldown'] = data['cooldown']
    
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
    for bool_field in ['auto_target_enemy', 'reset_on_hit', 'perm_stats_only', 'is_spawning']:
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
GREEN = '<span class="zvg">'
RED = '<span class="zvr">'
PURPLE = '<span class="zvp">'
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
    if add_op:
        try:
            if v > 0:
                s = '+' + s
        except (TypeError, ValueError):
            pass  # v is not a number (e.g., '{0}' placeholder)
    if add_pct:
        s = s + '%'
    return s

_keys_needing_operator = {
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

def needs_operator(key):
    """Check if a key needs + operator prefix (from Godot's keys_needing_operator)"""
    return key.lower() in _keys_needing_operator

_keys_needing_percent = {
        'effect_burn_chance', 'effect_explode_custom',
        'effect_damage_against_bosses',
        'stat_damage_against_bosses',
        'explosion_size', 'stat_explosion_size',
        'explosion_damage', 'stat_explosion_damage',
        'piercing_damage', 'effect_piercing_damage_short',
}

def needs_percent(key):
    """Check if a key needs % suffix.
    
    In Godot, keys_needing_percent is used for format string arg indices, not for 
    stat display names. Stat display names already include % where needed 
    (e.g., '%伤害' for stat_percent_damage). So we should NOT add % suffix for stat keys.
    
    The % suffix is only needed for non-stat keys where the raw value represents a 
    percentage (e.g., chance-based effects).
    """
    return key.lower() in _keys_needing_percent

def sign_color(eff):
    """Get sign color based on effect_sign and value"""
    sign = eff.get('effect_sign', 3)
    value = eff.get('value', 0)
    if sign == 0: return 'zvg'  # POSITIVE -> green
    elif sign == 1: return 'zvr'  # NEGATIVE -> red
    elif sign == 2: return ''  # NEUTRAL -> no color
    elif sign == 3:  # FROM_VALUE
        if value > 0: return 'zvg'
        elif value < 0: return 'zvr'
        return ''
    elif sign == 5: return 'zvp'  # OVERRIDE (curse) -> purple
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
    """Build scaling stat icon text like '100%<icon>ranged_damage</icon>'"""
    parts = []
    for ss in scaling_stats:
        if isinstance(ss, list) and len(ss) >= 2:
            pct = int(ss[1] * 100)
            stat_key = ss[0]  # e.g. "stat_ranged_damage"
            # Extract short key for icon: "stat_ranged_damage" -> "ranged_damage"
            ic_key = stat_key.replace('stat_', '', 1) if stat_key.startswith('stat_') else stat_key
            parts.append(f"{pct}%<icon>{ic_key}</icon>")
    return '+'.join(parts) if parts else ''


# ====================================================================
# keys_needing_operator / keys_needing_percent (from text.gd)
# Maps key -> list of arg indices that need + prefix or % suffix
# ====================================================================
KEYS_NEEDING_OPERATOR = {
    'stat_max_hp': [0], 'stat_damage': [0], 'stat_armor': [0],
    'stat_crit_chance': [0], 'stat_luck': [0], 'stat_attack_speed': [0],
    'stat_elemental_damage': [0], 'stat_hp_regeneration': [0], 'stat_lifesteal': [0],
    'stat_melee_damage': [0], 'stat_percent_damage': [0], 'stat_dodge': [0],
    'stat_engineering': [0], 'stat_range': [0], 'stat_ranged_damage': [0],
    'stat_speed': [0], 'stat_harvesting': [0], 'xp_gain': [0],
    'weapon_slot': [0], 'items_price': [0], 'weapons_price': [0],
    'number_of_enemies': [0], 'map_size': [0], 'enemy_speed': [0],
    'enemy_health': [0], 'enemy_damage': [0], 'enemy_damage_hp_increase': [0],
    'inflation_modifier': [0],
    'effect_enemy_health': [0], 'effect_enemy_speed': [0],
    'effect_temp_stats_per_interval': [0], 'effect_temp_stats_per_interval_singular': [0],
    'effect_piercing_damage': [0], 'effect_weapon_specific_bonus': [0],
    'effect_weapon_class_bonus': [0],
    'effect_weapon_stack': [0, 3], 'effect_unique_weapon_bonus': [0, 2],
    'effect_tier_iv_weapon_bonus': [0, 2], 'effect_tier_i_weapon_bonus': [0, 2],
    'effect_consumable_heal': [0], 'effect_pickup_range': [0],
    'effect_on_hit': [0], 'effect_chance_double_gold': [0],
    'effect_heal_when_pickup_gold': [0], 'effect_item_box_gold': [0],
    'effect_stat_while_not_moving': [0], 'effect_knockback': [0],
    'effect_gain_stat_end_of_wave': [0],
    'effect_gain_stat_for_every_stat': [0, 4],
    'effect_gain_stat_for_every_perm_stat': [0, 4],
    'effect_gain_stat_for_every_different_stat': [0, 4],
    'effect_gain_stat_for_every_enemy': [0, 4],
    'effect_gain_stat_for_every_burning_enemy': [0, 4],
    'effect_gain_stat_for_every_tree': [0, 4],
    'effect_gain_stat_every_killed_enemies': [0],
    'effect_gold_drops': [0], 'effect_neutral_gold_drops': [0],
    'effect_enemy_gold_drops': [0],
    'effect_gain_pct_gold_start_wave': [0],
    'effect_gain_pct_gold_start_wave_limited': [0],
    'effect_free_shop_reroll': [0], 'effect_free_shop_reroll_plural': [0],
    'effect_instant_gold_attracting': [0],
    'explosion_size': [0], 'explosion_damage': [0],
    'structure_attack_speed': [0], 'chal_stat_desc': [0],
    'effect_additional_weapon_bonus': [0, 2],
    'effect_upgrade_random_weapon': [0],
    'effect_gold_while_moving': [0], 'effect_gold_while_not_moving': [0, 2],
    'effect_stat_while_moving': [0], 'effect_stat_next_wave': [0],
    'effect_damage_against_bosses': [0],
    'effect_consumable_stat_while_max': [0],
    'effect_consumable_stat_while_max_limited': [0, 2],
    'effect_heal_on_crit_kill': [0],
    'effect_pct_start_wave_stat': [0], 'effect_pct_stack_stat': [0],
    'effect_piercing_damage_short': [0], 'effect_stat_on_level_up': [0],
    'effect_stat_below_half_health': [0], 'effect_temp_stat_on_dodge': [0],
    'effect_projectile': [0], 'effect_projectiles': [0],
    'effect_player_missing_health_damage_bonus': [0, 3],
    'effect_gain_stat_for_equipped_item_with_stat': [0, 2],
    'effect_temp_stat_on_structure_crit': [0],
    'effect_gain_stat_for_every_percent_player_missing_health': [0, 4],
    'effect_structure_attack_speed_while_moving': [0],
    'next_level_xp_needed': [0],
    'effect_bouncing': [0], 'effect_bouncing_plural': [0],
    'effect_gain_stat_for_killed_enemies_while_burning': [2, 3],
    'effect_no_hit_boost': [0],
    # DLC1 keys (from dlc_data.tres)
    'effect_bonus_damage_against_targets_above_hp': [0],
    'effect_bonus_damage_against_targets_below_hp': [0],
    'effect_bonus_non_elemental_damage_against_burning_targets': [0],
    'effect_bonus_weapon_class_damage_against_cursed_enemies': [0],
    'effect_builder_turret_upgrade': [0],
    'effect_crate_chance': [0],
    'effect_decaying_stat_on_consumable': [0],
    'effect_decaying_stat_on_hit': [0],
    'effect_extra_item_in_crate': [0],
    'effect_extra_random_item_in_crate': [0],
    'effect_gain_stat_for_duplicate_items': [4],
    'effect_gain_stat_for_free_weapon_slots': [0, 4],
    'effect_gain_stat_when_attack_killed_enemies': [0],
    'effect_gain_stats_on_reroll': [0, 2],
    'effect_gold_on_cursed_enemy_kill': [0],
    'effect_gold_on_cursed_enemy_kill_plural': [0],
    'effect_heal_on_kill': [0],
    'effect_increase_material_value': [0],
    'effect_level_upgrades_modifications': [0],
    'effect_loot_alien_chance': [0],
    'effect_loot_alien_speed': [0],
    'effect_melee_weapon_bonus': [0],
    'effect_modify_every_x_projectile': [2],
    'effect_modify_every_x_projectile_first': [2],
    'effect_modify_every_x_projectile_second': [2],
    'effect_modify_every_x_projectile_third': [2],
    'effect_pierce_on_crit_item': [0],
    'effect_scale_materials_with_distance': [0, 1],
    'effect_stat_on_every_step': [0],
    'effect_stat_on_fruit': [0],
    'effect_temp_consumable_stat_while_max': [0],
    'effect_temp_stat_on_consumable': [0],
    'effect_weapon_damage_for_free_weapon_slots': [0, 4],
    'effect_weapon_modify_every_x_projectile': [2],
    'effect_weapon_modify_every_x_projectile_first': [2],
    'effect_weapon_modify_every_x_projectile_second': [2],
    'effect_weapon_modify_every_x_projectile_third': [2],
    'reroll_price': [0],
    'stat_curse': [0],
    'structure_percent_damage': [0],
    'structure_range': [0],
}

KEYS_NEEDING_PERCENT = {
    'effect_increase_stat_gains': [1], 'effect_reduce_stat_gains': [1],
    'next_level_xp_needed': [0], 'weapons_price': [0], 'number_of_enemies': [0],
    'effect_burn_chance': [0], 'effect_start_wave_less_hp': [0],
    'effect_deal_dmg_when_pickup_gold': [0], 'effect_deal_dmg_when_death': [0],
    'effect_deal_dmg_when_heal': [0],
    'effect_piercing_damage': [0], 'effect_piercing_damage_short': [0],
    'effect_remove_speed': [0, 2],
    'info_pos_stat_crit_chance': [0], 'info_neg_stat_crit_chance': [0],
    'info_pos_stat_lifesteal': [0], 'info_neg_stat_lifesteal': [0],
    'info_pos_stat_percent_damage': [0], 'info_neg_stat_percent_damage': [0],
    'info_pos_stat_dodge': [0], 'info_neg_stat_dodge': [0],
    'info_pos_stat_speed': [0], 'info_neg_stat_speed': [0],
    'info_pos_stat_attack_speed': [0], 'info_neg_stat_attack_speed': [0],
    'info_pos_stat_luck': [0], 'info_neg_stat_luck': [0],
    'info_pos_stat_armor': [0], 'info_neg_stat_armor': [0],
    'damage_scaling': [0],
    'effect_pickup_range': [0], 'effect_chance_double_gold': [0],
    'effect_gain_pct_gold_start_wave': [0],
    'effect_gain_pct_gold_start_wave_limited': [0],
    'effect_heal_when_pickup_gold': [0],
    'effect_enemy_speed': [0], 'enemy_damage_hp_increase': [0],
    'inflation_modifier': [0], 'effect_enemy_health': [0],
    'effect_recycling_gains': [0], 'map_size': [0],
    'effect_dodge_cap': [0], 'effect_crit_chance_cap': [0],
    'effect_gold_on_crit_kill': [0], 'effect_heal_on_crit_kill': [0],
    'effect_explode_custom': [0],
    'effect_convert_stat_end_of_wave': [0],
    'effect_convert_stat_temp_half_wave': [0],
    'effect_gold_drops': [0], 'effect_neutral_gold_drops': [0],
    'effect_enemy_gold_drops': [0], 'effect_harvesting_growth': [0],
    'effect_instant_gold_attracting': [0],
    'effect_explode_on_death': [0], 'effect_explode_on_consumable': [0],
    'info_pos_stat_harvesting': [1],
    'info_pos_stat_harvesting_limited': [1, 3],
    'effect_burning_cooldown_reduction': [0],
    'effect_burning_cooldown_increase': [0],
    'effect_explode_melee': [0],
    'effect_gold_while_moving': [0], 'effect_gold_while_not_moving': [0],
    'effect_deal_dmg_when_dodge': [0], 'effect_heal_when_dodge': [0],
    'effect_damage_against_bosses': [0],
    'effect_giant_crit_damage': [0, 2],
    'effect_structures_cooldown_reduction': [0],
    'effect_pct_start_wave_stat': [0], 'effect_pct_stack_stat': [0],
    'effect_specific_item_price': [0], 'effect_accuracy': [0],
    'effect_player_missing_health_damage_bonus': [2],
    'effect_weapon_slow_on_hit': [0, 3],
    'effect_burning_enemy_hp_percent_damage': [0, 2],
    'effect_burning_enemy_speed_neg': [0],
    'effect_weapon_scaling_stats': [0],
    'effect_item_slow_on_hit': [0],
    'effect_enemy_percent_damage_taken': [0],
    'effect_enemy_percent_damage_taken_once': [0],
    'effect_spawn_landmine_on_death': [0],
    'effect_gain_stat_for_every_percent_player_missing_health': [2],
    'effect_structure_attack_speed_while_moving': [0],
    'effect_hp_regen_bonus_double': [2], 'effect_hp_regen_bonus_triple': [2],
    'effect_extra_elite_next_wave_chance': [0],
    'effect_one_shot_on_hit_effect': [0],
    'effect_pet_lootworm': [0], 'fog_visibility': [0],
    # DLC1 keys (from dlc_data.tres)
    'effect_bonus_current_health_damage': [0, 2],
    'effect_bonus_damage_against_targets_above_hp': [0, 2],
    'effect_bonus_damage_against_targets_below_hp': [0, 2],
    'effect_bonus_non_elemental_damage_against_burning_targets': [0],
    'effect_bonus_weapon_class_damage_against_cursed_enemies': [0],
    'effect_break_on_hit': [0],
    'effect_chance_explode_on_hit': [0],
    'effect_charm_below_hp': [0, 1],
    'effect_charm_below_hp_no_scaling': [0, 1],
    'effect_charm_on_hit': [0],
    'effect_crate_chance': [0],
    'effect_curse_locked_items': [0],
    'effect_explode_when_below_hp': [4],
    'effect_extra_item_in_crate': [0],
    'effect_extra_random_item_in_crate': [0],
    'effect_gain_stats_on_reroll': [2],
    'effect_heal_on_kill': [0],
    'effect_increase_damage_received': [0, 3],
    'effect_increase_material_value': [0],
    'effect_level_upgrades_modifications': [0],
    'effect_loot_alien_chance': [0],
    'effect_loot_alien_speed': [0],
    'effect_poisoned_fruit': [0],
    'effect_scale_materials_with_distance': [0, 1],
    'effect_stat_on_fruit': [2],
    'info_pos_stat_curse': [0, 1],
}

# Sign constants (from Effect.Sign enum)
SIGN_POSITIVE = 0
SIGN_NEGATIVE = 1
SIGN_NEUTRAL = 2
SIGN_FROM_VALUE = 3
SIGN_FROM_ARG = 4
SIGN_OVERRIDE = 5

# ArgValue constants (from CustomArg.ArgValue enum)
ARG_USUAL = 0
ARG_VALUE = 1
ARG_KEY = 2
ARG_UNIQUE_WEAPONS = 3
ARG_ADDITIONAL_WEAPONS = 4
ARG_TIER = 5
ARG_SCALING_STAT = 6
ARG_SCALING_STAT_VALUE = 7
ARG_MAX_NB_OF_WAVES = 8
ARG_TIER_IV_WEAPONS = 9
ARG_TIER_I_WEAPONS = 10
ARG_ABS_VALUE = 11
ARG_DIFFICULTY_VALUE = 12

# Format constants (from CustomArg.Format enum)
FORMAT_USUAL = 0
FORMAT_PERCENT = 1
FORMAT_ARG_VALUE_AS_NUMBER = 2
FORMAT_REMOVE_OPERATOR = 3

TIER_MAP = {0: 'TIER_I', 1: 'TIER_II', 2: 'TIER_III', 3: 'TIER_IV'}


def _get_effect_sign(sign_type, value, arg_value=0):
    """Replicate Effect.get_sign() from effect.gd"""
    if sign_type == SIGN_FROM_VALUE:
        return SIGN_POSITIVE if value > 0 else SIGN_NEGATIVE if value < 0 else SIGN_NEUTRAL
    elif sign_type == SIGN_FROM_ARG:
        return SIGN_POSITIVE if arg_value > 0 else SIGN_NEGATIVE if arg_value < 0 else SIGN_NEUTRAL
    return sign_type


def _sign_to_color(sign):
    """Convert sign constant to CSS class"""
    if sign == SIGN_POSITIVE: return 'zvg'
    elif sign == SIGN_NEGATIVE: return 'zvr'
    elif sign == SIGN_OVERRIDE: return 'zvp'
    return ''


def _get_formatted_value(value_str, arg_format, base_arg_value):
    """Replicate Effect.get_formatted() from effect.gd"""
    if arg_format == FORMAT_PERCENT:
        try:
            return str(float(value_str) / 100.0)
        except (ValueError, TypeError):
            return value_str
    elif arg_format == FORMAT_ARG_VALUE_AS_NUMBER:
        return str(base_arg_value)
    elif arg_format == FORMAT_REMOVE_OPERATOR:
        return value_str.replace('-', '')
    return value_str


def _sign_to_color(sign):
    """Map sign constant to CSS color class."""
    if sign == 'zvg':
        return 'zvg'
    elif sign == 'zvr':
        return 'zvr'
    elif sign == 'zvp':
        return 'zvp'
    return ''

SIGN_NEUTRAL = ''

# ====================================================================
# Curse system — arg schema (from dlc_1/dlc_1_data.gd curse_item())
# ====================================================================
# Each cursed arg: {"value": float, "type": str, ...optional...}
# Types: default, positive, negative, random, fixed, linked, none
# Optional: mult(float), ceil(bool), curse_value, curse_min, curse_max, linked_mult, max_val

def _curse_entry(val, typ='default', **kwargs):
    """Build a curse arg dict. Returns None if val is not numeric."""
    result = {'value': val, 'type': typ}
    result.update((k, v) for k, v in kwargs.items() if v is not None)
    return result

def _try_parse_val(raw):
    """Extract positive numeric value from a rendered arg string."""
    try:
        return float(str(raw).lstrip('+-').rstrip('%'))
    except (ValueError, TypeError):
        return None

def _build_curse_types(eff, args, arg_signs, parent_id='', is_weapon=False):
    """Build structured curse arg dicts for each arg index.
    
    Returns list parallel to args; None = not cursed, dict = curse data.
    """
    key = eff.get('key', '')
    text_key = eff.get('text_key', '')
    custom_key = eff.get('custom_key', '')
    extra = eff.get('extra', {})
    tk = (text_key or key).upper()
    n = len(args)
    curse = [None] * max(n, 10)

    def c(i, **kw):
        if i < len(curse) and i < len(args) and args[i]:
            val = _try_parse_val(args[i])
            if val is not None:
                curse[i] = _curse_entry(val, **kw)

    # 1. effect_no_hit_boost: positive, no ceil (int truncation in Godot)
    if key == 'effect_no_hit_boost' or tk == 'EFFECT_NO_HIT_BOOST':
        c(0, type='positive', ceil=False)
        return curse

    # 2-3. burn_chance: duration[1], damage[2] → positive
    if key in ('burn_chance', 'effect_burn_chance') or tk == 'EFFECT_BURN_CHANCE':
        c(1, type='positive')
        c(2, type='positive')
        return curse

    # 4-5. effect_burning: duration[0], damage[1] → positive
    if key == 'effect_burning' or tk == 'EFFECT_BURNING':
        c(0, type='positive')
        c(1, type='positive')
        return curse

    # 6. ItemExplodingEffect with scale_with_missing_health → default
    if key and ('explode' in key.lower() or 'EXPLODE' in tk):
        if extra.get('scale_with_missing_health'):
            # value lives at args[3] for explode_on_overkill/consumable, else args[0]
            idx = 3 if key in ('explode_on_overkill','explode_on_consumable') or \
                         tk in ('EFFECT_EXPLODE_ON_OVERKILL','EFFECT_EXPLODE_ON_CONSUMABLE') else 0
            c(idx, type='default')
        return curse  # !scale_with_missing_health → internal stats only

    # 7. gain_stat_every_killed_enemies: value[2] → negative
    if key == 'effect_gain_stat_every_killed_enemies':
        c(2, type='negative')
        return curse

    # 8. gain_stat_for_every_step_after_equip: value2 → negative
    if custom_key == 'gain_stat_for_every_step_after_equip':
        c(1, type='negative')
        return curse

    # 9. break_on_hit: value2[2] → default
    if key in ('break_on_hit', 'effect_break_on_hit'):
        c(2, type='default')
        return curse

    # 10. dodge_cap: random 72-76
    if key == 'dodge_cap':
        c(0, type='random', curse_min=72, curse_max=76)
        return curse

    # 11. will_o_the_wisp stat_elemental_damage: random 16-25
    if parent_id == 'item_will_o_the_wisp' and key == 'stat_elemental_damage':
        c(0, type='random', curse_min=16, curse_max=25)
        return curse

    # 12. candy_bag extra_elite_next_wave_chance: none
    if parent_id == 'item_candy_bag' and key == 'extra_elite_next_wave_chance':
        return curse

    # 13. hp_start_next_wave: fixed -100
    if key == 'hp_start_next_wave':
        c(0, type='fixed', curse_value=-100)
        return curse

    # 14. hit_protection (tardigrade): fixed 2
    if parent_id == 'item_tardigrade' and key == 'hit_protection':
        c(0, type='fixed', curse_value=2)
        return curse

    # 15. hp_regen_bonus (potion): value2 → positive, capped at 90
    if parent_id == 'item_potion' and key == 'hp_regen_bonus':
        c(1, type='positive', max_val=90)
        return curse

    # 16. consumable_heal_over_time: none (NEUTRAL override)
    if key == 'consumable_heal_over_time':
        return curse

    # 17. knockback_aura: negative
    if key == 'knockback_aura' or tk == 'KNOCKBACK_AURA':
        c(0, type='negative')
        return curse

    # 18. modify_every_x_projectile (EffectWithSubEffects, not weapon): negative
    if key == 'modify_every_x_projectile' and not eff.get('is_weapon_effect_with_sub_effects'):
        c(0, type='negative')
        return curse

    # 19. estys_couch stat_speed: positive (forced)
    if parent_id == 'item_estys_couch' and key == 'stat_speed':
        c(0, type='positive')
        return curse

    # 20. weapon_mace stat_attack_speed: positive (forced)
    if 'weapon_mace' in parent_id and key == 'stat_attack_speed':
        c(0, type='positive')
        return curse

    # 21-23. mult=3 group: baby_gecko stat_range, potion stat_hp_regeneration, pile_of_books, pocket_factory
    mult3 = (
        (parent_id == 'item_baby_gecko' and key == 'stat_range') or
        (parent_id == 'item_potion' and key == 'stat_hp_regeneration') or
        parent_id in ('item_pile_of_books', 'item_pocket_factory')
    )
    if mult3:
        c(0, type='default', mult=3.0)
        return curse

    # 24. gold_on_crit_kill: default with max 100
    if key == 'gold_on_crit_kill':
        c(0, type='default', max_val=100)
        return curse

    # 25-27. Linked value2 effects
    if custom_key == 'consumable_stats_while_max':
        c(1, type='linked', linked_mult=1.0)
        return curse
    if key == 'remove_speed':
        c(1, type='linked', linked_mult=4.0)
        return curse
    if key in ('burning_enemy_hp_percent_damage', 'giant_crit_damage', 'bonus_current_health_damage'):
        c(1, type='linked', linked_mult=0.1)
        return curse

    # ---- Default: arg[0] gets 'default' type ----
    c(0, type='default')
    return curse


def _build_cursed_extra_effects(eff, parent_id=''):
    """Return list of extra effects that only appear when the item is cursed.
    
    Each entry is a dict with at least: key, value, effect_sign, and optionally text_key.
    These are stat-type effects that the frontend will render as separate entries.
    """
    key = eff.get('key', '')
    custom_key = eff.get('custom_key', '')
    effect_sign = eff.get('effect_sign', 0)

    items = []

    # stat_jellyshield_count → stat_armor (base 1)
    if (key == 'stat_jellyshield_count' or key == 'jellyshield_count') and parent_id in ('item_jellyshield', 'item_jelly'):
        items.append({'key': 'stat_armor', 'value': 1, 'effect_sign': 0})

    # consumable_heal_over_time (jerky) → stat_hp_regeneration (base 2)
    if key == 'consumable_heal_over_time' and parent_id == 'item_jerky':
        items.append({'key': 'stat_hp_regeneration', 'value': 2, 'effect_sign': 0})

    # upgrade_random_weapon (anvil) → stat_armor (base 3)
    if custom_key == 'upgrade_random_weapon' and parent_id == 'item_anvil':
        items.append({'key': 'stat_armor', 'value': 3, 'effect_sign': 0})

    # extra_item_in_crate + random (treasure_map) → stat_luck (base 5, POSITIVE)
    if custom_key == 'extra_item_in_crate' and key == 'random' and parent_id == 'item_treasure_map':
        items.append({'key': 'stat_luck', 'value': 5, 'effect_sign': 0})

    # gold_on_crit_kill (hunting_trophy) → stat_crit_chance (base 5)
    if key == 'gold_on_crit_kill' and parent_id == 'item_hunting_trophy':
        items.append({'key': 'stat_crit_chance', 'value': 5, 'effect_sign': 0})

    # wandering_bot → stat_speed (base 5)
    if parent_id == 'item_wandering_bot' and key == 'wandering_bot':
        items.append({'key': 'stat_speed', 'value': 5, 'effect_sign': 0})

    # sifds_relic instant_gold_attracting → stat_dodge (base 10)
    if parent_id == 'item_sifds_relic' and key == 'instant_gold_attracting':
        items.append({'key': 'stat_dodge', 'value': 10, 'effect_sign': 0})

    # one_shot_trees / tree_turrets → trees (base 1)
    if key in ('one_shot_trees', 'tree_turrets'):
        items.append({'key': 'trees', 'value': 1, 'effect_sign': 0, 'text_key': 'effect_trees'})

    # Build text dicts for each extra effect (basic stat effects)
    for item in items:
        fake_eff = {
            'key': item['key'],
            'value': item['value'],
            'effect_sign': item.get('effect_sign', 0),
            'text_key': item.get('text_key', ''),
            'custom_key': '',
            'extra': {},
        }
        text_dict = build_effect_text_dict(fake_eff)
        if text_dict:
            item['text'] = text_dict
            item['text_en'] = text_dict['en']
            item['text_zh'] = text_dict['zh']

    return items



def _build_effect_args_and_signs(eff, lang):
    """Build args array and signs array for an effect, replicating each subclass's get_args().
    
    Returns (args: list[str], signs: list[int], lookup_key: str) or None if unrenderable.
    """
    key = eff.get('key', '')
    value = eff.get('value', 0)
    text_key = eff.get('text_key', '')
    extra = eff.get('extra', {})
    custom_key = eff.get('custom_key', '')
    effect_sign = eff.get('effect_sign', SIGN_FROM_VALUE)
    custom_args = eff.get('custom_args', [])
    
    # Determine lookup key: text_key if set, else key (uppercased)
    lookup_key = (text_key or key).upper()
    if not lookup_key:
        return None
    
    # Default sign computation for a value
    def default_sign(val):
        return _get_effect_sign(effect_sign, value, val)
    
    # Default args from base Effect.get_args()
    args = [str(value), tr(key.upper(), lang) if key else '']
    signs = [default_sign(value), SIGN_NEUTRAL]  # {1} is tr(key) → neutral
    
    # ================================================================
    # Override args based on effect type (identified by key/text_key/data)
    # ================================================================
    
    extra_key = (text_key or key).lower()
    
    # --- ExplodingEffect: effect_explode, effect_explode_melee, effect_explode_custom ---
    if key in ('effect_explode', 'effect_explode_melee', 'effect_explode_custom'):
        chance_val = extra.get('chance', 1.0)
        args = [str(int(chance_val * 100))]
        signs = [default_sign(chance_val)]
    
    # --- BurningEffect: effect_burning ---
    elif key == 'effect_burning':
        bd = eff.get('burning_data', {})
        if bd:
            duration = bd.get('duration', 0)
            dmg = bd.get('damage', 0)
            scaling = bd.get('scaling_stats', [])
            scaling_text = build_scaling_text(scaling, lang)
            args = [str(duration), str(dmg), scaling_text]
            # Custom arg: duration is NEUTRAL (BurningEffect._add_custom_args sets arg_sign=NEUTRAL for index 0)
            signs = [SIGN_NEUTRAL, default_sign(dmg), default_sign(dmg)]
    
    # --- GainStatEveryKilledEnemiesEffect ---
    elif key == 'effect_gain_stat_every_killed_enemies':
        stat_field = eff.get('stat', 'stat_percent_damage')
        stat_nb = extra.get('stat_nb', 1)
        args = [str(stat_nb), tr(stat_field.upper(), lang), str(value)]
        signs = [default_sign(stat_nb), SIGN_NEUTRAL, default_sign(value)]
    
    # --- SlowInZoneEffect ---
    elif key == 'effect_slow_in_zone':
        args = []
        signs = []
    
    # --- ProjectilesOnHitEffect / EFFECT_PROJECTILES_ON_HIT ---
    elif key in ('effect_projectiles_on_hit', 'EFFECT_PROJECTILES_ON_HIT'):
        ws = eff.get('weapon_stats', {})
        if ws:
            nb = abs(value) if value else ws.get('nb_projectiles', 3)
            dmg = ws.get('damage', 0)
            scaling_text = build_scaling_text(ws.get('scaling_stats', []), lang)
            bounce = ws.get('bounce', 0) + 1
            args = [str(nb), str(dmg), str(bounce), scaling_text]
            signs = [default_sign(value), default_sign(dmg), default_sign(bounce), default_sign(dmg)]
    
    # --- Lightning on hit ---
    elif key == 'effect_lightning_on_hit':
        ws = eff.get('weapon_stats', {})
        if ws:
            dmg = ws.get('damage', 0)
            scaling_text = build_scaling_text(ws.get('scaling_stats', []), lang)
            bounce = ws.get('bounce', 0) + 1
            args = [str(value), str(dmg), str(bounce), scaling_text]
            signs = [default_sign(value), default_sign(dmg), default_sign(bounce), default_sign(dmg)]
    
    # --- WeaponStackEffect: EFFECT_WEAPON_STACK ---
    elif key == 'EFFECT_WEAPON_STACK' and 'weapon_stacked_name' in eff:
        stat_key = eff.get('stat_displayed_name', 'stat_damage')
        stacked_name = tr(eff['weapon_stacked_name'].upper(), lang)
        stat_name = tr(stat_key.upper(), lang)
        # nb_same_weapon is runtime; we show total as 0 (placeholder)
        args = [str(value), stat_name, stacked_name, '0']
        signs = [default_sign(value), SIGN_NEUTRAL, SIGN_NEUTRAL, SIGN_NEUTRAL]
    
    # --- NullDoubleValueEffect / DoubleValueEffect ---
    elif 'value2' in extra and key and key not in ('effect_charm', 'effect_gain_stat_every_killed_enemies'):
        val2 = extra['value2']
        args = [str(value), tr(key.upper(), lang), str(val2)]
        signs = [default_sign(value), SIGN_NEUTRAL, default_sign(val2)]
    
    # --- PlayerNoHitEffect: effect_no_hit_boost ---
    elif key == 'effect_no_hit_boost':
        interval = extra.get('interval', 5)
        args = [str(value), str(interval)]
        signs = [default_sign(value), SIGN_NEUTRAL]
    
    # --- CharmEffect / NullCharmEffect ---
    elif key == 'effect_charm' or 'CHARM' in lookup_key:
        val2 = extra.get('value2', 60)
        args = [str(int(val2)), str(int(value)), '', str(8)]  # CHARM_DURATION=8
        signs = [SIGN_NEUTRAL, SIGN_NEUTRAL, SIGN_NEUTRAL, SIGN_NEUTRAL]
    
    # --- OneShotOnHitEffect: uses base args [value, tr(key)] ---
    elif key == 'effect_one_shot_on_hit' or lookup_key == 'EFFECT_ONE_SHOT_ON_HIT_EFFECT':
        args = [str(value)]
        signs = [default_sign(value)]
    
    # --- WeaponSlowOnHitEffect ---
    elif key in ('effect_weapon_slow_on_hit', 'EFFECT_WEAPON_SLOW_ON_HIT'):
        scaling_stat = eff.get('scaling_stat', 'stat_engineering')
        args = [str(value), '1', tr(scaling_stat.upper(), lang), '0']
        signs = [default_sign(value), SIGN_NEUTRAL, SIGN_NEUTRAL, SIGN_NEUTRAL]
    
    # --- StatGainsModificationEffect ---
    elif key in ('effect_increase_stat_gains', 'effect_reduce_stat_gains',
                 'EFFECT_INCREASE_STAT_GAINS', 'EFFECT_REDUCE_STAT_GAINS'):
        stat_displayed = eff.get('stat_displayed', '')
        args = [tr(stat_displayed.upper(), lang) if stat_displayed else '', str(abs(value))]
        signs = [SIGN_NEUTRAL, default_sign(abs(value))]
    
    # --- PercentDamageEffect / WeaponPercentDamageEffect ---
    elif 'duration_secs' in extra and 'max_stacks' in extra and key:
        dur = extra.get('duration_secs', 3)
        max_stacks = extra.get('max_stacks', 1)
        args = [str(value), tr(key.upper(), lang), str(dur), str(max_stacks * value)]
        signs = [default_sign(value), SIGN_NEUTRAL, SIGN_NEUTRAL, default_sign(max_stacks * value)]
    
    # --- GainStatForEveryStatEffect / WeaponGainStatForEveryStatEffect ---
    elif 'stat_scaled' in eff and key:
        nb = extra.get('nb_stat_scaled', eff.get('nb_stat_scaled', 0))
        stat_scaled = eff.get('stat_scaled', '')
        # Replicate Godot: "different_item" → tr("ITEM") (道具)
        if stat_scaled == "different_item":
            stat_scaled_text = tr("ITEM", lang)
        else:
            stat_scaled_text = tr(stat_scaled.upper(), lang) if stat_scaled else ''
        args = [str(value), tr(key.upper(), lang), str(nb), stat_scaled_text, '0']
        signs = [default_sign(value), SIGN_NEUTRAL, SIGN_NEUTRAL, SIGN_NEUTRAL, SIGN_NEUTRAL]
    
    # --- PlayerHealthStatEffect: effect_player_missing_health_damage_bonus ---
    elif 'for_every_health_percent' in extra:
        hp_pct = extra.get('for_every_health_percent', 25)
        args = [str(value), tr(key.upper(), lang), str(hp_pct), '0']
        signs = [default_sign(value), SIGN_NEUTRAL, SIGN_NEUTRAL, SIGN_NEUTRAL]
    
    # --- GainStatForKilledEnemiesWhileBurning ---
    elif 'value3' in extra and key:
        val2 = extra.get('value2', 0)
        val3 = extra.get('value3', 0)
        args = [str(value), tr(key.upper(), lang), str(val2), str(val3)]
        signs = [default_sign(value), SIGN_NEUTRAL, SIGN_NEUTRAL, SIGN_NEUTRAL]
    
    # --- StructureEffect (turrets, landmines, garden) ---
    elif 'structure_stats' in eff and text_key in ('effect_turret', 'effect_turret_flame',
            'effect_turret_laser', 'effect_turret_rocket', 'effect_landmines', 'effect_garden'):
        struct_stats = eff.get('structure_stats', {})
        is_spawning = eff.get('is_spawning', False)
        spawn_cd = extra.get('spawn_cooldown', 0)
        # spawn_cooldown is already in seconds; structure_stats.cooldown is in frames
        if spawn_cd > 0:
            cd_sec = spawn_cd
        elif struct_stats.get('cooldown', 0) > 0:
            cd_sec = struct_stats['cooldown'] / 60.0
        else:
            cd_sec = 12
        if cd_sec == int(cd_sec):
            cd_sec = int(cd_sec)
        dmg = struct_stats.get('damage', value)
        scaling = struct_stats.get('scaling_stats', [])
        scaling_text = build_scaling_text(scaling, lang)
        nb_proj = struct_stats.get('nb_projectiles', 1)
        bounce = struct_stats.get('bounce', 0)
        bd = eff.get('burning_data')
        if not bd:
            for se in eff.get('structure_effects', []):
                if se.get('burning_data'):
                    bd = se['burning_data']
                    break
        # TurretEffect.get_args() when is_spawning: [spawn_cd]
        # TurretEffect.get_args() when burning: [burn_dur, burn_dmg, burn_scaling, key_name]
        # TurretEffect.get_args() otherwise: [damage, scaling, nb_projectiles, bounce, key_name]
        # StructureEffect.get_args(): [value, spawn_cd, damage, scaling]
        if is_spawning:
            args = [str(cd_sec)]
            signs = [SIGN_NEUTRAL]
        elif bd and text_key in ('effect_turret_flame',):
            args = [str(bd.get('duration', 0)), str(bd.get('damage', 0)),
                    build_scaling_text(bd.get('scaling_stats', []), lang),
                    tr(key.upper(), lang) if key else '']
            signs = [SIGN_NEUTRAL, default_sign(bd.get('damage', 0)),
                     default_sign(bd.get('damage', 0)), SIGN_NEUTRAL]
        elif text_key in ('effect_turret', 'effect_turret_flame', 'effect_turret_laser', 'effect_turret_rocket'):
            args = [str(dmg), scaling_text, str(nb_proj), str(bounce),
                    tr(key.upper(), lang) if key else '']
            signs = [default_sign(dmg), default_sign(dmg), SIGN_NEUTRAL, SIGN_NEUTRAL, SIGN_NEUTRAL]
        else:
            args = [str(value), str(cd_sec), str(dmg), scaling_text]
            signs = [SIGN_NEUTRAL, SIGN_NEUTRAL, default_sign(dmg), default_sign(dmg)]
    
    # --- TurretEffect (spawning: is_spawning=true) ---
    elif custom_key == 'spawn_garden' or (key == 'effect_spawn_garden'):
        struct_stats = eff.get('structure_stats', {})
        cd_frames = struct_stats.get('cooldown', 900) if struct_stats else extra.get('interval', 900)
        cd_sec = cd_frames / 60.0 if cd_frames > 0 else 15
        if cd_sec == int(cd_sec):
            cd_sec = int(cd_sec)
        args = [str(cd_sec)]
        signs = [SIGN_NEUTRAL]
    
    # --- effect_spawn_landmine ---
    elif key == 'effect_spawn_landmine':
        ws = eff.get('weapon_stats', eff.get('structure_stats', {}))
        interval = extra.get('interval', 12)
        args = [str(interval)]
        signs = [SIGN_NEUTRAL]
    
    # --- effect_spawn_turret ---
    elif key == 'effect_spawn_turret':
        ws = eff.get('weapon_stats', {})
        if ws:
            dmg = ws.get('damage', 10)
            scaling_text = build_scaling_text(ws.get('scaling_stats', []), lang)
            args = [str(dmg), scaling_text]
            signs = [default_sign(dmg), default_sign(dmg)]
    
    # --- ItemExplodingEffect (item-level exploding) ---
    elif 'weapon_stats' in eff and key and 'explode' in key.lower():
        ws = eff.get('weapon_stats', {})
        chance_val = extra.get('chance', 1.0)
        dmg = ws.get('damage', 0)
        scaling_text = build_scaling_text(ws.get('scaling_stats', []), lang)
        args = [str(int(chance_val * 100)), str(dmg), scaling_text, str(value)]
        signs = [SIGN_NEUTRAL, default_sign(dmg), default_sign(dmg), default_sign(value)]
    
    # --- Pet effects: Ratzilla, CatlingGun ---
    elif key in ('ratzilla', 'catling_gun'):
        ws = eff.get('weapon_stats', {})
        if ws:
            dmg = ws.get('damage', 0)
            scaling_text = build_scaling_text(ws.get('scaling_stats', []), lang)
            args = [str(dmg), scaling_text]
            signs = [default_sign(dmg), default_sign(dmg)]
    
    # --- BonkDogEffect ---
    elif key == 'bonk_dog':
        ws = eff.get('weapon_stats', {})
        sub_effs = eff.get('sub_effects', eff.get('structure_effects', []))
        if ws:
            dmg = ws.get('damage', 0)
            scaling_text = build_scaling_text(ws.get('scaling_stats', []), lang)
            # Look for explosion sub-effect
            dash_dmg = ''
            dash_scaling = ''
            for se in sub_effs:
                se_ws = se.get('weapon_stats', se.get('structure_stats', {}))
                if se_ws:
                    dash_dmg = str(se_ws.get('damage', 0))
                    dash_scaling = build_scaling_text(se_ws.get('scaling_stats', []), lang)
                    break
            cd = ws.get('cooldown', 0) / 60.0
            if cd == int(cd): cd = int(cd)
            args = [str(dmg), scaling_text, str(cd), dash_dmg, dash_scaling]
            signs = [default_sign(dmg), default_sign(dmg), SIGN_NEUTRAL, default_sign(0), default_sign(0)]
    
    # --- BotOMineEffect ---
    elif key == 'bot_o_mine':
        ws = eff.get('weapon_stats', {})
        sub_effs = eff.get('sub_effects', eff.get('structure_effects', []))
        if ws:
            dmg = ws.get('damage', 0)
            scaling_text = build_scaling_text(ws.get('scaling_stats', []), lang)
            mine_dmg = ''
            mine_scaling = ''
            for se in sub_effs:
                se_ws = se.get('structure_stats', se.get('weapon_stats', {}))
                if se_ws:
                    mine_dmg = str(se_ws.get('damage', 0))
                    mine_scaling = build_scaling_text(se_ws.get('scaling_stats', []), lang)
                    break
            cd = ws.get('cooldown', 0) / 60.0
            if cd == int(cd): cd = int(cd)
            args = [str(dmg), scaling_text, str(cd), mine_dmg, mine_scaling]
            signs = [default_sign(dmg), default_sign(dmg), SIGN_NEUTRAL, default_sign(0), default_sign(0)]
    
    # --- BlazemanderEffect ---
    elif key == 'blazemander':
        ws = eff.get('weapon_stats', {})
        bd = eff.get('burning_data', {})
        if ws:
            dmg = ws.get('damage', 0)
            scaling_text = build_scaling_text(ws.get('scaling_stats', []), lang)
            burn_dur = bd.get('duration', 0) if bd else 0
            burn_dmg = bd.get('damage', 0) if bd else 0
            burn_scaling = build_scaling_text(bd.get('scaling_stats', []), lang) if bd else ''
            # ranged weapon stats from sub_effects or structure_effects
            proj_dmg = ''
            proj_scaling = ''
            cd = 0
            for se in eff.get('sub_effects', eff.get('structure_effects', [])):
                se_ws = se.get('weapon_stats', se.get('structure_stats', {}))
                if se_ws and se_ws.get('cooldown'):
                    cd = se_ws.get('cooldown', 0) / 60.0
                    proj_dmg = str(se_ws.get('damage', 0))
                    proj_scaling = build_scaling_text(se_ws.get('scaling_stats', []), lang)
                    break
            if cd == int(cd): cd = int(cd)
            args = [str(dmg), scaling_text, str(burn_dur), str(burn_dmg), burn_scaling,
                    str(cd), proj_dmg, proj_scaling]
            signs = [SIGN_NEUTRAL] * len(args)
    
    # --- LootwormEffect ---
    elif key == 'lootworm':
        dc = extra.get('double_chance', 0)
        pct = int(dc * 100) if dc and dc <= 1 else int(dc) if dc else 0
        args = [str(pct)]
        signs = [SIGN_NEUTRAL]
    
    # --- consumable_heal / effect_consumable_heal ---
    elif key in ('consumable_heal', 'effect_consumable_heal'):
        args = [str(value)]
        signs = [default_sign(value)]
    
    # --- reload_when_pickup_gold ---
    elif key in ('reload_when_pickup_gold', 'effect_reload_when_pickup_gold'):
        args = []
        signs = []
    
    # --- reload_turrets_on_shoot ---
    elif key in ('effect_reload_turrets_on_shoot', 'reload_turrets_on_shoot'):
        args = []
        signs = []
    
    # --- crit_on_hitting_burning_target ---
    elif key == 'crit_on_hitting_burning_target':
        args = []
        signs = []
    
    # --- effect_on_hit (temp stats on hit) ---
    elif custom_key == 'temp_stats_on_hit' or (key in ('effect_gain_stat_when_hit',)):
        stat_key = eff.get('stat', key)
        args = [str(value), tr(stat_key.upper(), lang) if stat_key else '']
        signs = [default_sign(value), SIGN_NEUTRAL]
    
    # --- effect_additional_weapon_bonus ---
    elif lookup_key == 'EFFECT_ADDITIONAL_WEAPON_BONUS' or custom_key == 'additional_weapon_effects':
        args = [str(value), tr(key.upper(), lang) if key else '']
        signs = [default_sign(value), SIGN_NEUTRAL]
    
    # --- effect_unique_weapon_bonus ---
    elif custom_key == 'unique_weapon_effects' or text_key == 'effect_unique_weapon_bonus':
        args = [str(value), tr(key.upper(), lang) if key else '', '0']
        signs = [default_sign(value), SIGN_NEUTRAL, SIGN_NEUTRAL]
    
    # --- effect_lose_hp_per_second ---
    elif key in ('effect_lose_hp_per_second', 'lose_hp_per_second'):
        args = [str(abs(value))]
        signs = [SIGN_NEUTRAL]
    
    # --- break_on_hit / effect_break_on_hit ---
    elif key in ('break_on_hit', 'effect_break_on_hit'):
        chance_pct = value
        materials = extra.get('value2', 10)
        args = [str(chance_pct), str(int(materials) if isinstance(materials, float) else str(materials))]
        signs = [SIGN_NEUTRAL, SIGN_NEUTRAL]
    
    # --- effect_explode_on_overkill ---
    elif key == 'explode_on_overkill' or lookup_key == 'EFFECT_EXPLODE_ON_OVERKILL':
        ws = eff.get('weapon_stats', eff.get('structure_stats', {}))
        if ws:
            dmg = ws.get('damage', 0)
            scaling_text = build_scaling_text(ws.get('scaling_stats', []), lang)
        else:
            dmg = value
            scaling_text = ''
        args = [str(abs(value)), str(dmg), scaling_text, str(abs(value))]
        signs = [SIGN_NEUTRAL, SIGN_NEUTRAL, SIGN_NEUTRAL, SIGN_NEUTRAL]
    
    # --- effect_burn_chance (scared_sausage) ---
    elif key == 'burn_chance' or lookup_key == 'EFFECT_BURN_CHANCE':
        bd = eff.get('burning_data', {})
        if bd:
            dur = bd.get('duration', 0)
            dmg = bd.get('damage', 0)
            scaling = build_scaling_text(bd.get('scaling_stats', []), lang)
            args = [str(int(value)), str(dur), str(dmg), scaling]
            signs = [SIGN_NEUTRAL, SIGN_NEUTRAL, SIGN_NEUTRAL, SIGN_NEUTRAL]
    
    # --- BuilderTurretUpgradeEffect ---
    elif lookup_key == 'EFFECT_BUILDER_TURRET_UPGRADE':
        args = [str(value), tr(key.upper(), lang) if key else '', '-', tr('STRUCTURE_RANGE', lang), '0', '-']
        signs = [SIGN_NEUTRAL] * 6
    
    # --- For effects with text_key that have format strings, use base args ---
    # This handles many generic effects like effect_gain_stat_end_of_wave,
    # effect_stat_while_moving, effect_stat_while_not_moving, etc.
    # The base args are [str(value), tr(key.upper())]
    
    # Now apply custom_args overrides
    args, signs = _apply_custom_args(args, signs, custom_args, eff, value, effect_sign, lang)
    
    return args, signs, lookup_key


def _apply_custom_args(args, signs, custom_args, eff, value, effect_sign, lang):
    """Apply custom_args from .tres files, replicating Effect.get_text() custom_arg logic."""
    if not custom_args:
        return args, signs
    
    for ca in custom_args:
        idx = ca.get('arg_index', 0)
        arg_sign = ca.get('arg_sign', SIGN_FROM_ARG)
        arg_value = ca.get('arg_value', ARG_USUAL)
        arg_format = ca.get('arg_format', FORMAT_USUAL)
        arg_key = ca.get('arg_key', '')
        
        # Extend args/signs if needed
        while len(args) <= idx:
            args.append('')
        while len(signs) <= idx:
            signs.append(SIGN_NEUTRAL)
        
        # Get the base value at this index (for FROM_ARG sign computation)
        base_val_str = args[idx]
        try:
            base_val_int = int(float(base_val_str)) if base_val_str else 0
        except (ValueError, TypeError):
            base_val_int = 0
        
        # Compute arg value based on ArgValue type
        if arg_value == ARG_VALUE:
            args[idx] = str(value)
        elif arg_value == ARG_ABS_VALUE:
            args[idx] = str(abs(value))
        elif arg_value == ARG_KEY:
            key_to_tr = arg_key if arg_key else eff.get('key', '')
            args[idx] = tr(key_to_tr.upper(), lang)
        elif arg_value == ARG_TIER:
            tier_key = TIER_MAP.get(value, 'TIER_I')
            args[idx] = tr(tier_key, lang)
        elif arg_value == ARG_SCALING_STAT:
            # Build scaling stat icon text
            key = eff.get('key', '')
            scaling_stats = eff.get('weapon_stats', {}).get('scaling_stats', [])
            if scaling_stats:
                args[idx] = build_scaling_text(scaling_stats, lang)
        elif arg_value == ARG_DIFFICULTY_VALUE:
            # Skip if difficulty < threshold (can't determine statically)
            pass
        
        # Compute sign
        try:
            new_val_int = int(float(args[idx])) if args[idx] else 0
        except (ValueError, TypeError):
            new_val_int = 0
        signs[idx] = _get_effect_sign(arg_sign, value, new_val_int)
        
        # Apply format
        args[idx] = _get_formatted_value(args[idx], arg_format, value)
    
    return args, signs


UNRENDERABLE_EFFECTS = []


def _find_tr_key(eff):
    """Find the translation key for an effect following Godot's key resolution.
    
    Godot uses text_key.to_upper() if text_key is set, else key.to_upper().
    We also try with/without EFFECT_ prefix, and fall back to key alone.
    """
    text_key = eff.get('text_key', '')
    key = eff.get('key', '')

    # Build candidate keys: text_key variants first, then key variants
    candidates = []
    if text_key:
        tk = text_key.upper()
        candidates.append(tk)
        if tk.startswith('EFFECT_'):
            candidates.append(tk[7:])
        else:
            candidates.append('EFFECT_' + tk)
    if key:
        kk = key.upper()
        if kk not in candidates:
            candidates.append(kk)
        if not kk.startswith('EFFECT_'):
            ek = 'EFFECT_' + kk
            if ek not in candidates:
                candidates.append(ek)

    for c in candidates:
        if c and c in TR:
            return c, TR[c]

    # Reverse lookup by English text
    if text_key and text_key in TR_BY_EN:
        rk = TR_BY_EN[text_key]
        return rk, TR[rk]
    if key and key in TR_BY_EN:
        rk = TR_BY_EN[key]
        return rk, TR[rk]

    return None, None


def _text_render(fmt_key, fmt, args, arg_signs, lang):
    """Render a format string following text.gd rules:
    1. Auto-prepend {0} if key needs operator but format lacks {0}
    2. For each arg: add operator(+), add percent(%), wrap color
    3. Replace {i} placeholders
    4. Remove runtime-value brackets like [X], [+X], [-X]
    """
    if not fmt:
        return ''

    key_lower = (fmt_key or '').lower()

    # Auto-prepend {0} if key needs operator but template has no {0}
    if '{0}' not in fmt and key_lower in KEYS_NEEDING_OPERATOR:
        fmt = ('{0}' if fmt.startswith('%') else '{0} ') + fmt

    if '{' not in fmt:
        return fmt

    # Determine max placeholder index
    max_idx = max((int(m.group(1)) for m in re.finditer(r'\{(\d+)\}', fmt)), default=-1)
    count = max(max_idx + 1, len(args))

    formatted = []
    for i in range(count):
        raw = str(args[i]) if i < len(args) and args[i] else ''
        sign = arg_signs[i] if i < len(arg_signs) else ''

        # Add operator (+) — game uses >= 0
        if key_lower in KEYS_NEEDING_OPERATOR and i in KEYS_NEEDING_OPERATOR[key_lower]:
            if raw and not raw.startswith('+') and not raw.startswith('-'):
                try:
                    v = float(raw.lstrip('+').rstrip('%'))
                    if v >= 0:
                        raw = '+' + raw
                except (ValueError, TypeError):
                    raw = '+' + raw

        # Add percent (%)
        if key_lower in KEYS_NEEDING_PERCENT and i in KEYS_NEEDING_PERCENT[key_lower]:
            if raw and not raw.endswith('%'):
                raw = raw + '%'

        # Wrap with color
        if sign and raw:
            raw = wrap_color(raw, sign)

        formatted.append(raw)

    # Replace placeholders
    result = fmt
    for i, arg in enumerate(formatted):
        result = result.replace('{' + str(i) + '}', str(arg))

    # Cleanup leftover placeholders and empty brackets
    result = re.sub(r'\s*\{\d+\}\s*', ' ', result)
    result = re.sub(r'[（(]\s*[）)]', '', result)
    # Remove runtime-value brackets: [anything] — game uses these for live computed values
    result = re.sub(r'\s*\[.*?\]', '', result)
    result = re.sub(r'\s+', ' ', result).strip()
    return result


def _text_render_template(fmt_key, fmt, args, arg_signs, curse_types, lang):
    """Render a format string to a template with {0},{1} placeholders for cursed values.
    
    Like _text_render but:
    - Cursed args: replaced with colored/operatored/{i} placeholder in template
    - Non-cursed args: baked into the template as final rendered text
    
    Returns tuple: (template_string_en, template_string_zh, curse_args_list)
    where curse_args_list = [{"value": v, "curse": type}, ...] for cursed args only.
    """
    if not fmt:
        return fmt, []

    key_lower = (fmt_key or '').lower()

    # Auto-prepend {0} if key needs operator but template has no {0}
    if '{0}' not in fmt and key_lower in KEYS_NEEDING_OPERATOR:
        fmt = ('{0}' if fmt.startswith('%') else '{0} ') + fmt

    if '{' not in fmt:
        return fmt, []

    max_idx = max((int(m.group(1)) for m in re.finditer(r'\{(\d+)\}', fmt)), default=-1)
    count = max(max_idx + 1, len(args))

    # Build rendered replacements and track curse
    rendered = []      # what goes into template for each {i}
    curse_args = []    # collected curse info
    curse_remap = {}   # original index → new curse arg index
    next_curse_idx = 0

    for i in range(count):
        raw = str(args[i]) if i < len(args) and args[i] else ''
        sign = arg_signs[i] if i < len(arg_signs) else ''
        ct = curse_types[i] if i < len(curse_types) else None

        # Parse numeric value for this arg
        try:
            # Strip both + and - signs: the sign in the template (e.g., "-{0}") 
            # carries the visual sign; the arg value should be positive.
            numeric_val = float(raw.lstrip('+-').rstrip('%'))
        except (ValueError, TypeError):
            numeric_val = None

        # Add operator (+)
        if key_lower in KEYS_NEEDING_OPERATOR and i in KEYS_NEEDING_OPERATOR[key_lower]:
            if raw and not raw.startswith('+') and not raw.startswith('-'):
                try:
                    v = float(raw.lstrip('+').rstrip('%'))
                    if v >= 0:
                        raw = '+' + raw
                except (ValueError, TypeError):
                    raw = '+' + raw

        # Add percent (%)
        if key_lower in KEYS_NEEDING_PERCENT and i in KEYS_NEEDING_PERCENT[key_lower]:
            if raw and not raw.endswith('%'):
                raw = raw + '%'

        if ct is not None and numeric_val is not None:
            # This arg is cursed → replace with {curse_idx} wrapped in color
            ci = next_curse_idx
            next_curse_idx += 1
            
            # Build the cursed placeholder: same color/operator/percent, but {ci} instead of value
            numeric_str = raw.lstrip('+-').rstrip('%')
            placeholder_raw = raw.replace(numeric_str, '{' + str(ci) + '}', 1)
            
            if sign and placeholder_raw:
                placeholder_raw = wrap_color(placeholder_raw, sign)
            rendered.append(placeholder_raw)
            
            # Use the structured curse dict (already built by _build_curse_types)
            curse_args.append(ct)
        else:
            # Not cursed → bake final rendered value into template
            if sign and raw:
                raw = wrap_color(raw, sign)
            rendered.append(raw)

    # Replace placeholders with rendered (some baked, some templates)
    result = fmt
    for i, rep in enumerate(rendered):
        result = result.replace('{' + str(i) + '}', str(rep))

    # Cleanup empty brackets and runtime-value brackets (KEEP {0},{1}... curse placeholders!)
    result = re.sub(r'[（(]\s*[）)]', '', result)
    # Remove runtime-value brackets: [anything]
    result = re.sub(r'\s*\[.*?\]', '', result)
    result = re.sub(r'\s+', ' ', result).strip()
    return result, curse_args


def render_effect_text(eff, lang, parent_id='', is_weapon=False):
    """Render an effect to human-readable text following Godot's rendering pipeline.

    Pipeline (mirrors effect.gd -> text.gd):
    1. Determine translation key (text_key or key, uppercased)
    2. Look up format string from TR
    3. Build args based on effect type (mimicking each class's get_args())
    4. Apply custom_args overrides (value, sign, format)
    5. Render with text.gd rules (operator/percent/color)
    """
    key = eff.get('key', '')
    value = eff.get('value', 0)
    text_key = eff.get('text_key', '')
    custom_key = eff.get('custom_key', '')
    extra = eff.get('extra', {})
    base_color = sign_color(eff)
    tk_upper = (text_key or key).upper()

    # Godot: Text.text("[EMPTY]") returns ""
    if text_key == '[EMPTY]' or (not text_key and not key):
        return '', []

    STAT_KEYS = {
        'stat_max_hp', 'stat_damage', 'stat_percent_damage', 'stat_armor',
        'stat_crit_chance', 'stat_luck', 'stat_attack_speed', 'stat_elemental_damage',
        'stat_hp_regeneration', 'stat_lifesteal', 'stat_melee_damage', 'stat_ranged_damage',
        'stat_dodge', 'stat_engineering', 'stat_range', 'stat_speed',
        'stat_harvesting', 'stat_knockback', 'stat_curse', 'stat_xp_gain',
        'xp_gain', 'explosion_size', 'stat_explosion_size',
        'explosion_damage', 'stat_explosion_damage',
    }

    # ------------------------------------------------------------------
    # Step 1: Find translation format string
    # ------------------------------------------------------------------
    fmt_key, fmt_trans = _find_tr_key(eff)
    fmt = None
    if fmt_trans:
        fmt = fmt_trans.get(lang, '') or fmt_trans.get('en', '')

    # ------------------------------------------------------------------
    # Step 2: Build args based on effect type (mimicking get_args())
    # ------------------------------------------------------------------
    args = [''] * 10
    arg_signs = [base_color] * 10
    args_built = False

    # --- ExplodingEffect ---
    if key in ('effect_explode', 'effect_explode_melee', 'effect_explode_custom'):
        args[0] = str(int(round(extra.get('chance', 1.0) * 100)))
        args_built = True

    # --- BurningEffect ---
    elif key == 'effect_burning':
        bd = eff.get('burning_data', {})
        if bd:
            args[0] = str(bd.get('duration', 0))
            arg_signs[0] = ''
            args[1] = str(bd.get('damage', 0))
            args[2] = build_scaling_text(bd.get('scaling_stats', []), lang)
        args_built = True

    # --- GainStatEveryKilledEnemiesEffect ---
    elif key == 'effect_gain_stat_every_killed_enemies':
        stat_field = eff.get('stat', 'stat_percent_damage')
        stat_nb = eff.get('stat_nb', 1)
        args[0] = str(stat_nb)
        args[1] = tr(stat_field.upper(), lang)
        args[2] = str(value)
        args_built = True

    # --- BreakOnHitEffect ---
    elif key in ('break_on_hit', 'effect_break_on_hit'):
        chance_pct = value
        materials = extra.get('value2', 10)
        # Format string uses {0} for chance and {2} for materials (skipping {1})
        args[0] = str(chance_pct)
        args[2] = str(int(materials) if isinstance(materials, float) else materials)
        args_built = True

    # --- SlowInZoneEffect ---
    elif key == 'effect_slow_in_zone':
        args_built = True

    # --- ProjectilesOnHitEffect ---
    elif key in ('effect_projectiles_on_hit', 'EFFECT_PROJECTILES_ON_HIT',
                 'EFFECT_SLOW_PROJECTILES_ON_HIT', 'effect_slow_projectiles_on_hit'):
        ws = eff.get('weapon_stats')
        if ws:
            args[0] = str(abs(value) if value else ws.get('nb_projectiles', 3))
            args[1] = str(ws.get('damage', 0))
            args[2] = str(ws.get('bounce', 0) + 1)
            args[3] = build_scaling_text(ws.get('scaling_stats', []), lang)
        args_built = True

    # --- LightningOnHitEffect ---
    elif key == 'effect_lightning_on_hit' or tk_upper == 'EFFECT_LIGHTNING_ON_HIT':
        ws = eff.get('weapon_stats')
        if ws:
            args[0] = str(value)
            args[1] = str(ws.get('damage', 0))
            args[2] = str(ws.get('bounce', 0) + 1)
            args[3] = build_scaling_text(ws.get('scaling_stats', []), lang)
        args_built = True

    # --- ProjectilesOnDeathEffect ---
    elif key == 'projectiles_on_death' or text_key == 'effect_projectiles_on_death':
        ws = eff.get('weapon_stats')
        if ws:
            args[0] = str(value)
            args[1] = str(ws.get('damage', 0))
            args[2] = str(ws.get('bounce', 0) + 1)
            args[3] = build_scaling_text(ws.get('scaling_stats', []), lang)
        args_built = True

    # --- CharmEffect ---
    elif key == 'effect_charm' or (not key and 'CHARM' in tk_upper):
        args[0] = str(int(extra.get('value2', 60)))
        args[1] = str(int(value))
        args[3] = '8'
        args_built = True

    # --- StructureEffect ---
    elif tk_upper in {k.upper() for k in (
        'effect_landmines', 'effect_turret', 'effect_turret_flame',
        'effect_turret_laser', 'effect_turret_rocket', 'effect_garden',
    )} or key in ('effect_spawn_garden', 'effect_spawn_landmine'):
        struct_stats = eff.get('structure_stats', {})
        is_spawning = eff.get('is_spawning', False)
        spawn_cd = extra.get('spawn_cooldown', extra.get('interval', 0))
        # spawn_cooldown is already in seconds; structure_stats.cooldown is in frames
        if spawn_cd > 0:
            cd_sec = spawn_cd
        elif struct_stats.get('cooldown', 0) > 0:
            cd_sec = struct_stats['cooldown'] / 60.0
        else:
            cd_sec = 12
        if cd_sec == int(cd_sec):
            cd_sec = int(cd_sec)
        dmg = struct_stats.get('damage', value) if struct_stats else value
        scaling = struct_stats.get('scaling_stats', []) if struct_stats else []
        scaling_text = build_scaling_text(scaling, lang)
        nb_proj = struct_stats.get('nb_projectiles', 1) if struct_stats else 1
        bounce = struct_stats.get('bounce', 0) if struct_stats else 0
        bd = eff.get('burning_data')
        if not bd:
            for se in eff.get('structure_effects', []):
                if se.get('burning_data'):
                    bd = se['burning_data']
                    break
        if is_spawning:
            args[0] = str(cd_sec)
        elif bd and tk_upper in ('EFFECT_TURRET_FLAME',):
            args[0] = str(bd.get('duration', 0))
            args[1] = str(bd.get('damage', 0))
            args[2] = build_scaling_text(bd.get('scaling_stats', []), lang)
            args[3] = tr(key.upper(), lang) if key else ''
        elif tk_upper in ('EFFECT_TURRET', 'EFFECT_TURRET_FLAME', 'EFFECT_TURRET_LASER', 'EFFECT_TURRET_ROCKET'):
            args[0] = str(dmg)
            args[1] = scaling_text
            args[2] = str(nb_proj)
            args[3] = str(bounce)
            args[4] = tr(key.upper(), lang) if key else ''
        else:
            args[0] = str(value)
            args[1] = str(cd_sec)
            args[2] = str(dmg)
            args[3] = scaling_text
        args_built = True

    # --- Pet effects ---
    elif tk_upper in ('EFFECT_PET_RATZILLA', 'EFFECT_PET_CATLING_GUN'):
        ws = eff.get('weapon_stats') or eff.get('structure_stats', {})
        if ws:
            args[0] = str(ws.get('damage', 0) or value)
            args[1] = build_scaling_text(ws.get('scaling_stats', []), lang)
        args_built = True

    elif tk_upper == 'EFFECT_PET_BONK_DOG':
        ws = eff.get('weapon_stats') or eff.get('structure_stats', {})
        if ws:
            args[0] = str(ws.get('damage', 0) or value)
            args[1] = build_scaling_text(ws.get('scaling_stats', []), lang)
            # Hardcoded: dash cooldown is 5 seconds (not in static data)
            args[2] = '5'
            for se in eff.get('structure_effects', []):
                se_ws = se.get('weapon_stats') or se.get('structure_stats', {})
                if se_ws:
                    args[3] = str(se_ws.get('damage', 0))
                    args[4] = build_scaling_text(se_ws.get('scaling_stats', []), lang)
                    break
        args_built = True

    elif tk_upper == 'EFFECT_PET_BLAZEMANDER':
        ws = eff.get('weapon_stats') or eff.get('structure_stats', {})
        bd = eff.get('burning_data', {})
        if ws:
            args[0] = str(ws.get('damage', 0) or value)
            args[1] = build_scaling_text(ws.get('scaling_stats', []), lang)
            if bd:
                args[2] = str(bd.get('duration', 0))
                args[3] = str(bd.get('damage', 0))
                args[4] = build_scaling_text(bd.get('scaling_stats', []), lang)
            # Hardcoded: projectile cooldown is 4 seconds (not in static data)
            args[5] = '4'
            for se in eff.get('structure_effects', []):
                se_ws = se.get('weapon_stats') or se.get('structure_stats', {})
                if se_ws:
                    args[6] = str(se_ws.get('damage', 0))
                    args[7] = build_scaling_text(se_ws.get('scaling_stats', []), lang)
                    break
        args_built = True
        args_built = True

    elif tk_upper == 'EFFECT_PET_LOOTWORM':
        dc = extra.get('double_chance', 0)
        if dc:
            args[0] = f'{int(dc * 100 if dc <= 1 else dc)}%'
        else:
            args[0] = f'{int(value * 10)}%'
        args_built = True

    elif tk_upper == 'EFFECT_PET_BOT_O_MINE':
        ws = eff.get('weapon_stats') or eff.get('structure_stats', {})
        if ws:
            args[0] = str(ws.get('damage', 0) or value)
            args[1] = build_scaling_text(ws.get('scaling_stats', []), lang)
            # Hardcoded: landmine cooldown is 5 seconds (not in static data)
            args[2] = '5'
            for se in eff.get('structure_effects', []):
                se_ws = se.get('structure_stats') or se.get('weapon_stats', {})
                if se_ws:
                    args[3] = str(se_ws.get('damage', 0))
                    args[4] = build_scaling_text(se_ws.get('scaling_stats', []), lang)
                    break
        args_built = True

    elif tk_upper in ('EFFECT_PET_DOC_MOTH', 'EFFECT_PET_SCAPEGOAT', 'EFFECT_PET_JELLYSHIELD',
                       'EFFECT_TURRET_HEALING', 'EFFECT_BUILDER_TURRET', 'EFFECT_BUILDER_TURRET_ALT',
                       'EFFECT_BUILDER_TURRET_UPGRADE', 'EFFECT_TYLER'):
        ws = eff.get('weapon_stats') or eff.get('structure_stats', {})
        if ws:
            args[0] = str(ws.get('damage', 0) or value)
            args[1] = build_scaling_text(ws.get('scaling_stats', []), lang)
            if tk_upper == 'EFFECT_TYLER':
                args[2] = str(ws.get('nb_projectiles', 1))
            if 'BUILDER_TURRET' in tk_upper:
                args[4] = tr('STRUCTURE_RANGE', lang)
        args_built = True

    elif tk_upper == 'EFFECT_ALIEN_EYES':
        ws = eff.get('weapon_stats') or eff.get('structure_stats', {})
        if ws:
            args[0] = str(value)
            args[1] = str(ws.get('damage', 0))
            args[3] = build_scaling_text(ws.get('scaling_stats', []), lang)
            # Use effect_cooldown (from effect file) instead of weapon_stats.cooldown
            cd = eff.get('effect_cooldown', 0)
            if cd > 0:
                args[4] = str(cd)
            else:
                cd_frames = ws.get('cooldown', 0)
                args[4] = str(int(cd_frames / 60)) if cd_frames else '0'
        args_built = True

    elif tk_upper == 'EFFECT_EXPLODE_AND_BURN_ON_CONSUMABLE':
        bd = eff.get('burning_data', {})
        # Translation: "捡起消耗品时，它会爆炸并造成{4}x{5}（{6}）燃烧伤害"
        # Parent (ItemExplodingEffect) args: {0}=chance%, {1}=damage, {2}=scaling, {3}=value
        # Sub-effect (burning) args: {4}=duration, {5}=damage, {6}=scaling
        ws = eff.get('weapon_stats') or eff.get('structure_stats', {})
        chance_val = extra.get('chance', 1.0)
        args[0] = f'{int(chance_val * 100)}%' if chance_val <= 1 else f'{int(chance_val)}%'
        if ws:
            args[1] = str(ws.get('damage', 0))
            args[2] = build_scaling_text(ws.get('scaling_stats', []), lang)
        if bd:
            args[4] = str(bd.get('duration', 0))
            args[5] = str(bd.get('damage', 0))
            args[6] = build_scaling_text(bd.get('scaling_stats', []), lang)
        args_built = True

    # --- ExplodeOnConsumable ---
    elif key == 'explode_on_consumable' or tk_upper == 'EFFECT_EXPLODE_ON_CONSUMABLE':
        ws = eff.get('weapon_stats') or eff.get('structure_stats', {})
        chance_val = extra.get('chance', 0.5)
        args[0] = f'{int(chance_val * 100)}%' if chance_val <= 1 else f'{int(chance_val)}%'
        if ws:
            # Hardcoded: spicy sauce base damage is 10 (data shows 0)
            dmg = ws.get('damage', 0)
            if dmg == 0 and ws.get('scaling_stats'):
                dmg = 10  # Spicy sauce base damage
            args[1] = str(dmg)
            args[2] = build_scaling_text(ws.get('scaling_stats', []), lang)
        args_built = True

    # --- ItemExplodingEffect ---
    elif tk_upper == 'EFFECT_EXPLODE_ON_OVERKILL' or key == 'explode_on_overkill':
        ws = eff.get('weapon_stats') or eff.get('structure_stats', {})
        args[0] = str(int(round(value * 100 if value <= 1 else value)))
        if ws:
            args[1] = str(ws.get('damage', 0))
            args[2] = build_scaling_text(ws.get('scaling_stats', []), lang)
        args[3] = str(value)
        args_built = True

    # --- WeaponStackEffect ---
    elif tk_upper == 'EFFECT_WEAPON_STACK':
        args[0] = str(value)
        args[1] = tr(eff.get('stat_displayed_name', 'stat_damage').upper(), lang)
        args[2] = tr(eff.get('weapon_stacked_name', key).upper(), lang)
        nb = eff.get('nb', 1)
        args[3] = str(nb * value)
        args_built = True

    # --- GainStatForEveryStatEffect ---
    elif tk_upper in ('EFFECT_GAIN_STAT_FOR_EVERY_STAT', 'EFFECT_GAIN_STAT_FOR_EVERY_PERM_STAT',
                       'EFFECT_GAIN_STAT_FOR_EVERY_DIFFERENT_STAT', 'EFFECT_GAIN_STAT_FOR_EVERY_ENEMY',
                       'EFFECT_GAIN_STAT_FOR_EVERY_BURNING_ENEMY', 'EFFECT_GAIN_STAT_FOR_EVERY_TREE',
                       'EFFECT_GAIN_STAT_FOR_DUPLICATE_ITEMS'):
        args[0] = str(value)
        args[1] = tr(key.upper(), lang)
        nb = extra.get('nb_stat_scaled', eff.get('stat_nb', 0))
        args[2] = str(int(nb)) if nb else ''
        scaled_s = eff.get('stat_scaled', eff.get('stat', key))
        # Replicate Godot: "different_item" → tr("ITEM") (道具)
        if scaled_s == "different_item":
            args[3] = tr("ITEM", lang)
        else:
            args[3] = stat_display_name(scaled_s, lang) if scaled_s else ''
        args_built = True

    # --- PercentDamageEffect ---
    elif tk_upper == 'EFFECT_INCREASE_DAMAGE_RECEIVED':
        args[0] = str(value)
        args[1] = tr(key.upper(), lang)
        args[2] = str(extra.get('duration_secs', 3))
        args[3] = str(extra.get('max_stacks', 3) * value)
        args_built = True

    # --- TempStatsPerIntervalEffect ---
    elif tk_upper == 'EFFECT_TEMP_STATS_PER_INTERVAL' or custom_key == 'temp_stats_per_interval':
        args[0] = str(value)
        args[1] = tr(key.upper(), lang)
        args[2] = str(extra.get('interval', 5))
        arg_signs[2] = ''
        args_built = True

    # --- PlayerNoHitEffect ---
    elif key == 'effect_no_hit_boost' or tk_upper == 'EFFECT_NO_HIT_BOOST':
        args[0] = str(value)
        args[1] = str(extra.get('interval', 5))
        args_built = True

    # --- NullDoubleValueEffect ---
    elif tk_upper in ('EFFECT_STAT_ON_EVERY_STEP', 'EFFECT_BONUS_DAMAGE_AGAINST_TARGETS_BELOW_HP',
                       'EFFECT_BONUS_DAMAGE_AGAINST_TARGETS_ABOVE_HP'):
        args[0] = str(value)
        args[1] = tr(key.upper(), lang)
        args[2] = str(int(extra.get('value2', 70)))
        args_built = True

    # --- WeaponSlowOnHitEffect ---
    elif key in ('effect_weapon_slow_on_hit', 'EFFECT_WEAPON_SLOW_ON_HIT'):
        args[0] = str(value)
        args[1] = '1'
        args[2] = tr(eff.get('scaling_stat', 'stat_engineering').upper(), lang)
        args[3] = str(value)
        args_built = True

    # --- PlayerHealthStatEffect ---
    elif tk_upper in ('EFFECT_PLAYER_MISSING_HEALTH_DAMAGE_BONUS',
                       'EFFECT_GAIN_STAT_FOR_EVERY_PERCENT_PLAYER_MISSING_HEALTH'):
        args[0] = str(value)
        args[1] = tr(key.upper(), lang)
        args[2] = str(int(extra.get('for_every_health_percent', extra.get('nb_stat_scaled', 25))))
        args[3] = str(extra.get('bonus_damage', 0))
        args_built = True

    # --- StatGainsModificationEffect ---
    elif key in ('effect_increase_stat_gains', 'effect_reduce_stat_gains') or tk_upper == 'EFFECT_REDUCE_STAT_GAINS':
        args[0] = tr(eff.get('stat_displayed', key).upper(), lang)
        args[1] = str(abs(value))
        args_built = True

    # --- MinimumWeaponCooldownEffect ---
    elif key == 'minimum_weapon_cooldowns' or tk_upper == 'EFFECT_MINIMUM_WEAPON_COOLDOWN':
        # value is in frames (60fps), convert to seconds
        args[0] = str(round(value / 60.0, 2))
        args_built = True

    # --- Heal when dodge (Adrenaline) ---
    elif tk_upper == 'EFFECT_HEAL_WHEN_DODGE':
        # Translation: "{0} chance to heal {1} HP when dodging an attack"
        # extra.chance is already a percentage (50 = 50%)
        chance_val = extra.get('chance', 100)
        args[0] = f'{int(chance_val)}%' if chance_val > 1 else f'{int(chance_val * 100)}%'
        args[1] = str(value)  # HP to heal
        args_built = True

    # --- ChanceStatDamageEffect (damage triggers) ---
    elif tk_upper in ('EFFECT_DEAL_DMG_WHEN_PICKUP_GOLD', 'EFFECT_DEAL_DMG_WHEN_DEATH',
                       'EFFECT_DEAL_DMG_WHEN_DODGE', 'EFFECT_DEAL_DMG_WHEN_HEAL'):
        chance_val = extra.get('chance', value)
        args[0] = f'{int(chance_val)}%'
        args[1] = '1'
        args[2] = build_scaling_text(
            [[key, value / 100.0 if value else 0]], lang) if value else ''
        args_built = True

    # --- BurnChanceEffect ---
    elif tk_upper == 'EFFECT_BURN_CHANCE':
        bd = eff.get('burning_data', {})
        # chance is in burning_data.chance (0.25 = 25%), not extra.chance
        chance_val = bd.get('chance', extra.get('chance', 0))
        args[0] = f'{int(chance_val * 100)}%'
        args[1] = str(bd.get('duration', 0))
        arg_signs[1] = ''
        args[2] = str(bd.get('damage', 0))
        args[3] = build_scaling_text(bd.get('scaling_stats', []), lang)
        args_built = True

    # --- WeaponCooldownEffect ---
    elif tk_upper == 'EFFECT_WEAPON_COOLDOWN':
        args[0] = str(round(value / 60.0, 2))
        args_built = True

    # --- Stat effects with text_key (translation-driven) ---
    elif key in STAT_KEYS and text_key:
        args[0] = str(value)
        args[1] = stat_display_name(key, lang)

        if tk_upper in ('EFFECT_GAIN_STATS_ON_REROLL',):
            v2 = extra.get('value2', extra.get('chance', 0))
            args[2] = f'{int(v2)}%' if v2 else ''

        elif tk_upper in ('EFFECT_TEMP_STATS_PER_INTERVAL', 'EFFECT_DECAYING_STAT_ON_CONSUMABLE',
                           'EFFECT_DECAYING_STAT_ON_HIT', 'EFFECT_GAIN_STAT_WHEN_ATTACK_KILLED_ENEMIES',
                           'EFFECT_CONSUMABLE_STAT_WHILE_MAX_LIMITED'):
            val_map = {
                'EFFECT_TEMP_STATS_PER_INTERVAL': extra.get('interval', 5),
                'EFFECT_DECAYING_STAT_ON_CONSUMABLE': extra.get('value2', extra.get('duration_secs', 2)),
                'EFFECT_DECAYING_STAT_ON_HIT': extra.get('value2', extra.get('duration_secs', 0)),
                'EFFECT_GAIN_STAT_WHEN_ATTACK_KILLED_ENEMIES': extra.get('stat_nb', extra.get('nb_stat_scaled', 2)),
                'EFFECT_CONSUMABLE_STAT_WHILE_MAX_LIMITED': extra.get('value2', extra.get('max_stacks', 3)),
            }
            v = val_map.get(tk_upper, 0)
            args[2] = str(int(v)) if v else ''

        elif tk_upper == 'EFFECT_GAIN_STAT_FOR_KILLED_ENEMIES_WHILE_BURNING':
            kc = extra.get('stat_nb', extra.get('nb_stat_scaled', 5))
            args[0] = str(int(kc)) if kc else ''
            args[1] = stat_display_name(key, lang)
            args[2] = str(value)
            mv = extra.get('max_stacks', 0)
            args[3] = str(int(mv)) if mv else ''

        elif tk_upper == 'EFFECT_ENEMY_PERCENT_DAMAGE_TAKEN_ONCE':
            args[0] = f'{value}%'
            args[1] = str(int(extra.get('duration_secs', 3)))
            args[2] = stat_display_name(key, lang)

        elif tk_upper == 'EFFECT_STAT_ON_FRUIT':
            v2 = extra.get('value2', extra.get('chance', 0))
            args[2] = f'{int(v2)}%' if v2 else ''

        elif tk_upper == 'EFFECT_GAIN_STAT_FOR_EQUIPPED_ITEM_WITH_STAT':
            scaled_s = eff.get('stat_scaled', eff.get('stat', key))
            if scaled_s:
                args[3] = stat_display_name(scaled_s, lang)

        # --- Convert stat effects ---
        elif tk_upper in ('EFFECT_CONVERT_STAT_TEMP_HALF_WAVE', 'EFFECT_CONVERT_STAT_END_OF_WAVE'):
            # Hardcoded values for known characters
            CONVERT_MAP = {
                'stat_ranged_damage': {'pct': 100, 'from': 'stat_ranged_damage', 'to': 'stat_engineering', 'from_r': 1, 'to_r': 2},
                'materials': {'pct': 50, 'from': 'materials', 'to': 'stat_max_hp', 'from_r': 13, 'to_r': 1},
            }
            cv = CONVERT_MAP.get(key, {'pct': value, 'from': key, 'to': '???', 'from_r': 1, 'to_r': 1})
            args[0] = f'{cv["pct"]}%'
            args[1] = stat_display_name(cv['from'], lang) if cv['from'] else ''
            args[2] = stat_display_name(cv['to'], lang) if cv['to'] else ''
            args[3] = str(cv['from_r'])
            args[4] = str(cv['to_r'])

        # --- Charm below HP ---
        elif tk_upper in ('EFFECT_CHARM_BELOW_HP', 'EFFECT_CHARM_BELOW_HP_NO_SCALING'):
            val2 = extra.get('value2', 25)
            args[0] = str(int(val2))
            args[1] = str(int(value))
            args[2] = str(int(val2))
            args[3] = '8'  # CHARM_DURATION

        # --- Enemy percent damage taken ---
        elif tk_upper == 'EFFECT_ENEMY_PERCENT_DAMAGE_TAKEN':
            args[0] = f'{value}%'
            args[1] = str(int(extra.get('duration_secs', 3)))
            args[2] = stat_display_name(key, lang)

        # --- Melee weapon bonus ---
        elif tk_upper == 'EFFECT_MELEE_WEAPON_BONUS':
            args[0] = fmt_val(value, add_op=True, add_pct=needs_percent(key))
            args[1] = stat_display_name(key, lang)

        # --- Weapon class bonus ---
        elif tk_upper == 'EFFECT_WEAPON_CLASS_BONUS':
            args[0] = fmt_val(value, add_op=True, add_pct=needs_percent(key))
            args[1] = stat_display_name(key, lang)
            # Convert set_id (e.g., "set_unarmed") to translation key ("WEAPON_CLASS_UNARMED")
            set_id = eff.get('set_id', '')
            if set_id:
                set_tr_key = set_id.replace('set_', 'WEAPON_CLASS_').upper()
                args[2] = tr(set_tr_key, lang) if lang == 'zh' else tr(set_tr_key, 'en')
            else:
                args[2] = '???'

        else:
            # Generic: fill extra fields into format slots > 1
            fmt_slots = sorted([int(m.group(1))
                                for m in re.finditer(r'\{(\d+)\}', fmt or '')
                                if int(m.group(1)) > 1])
            extra_fields = []
            for fn in ['value2', 'interval', 'chance', 'nb_stat_scaled',
                        'duration_secs', 'max_stacks', 'scale']:
                if fn in extra:
                    vv = extra[fn]
                    if fn == 'chance':
                        extra_fields.append(f'{int(vv)}%')
                    else:
                        extra_fields.append(
                            str(int(vv)) if isinstance(vv, float) and vv == int(vv) else str(vv))
            for i, fv in enumerate(extra_fields):
                if i < len(fmt_slots):
                    args[fmt_slots[i]] = fv
        args_built = True

    # --- Simple stat effects (no text_key) ---
    elif key in STAT_KEYS:
        args[0] = str(value)
        args[1] = stat_display_name(key, lang)
        args_built = True

    # --- Weapon class bonus (must be before KEYS_NEEDING_OPERATOR) ---
    elif key == 'EFFECT_WEAPON_CLASS_BONUS' or tk_upper == 'EFFECT_WEAPON_CLASS_BONUS':
        # Translation: "使用{2}类武器时{0}{1}"
        stat_key = eff.get('stat_displayed_name', eff.get('stat', ''))
        args[0] = fmt_val(value, add_op=True, add_pct=needs_percent(stat_key))
        args[1] = stat_display_name(stat_key, lang) if stat_key else ''
        # Convert set_id (e.g., "set_unarmed") to translation key ("WEAPON_CLASS_UNARMED")
        set_id = eff.get('set_id', '')
        if set_id:
            set_tr_key = set_id.replace('set_', 'WEAPON_CLASS_').upper()
            args[2] = tr(set_tr_key, lang) if lang == 'zh' else tr(set_tr_key, 'en')
        else:
            args[2] = '???'
        args_built = True

    # --- Keys in KEYS_NEEDING_OPERATOR that have translations (reroll_price, structure_attack_speed, etc.) ---
    elif key and key.lower() in KEYS_NEEDING_OPERATOR and fmt:
        args[0] = str(value)
        args[1] = tr(key.upper(), lang) if key else ''
        args_built = True

    # --- Tier effects (max_weapon_tier, min_weapon_tier) ---
    elif key in ('max_weapon_tier', 'min_weapon_tier') or tk_upper in ('EFFECT_MAX_WEAPON_TIER', 'EFFECT_MIN_WEAPON_TIER'):
        # Convert 0-indexed tier to Roman numerals: 0→Ⅰ, 1→Ⅱ, 2→Ⅲ, 3→Ⅳ
        ROMAN = ['Ⅰ', 'Ⅱ', 'Ⅲ', 'Ⅳ']
        tier_idx = int(value) if value < len(ROMAN) else value
        args[0] = ROMAN[tier_idx] if tier_idx < len(ROMAN) else str(value)
        args_built = True

    # --- Weapon class bonus ---
    elif key == 'EFFECT_WEAPON_CLASS_BONUS' or tk_upper == 'EFFECT_WEAPON_CLASS_BONUS':
        # Translation: "使用{2}类武器时{0}{1}"
        stat_key = eff.get('stat_displayed_name', eff.get('stat', ''))
        args[0] = fmt_val(value, add_op=True, add_pct=needs_percent(stat_key))
        args[1] = stat_display_name(stat_key, lang) if stat_key else ''
        # Convert set_id (e.g., "set_unarmed") to translation key ("WEAPON_CLASS_UNARMED")
        set_id = eff.get('set_id', '')
        if set_id:
            set_tr_key = set_id.replace('set_', 'WEAPON_CLASS_').upper()
            args[2] = tr(set_tr_key, lang) if lang == 'zh' else tr(set_tr_key, 'en')
        else:
            args[2] = '???'
        args_built = True

    # --- Convert stat effects ---
    elif tk_upper in ('EFFECT_CONVERT_STAT_TEMP_HALF_WAVE', 'EFFECT_CONVERT_STAT_END_OF_WAVE'):
        # Translation: "{0}的{1}在敌袭中途后会暂时转换为{2}（{3}{1}={4}{2}）"
        # Need: {0}=pct, {1}=from_stat, {2}=to_stat, {3}=from_ratio, {4}=to_ratio
        # The data only has key (from_stat) and value (pct or ratio)
        # Hardcoded values for known characters:
        CONVERT_MAP = {
            'character_cyborg': {'pct': 100, 'from': 'stat_ranged_damage', 'to': 'stat_engineering', 'from_r': 1, 'to_r': 2},
            'character_demon': {'pct': 50, 'from': 'materials', 'to': 'stat_max_hp', 'from_r': 13, 'to_r': 1},
        }
        # Find which character this effect belongs to (not available in effect data)
        # Use key to infer: stat_ranged_damage → cyborg, materials → demon
        if key == 'stat_ranged_damage':
            cv = CONVERT_MAP['character_cyborg']
        elif key == 'materials':
            cv = CONVERT_MAP['character_demon']
        else:
            cv = {'pct': value, 'from': key, 'to': '???', 'from_r': 1, 'to_r': 1}
        args[0] = f'{cv["pct"]}%'
        args[1] = stat_display_name(cv['from'], lang) if cv['from'] else ''
        args[2] = stat_display_name(cv['to'], lang) if cv['to'] else ''
        args[3] = str(cv['from_r'])
        args[4] = str(cv['to_r'])
        args_built = True

    # --- Guaranteed shop item ---
    elif tk_upper == 'EFFECT_GUARANTEED_SHOP_ITEM':
        # Translation: "商店通常销售一件{0}"
        # {0} = item name from key (e.g., "item_bait" → "诱饵")
        item_name = tr(key.upper(), lang) if key else ''
        args[0] = item_name
        args_built = True

    # --- Gain stat for every stat ---
    elif tk_upper == 'EFFECT_GAIN_STAT_FOR_EVERY_STAT':
        # Translation: "{0} {1} for every {2} {3} you have [{4}]"
        args[0] = fmt_val(value, add_op=True, add_pct=needs_percent(key))
        args[1] = stat_display_name(key, lang)
        args[2] = str(extra.get('nb_stat_scaled', 1))
        args[3] = tr(key.upper(), lang) if key else ''
        args[4] = '0'  # Runtime value
        args_built = True

    # --- Gain stat for duplicate items ---
    elif tk_upper == 'EFFECT_GAIN_STAT_FOR_DUPLICATE_ITEMS':
        # Translation: similar to EFFECT_GAIN_STAT_FOR_EVERY_STAT
        args[0] = fmt_val(value, add_op=True, add_pct=needs_percent(key))
        args[1] = stat_display_name(key, lang)
        args[2] = str(extra.get('nb_stat_scaled', 1))
        args[3] = tr('ITEM', lang) if lang == 'zh' else 'item'
        args[4] = '0'
        args_built = True

    # --- Charm below HP ---
    elif tk_upper in ('EFFECT_CHARM_BELOW_HP', 'EFFECT_CHARM_BELOW_HP_NO_SCALING'):
        # Translation: "击中生命值低于{0}%的敌人时，有{1}%（{2}%最大生命值）的几率使其在{3}秒内受到魅惑"
        val2 = extra.get('value2', 25)
        args[0] = str(int(val2))
        args[1] = str(int(value))
        args[2] = str(int(val2))
        args[3] = '8'  # CHARM_DURATION
        args_built = True

    # --- Enemy percent damage taken ---
    elif tk_upper == 'EFFECT_ENEMY_PERCENT_DAMAGE_TAKEN':
        # Translation: "敌人在被{2}命中时，会额外承受{0}伤害，持续{1}秒"
        args[0] = f'{value}%'
        args[1] = str(int(extra.get('duration_secs', 3)))
        args[2] = stat_display_name(key, lang)
        args_built = True

    # --- Melee weapon bonus ---
    elif tk_upper == 'EFFECT_MELEE_WEAPON_BONUS':
        # Translation: "使用近战武器时有{0}"
        # The value includes the stat bonus
        stat_key = eff.get('stat', eff.get('stat_displayed_name', 'stat_range'))
        args[0] = fmt_val(value, add_op=True, add_pct=needs_percent(stat_key))
        args[1] = stat_display_name(stat_key, lang) if stat_key else ''
        args_built = True

    # --- Starting weapon effects ---
    elif custom_key == 'starting_weapon':
        args[0] = str(value)
        displayed_key = key[:-2] if len(key) > 2 else key
        args[1] = stat_display_name(displayed_key, lang)
        args_built = True

    # --- Unique weapon bonus ---
    elif key in STAT_KEYS and (text_key == 'effect_unique_weapon_bonus'
                                or custom_key == 'unique_weapon_effects'):
        args[0] = str(value)
        args[1] = stat_display_name(key, lang)
        args_built = True

    # --- EffectWithSubEffects (modify_every_x_projectile, etc.) ---
    elif eff.get('sub_effects') and fmt and '{' in fmt:
        # Parent args: [value, tr(key)]
        args[0] = str(value)
        args[1] = tr(key.upper(), lang) if key else ''
        # Sub-effect args appended
        idx = 2
        for se in eff.get('sub_effects', []):
            se_val = se.get('value', 0)
            se_key = se.get('key', '')
            args[idx] = str(se_val)
            args[idx + 1] = tr(se_key.upper(), lang) if se_key else ''
            idx += 2
        args_built = True

    # --- Piggy bank (runtime wave number) ---
    elif tk_upper == 'EFFECT_GAIN_PCT_GOLD_START_WAVE_LIMITED':
        # Translation: "{0} of your materials at the start of waves (stops working at wave {1})"
        # {1} is a runtime value (RunData.nb_of_waves), hardcode as 20
        args[0] = f'{value}%'
        args[1] = '20'  # Default number of waves
        args_built = True

    # --- Generic with format string ---
    elif fmt and '{' in fmt:
        args[0] = str(value)
        args[1] = tr(key.upper(), lang)
        ws = eff.get('weapon_stats') or eff.get('structure_stats', {})
        if ws:
            ws_dmg = ws.get('damage', 0)
            if ws_dmg:
                args[1] = str(ws_dmg)
        if 'chance' in extra and extra['chance']:
            ch = extra['chance']
            # chance <= 1 is a decimal (0.25 = 25%), > 1 is already a percentage (50 = 50%)
            args[0] = f'{int(ch * 100)}%' if ch <= 1 else f'{int(ch)}%'
        if ws:
            ws_scaling = build_scaling_text(ws.get('scaling_stats', []), lang)
            if ws_scaling:
                args[2] = ws_scaling
        fmt_slots = sorted([int(m.group(1))
                            for m in re.finditer(r'\{(\d+)\}', fmt) if int(m.group(1)) > 1])
        extra_fields = []
        for fn in ['value2', 'interval', 'nb_stat_scaled', 'duration_secs', 'max_stacks']:
            if fn in extra:
                vv = extra[fn]
                extra_fields.append(
                    str(int(vv)) if isinstance(vv, float) and vv == int(vv) else str(vv))
        for i, fv in enumerate(extra_fields):
            slot = i + 2
            if slot in fmt_slots:
                args[slot] = fv
        args_built = True

    # ------------------------------------------------------------------
    # Step 3: Apply custom_args overrides
    # ------------------------------------------------------------------
    for ca in eff.get('custom_args', []):
        idx = ca.get('arg_index', 0)
        av = ca.get('arg_value', 0)
        af = ca.get('arg_format', 0)
        ak = ca.get('arg_key', '')
        arg_sign = ca.get('arg_sign', 3)

        while len(args) <= idx:
            args.append('')
            arg_signs.append(base_color)

        # Determine raw value
        if av == 0:    # USUAL - keep existing
            raw = args[idx]
        elif av == 1:  # VALUE
            raw = str(value)
        elif av == 2:  # KEY
            raw = tr(ak.upper() if ak else key.upper(), lang)
        elif av == 11: # ABS_VALUE
            raw = str(abs(value))
        else:
            raw = args[idx]

        # Apply format
        if af == 1 and raw and not raw.endswith('%'):
            raw = raw + '%'
        elif af == 3 and raw:
            raw = raw.lstrip('+')

        # Determine sign
        if arg_sign == 0:
            sign = 'g'
        elif arg_sign == 1:
            sign = 'r'
        elif arg_sign == 2:
            sign = ''
        elif arg_sign == 3:  # FROM_VALUE
            try:
                v = float(str(raw).lstrip('+').rstrip('%'))
                sign = 'g' if v > 0 else ('r' if v < 0 else '')
            except (ValueError, TypeError):
                sign = base_color
        elif arg_sign == 5:
            sign = 'p'
        else:
            sign = base_color

        args[idx] = raw
        arg_signs[idx] = sign

    # ------------------------------------------------------------------
    # Step 4: Build curse types and render
    # ------------------------------------------------------------------
    curse_types = _build_curse_types(eff, args, arg_signs, parent_id, is_weapon)
    
    if fmt and args_built:
        template, curse_args = _text_render_template(fmt_key, fmt, args, arg_signs, curse_types, lang)
        if template:
            return template, curse_args

    # Translation found but no args built (e.g. static text with no placeholders)
    if fmt and '{' not in fmt:
        return fmt, []

    # ------------------------------------------------------------------
    # Fallback: simple stat format (no translation found)
    # ------------------------------------------------------------------
    if key in STAT_KEYS:
        ct = curse_types[0] if len(curse_types) > 0 else None
        add_op = needs_operator(key)
        add_pct = needs_percent(key)
        
        if ct is not None:
            # Build template with {0} placeholder
            raw_val = fmt_val(value, add_op=add_op, add_pct=False)
            s_val_template = wrap_color(fmt_val('{0}', add_op=add_op if not raw_val.startswith('+') else False, add_pct=add_pct), base_color)
            s_name = stat_display_name(key, lang)
            if key == 'xp_gain':
                template = f'{s_val_template}%{s_name}' if lang == 'zh' else f'{s_val_template} XP Gain'
            else:
                template = f'{s_val_template}{s_name}' if lang == 'zh' else f'{s_val_template} {s_name}'
            # Parse the base numeric value (use abs: sign is in template)
            curse_args = [ct]
            return template, curse_args
        else:
            s_val = wrap_color(fmt_val(value, add_op=add_op, add_pct=add_pct), base_color)
            s_name = stat_display_name(key, lang)
            if key == 'xp_gain':
                template = f'{s_val}%{s_name}' if lang == 'zh' else f'{s_val} XP Gain'
            else:
                template = f'{s_val}{s_name}' if lang == 'zh' else f'{s_val} {s_name}'
            return template, []

    if custom_key == 'starting_weapon':
        ct = curse_types[0] if len(curse_types) > 0 else None
        add_op = needs_operator(key)
        add_pct = needs_percent(key)
        if ct is not None:
            s_val_template = wrap_color(fmt_val('{0}', add_op=True, add_pct=add_pct), base_color)
            displayed_key = key[:-2] if len(key) > 2 else key
            s_name = stat_display_name(displayed_key, lang)
            template = f'{s_val_template}{s_name}' if lang == 'zh' else f'{s_val_template} {s_name}'
            curse_args = [ct]
            return template, curse_args
        else:
            s_val = wrap_color(fmt_val(value, add_op=add_op, add_pct=add_pct), base_color)
            displayed_key = key[:-2] if len(key) > 2 else key
            s_name = stat_display_name(displayed_key, lang)
            template = f'{s_val}{s_name}' if lang == 'zh' else f'{s_val} {s_name}'
            return template, []

    # ------------------------------------------------------------------
    # Track unrenderable effect
    # ------------------------------------------------------------------
    UNRENDERABLE_EFFECTS.append({
        'key': key, 'text_key': text_key, 'custom_key': custom_key,
        'value': value, 'extra': extra,
    })

    # Final fallback
    ct = curse_types[0] if len(curse_types) > 0 else None
    if ct is not None:
        s_val_template = wrap_color(fmt_val('{0}', add_op=True, add_pct=False), base_color)
        s_key = tr(key.upper(), lang) if key else ''
        template = f'{s_val_template} {s_key}' if lang == 'en' else f'{s_val_template}{s_key}'
        curse_args = [{'value': float(value), 'curse': ct}]
        return template, curse_args
    else:
        s_val = wrap_color(str(value), base_color)
        s_key = tr(key.upper(), lang) if key else ''
        return f'{s_val} {s_key}' if lang == 'en' else f'{s_val}{s_key}', []

def render_effect_text_en(eff):
    template, _ = render_effect_text(eff, 'en')
    return template

def render_effect_text_zh(eff):
    template, _ = render_effect_text(eff, 'zh')
    return template

def build_effect_text_dict(eff):
    """Build the combined 'text' dict for an effect, with templates and curse args.
    
    Returns dict: {'en': template_en, 'zh': template_zh, 'args': curse_args}
    or None if neither language produces text.
    """
    parent_id = eff.pop('_parent_id', '')
    is_weapon = eff.pop('_is_weapon', False)
    
    template_en, args_en = render_effect_text(eff, 'en', parent_id, is_weapon)
    template_zh, args_zh = render_effect_text(eff, 'zh', parent_id, is_weapon)
    
    if not template_en and not template_zh:
        return None
    
    # Merge args: use whichever produced curse args (should be identical)
    curse_args = args_en if args_en else args_zh
    
    result = {
        'en': template_en,
        'zh': template_zh,
        'args': curse_args,
    }
    
    # Add cursed extra effects (only for cursed items)
    extra_effects = _build_cursed_extra_effects(eff, parent_id)
    if extra_effects:
        result['extra_effects'] = extra_effects
    
    # Put back popped keys
    eff['_parent_id'] = parent_id
    eff['_is_weapon'] = is_weapon
    
    return result

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
                        text_dict = build_effect_text_dict(eff_data)
                        # Skip [EMPTY] effects entirely
                        if not text_dict:
                            continue
                        eff_data['text'] = text_dict
                        # Also keep backward-compat fields
                        eff_data['text_en'] = text_dict['en']
                        eff_data['text_zh'] = text_dict['zh']
                        # Add stat icon prefix
                        eff_key = eff_data.get('key', '')
                        if eff_key.startswith('stat_') or eff_key in ('xp_gain', 'explosion_size', 'explosion_damage'):
                            ic_key = eff_key.replace('stat_', '', 1) if eff_key.startswith('stat_') else eff_key
                            eff_data['icon'] = ic_key
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

def get_effects(parsed, parent_id='', is_weapon=False):
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
                        # Build effect text dict with templates and curse args
                        eff_data['_parent_id'] = parent_id
                        eff_data['_is_weapon'] = is_weapon
                        text_dict = build_effect_text_dict(eff_data)
                        # Skip [EMPTY] effects entirely
                        if not text_dict:
                            continue
                        eff_data['text'] = text_dict
                        eff_data['text_en'] = text_dict['en']
                        eff_data['text_zh'] = text_dict['zh']
                        # Add stat icon prefix
                        eff_key = eff_data.get('key', '')
                        if eff_key.startswith('stat_') or eff_key in ('xp_gain', 'explosion_size', 'explosion_damage'):
                            ic_key = eff_key.replace('stat_', '', 1) if eff_key.startswith('stat_') else eff_key
                            eff_data['icon'] = ic_key
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
        
        effects = get_effects(parsed, parent_id=my_id, is_weapon=True)
        
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
    
    effects = get_effects(parsed, parent_id=my_id, is_weapon=False)
    
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
        
        effects = get_effects(parsed, parent_id=my_id, is_weapon=False)
        
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
        json.dump(data, f, ensure_ascii=False, separators=(',', ':'))
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
    
    if UNRENDERABLE_EFFECTS:
        unrenderable_path = OUTPUT_DIR / "data" / "unrenderable_effects.md"
        with open(unrenderable_path, 'w', encoding='utf-8') as f:
            f.write(f"# Unrenderable Effects ({len(UNRENDERABLE_EFFECTS)})\n\n")
            for ue in UNRENDERABLE_EFFECTS:
                f.write(f"- key=`{ue['key']}` text_key=`{ue['text_key']}` "
                        f"custom_key=`{ue['custom_key']}` value={ue['value']} "
                        f"extra={ue.get('extra', {})}\n")
        print(f"\n  Wrote {len(UNRENDERABLE_EFFECTS)} unrenderable effects to {unrenderable_path}")

if __name__ == '__main__':
    main()
