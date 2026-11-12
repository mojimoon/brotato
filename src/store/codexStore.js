import { ref, computed, watch, nextTick } from 'vue'

// ---- 数据基准地址 ----
export const BASE = import.meta.env.MODE === 'production'
  ? 'https://cdn.jsdmirror.com/gh/mojimoon/brotato@v3.6.0/public/'
  : import.meta.env.BASE_URL

// ---- 共享字符串字典 ----
// UI strings are embedded per-language inside rawData.ui (see main.py /
// build_ui_strings.py / ui_strings.json). Each per-language JSON carries only
// its own language's strings, so S automatically reflects the active language.
export const S = computed(() => rawData.value.ui || {})

// Map the browser locale to one of the supported Brotato languages.
function detectLang() {
  const nav = (navigator.language || 'en').toLowerCase()
  if (nav.startsWith('zh')) {
    if (nav.includes('tw') || nav.includes('hk') || nav.includes('mo')) return 'zh_TW'
    return 'zh'
  }
  const map = {
    'fr': 'fr', 'ja': 'ja', 'ko': 'ko', 'ru': 'ru', 'pl': 'pl',
    'es': 'es', 'pt': 'pt', 'de': 'de', 'tr': 'tr', 'it': 'it',
  }
  return map[nav.split('-')[0]] || 'en'
}

// ---- 响应式状态 ----
const lsGet = (k, d) => { try { const v = localStorage.getItem(k); return v !== null ? JSON.parse(v) : d } catch { return d } }

export const rawData = ref({ weapons: [], items: [], characters: [], translations: {}, stat_icons: {}, sets: {} })
export const mainContentRef = ref(null)
export const gridItemRefs = ref({})
export const activeTab = ref('weapons')
export const currentLang = ref(lsGet('brotato_lang', detectLang()))
export const searchText = ref('')
export const filterTier = ref(null)
export const filterType = ref(null)
export const filterItemSet = ref(null)
export const filterSpecial = ref(null)
export const filterSet = ref(null)
export const selectedItem = ref(null)
export const currentTierIndex = ref(0)
export const waveSlider = ref(0)
export const stickyTierIndex = ref(0)
export const filterTag = ref(null)
export const sortByWeapons = ref(lsGet('brotato_sortBy_weapons', 'default'))
export const sortByItems = ref(lsGet('brotato_sortBy_items', 'default'))
export const showBadges = ref(lsGet('brotato_showBadges', true))
export const isDark = ref(lsGet('brotato_isDark', true))
export const isMobile = ref(window.innerWidth < 768)
window.addEventListener('resize', () => { isMobile.value = window.innerWidth < 768 })
// 移动端：整页是列表，点击后详情在底部抽屉中打开
export const mobileDetailOpen = ref(false)
watch(isMobile, v => { if (!v) mobileDetailOpen.value = false })
export const showAttackSpeedCalc = ref(lsGet('brotato_showAtkCalc', false))
export const showPriceDetail = ref(lsGet('brotato_showPriceDetail', false))
export const attackSpeedSlider = ref(0)
export const statRangeSlider = ref(0)
export const weaponCountSlider = ref(lsGet('brotato_weaponCount', 6))
export const showFrames = ref(lsGet('brotato_showFrames', true))
export const curseEnabled = ref(false)
export const curseSlider = ref(110)
export const mecaEnabled = ref(false)
export const mecaSlider = ref(1)
// 异变复制预览（道具 / 角色页；可与诅咒同时开启：被诅咒道具的效果照样可被复制）
export const mutEnabled = ref(false)
export const mutSlider = ref(100)
export const mutActive = computed(() => mutEnabled.value && (activeTab.value === 'items' || activeTab.value === 'characters'))
// DLC2Data.get_mutation_scale() (1.2.0.2): 0.1 + 0.9 * min(|evolution| / 100, 1) ^ 0.442
export const mutScale = computed(() => 0.1 + 0.9 * Math.pow(Math.min(mutSlider.value / 100, 1), 0.442))
// 当前异变值下此效果能否被复制（需异变 >= mut_min 的效果低于阈值时不能）
export function mutCopyable(eff) {
  return mutActive.value && !eff.mut && !(eff.mut_min && mutSlider.value < eff.mut_min)
}
// DLC2Data._scale_copied_effect：c = ceil(|v|*s)，f = max(1, ceil(v*s))（爆炸几率 %），p = 显示为 value/100
function mutScaleArg(v, mode) {
  const n = parseFloat(v)
  if (!isFinite(n)) return v
  const s = mutScale.value, sg = n < 0 ? -1 : 1
  if (mode === 'f') return Math.max(1, Math.ceil(+(n * s).toFixed(3)))
  if (mode === 'p') return fmtDec(sg * Math.ceil(Math.abs(n) * 100 * s) / 100, 2)
  return sg * Math.ceil(Math.abs(n) * s)
}
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

// 诅咒 / 机械化互斥（游戏中一件物品只能是其中一种）
watch(curseEnabled, v => { if (v) mecaEnabled.value = false })
watch(mecaEnabled, v => { if (v) curseEnabled.value = false })

// 诅咒系数：滑块值 / 100
export const curseFactor = computed(() => curseEnabled.value ? curseSlider.value / 100 : 0)

// ---- 监听器：持久化与主题 ----
watch(currentLang, v => localStorage.setItem('brotato_lang', v))
watch(showBadges, v => localStorage.setItem('brotato_showBadges', JSON.stringify(v)))
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

    case 'threshold':  // e.g. curse extra armor: 2, or 3 when the modifier >= 0.5
      return cv >= curseArg.at ? curseArg.hi : curseArg.lo

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
// 列表卡片图标框：选中时用 tier 选中底色 + 同色外发光（卡片本身不再有外框）
export function iconStyle(tier, selected) {
  const c = tierColor(tier)
  return selected
    ? { borderColor: c, background: tierSelectedBg(tier), boxShadow: `0 0 10px ${c}` }
    : { borderColor: c, background: tierBgColor(tier) }
}
export function tierDisplayName(tier) { return ['T1', 'T2', 'T3', 'T4'][tier] || 'T1' }
export function tierSuffix(tier) { return ['', ' Ⅱ', ' Ⅲ', ' Ⅳ'][tier] || '' }
export function tierTagType(tier) { return ['info', '', 'warning', 'danger'][tier] || 'info' }

export function itemName(item, showWeaponTier = false) {
  if (showWeaponTier) {
    const tier = activeWeaponData.value?.tier ?? 0
    const suffix = tierSuffix(tier)
    return `${item.name}${suffix}`
  }
  return item.name
}
export function getIconSrc(p) { return p ? `${BASE}icons/${p}` : '' }

export function statTr(key) {
  const trans = rawData.value.translations || {}
  const uk = key.toUpperCase()
  return trans[uk] || key.replace('stat_', '').replace(/_/g, ' ')
}

export function setTr(key) {
  if (!key) return ''
  const trans = rawData.value.translations || {}
  return trans[key] || key.replace('WEAPON_CLASS_', '').replace(/_/g, ' ')
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
  if (!Array.isArray(bonus)) return ''
  const lang = currentLang.value
  return bonus.map(e => {
    const t = (e && e.text && e.text[lang]) || ''
    return t.replace(/\{0\}/g, String(e && e.value != null ? e.value : ''))
  }).join(' / ')
}

export function getStatIcon(statKey) {
  const map = rawData.value.stat_icons || {}
  return map[statKey] ? `${BASE}icons/${map[statKey]}` : null
}

// ---- 物品套组（1.2）----
const ITEM_SET_ABBR = { new_dawn: 'ND', paws_n_claws: 'PC', abyssal_terrors: 'DLC1', primal_dread: 'DLC2' }
const EVOLUTION_KEYS = { meca: ['MECA_ITEMS'], mutant: ['MUTANT_ITEMS'], both: ['MECA_ITEMS', 'MUTANT_ITEMS'] }
export const itemSetIds = computed(() => {
  const list = rawData.value[activeTab.value] || []
  return (rawData.value.meta?.item_sets || []).filter(id => list.some(i => i.set === id))
})
export function itemSetName(id) {
  if (!id || id === 'base') return S.value.baseGame
  return rawData.value.translations?.['ITEM_SET_' + id.toUpperCase()] || id
}
// 列表角标：DLC2 进化物品用机械 / 异变角标覆盖套组角标；本体无角标
export function itemSetBadge(item) {
  if (!item) return null
  if (item.evolution) {
    if (item.evolution == 'both') return { icons: evolutionIcons(item), cls: 'badge-set-' + item.set + ' badge-evo' }
    else return { icons: evolutionIcons(item), cls: 'badge-evo-' + item.evolution + ' badge-evo' }
  }
  if (ITEM_SET_ABBR[item.set]) return { text: ITEM_SET_ABBR[item.set], cls: 'badge-set-' + item.set }
  return null
}
// 道具「特殊」筛选：化石 / 机械道具 / 异变道具（双路线两者都算）
export const SPECIAL_FILTERS = ['fossil', 'meca', 'mutant']
export function matchesSpecial(item, f) {
  if (f === 'fossil') return !!item.fossil
  return item.evolution === f || item.evolution === 'both'
}
export function specialLabel(f) {
  if (f === 'fossil') return S.value.fossil
  return rawData.value.translations?.[f === 'meca' ? 'MECA_ITEMS' : 'MUTANT_ITEMS'] || f
}

// DLC2 进化物品角标图标：机械部件 / 异变催化果（双路线两个都显示）
export function evolutionIcons(item) {
  const icons = rawData.value.meta?.evolution_icons || {}
  const kinds = item?.evolution === 'both' ? ['mutant', 'meca'] : item?.evolution ? [item.evolution] : []
  return kinds.map(k => getIconSrc(icons[k]))
}
export function evolutionTags(item) {
  const tr = rawData.value.translations || {}
  return (EVOLUTION_KEYS[item?.evolution] || []).map(k => ({
    key: k, cls: 'badge-evo-' + (k === 'MECA_ITEMS' ? 'meca' : 'mutant'),
    label: tr[k] || k, desc: tr[k + '_DESCRIPTION'] || '',
    icon: getIconSrc(rawData.value.meta?.evolution_icons?.[k === 'MECA_ITEMS' ? 'meca' : 'mutant']),
  }))
}

export function getWeaponById(wid) { return rawData.value.weapons.find(x => x.id === wid) || null }

// ---- 标签翻译（由 build_ui_strings.py 生成，随每语言 JSON 加载到 rawData.ui.tag_translations）----
function _tagDict() {
  const ui = rawData.value.ui
  return (ui && ui.tag_translations) || {}
}

export function tagTr(tag) {
  const d = _tagDict()
  if (d[tag]) return d[tag]
  const game = rawData.value.translations?.[tag.toUpperCase()]
  if (game) return game
  return tag.replace(/_/g, ' ').replace(/\w/g, c => c.toUpperCase())
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
  mobileDetailOpen.value = false
  if (activeTab.value === 'characters') { pendingNavigate.value = true; activeTab.value = 'items'; filterTag.value = tag }
  else { filterTag.value = tag; selectedItem.value = null }
}

export function navigateToWeapon(wid) {
  const w = getWeaponById(wid)
  const familyId = w ? w.weapon_id : wid.replace(/_\d+$/, '')
  pendingNavigate.value = true; activeTab.value = 'weapons'
  clearAllFilters()
  setTimeout(() => {
    const family = weaponFamilies.value.find(f => f.id === familyId)
    if (family) selectItem(family)
    if (w) currentTierIndex.value = w.tier
  }, 100)
}

export function navigateToItem(id) {
  if (activeTab.value !== 'items') { pendingNavigate.value = true; activeTab.value = 'items' }
  clearAllFilters()
  setTimeout(() => {
    const item = (rawData.value.items || []).find(x => x.id === id)
    if (item) selectItem(item)
  }, 100)
}

// 关联内容（main.py add_related）：卡片数据 + 点击跳转
export function relatedEntries(entry, refs = entry?.related) {
  return (refs || []).map(r => {
    const data = r.kind === 'weapon' ? getWeaponById(r.id) : (rawData.value.items || []).find(x => x.id === r.id)
    return data ? { ...r, data, current: r.id === entry.id } : null
  }).filter(Boolean)
}
export function openRelated(r) {
  if (r.current) return
  if (r.kind === 'weapon') navigateToWeapon(r.id)
  else navigateToItem(r.id)
}

// =============================================================================
// 效果渲染
// =============================================================================
export function getSignColor(eff) {
  const es = eff.effect_sign ?? 3
  if (es === 0) return '#22c55e'; if (es === 1) return '#ef4444'
  if (es === 2) return ''; if (es === 5) return '#a855f7'
  if (es === 6) return 'var(--mark-meca)'; if (es === 7) return 'var(--mark-mutant)'
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
  if (eff.icon_path) return `<img src="${getIconSrc(eff.icon_path)}" class="stat-prefix-icon" />`
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
  const lang = currentLang.value
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

  const meca = mecaEnabled.value && eff.text?.meca
  if (meca && meca[lang]) return renderMecaEffectText(meca, meca[lang])

  const effectSign = eff.effect_sign ?? 3
  const origValue = eff.value
  const mutArgs = mutCopyable(eff) ? Object.fromEntries(eff.mut_args || []) : {}

  // Apply curse to placeholders
  if (curseArgs.length > 0) {
    let linkedParentVal = 0
    const parentArg = curseArgs[0]
    if (parentArg && curseEnabled.value) {
      linkedParentVal = applyCurse(parentArg, effectSign, origValue)
    } else if (parentArg) {
      linkedParentVal = Math.round(parentArg.value)
    }
    if (mutArgs[0]) linkedParentVal = mutScaleArg(linkedParentVal, mutArgs[0])

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
        if (mutArgs[i]) rawValue = mutScaleArg(rawValue, mutArgs[i])
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

  const cv = curseFactor.value
  return renderTags(text, fixed => (curseEnabled.value && cv > 0 && !fixed ? 1 + cv : 1))
}

// 机械化武器效果中的构筑物（DLC2Data._boost_evolved_structure_effect）：
// 伤害 ceil(d*(1+m))，冷却 max(2, int(cd/(1+m)))，系数 ×(1+m)，m = 0.03×机械化能量
function mecaStructureValue(kind, base, mod) {
  if (kind === 'damage') return String(Math.ceil(base * (1 + mod)))
  const cd = Math.max(MECA_MIN_COOLDOWN, Math.trunc(base / (1 + mod)))
  return kind === 'cd_frames' ? fmtDec(cd / 60, 2) : String(cd)
}

function renderMecaEffectText(meca, template) {
  const mod = MECA_DAMAGE_PER_POWER * mecaSlider.value
  let text = template.replace(/\{(m?)(\d+)\}/g, (m, lit, idx) => {
    const spec = lit ? meca.meca_lits?.[idx] : meca.meca_args?.[idx]
    if (spec) return `<span class="meca-modified">${mecaStructureValue(spec.kind, spec.base, mod)}</span>`
    const arg = lit ? null : meca.args?.[idx]
    if (!arg) return m
    return arg.decimalPlaces != null ? fmtDec(arg.value, arg.decimalPlaces) : String(Math.round(arg.value))
  })
  return renderTags(text, () => (meca.scaling ? 1 + mod : 1), meca.scaling)
}

// <scaling> 与 <icon> 标签；mult(fixed) 给出系数倍率
function renderTags(text, mult, mecaMark = false) {
  // Scaling tag: <scaling type="key" value="0.6" /> (may be inside color span)
  // fixed="1": the game doesn't boost this effect's scaling when cursed
  text = text.replace(/(?:<span[^>]*>)?\s*<scaling (fixed="1" )?type="([^"]+)" value="([^"]+)"\s*\/>\s*(?:<\/span>)?/g,
    (m, fixed, icKey, valStr) => {
      const cursedVal = parseFloat(valStr) * mult(fixed)
      const pct = Math.round(cursedVal * 100)
      const src = resolveStatIcon(icKey)
      const num = mecaMark ? `<span class="meca-modified">${pct}%</span>` : pct + '%'
      if (src) {
        return num + '<img src="' + src + '" class="stat-inline-icon" title="' + statTr('stat_' + icKey) + '" />'
      }
      return num + statTr('stat_' + icKey)
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
    if (!map[wid]) map[wid] = { id: wid, tiers: [], type: w.type, sets: w.sets, icon: w.icon, set: w.set }
    map[wid].tiers.push(w)
  }
  for (const key of Object.keys(map)) {
    map[key].tiers.sort((a, b) => a.tier - b.tier)
    const t0 = map[key].tiers[0]
    Object.assign(map[key], {
      name_key: t0.name_key, name: t0.name,
      tier: t0.tier, value: t0.value, icon: t0.icon, type: t0.type, set: t0.set, sets: t0.sets
    })
  }
  // 保留 JSON 插入顺序（后端已按 tier + 英文名排序），不按当前语言名重排
  return Object.values(map)
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
  else list = [...allCharactersRaw.value]  // JSON 已按游戏内（物品套组）顺序

  if (searchText.value) {
    const q = searchText.value.toLowerCase()
    list = list.filter(i => (i.name || '').toLowerCase().includes(q) || (i.id || '').toLowerCase().includes(q))
  }
  if (filterTier.value != null && filterTier.value !== '' && activeTab.value !== 'characters') list = list.filter(i => i.tier === filterTier.value)
  if (filterItemSet.value) list = list.filter(i => i.set === filterItemSet.value)
  if (activeTab.value === 'items' && filterSpecial.value) list = list.filter(i => matchesSpecial(i, filterSpecial.value))
  if (activeTab.value === 'weapons' && filterType.value && filterType.value !== '') list = list.filter(i => i.type === filterType.value)
  if (activeTab.value === 'weapons' && filterSet.value && filterSet.value !== '') list = list.filter(i => (i.sets || []).includes(filterSet.value))
  if ((activeTab.value === 'items' || activeTab.value === 'characters') && filterTag.value && filterTag.value !== '') {
    list = list.filter(i => (i.tags || []).includes(filterTag.value) || (i.wanted_tags || []).includes(filterTag.value))
  }

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
    // 默认（default）保留 JSON 原顺序（后端已按 tier + 英文名排序），不按当前语言重排
  } else if (activeTab.value === 'items') {
    if (sortKey === 'price') list.sort((a, b) => (a.value || 0) - (b.value || 0))
    // 默认（default）保留 JSON 原顺序
  }
  return list
})

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

// 机械化（DLC2Data._boost_evolved_weapon_stats，以基础武器属性为准）
const MECA_DAMAGE_PER_POWER = 0.03
const MECA_CRIT_DAMAGE_PER_POWER = 0.02
const MECA_MIN_COOLDOWN = 2  // WeaponService.MIN_COOLDOWN
function mecaStats(stats, power) {
  const dmgMod = MECA_DAMAGE_PER_POWER * power
  return {
    ...stats,
    damage: Math.ceil(stats.damage * (1 + dmgMod)),
    scaling_stats: (stats.scaling_stats || []).map(([k, v]) => [k, v * (1 + dmgMod)]),
    crit_damage: Math.round(stats.crit_damage * (1 + MECA_CRIT_DAMAGE_PER_POWER * power) * 10) / 10,
    lifesteal: stats.lifesteal > 0 ? Math.round(stats.lifesteal * (1 + dmgMod) * 100) / 100 : stats.lifesteal,
  }
}

// 受诅咒 / 机械化影响的武器属性
export const statsModified = computed(() => curseEnabled.value || mecaEnabled.value)
export const displayStats = computed(() => {
  const stats = activeWeaponData.value?.stats
  if (!stats) return null
  if (mecaEnabled.value) return mecaStats(stats, mecaSlider.value)
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
  const shots = reload.shots
  if (S.value.cooldownIs) segs.push({ text: S.value.cooldownIs.replace(/\{shots\}/g, shots), cls: 'calc-reload' })
  segs.push({ text: formatCooldown(reload.tooltip), cls: 'ws-val' })
  segs.push({ text: `(${S.value.tooltip})`, cls: 'calc-reload' })
  segs.push({ text: '/', cls: 'calc-reload-separator' })
  segs.push({ text: formatCooldown(reload.actual), cls: 'ws-val' })
  segs.push({ text: `(${S.value.actual})`, cls: 'calc-reload' })
  const cooldownEvery = S.value.cooldownEvery
  if (cooldownEvery) segs.push({ text: cooldownEvery.replace(/\{shots\}/g, shots), cls: 'calc-reload' })
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
  if (stats.attack_type === 0) return S.value.attackThrust || '(Thrust)'
  if (stats.attack_type === 1) return S.value.attackSweep || '(Sweep)'
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

// 1.2 动画驱动的近战武器（鞭子、连枷等）：挥击动画时长固定，不受攻速影响
export function isAnimationDriven(stats) { return Number(stats?.attack_duration) > 0 }

// 1.2 换弹冷却：攻速作用于 round(基础冷却 × 倍率)，且不低于普通冷却
// （WeaponService.init_ranged_stats 中的 big_reload）
export function getReloadFrames(stats, atkSpd, wcf) {
  const big = Math.round(Number(stats.cooldown) * Number(stats.additional_cooldown_multiplier))
  return Math.max(wcf, getWeaponCooldownFrames(big, atkSpd))
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
  const reloadWeaponCooldownFrames = getReloadFrames(stats, atkSpd, range.wcf)
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
  if (isAnimationDriven(stats)) return attackCooldown + Number(stats.attack_duration)

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
  if (isAnimationDriven(stats)) return attackCooldown + Number(stats.attack_duration)
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
    const reloadFrames = getReloadFrames(stats, atkSpd, wcf)
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
  if (isAnimationDriven(stats)) {
    // 冷却在动画播放期间暂停：一次攻击 = 动画 ceil(0.48×60)=29 帧 + ceil(随机冷却) 帧（1.2.0.1 无头逐帧实测，攻速 -50/0/100 下动画恒为 29 帧）
    const add_cd = Math.ceil(Number(stats.attack_duration) * COOLDOWN_FPS)
    const maxRand = Math.min((weaponCount * wcf) / 5.0, weaponCount * 5.0)
    return {
      wcf, add_cd,
      min: add_cd + Math.floor(Math.max(1, wcf - maxRand)) + 1,
      max: add_cd + Math.ceil(wcf + maxRand),
      avgFrames: add_cd + getAvgAttackDuration(Math.max(1, wcf - maxRand), wcf + maxRand),
    }
  }
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
    const reloadFrames = getReloadFrames(stats, atkSpd, wcf)
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
      text: (S.value.everyShotsColon || 'every {shots} shots:').replace(/\{shots\}/g, reload.shots),
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
    segs.push({ text: S.value.equiv || 'equiv', cls: 'calc-reload' })
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

export const atkSpeedMarks = computed(() => isMobile.value ? { [-100]: '-100', [0]: '0', [100]: '100', [300]: '300', [600]: '600' } : { [-100]: '-100', [0]: '0', [100]: '100', [200]: '200', [300]: '300', [400]: '400', [500]: '500', [600]: '600' })
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
  if (!showBadges.value) return false
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
// 网格点击：移动端额外打开详情抽屉（键盘 / 切换标签页的自动选择不打开）
export function openItem(item) {
  selectItem(item)
  if (isMobile.value) mobileDetailOpen.value = true
}

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
export const hasActiveFilter = computed(() => searchText.value || filterTier.value !== null || filterType.value || filterSet.value !== null || filterItemSet.value !== null || filterSpecial.value !== null || filterTag.value !== null)
export function clearAllFilters() {
  searchText.value = ''
  filterTier.value = null
  filterType.value = null
  filterSet.value = null
  filterItemSet.value = null
  filterSpecial.value = null
  filterTag.value = null
}

export function onTabChange() {
  filterType.value = null; filterSet.value = null; filterTag.value = null
  sortBy.value = 'default'; searchText.value = ''; filterTier.value = null; filterItemSet.value = null; filterSpecial.value = null
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
// 数据加载（按语言加载对应的 brotato_data.<lang>.json）
// =============================================================================
export const availableLangs = ref([])

async function loadLangData(lang) {
  const prevId = selectedItem.value?.id
  const resp = await fetch(`${BASE}data/brotato_data.${lang}.json`)
  const data = await resp.json()
  rawData.value = data
  // Re-point the currently selected entry to the same id in the new language.
  if (prevId != null) {
    nextTick(() => {
      const refind = weaponFamilies.value.find(f => f.id === prevId)
        || (rawData.value.items || []).find(x => x.id === prevId)
        || (rawData.value.characters || []).find(x => x.id === prevId)
      if (refind) selectedItem.value = refind
    })
  }
}

export async function initCodex() {
  try {
    const lr = await fetch(`${BASE}data/languages.json`)
    availableLangs.value = await lr.json()
  } catch (e) {
    availableLangs.value = []
  }
  await loadLangData(currentLang.value)
}

// Reload the per-language data file whenever the language changes.
watch(currentLang, (lang) => { loadLangData(lang) })
