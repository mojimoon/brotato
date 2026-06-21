<template>
  <div class="app-container">
    <!-- Header -->
    <header class="header">
      <h1 class="title">Brotato Codex</h1>
      <el-switch v-model="isZh" active-text="中文" inactive-text="EN" size="large" />
    </header>

    <!-- Tabs -->
    <el-tabs v-model="activeTab" class="main-tabs" @tab-change="onTabChange">
      <el-tab-pane name="weapons"><template #label>{{ isZh ? '武器' : 'Weapons' }}</template></el-tab-pane>
      <el-tab-pane name="items"><template #label>{{ isZh ? '道具' : 'Items' }}</template></el-tab-pane>
      <el-tab-pane name="characters"><template #label>{{ isZh ? '角色' : 'Characters' }}</template></el-tab-pane>
    </el-tabs>

    <!-- Filters -->
    <div class="filters">
      <el-input v-model="searchText" :placeholder="isZh ? '搜索...' : 'Search...'" clearable class="search-input" @input="onFilterChange">
        <template #prefix><el-icon><Search /></el-icon></template>
      </el-input>
      <el-select v-if="activeTab !== 'characters'" v-model="filterTier" :placeholder="isZh ? '稀有度' : 'Rarity'" clearable class="filter-select" popper-class="dark-dropdown" @change="onFilterChange">
        <el-option :label="tierDisplayName(0)" :value="0" />
        <el-option :label="tierDisplayName(1)" :value="1" />
        <el-option :label="tierDisplayName(2)" :value="2" />
        <el-option :label="tierDisplayName(3)" :value="3" />
      </el-select>
      <el-select v-if="activeTab === 'weapons'" v-model="filterType" :placeholder="isZh ? '类型' : 'Type'" clearable class="filter-select" popper-class="dark-dropdown" @change="onFilterChange">
        <el-option :label="isZh ? '近战' : 'Melee'" value="melee" />
        <el-option :label="isZh ? '远战' : 'Ranged'" value="ranged" />
      </el-select>
      <el-select v-if="activeTab === 'weapons'" v-model="filterSet" :placeholder="isZh ? '武器类别' : 'Set'" clearable class="filter-select" popper-class="dark-dropdown" @change="onFilterChange">
        <el-option v-for="setEntry in availableSets" :key="setEntry.key" :label="setEntry.label" :value="setEntry.key" />
      </el-select>
      <el-select v-model="filterDlc" :placeholder="isZh ? '来源' : 'Source'" clearable class="filter-select" popper-class="dark-dropdown" @change="onFilterChange">
        <el-option :label="isZh ? '本体' : 'Base Game'" :value="0" />
        <el-option label="DLC" :value="1" />
      </el-select>
      <el-select v-if="activeTab === 'items' || activeTab === 'characters'" v-model="filterTag" :placeholder="isZh ? '道具标签' : 'Tag'" clearable class="filter-select" popper-class="dark-dropdown" @change="onFilterChange">
        <el-option v-for="tag in allTags" :key="tag" :label="tagTr(tag)" :value="tag" />
      </el-select>
      <el-select v-if="activeTab === 'weapons' || activeTab === 'items'" v-model="sortBy" :placeholder="isZh ? '排序' : 'Sort'" class="sort-select" popper-class="dark-dropdown" @change="onFilterChange">
        <template #prefix><el-icon><Sort /></el-icon></template>
        <el-option :label="isZh ? '默认' : 'Default'" value="default" />
        <el-option :label="isZh ? '价格' : 'Price'" value="price" />
      </el-select>
    </div>

    <!-- Main Content -->
    <div class="main-content" tabindex="0" @keydown="onKeyDown" ref="mainContentRef">
      <!-- Left: Grid -->
      <div class="grid-panel">
        <div
          v-for="item in currentDisplayList"
          :key="item.id"
          :ref="el => { if (el) gridItemRefs[item.id] = el }"
          class="grid-item"
          :class="{ selected: selectedItem?.id === item.id }"
          :style="selectedItem?.id === item.id ? { background: tierSelectedBg(item.tier), borderColor: tierColor(item.tier) } : {}"
          @click="selectItem(item)"
        >
          <div class="item-icon" :style="{ borderColor: tierColor(item.tier), background: tierBgColor(item.tier) }">
            <img :src="getIconSrc(item.icon)" />
          </div>
          <div class="item-name-text">{{ itemName(item) }}</div>
          <div v-if="item.dlc" class="item-dlc-badge">DLC</div>
        </div>
      </div>

      <!-- Right: Detail Panel -->
      <div class="detail-panel" v-if="selectedItem">
        <!-- Weapon Detail -->
        <template v-if="activeTab === 'weapons'">
          <div class="detail-header">
            <div class="detail-icon-wrap" :style="{ borderColor: tierColor(activeWeaponTier), background: tierBgColor(activeWeaponTier) }">
              <img :src="getIconSrc(selectedItem.icon)" />
            </div>
            <div class="detail-title-wrap">
              <h2 :style="{ color: tierColor(activeWeaponTier) }">{{ itemName(selectedItem) }}</h2>
              <div class="detail-badges">
                <span class="type-badge" :class="selectedItem.type">{{ selectedItem.type === 'melee' ? (isZh ? '近战' : 'Melee') : (isZh ? '远战' : 'Ranged') }}</span>
                <span v-if="selectedItem.dlc" class="dlc-badge">DLC</span>
                <!-- Set tooltips only (no inline text) -->
                <el-tooltip v-for="(setNameKey, si) in (selectedItem.sets || [])" :key="si" placement="top" effect="dark" :hide-after="0">
                  <template #content>
                    <div class="set-tooltip-content">
                      <div class="set-tooltip-name">{{ setTr(setNameKey) }}</div>
                      <div v-for="(bonus, bi) in (getSetBonuses(setNameKey) || [])" :key="bi" class="set-tooltip-line">
                        ({{ bi + 2 }}) <span v-html="renderSetBonusHtml(bonus)"></span>
                      </div>
                    </div>
                  </template>
                  <span class="set-badge">{{ setTr(setNameKey) }}</span>
                </el-tooltip>
              </div>

            </div>
          </div>

          <!-- Tier Tabs -->
          <div class="tier-tabs" v-if="activeTierWeapons.length > 1">
            <button
              v-for="(tw, idx) in allFourTierSlots"
              :key="idx"
              class="tier-tab"
              :class="{ active: currentTierIndex === idx && tw !== null, disabled: tw === null }"
              :disabled="tw === null"
              :style="tw !== null ? { background: currentTierIndex === idx ? tierColor(idx) : tierBgColor(idx), borderColor: tierColor(idx), color: currentTierIndex === idx ? '#fff' : tierColor(idx) } : {}"
              @click="tw !== null && (currentTierIndex = idx, stickyTierIndex = idx)"
            >
              T{{ idx + 1 }}
            </button>
          </div>

          <!-- Stats -->
          <div v-if="activeWeaponData.stats" class="detail-section">
            <!-- Damage -->
            <div class="weapon-stat-row">
              <span class="ws-label">{{ isZh ? '伤害' : 'Damage' }}</span>
              <span class="ws-val">{{ activeWeaponData.stats.damage }}</span>
              <span v-if="activeWeaponData.stats.scaling_stats?.length" class="ws-scaling">
                (<template v-for="(ss, i) in activeWeaponData.stats.scaling_stats" :key="i">
                  <span v-if="i > 0">+</span><span class="ws-scaling-pct">{{ (ss[1] * 100).toFixed(0) }}%</span>
                  <img v-if="getStatIcon(ss[0])" :src="getStatIcon(ss[0])" class="stat-inline-icon" />
                  <span v-else>{{ statTr(ss[0]) }}</span>
                </template>)
              </span>
            </div>

            <!-- Crit -->
            <div class="weapon-stat-row">
              <span class="ws-label">{{ isZh ? '暴击' : 'Crit' }}</span>
              <span class="ws-val">{{ (activeWeaponData.stats.crit_chance * 100).toFixed(0) }}%</span>
              <span class="ws-val crit-dmg">x{{ activeWeaponData.stats.crit_damage }}</span>
            </div>

            <!-- Cooldown -->
            <div class="weapon-stat-row">
              <span class="ws-label">{{ isZh ? '冷却' : 'Cooldown' }}</span>
              <span class="ws-val">{{ (activeWeaponData.stats.cooldown / 60).toFixed(2) }}s</span>
            </div>

            <!-- Knockback -->
            <div v-if="activeWeaponData.stats.knockback !== 0" class="weapon-stat-row">
              <span class="ws-label">{{ isZh ? '击退' : 'Knockback' }}</span>
              <span class="ws-val">{{ activeWeaponData.stats.knockback }}</span>
            </div>

            <!-- Range (melee shows attack type) -->
            <div class="weapon-stat-row">
              <span class="ws-label">{{ isZh ? '范围' : 'Range' }}</span>
              <span class="ws-val">{{ activeWeaponData.stats.max_range }}
                <span v-if="activeWeaponData.type === 'melee'" class="ws-attack-type">{{ meleeAttackTypeText }}</span>
              </span>
            </div>

            <!-- Accuracy (hide at 100%) -->
            <div v-if="(activeWeaponData.stats.accuracy * 100) < 100" class="weapon-stat-row">
              <span class="ws-label">{{ isZh ? '命中率' : 'Accuracy' }}</span>
              <span class="ws-val">{{ (activeWeaponData.stats.accuracy * 100).toFixed(0) }}%</span>
            </div>

            <!-- Lifesteal -->
            <div v-if="activeWeaponData.stats.lifesteal > 0" class="weapon-stat-row">
              <span class="ws-label">{{ isZh ? '生命窃取' : 'Lifesteal' }}</span>
              <span class="ws-val">{{ (activeWeaponData.stats.lifesteal * 100).toFixed(0) }}%</span>
            </div>

            <!-- Piercing (ranged) -->
            <div v-if="activeWeaponData.type === 'ranged' && activeWeaponData.stats.piercing > 0" class="weapon-stat-row">
              <span class="ws-label">{{ isZh ? '贯通' : 'Piercing' }}</span>
              <span class="ws-val">{{ activeWeaponData.stats.piercing }}
                <span v-if="activeWeaponData.stats.piercing_dmg_reduction > 0" class="ws-attack-type"> (-{{ (activeWeaponData.stats.piercing_dmg_reduction * 100).toFixed(0) }}% {{ isZh ? '伤害' : 'dmg' }})</span>
              </span>
            </div>

            <!-- Bounce -->
            <div v-if="activeWeaponData.type === 'ranged' && activeWeaponData.stats.bounce > 0" class="weapon-stat-row">
              <span class="ws-label">{{ isZh ? '反弹' : 'Bounce' }}</span>
              <span class="ws-val">{{ activeWeaponData.stats.bounce }}</span>
            </div>

            <!-- Projectiles -->
            <div v-if="activeWeaponData.type === 'ranged' && activeWeaponData.stats.nb_projectiles > 1" class="weapon-stat-row">
              <span class="ws-label">{{ isZh ? '投射物' : 'Projectiles' }}</span>
              <span class="ws-val">{{ activeWeaponData.stats.nb_projectiles }}</span>
            </div>
          </div>

          <!-- Price Section -->
          <div v-if="getBasePrice() > 1" class="detail-section price-section">
            <div class="price-header">
              <span class="price-label">{{ waveSlider === 0 ? (isZh ? '基础价格' : 'Base Price') : (isZh ? '第' + waveSlider + '波价格' : 'Wave ' + waveSlider + ' Price') }}</span>
              <span class="price-value">{{ computedPrice }}</span>
              <img :src="BASE + 'icons/items/materials/harvesting_icon.png'" class="price-icon" />
            </div>
            <div class="price-waves">
              <span class="price-wave">{{ isZh ? '第1波' : 'Wave 1' }}:</span><span class="ws-val">{{ priceAtWave(1) }}</span>
              <span class="price-wave">{{ isZh ? '第4波' : 'Wave 4' }}:</span><span class="ws-val">{{ priceAtWave(4) }}</span>
              <span class="price-wave">{{ isZh ? '第8波' : 'Wave 8' }}:</span><span class="ws-val">{{ priceAtWave(8) }}</span>
              <span class="price-wave">{{ isZh ? '第19波' : 'Wave 19' }}:</span><span class="ws-val">{{ priceAtWave(19) }}</span>
            </div>
            <div class="price-slider-row">
              <span class="price-slider-label">{{ isZh ? '波次' : 'Wave' }}</span>
              <el-slider v-model="waveSlider" :min="0" :max="19" :step="1" show-input class="price-slider" />
            </div>
          </div>

          <!-- Effects (pre-rendered from JSON) -->
          <div v-if="activeWeaponData.effects?.length" class="detail-section">
            <h3 class="section-title">{{ isZh ? '效果' : 'Effects' }}</h3>
            <div class="effects-list">
              <div v-for="(eff, idx) in activeWeaponData.effects" :key="idx" class="effect-item">
                <span v-html="renderEffectPreprocessed(eff)"></span>
              </div>
            </div>
          </div>
        </template>

        <!-- Item Detail -->
        <template v-else-if="activeTab === 'items'">
          <div class="detail-header">
            <div class="detail-icon-wrap" :style="{ borderColor: tierColor(selectedItem.tier), background: tierBgColor(selectedItem.tier) }">
              <img :src="getIconSrc(selectedItem.icon)" />
            </div>
            <div class="detail-title-wrap">
              <h2 :style="{ color: tierColor(selectedItem.tier) }">{{ itemName(selectedItem) }}</h2>
              <div class="detail-badges">
                <span v-if="selectedItem.dlc" class="dlc-badge">DLC</span>
                <span v-if="isUniqueItem(selectedItem)" class="limit-badge unique">{{ isZh ? '独特' : 'Unique' }}</span>
                <span v-else-if="isLimitedItem(selectedItem)" class="limit-badge limited">{{ isZh ? '限制' : 'Limited' }}({{ selectedItem.max_nb }})</span>
                <span v-for="tag in sortedItemTags(selectedItem)" :key="tag" class="tag-badge clickable" :class="specialTagClass(tag)" @click.stop="onTagClick(tag)">
                  <el-tooltip placement="top" effect="dark" :hide-after="0">
                    <template #content>
                      <div class="tag-tooltip-content">
                        <div class="tag-tooltip-name">{{ tagTr(tag) }}</div>
                        <div v-if="tagItems(tag).length" class="tag-tooltip-line">{{ isZh ? '道具' : 'Items' }}：{{ tagItems(tag).join('、') }}</div>
                        <div v-if="tagCharacters(tag).length" class="tag-tooltip-line">{{ isZh ? '角色' : 'Characters' }}：{{ tagCharacters(tag).join('、') }}</div>
                      </div>
                    </template>
                    {{ tagTr(tag) }}
                  </el-tooltip>
                </span>
              </div>
            </div>
          </div>
          <!-- Item Price Section -->
          <div v-if="(selectedItem.value || 0) > 1" class="detail-section price-section">
            <div class="price-header">
              <span class="price-label">{{ waveSlider === 0 ? (isZh ? '基础价格' : 'Base Price') : (isZh ? '第' + waveSlider + '波价格' : 'Wave ' + waveSlider + ' Price') }}</span>
              <span class="price-value">{{ computedPrice }}</span>
              <img :src="BASE + 'icons/items/materials/harvesting_icon.png'" class="price-icon" />
            </div>
            <div class="price-waves">
              <span class="price-wave">{{ isZh ? '第1波' : 'Wave 1' }}：{{ priceAtWave(1) }}</span>
              <span class="price-wave">{{ isZh ? '第4波' : 'Wave 4' }}：{{ priceAtWave(4) }}</span>
              <span class="price-wave">{{ isZh ? '第8波' : 'Wave 8' }}：{{ priceAtWave(8) }}</span>
              <span class="price-wave">{{ isZh ? '第19波' : 'Wave 19' }}：{{ priceAtWave(19) }}</span>
            </div>
            <div class="price-slider-row">
              <span class="price-slider-label">{{ isZh ? '波次' : 'Wave' }}</span>
              <el-slider v-model="waveSlider" :min="0" :max="19" :step="1" show-input class="price-slider" />
            </div>
          </div>
          <div v-if="selectedItem.effects?.length" class="detail-section">
            <h3 class="section-title">{{ isZh ? '效果' : 'Effects' }}</h3>
            <div class="effects-list">
              <div v-for="(eff, idx) in selectedItem.effects" :key="idx" class="effect-item">
                <span v-html="renderEffectPreprocessed(eff)"></span>
              </div>
            </div>
          </div>
        </template>

        <!-- Character Detail -->
        <template v-else>
          <div class="detail-header">
            <div class="detail-icon-wrap" :style="{ borderColor: tierColor(selectedItem.tier), background: tierBgColor(selectedItem.tier) }">
              <img :src="getIconSrc(selectedItem.icon)" />
            </div>
            <div class="detail-title-wrap">
              <h2>{{ itemName(selectedItem) }}</h2>
              <div class="detail-badges">
                <span v-if="selectedItem.dlc" class="dlc-badge">DLC</span>
                <span v-for="tag in (selectedItem.tags || [])" :key="tag" class="tag-badge clickable" :class="specialTagClass(tag)" @click.stop="onTagClick(tag)">
                  <el-tooltip placement="top" effect="dark" :hide-after="0">
                    <template #content>
                      <div class="tag-tooltip-content">
                        <div class="tag-tooltip-name">{{ tagTr(tag) }}</div>
                        <div v-if="tagItems(tag).length" class="tag-tooltip-line">{{ isZh ? '道具' : 'Items' }}：{{ tagItems(tag).join('、') }}</div>
                        <div v-if="tagCharacters(tag).length" class="tag-tooltip-line">{{ isZh ? '角色' : 'Characters' }}：{{ tagCharacters(tag).join('、') }}</div>
                      </div>
                    </template>
                    {{ tagTr(tag) }}
                  </el-tooltip>
                </span>
              </div>
            </div>
          </div>
          <div v-if="selectedItem.effects?.length" class="detail-section">
            <h3 class="section-title">{{ isZh ? '效果' : 'Effects' }}</h3>
            <div class="effects-list">
              <div v-for="(eff, idx) in selectedItem.effects" :key="idx" class="effect-item">
                <span v-html="renderEffectPreprocessed(eff)"></span>
              </div>
            </div>
          </div>
          <div v-if="selectedItem.starting_weapons?.length" class="detail-section">
            <h3 class="section-title">{{ isZh ? '起始武器' : 'Starting Weapons' }}</h3>
            <div class="tags-wrap">
              <span v-for="wid in selectedItem.starting_weapons" :key="wid" class="tag-badge clickable weapon-link" @click="navigateToWeapon(wid)">{{ resolveWeaponName(wid) }}</span>
            </div>
          </div>
          <div v-if="(selectedItem.wanted_tags || []).length" class="detail-section">
            <h3 class="section-title">{{ isZh ? '偏好标签' : 'Preferred Tags' }}</h3>
            <div class="tags-wrap">
              <span v-for="tag in selectedItem.wanted_tags" :key="tag" class="tag-badge clickable" @click.stop="onTagClick(tag)">
                <el-tooltip placement="top" effect="dark" :hide-after="0">
                  <template #content>
                    <div class="tag-tooltip-content">
                      <div class="tag-tooltip-name">{{ tagTr(tag) }}</div>
                      <div v-if="tagItems(tag).length" class="tag-tooltip-line">{{ isZh ? '道具' : 'Items' }}：{{ tagItems(tag).join('、') }}</div>
                      <div v-if="tagCharacters(tag).length" class="tag-tooltip-line">{{ isZh ? '角色' : 'Characters' }}：{{ tagCharacters(tag).join('、') }}</div>
                    </div>
                  </template>
                  {{ tagTr(tag) }}
                </el-tooltip>
              </span>
            </div>
          </div>
        </template>
      </div>

      <!-- Empty -->
      <div class="detail-panel empty-panel" v-else>
        <el-empty :description="isZh ? '点击左侧查看详情' : 'Click to see details'" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick } from 'vue'
import { Search, Sort } from '@element-plus/icons-vue'

const BASE = import.meta.env.BASE_URL

const rawData = ref({ weapons: [], items: [], characters: [], translations: {}, stat_icons: {}, sets: {} })
const mainContentRef = ref(null)
const gridItemRefs = ref({})
const activeTab = ref('weapons')
const isZh = ref(true)
const searchText = ref('')
const filterTier = ref(null)
const filterType = ref(null)
const filterDlc = ref(null)
const filterSet = ref(null)
const selectedItem = ref(null)
const currentTierIndex = ref(0)
const waveSlider = ref(0)
const stickyTierIndex = ref(0) // remembered tier across selections
const filterTag = ref(null)
const sortBy = ref('default')

// ---- Tier colors ----
const TIER_COLORS = ['#aaaaaa', '#5cc4ff', '#b75cff', '#ff3d3d']
const TIER_BG_COLORS = ['rgba(170,170,170,0.15)', 'rgba(92,196,255,0.12)', 'rgba(183,92,255,0.12)', 'rgba(255,61,61,0.12)']

function tierColor(tier) { return TIER_COLORS[tier] || '#aaaaaa' }
function tierBgColor(tier) { return TIER_BG_COLORS[tier] || 'rgba(170,170,170,0.1)' }
const TIER_SELECTED_BG = ['rgba(170,170,170,0.35)', 'rgba(92,196,255,0.30)', 'rgba(183,92,255,0.30)', 'rgba(255,61,61,0.30)']
function tierSelectedBg(tier) { return TIER_SELECTED_BG[tier] || TIER_SELECTED_BG[0] }
function tierDisplayName(tier) { const labels = ['T1', 'T2', 'T3', 'T4']; return labels[tier] || 'T1' }
function tierTagType(tier) { return ['info', '', 'warning', 'danger'][tier] || 'info' }

function itemName(item) { return isZh.value ? item.name_zh : item.name_en }
function getIconSrc(p) { return p ? `${BASE}icons/${p}` : '' }

function statTr(key) {
  const trans = rawData.value.translations || {}
  const uk = key.toUpperCase()
  if (trans[uk]) return isZh.value ? (trans[uk].zh || key) : (trans[uk].en || key)
  return key.replace('stat_', '').replace(/_/g, ' ')
}

function setTr(key) {
  if (!key) return ''
  const sets = rawData.value.sets || {}
  // Check manual sets data
  if (sets[key] && sets[key]._manual) {
    return isZh.value ? sets[key].name_zh : sets[key].name_en
  }
  const trans = rawData.value.translations || {}
  if (trans[key]) return isZh.value ? (trans[key].zh || key) : (trans[key].en || key)
  return key.replace('WEAPON_CLASS_', '').replace(/_/g, ' ')
}

function getSetBonuses(setNameKey) {
  // sets data: { name_key: [[tier1_effects], [tier2_effects], ...] }
  // or _manual: { tiers: [{en, zh}, ...] }
  const sets = rawData.value.sets || {}
  const setData = sets[setNameKey]
  if (!setData) return []
  if (setData._manual) {
    // Manual format: tiers array of {en, zh}
    return setData.tiers
  }
  // Standard format: array of arrays of effects
  return setData
}

function setBonusText(bonus) {
  if (!bonus) return ''
  if (typeof bonus === 'string') return bonus
  if (bonus.en || bonus.zh) return isZh.value ? (bonus.zh || bonus.en) : (bonus.en || bonus.zh)
  if (!Array.isArray(bonus)) return ''
  return bonus.map(eff => {
    const lang = isZh.value ? 'zh' : 'en'
    return eff['text_' + lang] || eff.text_en || ''
  }).join(' / ')
}

function renderSetBonusHtml(bonus) {
  // Get the raw text first
  const rawText = setBonusText(bonus)
  if (!rawText) return ''
  
  // Process color markers from Python preprocessor
  let text = rawText
  text = text.replace(/<span class="g">/g, '<span style="color:#22c55e">')
  text = text.replace(/<span class="r">/g, '<span style="color:#ef4444">')
  text = text.replace(/<span class="p">/g, '<span style="color:#a855f7">')
  
  return text
}

function getStatIcon(statKey) {
  const map = rawData.value.stat_icons || {}
  return map[statKey] ? `${BASE}icons/${map[statKey]}` : null
}

function resolveWeaponName(wid) {
  const w = rawData.value.weapons.find(x => x.id === wid)
  return w ? itemName(w) : wid
}

// ---- Tag translations ----
const TAG_TRANSLATIONS = {
  consumable: { en: 'Consumable', zh: '消耗品' },
  economy: { en: 'Economy', zh: '经济' },
  exploration: { en: 'Exploration', zh: '探索' },
  explosive: { en: 'Explosive', zh: '爆炸' },
  knockback: { en: 'Knockback', zh: '击退' },
  less_enemies: { en: 'Less Enemies', zh: '减少敌人' },
  less_enemy_speed: { en: 'Less Enemy Speed', zh: '减少敌人速度' },
  lock: { en: 'Lock', zh: '锁定' },
  more_enemies: { en: 'More Enemies', zh: '更多敌人' },
  number_of_enemies: { en: 'Enemy Count', zh: '敌人数量' },
  pet: { en: 'Pet', zh: '宠物' },
  pickup: { en: 'Pickup', zh: '拾取' },
  stand_still: { en: 'Stand Still', zh: '静止' },
  stat_armor: { en: 'Armor', zh: '护甲' },
  stat_attack_speed: { en: 'Attack Speed', zh: '攻击速度' },
  stat_crit_chance: { en: 'Crit Chance', zh: '暴击率' },
  stat_curse: { en: 'Curse', zh: '诅咒' },
  stat_dodge: { en: 'Dodge', zh: '闪避' },
  stat_elemental_damage: { en: 'Elemental Damage', zh: '元素伤害' },
  stat_engineering: { en: 'Engineering', zh: '工程学' },
  stat_harvesting: { en: 'Harvesting', zh: '收获' },
  stat_hp_regeneration: { en: 'HP Regen', zh: '生命再生' },
  stat_lifesteal: { en: 'Lifesteal', zh: '生命窃取' },
  stat_luck: { en: 'Luck', zh: '幸运' },
  stat_max_hp: { en: 'Max HP', zh: '最大生命' },
  stat_melee_damage: { en: 'Melee Damage', zh: '近战伤害' },
  stat_percent_damage: { en: '% Damage', zh: '%伤害' },
  stat_range: { en: 'Range', zh: '范围' },
  stat_ranged_damage: { en: 'Ranged Damage', zh: '远程伤害' },
  stat_speed: { en: 'Speed', zh: '速度' },
  structure: { en: 'Structure', zh: '构筑物' },
  xp_gain: { en: 'XP Gain', zh: '经验获取' },
}

function tagTr(tag) {
  const t = TAG_TRANSLATIONS[tag]
  if (!t) return tag.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())
  return isZh.value ? t.zh : t.en
}

// Special tag types with distinct background colors
const SPECIAL_TAGS = ['pet', 'structure']
function specialTagClass(tag) {
  if (tag === 'pet') return 'tag-pet'
  if (tag === 'structure') return 'tag-structure'
  return ''
}

// Limited / Unique item helpers
function isUniqueItem(item) {
  return item && item.max_nb === 1
}
function isLimitedItem(item) {
  return item && item.max_nb > 1
}

// Sort tags: pet first, then structure, then others alphabetically
const TAG_SORT_ORDER = { pet: 0, structure: 1 }
function sortedItemTags(item) {
  if (!item || !item.tags) return []
  return [...item.tags].sort((a, b) => {
    const oa = TAG_SORT_ORDER[a] ?? 99
    const ob = TAG_SORT_ORDER[b] ?? 99
    if (oa !== ob) return oa - ob
    return tagTr(a).localeCompare(tagTr(b))
  })
}

// ---- All unique tags (for filter) ----
const allTags = computed(() => {
  const tagSet = new Set()
  if (activeTab.value === 'items') {
    for (const item of rawData.value.items) {
      for (const t of (item.tags || [])) tagSet.add(t)
    }
  } else if (activeTab.value === 'characters') {
    for (const c of rawData.value.characters) {
      for (const t of (c.wanted_tags || [])) tagSet.add(t)
      for (const t of (c.tags || [])) tagSet.add(t)
    }
  }
  return [...tagSet].sort((a, b) => tagTr(a).localeCompare(tagTr(b)))
})

// ---- Tag tooltip helpers ----
function tagItems(tag) {
  return (rawData.value.items || [])
    .filter(item => (item.tags || []).includes(tag))
    .map(item => itemName(item))
    .slice(0, 10)
}

function tagCharacters(tag) {
  return (rawData.value.characters || [])
    .filter(c => (c.wanted_tags || []).includes(tag) || (c.tags || []).includes(tag))
    .map(c => itemName(c))
    .slice(0, 10)
}

// ---- Tag click → filter ----
function onTagClick(tag) {
  if (activeTab.value === 'characters') {
    // From character page: navigate to items tab and filter by tag
    pendingNavigate.value = true
    activeTab.value = 'items'
    filterTag.value = tag
  } else {
    filterTag.value = tag
    selectedItem.value = null
  }
}

// ---- Navigate to weapon from character starting weapon ----
function navigateToWeapon(wid) {
  // wid is like "weapon_fist_1", extract family ID
  const familyId = wid.replace(/_\d+$/, '')
  pendingNavigate.value = true
  activeTab.value = 'weapons'
  filterType.value = null
  filterSet.value = null
  filterTag.value = null
  // Use nextTick to ensure tab switch completes before selecting
  setTimeout(() => {
    const family = weaponFamilies.value.find(f => f.id === familyId)
    if (family) {
      selectItem(family)
    }
  }, 100)
}

// ---- Effect rendering - uses preprocessed text from JSON ----
function getSignColor(eff) {
  const es = eff.effect_sign ?? 3
  if (es === 0) return '#22c55e'  // POSITIVE = green (even if value is negative, like Coupon -5%)
  if (es === 1) return '#ef4444'  // NEGATIVE = red
  if (es === 2) return ''         // NEUTRAL = no color (e.g. Gentle Alien +5% enemies)
  if (es === 5) return '#a855f7'  // CURSE = purple
  // FROM_VALUE (3): green for positive, red for negative
  const value = eff.value ?? 0
  if (value > 0) return '#22c55e'
  if (value < 0) return '#ef4444'
  return ''
}

function renderEffectPreprocessed(eff) {
  // Use preprocessed text from JSON
  const lang = isZh.value ? 'zh' : 'en'
  let text = eff['text_' + lang] || eff.text_en || ''
  if (!text) {
    return `${eff.value} ${statTr(eff.key)}`
  }

  // Step 1: Process color markers from Python preprocessor
  // <span class="g"> → green, <span class="r"> → red, <span class="p"> → purple
  text = text.replace(/<span class="g">/g, '<span style="color:#22c55e">')
  text = text.replace(/<span class="r">/g, '<span style="color:#ef4444">')
  text = text.replace(/<span class="p">/g, '<span style="color:#a855f7">')
  // All closing tags are the same
  text = text.replace(/<\/span>/g, '</span>')

  // Step 2: Replace <span class="ic" data-ic="ranged_damage"></span> with stat icons
  text = text.replace(/<span class="ic" data-ic="([^"]+)"><\/span>/g, (match, icKey) => {
    // icKey is like "ranged_damage", look up "stat_ranged_damage" in stat_icons
    const fullKey = 'stat_' + icKey
    const iconPath = (rawData.value.stat_icons || {})[fullKey]
    if (iconPath) {
      const iconSrc = `${BASE}icons/${iconPath}`
      const displayName = statTr(fullKey)
      return `<img src="${iconSrc}" class="stat-inline-icon" style="width:16px;height:16px;vertical-align:middle;margin:0 1px" title="${displayName}" />`
    }
    // Fallback: try matching without stat_ prefix
    for (const [key, path] of Object.entries(rawData.value.stat_icons || {})) {
      if (key.replace('stat_', '') === icKey) {
        const iconSrc = `${BASE}icons/${path}`
        const displayName = statTr(key)
        return `<img src="${iconSrc}" class="stat-inline-icon" style="width:16px;height:16px;vertical-align:middle;margin:0 1px" title="${displayName}" />`
      }
    }
    return match
  })

  // Step 3: Also handle legacy [stat名] format for backward compatibility
  text = text.replace(/\[([^\]]+)\]/g, (match, statName) => {
    for (const [key, iconPath] of Object.entries(rawData.value.stat_icons || {})) {
      const displayName = statTr(key)
      if (displayName === statName) {
        const iconSrc = `${BASE}icons/${iconPath}`
        return `<img src="${iconSrc}" class="stat-inline-icon" style="width:16px;height:16px;vertical-align:middle;margin:0 1px" title="${statName}" />`
      }
    }
    return match
  })

  return text
}

// ---- Weapon grouping ----
const weaponFamilies = computed(() => {
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

const allItemsRaw = computed(() => rawData.value.items)
const allCharactersRaw = computed(() => rawData.value.characters)

// All unique weapon sets/classes across all weapons
const availableSets = computed(() => {
  const seen = new Set()
  const result = []
  for (const w of rawData.value.weapons) {
    for (const s of (w.sets || [])) {
      if (!seen.has(s)) {
        seen.add(s)
        result.push({ key: s, label: setTr(s) })
      }
    }
  }
  result.sort((a, b) => a.label.localeCompare(b.label))
  return result
})

// ---- Display list ----
const currentDisplayList = computed(() => {
  let list
  if (activeTab.value === 'weapons') {
    list = [...weaponFamilies.value]
  } else if (activeTab.value === 'items') {
    list = [...allItemsRaw.value]
  } else {
    // Characters: use in-game order
    list = sortCharacters([...allCharactersRaw.value])
  }
  
  if (searchText.value) {
    const q = searchText.value.toLowerCase()
    list = list.filter(item => (item.name_en || '').toLowerCase().includes(q) || (item.name_zh || '').includes(q) || (item.id || '').toLowerCase().includes(q))
  }
  if (filterTier.value !== null && filterTier.value !== '' && filterTier.value !== undefined && activeTab.value !== 'characters') {
    list = list.filter(item => item.tier === filterTier.value)
  }
  if (filterDlc.value !== null && filterDlc.value !== '' && filterDlc.value !== undefined) list = list.filter(item => item.dlc === filterDlc.value)
  if (activeTab.value === 'weapons' && filterType.value && filterType.value !== '') list = list.filter(item => item.type === filterType.value)
  if (activeTab.value === 'weapons' && filterSet.value && filterSet.value !== '') list = list.filter(item => (item.sets || []).includes(filterSet.value))
  if ((activeTab.value === 'items' || activeTab.value === 'characters') && filterTag.value && filterTag.value !== '') {
    list = list.filter(item => (item.tags || []).includes(filterTag.value) || (item.wanted_tags || []).includes(filterTag.value))
  }
  
  // Sort
  if (sortBy.value === 'price' && (activeTab.value === 'weapons' || activeTab.value === 'items')) {
    list.sort((a, b) => (a.value || 0) - (b.value || 0))
  } else if (activeTab.value === 'items' && sortBy.value === 'default') {
    // Items: default sort by tier then name
    list.sort((a, b) => a.tier - b.tier || (a.name_en || '').localeCompare(b.name_en || ''))
  } else if (activeTab.value === 'weapons' && sortBy.value === 'default') {
    // Weapons: default sort by tier then name (same as weaponFamilies original order)
    list.sort((a, b) => a.tier - b.tier || (a.name_en || '').localeCompare(b.name_en || ''))
  }
  
  return list
})

// ---- Character ordering (in-game order) ----
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
]
const CHAR_DLC_ORDER = [
  'character_sailor', 'character_curious', 'character_builder', 'character_captain',
  'character_creature', 'character_chef', 'character_druid', 'character_dwarf',
  'character_gangster', 'character_diver', 'character_hiker', 'character_buccaneer',
  'character_ogre', 'character_romantic',
]
const CHAR_ORDER_MAP = {}
CHAR_BASE_ORDER.forEach((id, i) => { CHAR_ORDER_MAP[id] = i })
CHAR_DLC_ORDER.forEach((id, i) => { CHAR_ORDER_MAP[id] = i + CHAR_BASE_ORDER.length })

function sortCharacters(chars) {
  return chars.sort((a, b) => {
    const oa = CHAR_ORDER_MAP[a.id] ?? 9999
    const ob = CHAR_ORDER_MAP[b.id] ?? 9999
    return oa - ob
  })
}

// ---- Active weapon tier ----
const activeTierWeapons = computed(() => {
  if (activeTab.value !== 'weapons' || !selectedItem.value) return []
  const family = weaponFamilies.value.find(f => f.id === selectedItem.value.id)
  return family ? family.tiers : []
})

const activeWeaponData = computed(() => {
  if (activeTierWeapons.value.length === 0) return selectedItem.value || {}
  const found = activeTierWeapons.value.find(tw => tw.tier === currentTierIndex.value)
  return found || activeTierWeapons.value[0]
})

const activeWeaponTier = computed(() => activeWeaponData.value.tier || 0)

const allFourTierSlots = computed(() => {
  const slots = [null, null, null, null]
  for (const tw of activeTierWeapons.value) {
    slots[tw.tier] = tw
  }
  return slots
})

// ---- Melee attack type text ----
const meleeAttackTypeText = computed(() => {
  const stats = activeWeaponData.value?.stats
  if (!stats || activeWeaponData.value?.type !== 'melee') return ''
  // attack_type: 0 = THRUST, 1 = SWEEP
  const at = stats.attack_type
  if (at === 0) return isZh.value ? '(突刺)' : '(Thrust)'
  if (at === 1) return isZh.value ? '(横扫)' : '(Sweep)'
  return ''
})

// ---- Price calculation ----
function getBasePrice() {
  if (activeTab.value === 'weapons') return activeWeaponData.value?.value || 0
  if (activeTab.value === 'items') return selectedItem.value?.value || 0
  return 0
}

function priceAtWave(wave) {
  const bp = getBasePrice()
  /* if (wave > 20) {
    const endless_wave = Math.max(0, wave - 20)
    const endless_mult = 2.0 + Math.max(0, (wave - 35) * 0.2)
    const endless_factor = Math.max(0, ((endless_wave * (endless_wave + 1)) / 2) / 100) * endless_mult
    return Math.floor(bp * (1 + wave * 0.1 + endless_factor))
  } */
  return Math.floor(bp + wave + (bp * wave * 0.1))
}

const computedPrice = computed(() => priceAtWave(waveSlider.value))

// ---- Selection ----
function selectItem(item) {
  selectedItem.value = item
  // Remember tier: use sticky tier, but clamp to available tiers
  if (activeTab.value === 'weapons') {
    const family = weaponFamilies.value.find(f => f.id === item.id)
    const maxTier = family && family.tiers.length > 0 ? family.tiers[family.tiers.length - 1].tier : 0
    currentTierIndex.value = Math.min(stickyTierIndex.value, maxTier)
  }
  // waveSlider stays as-is (user's choice persists)
  // Scroll selected item into view
  nextTick(() => {
    const el = gridItemRefs.value[item.id]
    if (el) {
      el.scrollIntoView({ block: 'nearest', behavior: 'smooth' })
    }
  })
}

// ---- Keyboard navigation ----
function getGridColumns() {
  const gridEl = mainContentRef.value?.querySelector('.grid-panel')
  if (!gridEl) return 4
  const style = getComputedStyle(gridEl)
  const colTemplate = style.gridTemplateColumns
  // Count columns from template
  const cols = colTemplate.split(' ').length
  return cols > 0 ? cols : 4
}

function onKeyDown(e) {
  const list = currentDisplayList.value
  if (!list.length) return

  const currentIdx = selectedItem.value ? list.findIndex(item => item.id === selectedItem.value.id) : -1
  const cols = getGridColumns()
  let nextIdx = currentIdx

  switch (e.key) {
    case 'ArrowUp':
      nextIdx = Math.max(0, currentIdx - cols)
      break
    case 'ArrowDown':
      nextIdx = Math.min(list.length - 1, currentIdx + cols)
      break
    case 'ArrowLeft':
      if (currentIdx > 0) nextIdx = currentIdx - 1
      break
    case 'ArrowRight':
      if (currentIdx < list.length - 1) nextIdx = currentIdx + 1
      break
    default:
      return
  }

  if (nextIdx !== currentIdx && nextIdx >= 0 && nextIdx < list.length) {
    e.preventDefault()
    selectItem(list[nextIdx])
  }
}
function onFilterChange() { /* keep selectedItem, allow viewing item even when filtered out */ }
const pendingNavigate = ref(false) // flag: external navigation pending, skip auto-select
function onTabChange() {
  filterType.value = null; filterSet.value = null; filterTag.value = null; sortBy.value = 'default'; searchText.value = ''; filterTier.value = null; filterDlc.value = null
  if (!pendingNavigate.value) {
    selectedItem.value = null
    // Auto-select first item after DOM updates
    setTimeout(() => {
      if (currentDisplayList.value.length > 0) {
        selectItem(currentDisplayList.value[0])
      }
    }, 50)
  }
  pendingNavigate.value = false
}

// ---- Init ----
onMounted(async () => {
  const resp = await fetch(BASE + 'data/brotato_data.json')
  rawData.value = await resp.json()
})
</script>

<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { background: #121520; color: #ccc; font-family: 'Segoe UI', system-ui, sans-serif; }

.app-container { max-width: 1400px; margin: 0 auto; min-height: 100vh; display: flex; flex-direction: column; }

/* Header */
.header { display: flex; align-items: center; justify-content: space-between; padding: 10px 24px; background: #0d1117; border-bottom: 2px solid #ff3d3d; }
.title { font-size: 22px; font-weight: 800; color: #ff3d3d; letter-spacing: 2px; }

/* Tabs */
.main-tabs { background: #0d1117; padding: 0 24px; }
.main-tabs :deep(.el-tabs__header) { margin: 0; }
.main-tabs :deep(.el-tabs__item) { color: #bbb !important; height: 40px; line-height: 40px; font-size: 14px; }
.main-tabs :deep(.el-tabs__item.is-active) { color: #ff3d3d !important; }
.main-tabs :deep(.el-tabs__active-bar) { background: #ff3d3d; }

/* Filters */
.filters { display: flex; gap: 10px; padding: 8px 24px; background: #121520; border-bottom: 1px solid #222; flex-wrap: wrap; align-items: center; }
.search-input { flex: 1; max-width: 280px; }
.filter-select { width: 130px; }
.sort-select { width: 120px; }
/* Sort select visual distinction */
.sort-select :deep(.el-input__wrapper) {
  border: 1px dashed #555 !important;
  background-color: #1e2130 !important;
}
.sort-select :deep(.el-input__wrapper:hover) {
  border-color: #888 !important;
}
.sort-select :deep(.el-input__inner) {
  color: #aabbcc !important;
}
.sort-select :deep(.el-input__prefix) {
  color: #aabbcc !important;
}

/* Main */
.main-content { position: relative; height: calc(100vh - 158px); overflow: hidden; }

/* Grid - left panel, independent scroll */
.grid-panel {
  position: absolute; left: 0; top: 0; bottom: 0; width: 50%; overflow-y: auto; padding: 10px;
  display: grid; grid-template-columns: repeat(auto-fill, minmax(90px, 1fr));
  gap: 5px; align-content: start; background: #121520;
}
.grid-item {
  background: #1a1d28; border-radius: 6px; padding: 8px 4px; cursor: pointer;
  transition: all .15s; display: flex; flex-direction: column; align-items: center; gap: 3px; position: relative;
  border: 2px solid transparent;
}
.grid-item:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(255,255,255,.12); }
.grid-item.selected { box-shadow: 0 0 12px rgba(255,255,255,0.12); }
.item-icon {
  width: 52px; height: 52px; display: flex; align-items: center; justify-content: center;
  background: #14171f; border-radius: 6px; overflow: hidden; border: 2px solid #333;
}
.item-icon img { max-width: 44px; max-height: 44px; image-rendering: pixelated; }
.item-name-text { font-size: 12px; font-weight: 600; text-align: center; max-width: 80px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.item-dlc-badge { position: absolute; top: 3px; right: 3px; font-size: 8px; padding: 1px 3px; border-radius: 3px; background: #a855f7; color: #fff; font-weight: bold; }

/* Detail Panel - right panel, independent scroll */
.detail-panel {
  position: absolute; right: 0; top: 0; bottom: 0; left: 50%; overflow-y: auto; padding: 20px;
  background: #0f131a; border-left: 2px solid #222;
}
.empty-panel { display: flex; align-items: center; justify-content: center; }

.detail-header { display: flex; gap: 14px; align-items: center; margin-bottom: 12px; padding-bottom: 12px; border-bottom: 1px solid #222; }
.detail-icon-wrap {
  width: 68px; height: 68px; border-radius: 10px; display: flex; align-items: center; justify-content: center;
  background: #14171f; border: 2px solid #333; overflow: hidden; flex-shrink: 0;
}
.detail-icon-wrap img { max-width: 56px; max-height: 56px; image-rendering: pixelated; }
.detail-title-wrap { flex: 1; min-width: 0; }
.detail-title-wrap h2 { font-size: 20px; margin-bottom: 4px; }
.detail-badges { display: flex; gap: 6px; flex-wrap: wrap; align-items: center; margin-bottom: 2px; }
.type-badge { font-size: 11px; padding: 3px 8px; border-radius: 3px; color: #fff; line-height: 1.4; font-weight: 600; }
.type-badge.melee { background: #c0392b; }
.type-badge.ranged { background: #2980b9; }
.dlc-badge { font-size: 11px; padding: 3px 8px; border-radius: 3px; background: #a855f7; color: #fff; font-weight: 600; }
.dlc-tag { --el-tag-bg-color: #a855f7; --el-tag-border-color: #a855f7; --el-tag-text-color: #fff; }
.set-badge { font-size: 11px; padding: 3px 8px; border-radius: 3px; background: #3a3a50; color: #ccc; cursor: help; font-weight: 600; }
.detail-price { font-size: 14px; color: #eae2b0; margin-top: 4px; }

/* Tier Tabs */
.tier-tabs { display: flex; gap: 4px; margin-bottom: 12px; }
.tier-tab {
  flex: 1; padding: 7px 0; border: 2px solid #444; background: #1a1d28; color: #666;
  border-radius: 4px; cursor: pointer; font-size: 13px; font-weight: 700; transition: all .15s;
}
.tier-tab:hover:not(.disabled) { color: #fff; }
.tier-tab.active { color: #fff !important; }
.tier-tab.disabled { opacity: 0.3; cursor: default; border-color: #2a2a3a !important; background: #1a1d28 !important; color: #444 !important; }

/* Set tooltip */
.set-tooltip-content { font-size: 12px; line-height: 1.6; }
.set-tooltip-name { font-weight: bold; margin-bottom: 4px; color: #fff; }
.set-tooltip-line { color: #ccc; }

/* Weapon Stat Rows */
.detail-section { margin-top: 8px; }
.section-title { font-size: 12px; color: #ff3d3d; margin-bottom: 6px; text-transform: uppercase; letter-spacing: 1px; }
.weapon-stat-row {
  display: flex; align-items: center; gap: 8px; padding: 6px 10px;
  background: #14171f; border-radius: 5px; margin-bottom: 3px;
}
.ws-label { font-size: 14px; color: #bbb; min-width: 70px; }
.ws-val { font-size: 15px; color: #eee; font-weight: 600; }
.crit-dmg { color: #f39c12; font-size: 14px; margin-left: 0; }
.ws-scaling { font-size: 15px; color: #eae2b0; }
.ws-scaling-pct { color: #ddd; }
.ws-attack-type { font-size: 13px; color: #bbb; font-weight: 400; margin-left: 4px; }
.stat-inline-icon { width: 16px; height: 16px; vertical-align: middle; image-rendering: pixelated; margin: 0 1px; }

/* Price Section */
.price-section {
  margin-top: 12px;
  padding: 12px 14px;
  background: #1a1d28;
  border-radius: 8px;
  border: 1px solid #2a2a3a;
}
.price-header {
  display: flex; align-items: center; gap: 10px; margin-bottom: 8px;
}
.price-label { font-size: 13px; color: #bbb; }
.price-value {
  font-size: 16px; font-weight: 800; color: #fff;
  /* text-shadow: 0 0 8px rgba(255,255,255,0.15); */
}
.price-icon { width: 24px; height: 24px; image-rendering: pixelated; }
.price-waves {
  display: flex; gap: 8px; margin-bottom: 8px; flex-wrap: wrap;
}
.price-wave { font-size: 14px; color: #bbb; }
.price-slider-row {
  display: flex; align-items: center; gap: 10px;
}
.price-slider-label { font-size: 13px; color: #bbb; min-width: 36px; }
.price-slider { flex: 1; }
.price-slider :deep(.el-slider__input) { width: 48px; }
.price-slider :deep(.el-slider__runway) { background: #2a2a3a; }
.price-slider :deep(.el-slider__bar) { background: #ff3d3d; }
.price-slider :deep(.el-slider__button) { border-color: #ff3d3d; }

/* Effects */
.effects-list { display: flex; flex-direction: column; gap: 3px; }
.effect-item {
  padding: 5px 10px; border-radius: 4px; font-size: 13px; background: #14171f; color: #ddd; line-height: 1.5;
}

/* Tags */
.tags-wrap { display: flex; flex-wrap: wrap; gap: 5px; }
.tag-badge {
  font-size: 11px; padding: 3px 8px; border-radius: 3px; background: #2a2a40; color: #bbb;
  font-weight: 600; line-height: 1.4; display: inline-block;
}
.tag-badge.clickable { cursor: pointer; transition: all .15s; }
.tag-badge.clickable:hover { background: #3a3a55; color: #fff; }
.weapon-link { background: #2d2d1f; color: #eae2b0; }
.weapon-link:hover { background: #4a4a2f; color: #fff; }

/* Limited / Unique badge */
.limit-badge {
  font-size: 11px; padding: 3px 8px; border-radius: 3px; color: #fff; font-weight: 600; line-height: 1.4;
}
.limit-badge.unique { background: #c0392b; }
.limit-badge.limited { background: #d35400; }

/* Special tag backgrounds */
.tag-pet { background: #2d4a2d; color: #7dff7d; }
.tag-pet:hover { background: #3d6a3d !important; color: #a0ffa0 !important; }
.tag-structure { background: #4a3520; color: #ffb74d; }
.tag-structure:hover { background: #6a4a30 !important; color: #ffcc80 !important; }

/* Tag tooltip */
.tag-tooltip-content { font-size: 12px; line-height: 1.6; max-width: 320px; }
.tag-tooltip-name { font-weight: bold; margin-bottom: 2px; color: #fff; }
.tag-tooltip-line { color: #aaa; word-break: break-all; }

/* Element Plus Dark Mode Overrides */

/* ---- Input fields (search, select trigger) ---- */
.el-input__wrapper {
  background-color: #1a1d28 !important;
  border-color: #333 !important;
  box-shadow: none !important;
}
.el-input__wrapper:hover { border-color: #555 !important; }
.el-input.is-focus .el-input__wrapper {
  border-color: #ff3d3d !important;
  box-shadow: 0 0 0 1px #ff3d3d inset !important;
}
.el-input__inner { color: #ccc !important; }
.el-input__inner::placeholder { color: #666 !important; }

/* ---- Select caret / suffix ---- */
.el-select .el-select__caret { color: #888 !important; }
.el-select .el-input .el-input__suffix .el-icon { color: #888 !important; }

/* ---- Dropdown panel (teleported to body, targeted via popper-class="dark-dropdown") ---- */
.dark-dropdown,
.dark-dropdown.el-popper {
  background-color: #1a1d28 !important;
  border: 1px solid #333 !important;
  border-radius: 6px !important;
  box-shadow: 0 6px 16px rgba(0,0,0,.6) !important;
}
.dark-dropdown .el-select-dropdown,
.dark-dropdown .el-scrollbar,
.dark-dropdown .el-scrollbar__wrap,
.dark-dropdown .el-scrollbar__view,
.dark-dropdown .el-select-dropdown__list {
  background-color: #1a1d28 !important;
}
.dark-dropdown .el-popper__arrow::before {
  background: #1a1d28 !important;
  border-color: #333 !important;
}
.dark-dropdown .el-select-dropdown__item {
  color: #bbb !important;
  padding: 8px 14px !important;
  font-size: 13px;
  transition: background .12s, color .12s;
  display: flex;
  align-items: center;
  min-height: 32px;
  line-height: 1.2;
}
.dark-dropdown .el-select-dropdown__item:hover {
  background-color: #2a2d3a !important;
  color: #fff !important;
}
.dark-dropdown .el-select-dropdown__item.is-selected,
.dark-dropdown .el-select-dropdown__item.selected {
  color: #ff3d3d !important;
  font-weight: 600;
}
.dark-dropdown .el-select-dropdown__item.is-hovering {
  background-color: #2a2d3a !important;
}
/* Empty state inside dropdown */
.dark-dropdown .el-select-dropdown__empty {
  color: #666 !important;
  padding: 10px;
}

/* ---- Tooltip / Popper (global, Element Plus renders tooltips to body) ---- */
.el-popper.is-dark {
  background: #1a1d28 !important;
  border: 1px solid #333 !important;
  color: #ccc !important;
}

/* ---- Select tags (not used here but kept for safety) ---- */
.el-select .el-tag { background-color: #2a2d3a !important; border-color: #444 !important; color: #ccc !important; }
.el-select .el-tag .el-tag__close { color: #888 !important; }
.el-select .el-tag .el-tag__close:hover { background-color: #444 !important; color: #fff !important; }

/* Scrollbar */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: #121520; }
::-webkit-scrollbar-thumb { background: #333; border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: #555; }
</style>
