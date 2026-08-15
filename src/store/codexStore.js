import { ref, computed, watch, nextTick } from 'vue'

// ---- 数据基准地址 ----
export const BASE = import.meta.env.MODE === 'production'
  ? 'https://cdn.jsdmirror.com/gh/mojimoon/brotato@v1.7.1/public/'
  : import.meta.env.BASE_URL

// ---- 共享字符串字典 ----
export const S = computed(() => isZh.value ? {
  weapons: '武器', items: '道具', characters: '角色', resources: '资源',
  search: '搜索...', all: '全部', tier: '稀有度', type: '类型',
  melee: '近战', ranged: '远战', set: '武器类别', source: '来源',
  base: '本体', baseGame: '本体', tag: '道具标签', sort: '排序',
  default: '默认', price: '价格', showPrice: '显示价格', on: '开', off: '关',
  sortDamage: '伤害', sortCrit: '暴击', sortCooldown: '冷却', sortRange: '范围',
  damage: '伤害', crit: '暴击', cooldown: '冷却', knockback: '击退',
  range: '范围', accuracy: '命中率', lifesteal: '生命窃取', piercing: '贯通',
  bounce: '反弹', projectiles: '投射物', dmg: '伤害', dps: 'DPS',
  basePrice: '基础价格', perWave: '每波', wave: '波次',
  effects: '效果', startingWeapons: '起始武器', preferredTags: '偏好标签',
  unique: '独特', limited: '限制', clickToSee: '点击左侧查看详情',
  belowNightmare: '难5', nightmare: '噩梦', basePriceShort: '价格',
  belowNightmareShort: '难5', nightmareShort: '噩梦',
  attackSpeedCalc: '攻速计算器', attackSpeed: '攻速', statRange: '范围',
  attackSpeedBreakpoints: '攻速断点',
  curse: '诅咒', clear: '清除筛选', weaponCount: '武器数量', frames: '帧数',
  tooltipCooldown: '显示冷却', actualCooldown: '实际冷却', tooltip: '显示', actual: '实际',
  rangeInfo: '玩家范围属性。实际加成减半（例如，150基础范围 + 100范围属性 → 200武器范围）'
} : {
  weapons: 'Weapons', items: 'Items', characters: 'Characters', resources: 'Resources',
  search: 'Search...', all: 'All', tier: 'Rarity', type: 'Type',
  melee: 'Melee', ranged: 'Ranged', set: 'Set', source: 'Source',
  base: 'Base', baseGame: 'Base Game', tag: 'Tag', sort: 'Sort',
  default: 'Default', price: 'Price', showPrice: 'Show Price', on: 'On', off: 'Off',
  sortDamage: 'Damage', sortCrit: 'Crit', sortCooldown: 'Cooldown', sortRange: 'Range',
  damage: 'Damage', crit: 'Crit', cooldown: 'Cooldown', knockback: 'Knockback',
  range: 'Range', accuracy: 'Accuracy', lifesteal: 'Lifesteal', piercing: 'Piercing',
  bounce: 'Bounce', projectiles: 'Projectiles', dmg: 'dmg', dps: 'DPS',
  basePrice: 'Base Price', perWave: '/wave', wave: 'Wave',
  effects: 'Effects', startingWeapons: 'Starting Weapons', preferredTags: 'Preferred Tags',
  unique: 'Unique', limited: 'Limited', clickToSee: 'Click to see details',
  belowNightmare: 'Danger 5', nightmare: 'Nightmare', basePriceShort: 'Price',
  belowNightmareShort: 'D5', nightmareShort: 'NM',
  attackSpeedCalc: 'Attack Speed Calculator', attackSpeed: 'A.Spd', statRange: 'Range',
  attackSpeedBreakpoints: 'A.Spd Breakpoints',
  curse: 'Curse', clear: 'Clear Filters', weaponCount: '#Weapon', frames: 'Frames',
  tooltipCooldown: 'Tooltip Cooldown', actualCooldown: 'Actual Cooldown', tooltip: 'Tooltip', actual: 'Actual',
  rangeInfo: 'Player range stat. Actual bonus is halved (e.g. 150 base range + 100 range stat → 200 weapon range)'
})

// ---- 响应式状态 ----
const lsGet = (k, d) => { try { const v = localStorage.getItem(k); return v !== null ? JSON.parse(v) : d } catch { return d } }

export const rawData = ref({ weapons: [], items: [], characters: [], translations: {}, stat_icons: {}, sets: {} })
export const mainContentRef = ref(null)
export const gridItemRefs = ref({})
export const activeTab = ref('weapons')
export const isZh = ref(lsGet('brotato_isZh', navigator.language.startsWith('zh')))
export const searchText = ref('')
export const filterTier = ref(null)
export const filterType = ref(null)
export const filterDlc = ref(null)
export const filterSet = ref(null)
export const selectedItem = ref(null)
export const currentTierIndex = ref(0)
export const waveSlider = ref(0)
export const stickyTierIndex = ref(0)
export const filterTag = ref(null)
export const sortByWeapons = ref(lsGet('brotato_sortBy_weapons', 'default'))
export const sortByItems = ref(lsGet('brotato_sortBy_items', 'default'))
export const showingPrice = ref(lsGet('brotato_showingPrice', true))
export const isDark = ref(lsGet('brotato_isDark', true))
export const isMobile = ref(window.innerWidth < 768)
export const showAttackSpeedCalc = ref(lsGet('brotato_showAtkCalc', false))
export const showPriceDetail = ref(lsGet('brotato_showPriceDetail', false))
export const attackSpeedSlider = ref(0)
export const statRangeSlider = ref(0)
export const weaponCountSlider = ref(lsGet('brotato_weaponCount', 1))
export const showFrames = ref(lsGet('brotato_showFrames', true))
export const curseEnabled = ref(false)
export const curseSlider = ref(110)
export const pendingNavigate = ref(false)

// 武器与道具各自保留独立排序状态，避免切换互相影响。sortBy 镜像当前 tab 的值。
export const sortBy = computed({
  get: () => activeTab.value === 'items' ? sortByItems.value : sortByWeapons.value,
  set: (v) => {
    if (activeTab.value === 'items') sortByItems.value = v
    else sortByWeapons.value = v
  }
})

// 排序按钮上显示的标签
export const currentSortLabel = computed(() => {
  switch (sortBy.value) {
    case 'price': return S.value.price
    case 'damage': return S.value.sortDamage
    case 'crit': return S.value.sortCrit
    case 'cooldown': return S.value.sortCooldown
    case 'range': return S.value.sortRange
    default: return S.value.default
  }
})

export const priceIconSrc = computed(() => `${BASE}icons/items/materials/harvesting_icon.png`)

// 诅咒系数：滑块值 / 100
export const curseFactor = computed(() => curseEnabled.value ? curseSlider.value / 100 : 0)

// ---- 监听器：持久化与主题 ----
watch(isZh, v => localStorage.setItem('brotato_isZh', JSON.stringify(v)))
watch(showingPrice, v => localStorage.setItem('brotato_showingPrice', JSON.stringify(v)))
watch(isDark, v => localStorage.setItem('brotato_isDark', JSON.stringify(v)))
watch(showAttackSpeedCalc, v => localStorage.setItem('brotato_showAtkCalc', JSON.stringify(v)))
watch(showPriceDetail, v => localStorage.setItem('brotato_showPriceDetail', JSON.stringify(v)))
watch(showFrames, v => localStorage.setItem('brotato_showFrames', JSON.stringify(v)))
watch(weaponCountSlider, v => localStorage.setItem('brotato_weaponCount', JSON.stringify(v)))

watch(isDark, (v) => {
  document.documentElement.classList.toggle('light-theme', !v)
  document.body.classList.toggle('light-theme', !v)
}, { immediate: true })

// =============================================================================
// 诅咒系统
// =============================================================================
export function applyCurse(curseArg, effectSign, originalValue) {
  // curseArg: {value, type, mult?, ceil?, curse_value?, curse_min?, curse_max?, linked_mult?, max_val?, decimalPlaces?}
  // type: default|positive|negative|random|fixed|linked|none
  const cv = curseFactor.value
  const dp = curseArg.decimalPlaces
  if (cv <= 0) return Math.round(curseArg.value)

  const type = curseArg.type || 'default'
  const absV = Math.abs(curseArg.value)
  const sign = curseArg.value < 0 ? -1 : 1
  const mult = curseArg.mult ?? 1.0
  const useCeil = curseArg.ceil ?? true
  const effMod = cv * mult

  if (dp != null) {
    const scaled = type === 'negative' ? absV / (1 + effMod) : absV * (1 + effMod)
    return sign * scaled
  }

  switch (type) {
    case 'positive':
      return sign * (useCeil ? Math.ceil(absV * (1 + effMod)) : Math.trunc(absV * (1 + effMod)))

    case 'negative': {
      if (curseArg.no_min) {
        return sign * (absV / (1 + effMod))  // raw division, no floor/max
      }
      return sign * Math.max(1, Math.floor(absV / (1 + effMod)))
    }

    case 'random':
      if (curseArg.curse_min != null && curseArg.curse_max != null) {
        return Math.round(curseArg.curse_min) + '~' + Math.round(curseArg.curse_max)
      }
      return Math.round(curseArg.curse_min ?? curseArg.value)

    case 'fixed': {
      const fv = Math.round(curseArg.curse_value ?? curseArg.value)
      return fv
    }

    case 'none':
      return Math.round(curseArg.value)

    case 'linked':
      return Math.round(curseArg.value)  // placeholder; real calc in renderEffectText

    case 'default':
    default: {
      let isPositive
      if (effectSign === 0 || effectSign === 5) isPositive = true
      else if (effectSign === 1) isPositive = false
      else if (effectSign === 3) isPositive = (originalValue ?? curseArg.value) > 0
      else return Math.round(curseArg.value)

      if (isPositive) {
        let v = sign * Math.ceil(absV * (1 + effMod))
        if (curseArg.max_val != null) v = Math.min(v, Math.round(curseArg.max_val))
        return v
      } else {
        let v = sign * Math.max(1, Math.floor(absV / (1 + effMod)))
        if (curseArg.max_val != null) v = Math.min(v, Math.round(curseArg.max_val))
        return v
      }
    }
  }
}

// =============================================================================
// Tier 配色
// =============================================================================
const TIER_COLORS = ['#aaaaaa', '#5cc4ff', '#b75cff', '#ff3d3d']
const TIER_BG_COLORS = ['rgba(170,170,170,0.15)', 'rgba(92,196,255,0.12)', 'rgba(183,92,255,0.12)', 'rgba(255,61,61,0.12)']
const TIER_SELECTED_BG = ['rgba(170,170,170,0.35)', 'rgba(92,196,255,0.30)', 'rgba(183,92,255,0.30)', 'rgba(255,61,61,0.30)']

export function tierColor(tier) { return TIER_COLORS[tier] || '#aaaaaa' }
export function tierBgColor(tier) { return TIER_BG_COLORS[tier] || 'rgba(170,170,170,0.1)' }
export function tierSelectedBg(tier) { return TIER_SELECTED_BG[tier] || TIER_SELECTED_BG[0] }
export function tierDisplayName(tier) { return ['T1', 'T2', 'T3', 'T4'][tier] || 'T1' }
export function tierSuffix(tier) { return ['', ' Ⅱ', ' Ⅲ', ' Ⅳ'][tier] || '' }
export function tierTagType(tier) { return ['info', '', 'warning', 'danger'][tier] || 'info' }

export function itemName(item, showWeaponTier = false) {
  if (showWeaponTier) {
    const tier = activeWeaponData.value?.tier ?? 0
    const suffix = tierSuffix(tier)
    return isZh.value ? `${item.name_zh}${suffix}` : `${item.name_en}${suffix}`
  }
  return isZh.value ? item.name_zh : item.name_en
}
export function getIconSrc(p) { return p ? `${BASE}icons/${p}` : '' }

export function statTr(key) {
  const trans = rawData.value.translations || {}
  const uk = key.toUpperCase()
  if (trans[uk]) return isZh.value ? (trans[uk].zh || key) : (trans[uk].en || key)
  return key.replace('stat_', '').replace(/_/g, ' ')
}

export function setTr(key) {
  if (!key) return ''
  const trans = rawData.value.translations || {}
  if (trans[key]) return isZh.value ? (trans[key].zh || key) : (trans[key].en || key)
  return key.replace('WEAPON_CLASS_', '').replace(/_/g, ' ')
}

export function getSetBonuses(key) {
  const sets = rawData.value.sets || {}
  const sd = sets[key]
  if (!sd) return []
  return sd
}

export function setBonusText(bonus) {
  if (!bonus) return ''
  if (typeof bonus === 'string') return bonus
  if (bonus.en || bonus.zh) return isZh.value ? (bonus.zh || bonus.en) : (bonus.en || bonus.zh)
  if (!Array.isArray(bonus)) return ''
  const lang = isZh.value ? 'zh' : 'en'
  return bonus.map(e => {
    const t = (e && e.text && e.text[lang]) || ''
    return t.replace(/\{0\}/g, String(e && e.value != null ? e.value : ''))
  }).join(' / ')
}

export function getStatIcon(statKey) {
  const map = rawData.value.stat_icons || {}
  return map[statKey] ? `${BASE}icons/${map[statKey]}` : null
}

export function getWeaponById(wid) { return rawData.value.weapons.find(x => x.id === wid) || null }

// ---- 标签翻译 ----
const TAG_TRANSLATIONS = {
  consumable: { en: 'Consumable', zh: '消耗品' }, economy: { en: 'Economy', zh: '经济' },
  exploration: { en: 'Exploration', zh: '探索' }, explosive: { en: 'Explosive', zh: '爆炸' },
  knockback: { en: 'Knockback', zh: '击退' }, less_enemies: { en: 'Less Enemies', zh: '减少敌人' },
  less_enemy_speed: { en: 'Less Enemy Speed', zh: '减少敌人速度' }, lock: { en: 'Lock', zh: '锁定' },
  more_enemies: { en: 'More Enemies', zh: '更多敌人' }, number_of_enemies: { en: 'Enemy Count', zh: '敌人数量' },
  pet: { en: 'Pet', zh: '宠物' }, pickup: { en: 'Pickup', zh: '拾取' },
  stand_still: { en: 'Stand Still', zh: '静止' }, stat_armor: { en: 'Armor', zh: '护甲' },
  stat_attack_speed: { en: 'Attack Speed', zh: '攻击速度' }, stat_crit_chance: { en: 'Crit Chance', zh: '暴击率' },
  stat_curse: { en: 'Curse', zh: '诅咒' }, stat_dodge: { en: 'Dodge', zh: '闪避' },
  stat_elemental_damage: { en: 'Elemental Damage', zh: '元素伤害' }, stat_engineering: { en: 'Engineering', zh: '工程学' },
  stat_harvesting: { en: 'Harvesting', zh: '收获' }, stat_hp_regeneration: { en: 'HP Regen', zh: '生命再生' },
  stat_lifesteal: { en: 'Lifesteal', zh: '生命窃取' }, stat_luck: { en: 'Luck', zh: '幸运' },
  stat_max_hp: { en: 'Max HP', zh: '最大生命' }, stat_melee_damage: { en: 'Melee Damage', zh: '近战伤害' },
  stat_percent_damage: { en: '% Damage', zh: '%伤害' }, stat_range: { en: 'Range', zh: '范围' },
  stat_ranged_damage: { en: 'Ranged Damage', zh: '远程伤害' }, stat_speed: { en: 'Speed', zh: '速度' },
  structure: { en: 'Structure (Preference)', zh: '构筑物(偏好)' }, structure_real: { en: 'Structure', zh: '构筑物' }, xp_gain: { en: 'XP Gain', zh: '经验获取' },
}

export function tagTr(tag) {
  const t = TAG_TRANSLATIONS[tag]
  if (!t) return tag.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())
  return isZh.value ? t.zh : t.en
}

const SPECIAL_TAGS = ['pet', 'structure_real']
export function specialTagClass(tag) { return SPECIAL_TAGS.includes(tag) ? 'tag-' + tag : '' }

export function isUniqueItem(item) { return item && item.max_nb === 1 }
export function isLimitedItem(item) { return item && item.max_nb > 1 }

const TAG_SORT_ORDER = { pet: 0, structure_real: 1, structure: 2 }
export function sortedItemTags(item) {
  if (!item || !item.tags) return []
  return [...item.tags].sort((a, b) => {
    const oa = TAG_SORT_ORDER[a] ?? 99
    const ob = TAG_SORT_ORDER[b] ?? 99
    if (oa !== ob) return oa - ob
    return tagTr(a).localeCompare(tagTr(b))
  })
}

// ---- Tooltip helpers ----
export function tagItems(tag) {
  return (rawData.value.items || []).filter(i => (i.tags || []).includes(tag)).map(i => itemName(i))
}
export function tagCharacters(tag) {
  return (rawData.value.characters || []).filter(c => (c.wanted_tags || []).includes(tag) || (c.tags || []).includes(tag)).map(c => itemName(c))
}
export function onTagClick(tag) {
  if (activeTab.value === 'characters') { pendingNavigate.value = true; activeTab.value = 'items'; filterTag.value = tag }
  else { filterTag.value = tag; selectedItem.value = null }
}

export function navigateToWeapon(wid) {
  const familyId = wid.replace(/_\d+$/, '')
  pendingNavigate.value = true; activeTab.value = 'weapons'
  filterType.value = null; filterSet.value = null; filterTag.value = null
  setTimeout(() => {
    const family = weaponFamilies.value.find(f => f.id === familyId)
    if (family) selectItem(family)
  }, 100)
}

// =============================================================================
// 效果渲染
// =============================================================================
export function getSignColor(eff) {
  const es = eff.effect_sign ?? 3
  if (es === 0) return '#22c55e'; if (es === 1) return '#ef4444'
  if (es === 2) return ''; if (es === 5) return '#a855f7'
  const v = eff.value ?? 0
  return v > 0 ? '#22c55e' : v < 0 ? '#ef4444' : ''
}

export function resolveStatIcon(iconKey) {
  const fullKey = 'stat_' + iconKey
  const icons = rawData.value.stat_icons || {}
  if (icons[fullKey]) return `${BASE}icons/${icons[fullKey]}`
  for (const [k, p] of Object.entries(icons)) {
    if (k.replace('stat_', '') === iconKey) return `${BASE}icons/${p}`
  }
  return null
}

export function renderEffectPrefix(eff) {
  const iconKey = eff.icon
  if (!iconKey) return '·'
  const src = resolveStatIcon(iconKey)
  if (src) {
    return `<img src="${src}" class="stat-prefix-icon" title="${statTr('stat_' + iconKey)}" />`
  }
  return '·'
}

// Format a number with up to `dp` decimals, stripping trailing zeros
// (0.65 -> "0.65", 1.0 -> "1", 12.0 -> "12") — used for decimal-aware args.
function fmtDec(v, dp) {
  const n = parseFloat(v)
  if (!isFinite(n)) return String(v)
  return parseFloat(n.toFixed(dp)).toString()
}

export function renderEffectText(eff) {
  const lang = isZh.value ? 'zh' : 'en'
  let text, curseArgs, useCurseData

  // Choose text source: cursed or normal
  const textSrc = (curseEnabled.value && eff.text?.text_cursed) ? eff.text.text_cursed : eff.text
  const special = eff.text?.special

  if (textSrc && textSrc[lang]) {
    text = textSrc[lang]
    curseArgs = textSrc.args || []
    useCurseData = true  // always allow curse when we have args
  } else if (eff.text && eff.text[lang]) {
    text = eff.text[lang]
    curseArgs = eff.text.args || []
    useCurseData = true
  } else {
    text = eff.text?.[lang] || ''
    curseArgs = []
    useCurseData = false
  }

  if (!text) return `${eff.value} ${statTr(eff.key)}`

  const effectSign = eff.effect_sign ?? 3
  const origValue = eff.value

  // Apply curse to placeholders
  if (curseArgs.length > 0) {
    let linkedParentVal = 0
    const parentArg = curseArgs[0]
    if (parentArg && curseEnabled.value) {
      linkedParentVal = applyCurse(parentArg, effectSign, origValue)
    } else if (parentArg) {
      linkedParentVal = Math.round(parentArg.value)
    }

    text = text.replace(/\{(\d+)\}/g, (m, idx) => {
      const i = parseInt(idx)
      if (i < curseArgs.length && curseArgs[i]) {
        const arg = curseArgs[i]
        if (arg.type === 'linked') {
          const val = linkedParentVal * (arg.linked_mult ?? 1)
          const dp = arg.decimalPlaces
          return dp != null ? fmtDec(val, dp) : String(Math.round(val))
        }
        let rawValue
        if (curseEnabled.value) {
          rawValue = applyCurse(arg, effectSign, origValue)
          if (arg.decimalPlaces != null) rawValue = fmtDec(rawValue, arg.decimalPlaces)
        } else {
          rawValue = arg.decimalPlaces != null ? fmtDec(arg.value, arg.decimalPlaces) : Math.round(arg.value)
        }
        return String(rawValue)
      }
      return m
    })
  }

  // Handle special cases
  if (curseEnabled.value && special) {
    if (special.special === 'modify_projectile' || special.special === 'modify_projectile_weapon') {
      let effectiveVal
      if (special.special === 'modify_projectile_weapon') {
        effectiveVal = Math.max(1, (special.base_value ?? origValue) - 1)
      } else {
        const arg = curseArgs[0]
        effectiveVal = arg ? applyCurse(arg, effectSign, origValue) : origValue
      }
      const tpl = special.base_text?.[effectiveVal]
      if (tpl) {
        text = (tpl[lang] || tpl.en || '').replace(/\{0\}/g, String(effectiveVal))
      }
    } else if (special.special === 'weapon_explode') {
      const arg = curseArgs[0]
      if (arg) {
        const cursedChance = applyCurse(arg, effectSign, origValue)
        if (cursedChance >= 100 && special.cursed_text) {
          text = special.cursed_text[lang] || special.cursed_text.en || text
          curseArgs = []
        }
      }
    }
  }

  // Scaling tag: <scaling type="key" value="0.6" /> (may be inside color span)
  text = text.replace(/(?:<span[^>]*>)?\s*<scaling type="([^"]+)" value="([^"]+)"\s*\/>\s*(?:<\/span>)?/g,
    (m, icKey, valStr) => {
      const baseVal = parseFloat(valStr)
      const cv = curseFactor.value
      const cursedVal = curseEnabled.value && cv > 0 ? baseVal * (1 + cv) : baseVal
      const pct = Math.round(cursedVal * 100)
      const src = resolveStatIcon(icKey)
      if (src) {
        return pct + '%<img src="' + src + '" class="stat-inline-icon" title="' + statTr('stat_' + icKey) + '" />'
      }
      return pct + '%' + statTr('stat_' + icKey)
    })

  // Icon replacement
  text = text.replace(/<icon>([^<]+)<\/icon>/g, (m, icKey) => {
    const src = resolveStatIcon(icKey)
    if (src) {
      const fullKey = 'stat_' + icKey
      return `<img src="${src}" class="stat-inline-icon" title="${statTr(fullKey)}" />`
    }
    return m
  })
  return text
}

// =============================================================================
// 武器分组
// =============================================================================
export const weaponFamilies = computed(() => {
  const map = {}
  for (const w of rawData.value.weapons) {
    const wid = w.weapon_id
    if (!map[wid]) map[wid] = { id: wid, tiers: [], type: w.type, sets: w.sets, icon: w.icon, dlc: w.dlc }
    map[wid].tiers.push(w)
  }
  for (const key of Object.keys(map)) {
    map[key].tiers.sort((a, b) => a.tier - b.tier)
    const t0 = map[key].tiers[0]
    Object.assign(map[key], {
      name_key: t0.name_key, name_en: t0.name_en, name_zh: t0.name_zh,
      tier: t0.tier, value: t0.value, icon: t0.icon, type: t0.type, dlc: t0.dlc, sets: t0.sets
    })
  }
  return Object.values(map).sort((a, b) => a.tier - b.tier || a.name_en.localeCompare(b.name_en))
})

export const allItemsRaw = computed(() => rawData.value.items)
export const allCharactersRaw = computed(() => rawData.value.characters)

export const availableSets = computed(() => {
  const seen = new Set(); const result = []
  for (const w of rawData.value.weapons) {
    for (const s of (w.sets || [])) {
      if (!seen.has(s)) { seen.add(s); result.push({ key: s, label: setTr(s) }) }
    }
  }
  result.sort((a, b) => a.label.localeCompare(b.label))
  return result
})

// ---- 所有唯一标签 ----
export const allTags = computed(() => {
  const tagSet = new Set()
  if (activeTab.value === 'items') {
    for (const item of rawData.value.items) { for (const t of (item.tags || [])) tagSet.add(t) }
  } else if (activeTab.value === 'characters') {
    for (const c of rawData.value.characters) { for (const t of (c.wanted_tags || [])) tagSet.add(t) }
  }
  return [...tagSet].sort((a, b) => tagTr(a).localeCompare(tagTr(b)))
})

// =============================================================================
// 展示列表（过滤 + 排序）
// =============================================================================
export const currentDisplayList = computed(() => {
  let list
  if (activeTab.value === 'weapons') list = [...weaponFamilies.value]
  else if (activeTab.value === 'items') list = [...allItemsRaw.value]
  else list = sortCharacters([...allCharactersRaw.value])

  if (searchText.value) {
    const q = searchText.value.toLowerCase()
    list = list.filter(i => (i.name_en || '').toLowerCase().includes(q) || (i.name_zh || '').includes(q) || (i.id || '').toLowerCase().includes(q))
  }
  if (filterTier.value != null && filterTier.value !== '' && activeTab.value !== 'characters') list = list.filter(i => i.tier === filterTier.value)
  if (filterDlc.value != null && filterDlc.value !== '') list = list.filter(i => i.dlc === filterDlc.value)
  if (activeTab.value === 'weapons' && filterType.value && filterType.value !== '') list = list.filter(i => i.type === filterType.value)
  if (activeTab.value === 'weapons' && filterSet.value && filterSet.value !== '') list = list.filter(i => (i.sets || []).includes(filterSet.value))
  if ((activeTab.value === 'items' || activeTab.value === 'characters') && filterTag.value && filterTag.value !== '') {
    list = list.filter(i => (i.tags || []).includes(filterTag.value) || (i.wanted_tags || []).includes(filterTag.value))
  }

  const byTierThenName = (a, b) => a.tier - b.tier || (a.name_en || '').localeCompare(b.name_en || '')
  const baseStats = (f) => (f.tiers && f.tiers.length ? f.tiers[0].stats : {})
  const sortKey = sortBy.value
  if (activeTab.value === 'weapons') {
    if (sortKey === 'price') list.sort((a, b) => (a.value - b.value))
    else if (sortKey === 'damage') list.sort((a, b) => (baseStats(a).damage - baseStats(b).damage))
    else if (sortKey === 'crit') list.sort((a, b) => {
      const sa = baseStats(a), sb = baseStats(b)
      return (sa.crit_chance - sb.crit_chance) || (sa.crit_damage - sb.crit_damage)
    })
    else if (sortKey === 'cooldown') list.sort((a, b) => weaponSortCooldown(a) - weaponSortCooldown(b))
    else if (sortKey === 'range') list.sort((a, b) => baseStats(a).max_range - baseStats(b).max_range)
    else list.sort(byTierThenName)
  } else if (activeTab.value === 'items') {
    if (sortKey === 'price') list.sort((a, b) => (a.value || 0) - (b.value || 0))
    else list.sort(byTierThenName)
  }
  return list
})

// =============================================================================
// 角色排序
// =============================================================================
const CHAR_BASE_ORDER = [
  'character_well_rounded', 'character_brawler', 'character_crazy', 'character_ranger',
  'character_mage', 'character_chunky', 'character_old', 'character_lucky',
  'character_mutant', 'character_generalist', 'character_loud', 'character_multitasker',
  'character_wildling', 'character_pacifist', 'character_gladiator', 'character_saver',
  'character_sick', 'character_farmer', 'character_ghost', 'character_speedy',
  'character_entrepreneur', 'character_engineer', 'character_explorer', 'character_doctor',
  'character_hunter', 'character_artificer', 'character_arms_dealer', 'character_streamer',
  'character_cyborg', 'character_glutton', 'character_jack', 'character_lich',
  'character_apprentice', 'character_cryptid', 'character_fisherman', 'character_golem',
  'character_king', 'character_renegade', 'character_one_arm', 'character_bull',
  'character_soldier', 'character_masochist', 'character_knight', 'character_demon',
  'character_baby', 'character_vagabond', 'character_technomage', 'character_vampire',
  'character_beast_master', 'character_wounded',
  'character_sailor', 'character_curious', 'character_builder', 'character_captain',
  'character_creature', 'character_chef', 'character_druid', 'character_dwarf',
  'character_gangster', 'character_diver', 'character_hiker', 'character_buccaneer',
  'character_ogre', 'character_romantic',
]
const CHAR_ORDER_MAP = {}
CHAR_BASE_ORDER.forEach((id, i) => { CHAR_ORDER_MAP[id] = i })
export function sortCharacters(chars) {
  return chars.sort((a, b) => (CHAR_ORDER_MAP[a.id] ?? 9999) - (CHAR_ORDER_MAP[b.id] ?? 9999))
}

// =============================================================================
// 当前武器 / 展示数据
// =============================================================================
export const activeTierWeapons = computed(() => {
  if (activeTab.value !== 'weapons' || !selectedItem.value) return []
  const f = weaponFamilies.value.find(f => f.id === selectedItem.value.id)
  return f ? f.tiers : []
})

export const activeWeaponData = computed(() => {
  if (activeTierWeapons.value.length === 0) return selectedItem.value || {}
  return activeTierWeapons.value.find(tw => tw.tier === currentTierIndex.value) || activeTierWeapons.value[0]
})

export const activeWeaponTier = computed(() => activeWeaponData.value.tier || 0)

// 受诅咒影响的武器属性
export const displayStats = computed(() => {
  const stats = activeWeaponData.value?.stats
  if (!stats) return null
  const cv = curseFactor.value
  if (cv <= 0) return stats
  return {
    ...stats,
    damage: Math.ceil(stats.damage * (1 + cv)),
    crit_damage: Math.round(stats.crit_damage * (1 + cv / 5) * 10) / 10,
    lifesteal: stats.lifesteal > 0 ? Math.round(stats.lifesteal * (1 + cv) * 100) / 100 : stats.lifesteal,
    piercing: stats.piercing > 0 ? Math.min(stats.piercing + 1, Math.ceil(stats.piercing * (1 + cv / 5))) : stats.piercing,
    bounce: stats.bounce > 0 ? Math.min(stats.bounce + 1, Math.ceil(stats.bounce * (1 + cv / 5))) : stats.bounce,
    scaling_stats: (stats.scaling_stats || []).map(([k, v]) => [k, v * (1 + cv)]),
  }
})

export const allFourTierSlots = computed(() => {
  const slots = [null, null, null, null]
  for (const tw of activeTierWeapons.value) slots[tw.tier] = tw
  return slots
})

// 带装填的武器额外冷却信息（武器面板 stat 列表）
export const addlCooldownInfo = computed(() => {
  const reload = getReloadCooldowns(activeWeaponData.value?.stats, 0)
  if (!reload) return null

  const segs = []
  segs.push({ text: isZh.value ? `每发射${reload.shots}次冷却为` : 'Cooldown is', cls: 'calc-reload' })
  segs.push({ text: formatCooldown(reload.tooltip), cls: 'ws-val' })
  segs.push({ text: `(${S.value.tooltip})`, cls: 'calc-reload' })
  segs.push({ text: '/', cls: 'calc-reload-separator' })
  segs.push({ text: formatCooldown(reload.actual), cls: 'ws-val' })
  segs.push({ text: `(${S.value.actual})`, cls: 'calc-reload' })
  if (!isZh.value) segs.push({ text: ` every ${reload.shots} shots`, cls: 'calc-reload' })
  return segs
})

// 装填武器的等效每发冷却
export function effectiveCooldown(cd, reload) {
  if (reload && reload.shots > 0) return cd + (reload.actual - cd) / reload.shots
  return cd
}

// DPS
export const dpsData = computed(() => {
  if (!displayStats.value) return null
  const stats = activeWeaponData.value?.stats
  const base = totalCooldown.value
  if (!base || base <= 0) return null
  const cd = effectiveCooldown(base, getReloadCooldowns(stats, 0))
  // 多射弹武器（双管霰弹枪 / 电击枪 / 链枪等）：DPS 与 scaling 均乘以 nb_projectiles
  const nbProj = (displayStats.value.nb_projectiles || 1) > 1 ? displayStats.value.nb_projectiles : 1
  const dmg = (displayStats.value.damage * nbProj) / cd
  const scaling = (displayStats.value.scaling_stats || []).map(([k, v]) => [k, (v * 100 * nbProj) / cd])
  return { dmg, cd, scaling }
})

// ---- 共享 computed：效果来源 ----
export const currentEffects = computed(() => {
  if (activeTab.value === 'weapons') return activeWeaponData.value?.effects
  if (activeTab.value === 'items' || activeTab.value === 'characters') return selectedItem.value?.effects
  return null
})

export const meleeAttackTypeText = computed(() => {
  const stats = activeWeaponData.value?.stats
  if (!stats || activeWeaponData.value?.type !== 'melee') return ''
  if (stats.attack_type === 0) return isZh.value ? '(突刺)' : '(Thrust)'
  if (stats.attack_type === 1) return isZh.value ? '(横扫)' : '(Sweep)'
  return ''
})

// =============================================================================
// 冷却计算
// =============================================================================
const COOLDOWN_FPS = 60
const MIN_WEAPON_COOLDOWN_FRAMES = 2
const BASE_MELEE_ATTACK_DURATION = 0.2
const DEFAULT_WEAPON_COUNT = 6

export const totalCooldown = computed(() => {
  const stats = activeWeaponData.value?.stats
  if (!stats) return 0
  return calculateCooldownWithAttackSpeed(stats, 0, 0, weaponCountSlider.value)
})

export const displayCooldown = computed(() => {
  const stats = displayStats.value
  if (!stats) return 0
  return calculateTooltipCooldown(stats, 0, 0)
})

export function formatCooldown(seconds) {
  if (seconds < 0.1) return seconds.toFixed(3) + 's'
  return seconds.toFixed(2) + 's'
}
export function formatCooldownFixed(seconds) {
  return seconds.toFixed(3) + 's'
}

export function frameRange() {
  if (!showFrames.value) return ''
  const stats = activeWeaponData.value?.stats
  if (!stats) return ''
  const atkSpd = getAttackSpeedFactor(attackSpeedSlider.value)
  const count = weaponCountSlider.value
  const range = getCooldownRange(stats, atkSpd, count, statRangeSlider.value)
  return ` (${range.min}-${range.max}f)`
}

export function getAttackSpeedFactor(attackSpeed) {
  const value = Number(attackSpeed)
  return Number.isFinite(value) ? value / 100 : 0
}

export function getBaseRecoilDuration(stats) {
  const recoilDuration = Number(stats?.recoil_duration)
  return Number.isFinite(recoilDuration) ? recoilDuration : 0.1
}

export function getWeaponCooldownFrames(baseCooldownFrames, atkSpd) {
  const base = Number(baseCooldownFrames)
  if (!Number.isFinite(base)) return MIN_WEAPON_COOLDOWN_FRAMES

  const modified = atkSpd >= 0
    ? base / (1 + atkSpd)
    : base * (1 + Math.abs(atkSpd))
  return Math.max(MIN_WEAPON_COOLDOWN_FRAMES, Math.floor(modified))
}

export function getRecoilDuration(stats, atkSpd) {
  const baseRecoil = getBaseRecoilDuration(stats)
  return atkSpd >= 0
    ? baseRecoil / (1 + atkSpd)
    : baseRecoil
}

export function getReloadCooldowns(stats, attackSpeed) {
  const shots = Number(stats?.additional_cooldown_every_x_shots)
  const multiplier = Number(stats?.additional_cooldown_multiplier)
  if (!Number.isFinite(shots) || shots <= 0 || !Number.isFinite(multiplier) || multiplier <= 0) return null

  const atkSpd = getAttackSpeedFactor(attackSpeed)
  const count = weaponCountSlider.value
  const range = activeWeaponData.value?.type === 'melee'
    ? getMeleeCooldownRange(stats, atkSpd, count, statRangeSlider.value)
    : getRangedCooldownRange(stats, atkSpd, count)
  const reloadWeaponCooldownFrames = range.wcf * multiplier
  const recoilDuration = getRecoilDuration(stats, atkSpd)
  const tooltipRecoilFrames = Math.floor(recoilDuration * COOLDOWN_FPS)
  const tooltip = reloadWeaponCooldownFrames / COOLDOWN_FPS + (tooltipRecoilFrames / COOLDOWN_FPS) * 2
  const actual = (range.add_cd + reloadWeaponCooldownFrames) / COOLDOWN_FPS
  return { shots, tooltip, actual }
}

export function getMeleeTiming(stats, atkSpd, statRange) {
  const baseRange = Number(stats?.max_range)
  const effectiveRange = Math.max(25, (Number.isFinite(baseRange) ? baseRange : 150) + (Number(statRange) || 0) / 2)
  const rangeDenominator = Math.min(
    Math.max(70, 70 * (1 + atkSpd / 3)),
    120,
  )
  const rangeFactor = Math.max(0, effectiveRange / rangeDenominator)
  const attackDuration = Math.max(0.01, BASE_MELEE_ATTACK_DURATION - atkSpd / 10) + rangeFactor * 0.15
  const backDuration = BASE_MELEE_ATTACK_DURATION / (1 + Math.max(0, atkSpd) * 3)
  return { attackDuration, backDuration }
}

export function calculateTooltipCooldown(stats, attackSpeed, statRange = 0) {
  const atkSpd = getAttackSpeedFactor(attackSpeed)
  const weaponCooldownFrames = getWeaponCooldownFrames(stats?.cooldown, atkSpd)
  const recoilDuration = getRecoilDuration(stats, atkSpd)
  const attackCooldown = weaponCooldownFrames / COOLDOWN_FPS

  if (activeWeaponData.value?.type !== 'melee') {
    return attackCooldown + recoilDuration * 2
  }

  const { attackDuration, backDuration } = getMeleeTiming(stats, atkSpd, statRange)
  return attackCooldown + recoilDuration + attackDuration / 2 + backDuration
}

export function weaponSortCooldown(family) {
  const w = family.tiers && family.tiers.length ? family.tiers[0] : null
  const stats = w ? w.stats : null
  if (!stats) return Infinity
  const atkSpd = getAttackSpeedFactor(0)
  const weaponCooldownFrames = getWeaponCooldownFrames(stats.cooldown, atkSpd)
  const recoilDuration = getRecoilDuration(stats, atkSpd)
  const attackCooldown = weaponCooldownFrames / COOLDOWN_FPS
  if (family.type !== 'melee') {
    return attackCooldown + recoilDuration * 2
  }
  const { attackDuration, backDuration } = getMeleeTiming(stats, atkSpd, 0)
  return attackCooldown + recoilDuration + attackDuration / 2 + backDuration
}

export function getTweenDuration(duration) {
  const d = Number(duration)
  if (d === 0.05) return 4
  return Math.floor(d * 60) + 2
}

export function getAvgAttackDuration(minCd, maxCd) {
  if (maxCd <= minCd) return maxCd
  const tri = (v) => (v * (v + 1)) / 2
  const ceilMin = Math.ceil(minCd)
  const floorMax = Math.floor(maxCd)
  return ((ceilMin - minCd) * ceilMin + tri(floorMax) - tri(ceilMin) + (maxCd - floorMax) * Math.ceil(maxCd)) / (maxCd - minCd)
}

export function getRangedCooldownRange(stats, atkSpd, weaponCount = DEFAULT_WEAPON_COUNT, bigReload = false) {
  const wcf = getWeaponCooldownFrames(stats.cooldown, atkSpd)
  const recoil = getRecoilDuration(stats, atkSpd)
  const add_cd = 2 * getTweenDuration(recoil) - 1
  if (bigReload) {
    const reloadFrames = wcf * (Number(stats?.additional_cooldown_multiplier) || 1)
    return { wcf, add_cd, min: add_cd + reloadFrames, max: add_cd + reloadFrames, avgFrames: add_cd + reloadFrames }
  }
  const maxRand = Math.min((weaponCount * wcf) / 5.0, weaponCount * 5.0)
  const min_cd = add_cd + Math.floor(Math.max(1, wcf - maxRand)) + 1
  const max_cd = add_cd + Math.ceil(wcf + maxRand)
  const avgFrames = add_cd + getAvgAttackDuration(Math.max(1, wcf - maxRand), wcf + maxRand)
  return { wcf, add_cd, min: min_cd, max: max_cd, avgFrames }
}

export function getMeleeCooldownRange(stats, atkSpd, weaponCount = DEFAULT_WEAPON_COUNT, statRange = 0, bigReload = false) {
  const wcf = getWeaponCooldownFrames(stats.cooldown, atkSpd)
  const recoil = getRecoilDuration(stats, atkSpd)
  const { attackDuration, backDuration } = getMeleeTiming(stats, atkSpd, statRange)
  let add_cd = getTweenDuration(recoil) + getTweenDuration(backDuration) - 1
  const tweenAtkHalf = getTweenDuration(attackDuration / 2)
  const tweenAtkQuarter = getTweenDuration(attackDuration / 4)
  if (Number(stats?.attack_type) === 0) {
    add_cd += tweenAtkHalf
  } else {
    add_cd += 2 * tweenAtkQuarter
  }
  if (bigReload) {
    const reloadFrames = wcf * (Number(stats?.additional_cooldown_multiplier) || 1)
    return { wcf, add_cd, min: add_cd + reloadFrames, max: add_cd + reloadFrames, avgFrames: add_cd + reloadFrames }
  }
  const maxRand = Math.min((weaponCount * wcf) / 5.0, weaponCount * 5.0)
  let min_cd = add_cd + Math.floor(Math.max(1, wcf - maxRand)) + 1
  let max_cd = add_cd + Math.ceil(wcf + maxRand)
  let avgFrames = add_cd + getAvgAttackDuration(Math.max(1, wcf - maxRand), wcf + maxRand)
  if (stats?.alternate_attack_type && tweenAtkHalf > 2 * tweenAtkQuarter) {
    min_cd -= 2
    avgFrames -= 1
  }
  return { wcf, add_cd, min: min_cd, max: max_cd, avgFrames }
}

export function getCooldownRange(stats, atkSpd, weaponCount, statRange = 0, bigReload = false) {
  return activeWeaponData.value?.type === 'melee'
    ? getMeleeCooldownRange(stats, atkSpd, weaponCount, statRange, bigReload)
    : getRangedCooldownRange(stats, atkSpd, weaponCount, bigReload)
}

export function calculateCooldownWithAttackSpeed(stats, attackSpeed, statRange = 0, weaponCount = DEFAULT_WEAPON_COUNT) {
  if (!stats) return 0
  const atkSpd = getAttackSpeedFactor(attackSpeed)
  return getCooldownRange(stats, atkSpd, weaponCount, statRange).avgFrames / COOLDOWN_FPS
}

export const calculatedCooldown = computed(() => {
  const stats = activeWeaponData.value?.stats
  if (!stats) return 0
  return calculateCooldownWithAttackSpeed(
    stats,
    attackSpeedSlider.value,
    statRangeSlider.value,
    weaponCountSlider.value
  )
})

export const calculatedTooltipCooldown = computed(() => {
  const stats = activeWeaponData.value?.stats
  if (!stats) return 0
  return calculateTooltipCooldown(
    stats,
    attackSpeedSlider.value,
    statRangeSlider.value,
  )
})

export const calculatedReloadCooldowns = computed(() => {
  const stats = activeWeaponData.value?.stats
  if (!stats) return null
  return getReloadCooldowns(stats, attackSpeedSlider.value)
})

// 冷却行尾部分段
export function cooldownSegments(kind) {
  const reload = calculatedReloadCooldowns.value
  const segs = []
  if (reload) {
    segs.push({ text: '/', cls: 'calc-reload-separator' })
    segs.push({
      text: isZh.value ? `每发射${reload.shots}次:` : `every ${reload.shots} shots:`,
      cls: 'calc-reload',
    })
    segs.push({
      text: formatCooldown(kind === 'tooltip' ? reload.tooltip : reload.actual),
      cls: 'calc-reload',
    })
  }
  if (kind === 'actual' && reload) {
    const equiv = effectiveCooldown(calculatedCooldown.value, reload)
    segs.push({ text: '/', cls: 'calc-reload-separator' })
    segs.push({ text: isZh.value ? '等效' : 'equiv', cls: 'calc-reload' })
    segs.push({ text: formatCooldownFixed(equiv), cls: 'calc-value' })
  }
  return segs
}

export const cooldownChangePct = computed(() => {
  const base = totalCooldown.value
  const cur = calculatedCooldown.value
  if (!base || !cur) return 0
  const effBase = effectiveCooldown(base, getReloadCooldowns(activeWeaponData.value?.stats, 0))
  const effCur = effectiveCooldown(cur, calculatedReloadCooldowns.value)
  return (effBase / effCur - 1) * 100
})

// 攻速断点
export const attackSpeedBreakpoints = computed(() => {
  const stats = activeWeaponData.value?.stats
  if (!stats || !activeWeaponData.value) return []
  if (totalCooldown.value >= 0.25) return []
  const count = weaponCountSlider.value
  const statRange = statRangeSlider.value
  const baseRel = getReloadCooldowns(stats, 0)
  const baseCd = effectiveCooldown(totalCooldown.value, baseRel)
  const bps = []
  let prevFrames = null
  for (let a = 1; a <= 67; a++) {
    const atkSpd = getAttackSpeedFactor(a)
    const range = getCooldownRange(stats, atkSpd, count, statRange)
    const frames = Math.round(range.avgFrames)
    if (frames !== prevFrames) {
      const curRel = getReloadCooldowns(stats, a)
      const curCd = effectiveCooldown(range.avgFrames / COOLDOWN_FPS, curRel)
      const dpsPct = baseCd > 0 ? (baseCd / curCd - 1) * 100 : 0
      prevFrames = frames
      if (dpsPct < 1) continue
      bps.push({ aspd: a, frames, dpsPct })
    }
  }
  return bps
})

export const atkSpeedMarks = computed(() => isMobile.value ? { [-200]: '-200', [0]: '0', [100]: '100', [300]: '300', [500]: '500' } : { [-200]: '-200', [-100]: '-100', [0]: '0', [100]: '100', [200]: '200', [300]: '300', [400]: '400', [500]: '500' })
export const rangeMarks = { [-200]: '-200', [-100]: '-100', [0]: '0', [100]: '100', [200]: '200' }
export const weaponCountMarks = { 1: '1', 2: '2', 3: '3', 4: '4', 5: '5', 6: '6' }

// =============================================================================
// 价格计算
// =============================================================================
export function getBasePrice() {
  if (activeTab.value === 'weapons') return activeWeaponData.value?.value || 0
  if (activeTab.value === 'items') return selectedItem.value?.value || 0
  return 0
}

export function getListPrice(item) {
  return item?.value || 0
}

export function shouldShowCardPrice(item) {
  if (!showingPrice.value) return false
  if (activeTab.value !== 'weapons' && activeTab.value !== 'items') return false
  return getListPrice(item) > 1
}

export function priceAtWave(wave) {
  const bp = getBasePrice()
  return Math.floor(bp + wave + (bp * wave * 0.1))
}

export function priceAtWaveNM(wave) {
  const bp = getBasePrice()
  return Math.floor(bp + wave + (bp * wave * 0.11))
}

export const computedPrice = computed(() => priceAtWave(waveSlider.value))
export const computedPriceNM = computed(() => priceAtWaveNM(waveSlider.value))
export const showPriceSection = computed(() => (activeTab.value === 'weapons' || activeTab.value === 'items') && getBasePrice() > 1)

export function getWaveIncrement() { return getBasePrice() * 0.1 + 1 }
export function getWaveIncrementNM() { return getBasePrice() * 0.11 + 1 }

export function getCurrentTier() {
  if (activeTab.value === 'weapons') return activeWeaponData.value?.tier ?? 0
  if (activeTab.value === 'items') return selectedItem.value?.tier ?? 0
  return 0
}

export function showPriceCell(wave) {
  const tier = getCurrentTier()
  if (tier >= 3 && wave < 8) return false
  if (tier >= 2 && wave < 4) return false
  return true
}

export const waveSliderMarks = computed(() => ({ 1: '1', 5: '5', 10: '10', 15: '15', 19: '19' }))

export function formatIncr(v) {
  return v.toFixed(2).replace(/\.?0+$/, '')
}

// =============================================================================
// 选择与键盘导航
// =============================================================================
export function selectItem(item) {
  selectedItem.value = item
  if (activeTab.value === 'weapons') {
    const family = weaponFamilies.value.find(f => f.id === item.id)
    const maxTier = family && family.tiers.length > 0 ? family.tiers[family.tiers.length - 1].tier : 0
    currentTierIndex.value = Math.min(stickyTierIndex.value, maxTier)
  }
  nextTick(() => {
    const el = gridItemRefs.value[item.id]
    if (el) el.scrollIntoView({ block: 'nearest', behavior: 'smooth' })
  })
}

export function getGridColumns() {
  const gridEl = mainContentRef.value?.querySelector('.grid-panel')
  if (!gridEl) return 4
  const colTemplate = getComputedStyle(gridEl).gridTemplateColumns
  return colTemplate.split(' ').length || 4
}

export function onKeyDown(e) {
  const list = currentDisplayList.value
  if (!list.length) return
  const currentIdx = selectedItem.value ? list.findIndex(i => i.id === selectedItem.value.id) : -1
  const cols = getGridColumns()
  let nextIdx = currentIdx
  switch (e.key) {
    case 'ArrowUp': nextIdx = Math.max(0, currentIdx - cols); break
    case 'ArrowDown': nextIdx = Math.min(list.length - 1, currentIdx + cols); break
    case 'ArrowLeft': if (currentIdx > 0) nextIdx = currentIdx - 1; break
    case 'ArrowRight': if (currentIdx < list.length - 1) nextIdx = currentIdx + 1; break
    default: return
  }
  if (nextIdx !== currentIdx && nextIdx >= 0 && nextIdx < list.length) {
    e.preventDefault(); selectItem(list[nextIdx])
  }
}

export function onFilterChange() { }
export const hasActiveFilter = computed(() => searchText.value || filterTier.value !== null || filterType.value || filterSet.value !== null || filterDlc.value !== null || filterTag.value !== null)
export function clearAllFilters() {
  searchText.value = ''
  filterTier.value = null
  filterType.value = null
  filterSet.value = null
  filterDlc.value = null
  filterTag.value = null
}

export function onTabChange() {
  filterType.value = null; filterSet.value = null; filterTag.value = null
  sortBy.value = 'default'; searchText.value = ''; filterTier.value = null; filterDlc.value = null
  if (!pendingNavigate.value) {
    selectedItem.value = null
    if (activeTab.value !== 'resources') {
      setTimeout(() => {
        if (currentDisplayList.value.length > 0) selectItem(currentDisplayList.value[0])
      }, 50)
    }
  }
  pendingNavigate.value = false
}

// =============================================================================
// 数据加载
// =============================================================================
export async function initCodex() {
  const resp = await fetch(BASE + 'data/brotato_data.json')
  rawData.value = await resp.json()
}
