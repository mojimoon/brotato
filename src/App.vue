<template>
  <div class="app-container">
    <!-- Header -->
    <header class="header">
      <h1>
        <span class="title">Brotato Codex</span>
         <a href="https://github.com/mojimoon/" target="_blank" rel="noopener noreferrer" class="author-link">@mojimoon</a>
      </h1>
      <div class="header-actions">
        <!-- [![](https://img.shields.io/github/stars/mojimoon/brotato)](https://github.com/mojimoon/brotato) -->
        <a href="https://github.com/mojimoon/brotato" target="_blank" rel="noopener noreferrer">
          <img src="https://img.shields.io/github/stars/mojimoon/brotato?style=social" alt="GitHub stars" style="height: 20px;" />
        </a>
        <a href="https://brotato.wiki.spellsandguns.com/" target="_blank" rel="noopener noreferrer">
          <el-button class="header-btn" circle>Wiki</el-button>
        </a>
        <el-dropdown @command="(cmd) => { isZh = cmd === 'zh' }" trigger="click">
          <el-button class="header-btn lang-btn" circle>{{ isZh ? '中' : 'EN' }}</el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item :command="'zh'" :class="{ 'is-active-lang': isZh }">中文</el-dropdown-item>
              <el-dropdown-item :command="'en'" :class="{ 'is-active-lang': !isZh }">English</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
        <el-button class="header-btn" :icon="isDark ? Moon : Sunny" circle @click="isDark = !isDark" />
      </div>
    </header>

    <!-- Tabs -->
    <el-tabs v-model="activeTab" type="card" class="main-tabs" @tab-change="onTabChange">
      <el-tab-pane name="weapons"><template #label><el-icon style="vertical-align:middle;margin-right:4px"><Aim /></el-icon>{{ S.weapons }}</template></el-tab-pane>
      <el-tab-pane name="items"><template #label><el-icon style="vertical-align:middle;margin-right:4px"><Box /></el-icon>{{ S.items }}</template></el-tab-pane>
      <el-tab-pane name="characters"><template #label><el-icon style="vertical-align:middle;margin-right:4px"><User /></el-icon>{{ S.characters }}</template></el-tab-pane>
    </el-tabs>

    <!-- Filters -->
    <div class="filters">
      <el-input v-model="searchText" :placeholder="S.search" clearable class="search-input" @input="onFilterChange">
        <template #prefix><el-icon><Search /></el-icon></template>
      </el-input>

      <el-dropdown v-if="activeTab !== 'characters'" trigger="click" popper-class="dark-dropdown" @command="(v) => { filterTier = v; onFilterChange(); }">
        <el-button class="filter-btn" :class="{ 'has-value': filterTier !== null }">
          {{ filterTier !== null ? tierDisplayName(filterTier) : S.tier }}
          <el-icon class="el-icon--right"><ArrowDown /></el-icon>
        </el-button>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item :command="null" :class="{ 'is-active-opt': filterTier === null }">{{ S.all }}</el-dropdown-item>
            <el-dropdown-item v-for="n in 4" :key="n-1" :command="n-1" :class="{ 'is-active-opt': filterTier === n-1 }">{{ tierDisplayName(n-1) }}</el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>

      <el-dropdown v-if="activeTab === 'weapons'" trigger="click" popper-class="dark-dropdown" @command="(v) => { filterType = v; onFilterChange(); }">
        <el-button class="filter-btn" :class="{ 'has-value': !!filterType }">
          {{ filterType ? S[filterType] : S.type }}
          <el-icon class="el-icon--right"><ArrowDown /></el-icon>
        </el-button>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item :command="null" :class="{ 'is-active-opt': !filterType }">{{ S.all }}</el-dropdown-item>
            <el-dropdown-item command="melee" :class="{ 'is-active-opt': filterType === 'melee' }">{{ S.melee }}</el-dropdown-item>
            <el-dropdown-item command="ranged" :class="{ 'is-active-opt': filterType === 'ranged' }">{{ S.ranged }}</el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>

      <el-dropdown v-if="activeTab === 'weapons'" trigger="click" popper-class="dark-dropdown" @command="(v) => { filterSet = v; onFilterChange(); }">
        <el-button class="filter-btn" :class="{ 'has-value': filterSet !== null }">
          {{ filterSet !== null ? ((availableSets.find(s => s.key === filterSet) || {}).label || filterSet) : S.set }}
          <el-icon class="el-icon--right"><ArrowDown /></el-icon>
        </el-button>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item :command="null" :class="{ 'is-active-opt': filterSet === null }">{{ S.all }}</el-dropdown-item>
            <el-dropdown-item v-for="s in availableSets" :key="s.key" :command="s.key" :class="{ 'is-active-opt': filterSet === s.key }">{{ s.label }}</el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>

      <el-dropdown trigger="click" popper-class="dark-dropdown" @command="(v) => { filterDlc = v; onFilterChange(); }">
        <el-button class="filter-btn" :class="{ 'has-value': filterDlc !== null }">
          {{ filterDlc === 0 ? S.base : filterDlc === 1 ? 'DLC' : S.source }}
          <el-icon class="el-icon--right"><ArrowDown /></el-icon>
        </el-button>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item :command="null" :class="{ 'is-active-opt': filterDlc === null }">{{ S.all }}</el-dropdown-item>
            <el-dropdown-item :command="0" :class="{ 'is-active-opt': filterDlc === 0 }">{{ S.baseGame }}</el-dropdown-item>
            <el-dropdown-item :command="1" :class="{ 'is-active-opt': filterDlc === 1 }">DLC</el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>

      <el-dropdown v-if="activeTab === 'items' || activeTab === 'characters'" trigger="click" popper-class="dark-dropdown" @command="(v) => { filterTag = v; onFilterChange(); }">
        <el-button class="filter-btn" :class="{ 'has-value': filterTag !== null }">
          {{ filterTag !== null ? tagTr(filterTag) : S.tag }}
          <el-icon class="el-icon--right"><ArrowDown /></el-icon>
        </el-button>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item :command="null" :class="{ 'is-active-opt': filterTag === null }">{{ S.all }}</el-dropdown-item>
            <el-dropdown-item v-for="t in allTags" :key="t" :command="t" :class="{ 'is-active-opt': filterTag === t }">{{ tagTr(t) }}</el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>

      <el-dropdown v-if="activeTab === 'weapons' || activeTab === 'items'" trigger="click" popper-class="dark-dropdown" @command="(v) => { sortBy = v; onFilterChange(); }">
        <el-button class="filter-btn sort-btn" :class="{ 'has-value': sortBy !== 'default' }">
          <el-icon style="margin-right:4px"><Sort /></el-icon>
          {{ sortBy === 'price' ? S.price : S.default }}
          <el-icon class="el-icon--right"><ArrowDown /></el-icon>
        </el-button>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item command="default" :class="{ 'is-active-opt': sortBy === 'default' }">{{ S.default }}</el-dropdown-item>
            <el-dropdown-item command="price" :class="{ 'is-active-opt': sortBy === 'price' }">{{ S.price }}</el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>

      <el-button v-if="activeTab === 'weapons' || activeTab === 'items'" class="filter-btn price-toggle-btn" :class="{ 'has-value': showPriceEnabled }" @click="showPriceEnabled = !showPriceEnabled">
        <el-icon style="margin-right:4px"><View v-if="showPriceEnabled" /><Hide v-else /></el-icon>
        {{ S.price }}
      </el-button>
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
          <div v-if="shouldShowCardPrice(item)" class="item-price-badge">{{ getListPrice(item) }}</div>
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
                <span class="type-badge" :class="selectedItem.type">{{ S[selectedItem.type] }}</span>
                <span v-if="selectedItem.dlc" class="dlc-badge">DLC</span>
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

          <div class="tier-tabs" v-if="activeTierWeapons.length > 1">
            <button v-for="(tw, idx) in allFourTierSlots" :key="idx" class="tier-tab"
              :class="{ active: currentTierIndex === idx && tw !== null, disabled: tw === null }"
              :disabled="tw === null"
              :style="tw !== null ? { background: currentTierIndex === idx ? tierColor(idx) : tierBgColor(idx), borderColor: tierColor(idx), color: currentTierIndex === idx ? '#fff' : tierColor(idx) } : {}"
              @click="tw !== null && (currentTierIndex = idx, stickyTierIndex = idx)">
              T{{ idx + 1 }}
            </button>
          </div>

          <div v-if="activeWeaponData.stats" class="detail-section">
            <div class="weapon-stat-row">
              <span class="ws-label">{{ S.damage }}</span>
              <span class="ws-val">{{ activeWeaponData.stats.damage }}</span>
              <span v-if="activeWeaponData.stats.scaling_stats?.length" class="ws-scaling">
                (<template v-for="(ss, i) in activeWeaponData.stats.scaling_stats" :key="i">
                  <span v-if="i > 0">+</span><span class="ws-scaling-pct">{{ (ss[1] * 100).toFixed(0) }}%</span>
                  <img v-if="getStatIcon(ss[0])" :src="getStatIcon(ss[0])" class="stat-inline-icon" />
                  <span v-else>{{ statTr(ss[0]) }}</span>
                </template>)
              </span>
            </div>

            <div class="weapon-stat-row">
              <span class="ws-label">{{ S.crit }}</span>
              <span class="ws-val">{{ (activeWeaponData.stats.crit_chance * 100).toFixed(0) }}%</span>
              <span class="ws-val crit-dmg">x{{ activeWeaponData.stats.crit_damage }}</span>
            </div>

            <div class="weapon-stat-row">
              <span class="ws-label">{{ S.cooldown }}</span>
              <span class="ws-val">{{ (activeWeaponData.stats.cooldown / 60).toFixed(2) }}s</span>
            </div>

            <div v-if="activeWeaponData.stats.knockback !== 0" class="weapon-stat-row">
              <span class="ws-label">{{ S.knockback }}</span>
              <span class="ws-val">{{ activeWeaponData.stats.knockback }}</span>
            </div>

            <div class="weapon-stat-row">
              <span class="ws-label">{{ S.range }}</span>
              <span class="ws-val">{{ activeWeaponData.stats.max_range }}
                <span v-if="activeWeaponData.type === 'melee'" class="ws-attack-type">{{ meleeAttackTypeText }}</span>
              </span>
            </div>

            <div v-if="(activeWeaponData.stats.accuracy * 100) < 100" class="weapon-stat-row">
              <span class="ws-label">{{ S.accuracy }}</span>
              <span class="ws-val">{{ (activeWeaponData.stats.accuracy * 100).toFixed(0) }}%</span>
            </div>

            <div v-if="activeWeaponData.stats.lifesteal > 0" class="weapon-stat-row">
              <span class="ws-label">{{ S.lifesteal }}</span>
              <span class="ws-val">{{ (activeWeaponData.stats.lifesteal * 100).toFixed(0) }}%</span>
            </div>

            <div v-if="activeWeaponData.type === 'ranged' && activeWeaponData.stats.piercing > 0" class="weapon-stat-row">
              <span class="ws-label">{{ S.piercing }}</span>
              <span class="ws-val">{{ activeWeaponData.stats.piercing }}
                <span v-if="activeWeaponData.stats.piercing_dmg_reduction > 0" class="ws-attack-type"> (-{{ (activeWeaponData.stats.piercing_dmg_reduction * 100).toFixed(0) }}% {{ S.dmg }})</span>
              </span>
            </div>

            <div v-if="activeWeaponData.type === 'ranged' && activeWeaponData.stats.bounce > 0" class="weapon-stat-row">
              <span class="ws-label">{{ S.bounce }}</span>
              <span class="ws-val">{{ activeWeaponData.stats.bounce }}</span>
            </div>

            <div v-if="activeWeaponData.type === 'ranged' && activeWeaponData.stats.nb_projectiles > 1" class="weapon-stat-row">
              <span class="ws-label">{{ S.projectiles }}</span>
              <span class="ws-val">{{ activeWeaponData.stats.nb_projectiles }}</span>
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
                <span v-if="isUniqueItem(selectedItem)" class="limit-badge unique">{{ S.unique }}</span>
                <span v-else-if="isLimitedItem(selectedItem)" class="limit-badge limited">{{ S.limited }}({{ selectedItem.max_nb }})</span>
                <span v-for="tag in sortedItemTags(selectedItem)" :key="tag" class="tag-badge clickable" :class="specialTagClass(tag)" @click.stop="onTagClick(tag)">
                  <el-tooltip placement="top" effect="dark" :hide-after="0">
                    <template #content>
                      <div class="tag-tooltip-content">
                        <div class="tag-tooltip-name">{{ tagTr(tag) }}</div>
                        <div v-if="tagItems(tag).length" class="tag-tooltip-line">{{ S.items }}：{{ tagItems(tag).join(', ') }}</div>
                        <div v-if="tagCharacters(tag).length" class="tag-tooltip-line">{{ S.characters }}：{{ tagCharacters(tag).join(', ') }}</div>
                      </div>
                    </template>
                    {{ tagTr(tag) }}
                  </el-tooltip>
                </span>
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
              </div>
            </div>
          </div>
          <div v-if="selectedItem.starting_weapons?.length" class="detail-section">
            <h3 class="section-title">{{ S.startingWeapons }}</h3>
            <div class="starting-weapons-grid">
              <div v-for="wid in selectedItem.starting_weapons" :key="wid" class="grid-item starting-weapon-card" @click="navigateToWeapon(wid)">
                <div class="item-icon" :style="{ borderColor: tierColor(getWeaponById(wid)?.tier ?? 0), background: tierBgColor(getWeaponById(wid)?.tier ?? 0) }">
                  <img :src="getIconSrc(getWeaponById(wid)?.icon)" />
                </div>
                <div class="item-name-text">{{ getWeaponById(wid) ? itemName(getWeaponById(wid)) : wid }}</div>
              </div>
            </div>
          </div>
          <div v-if="(selectedItem.wanted_tags || []).length" class="detail-section">
            <h3 class="section-title">{{ S.preferredTags }}</h3>
            <div class="tags-wrap">
              <span v-for="tag in selectedItem.wanted_tags" :key="tag" class="tag-badge clickable" @click.stop="onTagClick(tag)">
                <el-tooltip placement="top" effect="dark" :hide-after="0">
                  <template #content>
                    <div class="tag-tooltip-content">
                      <div class="tag-tooltip-name">{{ tagTr(tag) }}</div>
                      <div v-if="tagItems(tag).length" class="tag-tooltip-line">{{ S.items }}：{{ tagItems(tag).join(', ') }}</div>
                      <div v-if="tagCharacters(tag).length" class="tag-tooltip-line">{{ S.characters }}：{{ tagCharacters(tag).join(', ') }}</div>
                    </div>
                  </template>
                  {{ tagTr(tag) }}
                </el-tooltip>
              </span>
            </div>
          </div>
        </template>

        <!-- Shared: Price Section (weapons & items) -->
        <div v-if="showPriceSection" class="detail-section price-section">
          <div class="price-formula">
            <span class="price-label">{{ S.basePrice }}</span>
            <span class="price-base">{{ getBasePrice() }}</span>
            <!-- <template v-if="showPriceEnabled"> -->
              <span class="price-op">(+</span>
              <span class="price-incr">{{ getWaveIncrement().toFixed(1) }}</span>
              <template v-if="waveSlider > 0">
                <span class="price-op"> × {{ waveSlider }}) =</span>
                <span class="price-final">{{ computedPrice }}</span>
              </template>
              <span v-else class="price-op">)</span>
            <!-- </template> -->
            <img :src="BASE + 'icons/items/materials/harvesting_icon.png'" class="price-icon" />
          </div>
          <table v-if="showPriceEnabled" class="price-table">
            <thead>
              <tr><th>{{ S.wave }}</th><th>1</th><th>4</th><th>8</th><th>14</th><th>19</th></tr>
            </thead>
            <tbody>
              <tr><td>{{ S.price }}</td>
                <td>{{ showPriceCell(1) ? priceAtWave(1) : '—' }}</td>
                <td>{{ showPriceCell(4) ? priceAtWave(4) : '—' }}</td>
                <td>{{ priceAtWave(8) }}</td>
                <td>{{ priceAtWave(14) }}</td>
                <td>{{ priceAtWave(19) }}</td>
              </tr>
            </tbody>
          </table>
          <div v-if="showPriceEnabled" class="price-slider-row">
            <span class="price-label">{{ S.wave }}</span>
            <el-slider v-model="waveSlider" :min="0" :max="20" :step="1" :marks="waveSliderMarks" class="price-slider" placement="bottom" />
          </div>
        </div>

        <!-- Shared: Effects Section -->
        <div v-if="currentEffects?.length" class="detail-section">
          <h3 class="section-title">{{ S.effects }}</h3>
          <div class="effects-list">
            <div v-for="(eff, idx) in currentEffects" :key="idx" class="effect-item">
              <span class="eff-prefix" v-html="renderEffectPrefix(eff)"></span>
              <span class="eff-text" v-html="renderEffectText(eff)"></span>
            </div>
          </div>
        </div>
      </div>

      <!-- Empty -->
      <div class="detail-panel empty-panel" v-else>
        <el-empty :description="S.clickToSee" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick, watch } from 'vue'
import { Search, Sort, User, Sunny, Moon, Box, Aim, ArrowDown, View, Hide } from '@element-plus/icons-vue'

const BASE = import.meta.env.BASE_URL

// ---- Shared string dictionary ----
const S = computed(() => isZh.value ? {
  weapons: '武器', items: '道具', characters: '角色',
  search: '搜索...', all: '全部', tier: '稀有度', type: '类型',
  melee: '近战', ranged: '远战', set: '武器类别', source: '来源',
  base: '本体', baseGame: '本体', tag: '道具标签', sort: '排序',
  default: '默认', price: '价格', showPrice: '显示价格', on: '开', off: '关',
  damage: '伤害', crit: '暴击', cooldown: '冷却', knockback: '击退',
  range: '范围', accuracy: '命中率', lifesteal: '生命窃取', piercing: '贯通',
  bounce: '反弹', projectiles: '投射物', dmg: '伤害',
  basePrice: '基础价格', perWave: '每波', wave: '波次',
  effects: '效果', startingWeapons: '起始武器', preferredTags: '偏好标签',
  unique: '独特', limited: '限制',
  clickToSee: '点击左侧查看详情',
} : {
  weapons: 'Weapons', items: 'Items', characters: 'Characters',
  search: 'Search...', all: 'All', tier: 'Rarity', type: 'Type',
  melee: 'Melee', ranged: 'Ranged', set: 'Set', source: 'Source',
  base: 'Base', baseGame: 'Base Game', tag: 'Tag', sort: 'Sort',
  default: 'Default', price: 'Price', showPrice: 'Show Price', on: 'On', off: 'Off',
  damage: 'Damage', crit: 'Crit', cooldown: 'Cooldown', knockback: 'Knockback',
  range: 'Range', accuracy: 'Accuracy', lifesteal: 'Lifesteal', piercing: 'Piercing',
  bounce: 'Bounce', projectiles: 'Projectiles', dmg: 'dmg',
  basePrice: 'Base Price', perWave: '/wave', wave: 'Wave',
  effects: 'Effects', startingWeapons: 'Starting Weapons', preferredTags: 'Preferred Tags',
  unique: 'Unique', limited: 'Limited',
  clickToSee: 'Click to see details',
})

// ---- Reactivity ----
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
const stickyTierIndex = ref(0)
const filterTag = ref(null)
const sortBy = ref('default')
const showPriceEnabled = ref(true)
const isDark = ref(true)

watch(isDark, (v) => {
  document.documentElement.classList.toggle('light-theme', !v)
  document.body.classList.toggle('light-theme', !v)
}, { immediate: true })

// ---- Tier colors ----
const TIER_COLORS = ['#aaaaaa', '#5cc4ff', '#b75cff', '#ff3d3d']
const TIER_BG_COLORS = ['rgba(170,170,170,0.15)', 'rgba(92,196,255,0.12)', 'rgba(183,92,255,0.12)', 'rgba(255,61,61,0.12)']

function tierColor(tier) { return TIER_COLORS[tier] || '#aaaaaa' }
function tierBgColor(tier) { return TIER_BG_COLORS[tier] || 'rgba(170,170,170,0.1)' }
const TIER_SELECTED_BG = ['rgba(170,170,170,0.35)', 'rgba(92,196,255,0.30)', 'rgba(183,92,255,0.30)', 'rgba(255,61,61,0.30)']
function tierSelectedBg(tier) { return TIER_SELECTED_BG[tier] || TIER_SELECTED_BG[0] }
function tierDisplayName(tier) { return ['T1','T2','T3','T4'][tier] || 'T1' }
function tierTagType(tier) { return ['info','','warning','danger'][tier] || 'info' }

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
  if (sets[key] && sets[key]._manual) return isZh.value ? sets[key].name_zh : sets[key].name_en
  const trans = rawData.value.translations || {}
  if (trans[key]) return isZh.value ? (trans[key].zh || key) : (trans[key].en || key)
  return key.replace('WEAPON_CLASS_', '').replace(/_/g, ' ')
}

function getSetBonuses(key) {
  const sets = rawData.value.sets || {}
  const sd = sets[key]
  if (!sd) return []
  return sd._manual ? sd.tiers : sd
}

function setBonusText(bonus) {
  if (!bonus) return ''
  if (typeof bonus === 'string') return bonus
  if (bonus.en || bonus.zh) return isZh.value ? (bonus.zh || bonus.en) : (bonus.en || bonus.zh)
  if (!Array.isArray(bonus)) return ''
  const lang = isZh.value ? 'zh' : 'en'
  return bonus.map(e => e['text_' + lang] || e.text_en || '').join(' / ')
}

function renderSetBonusHtml(bonus) {
  const raw = setBonusText(bonus)
  if (!raw) return ''
  return raw.replace(/<span class="g">/g, '<span style="color:#22c55e">')
    .replace(/<span class="r">/g, '<span style="color:#ef4444">')
    .replace(/<span class="p">/g, '<span style="color:#a855f7">')
}

function getStatIcon(statKey) {
  const map = rawData.value.stat_icons || {}
  return map[statKey] ? `${BASE}icons/${map[statKey]}` : null
}

function getWeaponById(wid) { return rawData.value.weapons.find(x => x.id === wid) || null }

// ---- Tag translations ----
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
  structure: { en: 'Structure', zh: '构筑物' }, xp_gain: { en: 'XP Gain', zh: '经验获取' },
  pet_or_tongue: { en: 'Pet/Tongue', zh: '宠物/舌头' },
}

function tagTr(tag) {
  const t = TAG_TRANSLATIONS[tag]
  if (!t) return tag.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())
  return isZh.value ? t.zh : t.en
}

const SPECIAL_TAGS = ['pet', 'structure']
function specialTagClass(tag) { return SPECIAL_TAGS.includes(tag) ? 'tag-' + tag : '' }

function isUniqueItem(item) { return item && item.max_nb === 1 }
function isLimitedItem(item) { return item && item.max_nb > 1 }

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

// ---- Tooltip helpers ----
function tagItems(tag) {
  return (rawData.value.items || []).filter(i => (i.tags || []).includes(tag)).map(i => itemName(i)).slice(0, 10)
}
function tagCharacters(tag) {
  return (rawData.value.characters || []).filter(c => (c.wanted_tags || []).includes(tag) || (c.tags || []).includes(tag)).map(c => itemName(c)).slice(0, 10)
}
function onTagClick(tag) {
  if (activeTab.value === 'characters') { pendingNavigate.value = true; activeTab.value = 'items'; filterTag.value = tag }
  else { filterTag.value = tag; selectedItem.value = null }
}

function navigateToWeapon(wid) {
  const familyId = wid.replace(/_\d+$/, '')
  pendingNavigate.value = true; activeTab.value = 'weapons'
  filterType.value = null; filterSet.value = null; filterTag.value = null
  setTimeout(() => {
    const family = weaponFamilies.value.find(f => f.id === familyId)
    if (family) selectItem(family)
  }, 100)
}

// ---- Effect rendering ----
function getSignColor(eff) {
  const es = eff.effect_sign ?? 3
  if (es === 0) return '#22c55e'; if (es === 1) return '#ef4444'
  if (es === 2) return ''; if (es === 5) return '#a855f7'
  const v = eff.value ?? 0
  return v > 0 ? '#22c55e' : v < 0 ? '#ef4444' : ''
}

function resolveStatIcon(iconKey) {
  const fullKey = 'stat_' + iconKey
  const icons = rawData.value.stat_icons || {}
  if (icons[fullKey]) return `${BASE}icons/${icons[fullKey]}`
  for (const [k, p] of Object.entries(icons)) {
    if (k.replace('stat_', '') === iconKey) return `${BASE}icons/${p}`
  }
  return null
}

function renderEffectPrefix(eff) {
  const iconKey = eff.icon
  if (!iconKey) return '·'
  const src = resolveStatIcon(iconKey)
  if (src) {
    return `<img src="${src}" class="stat-prefix-icon" title="${statTr('stat_' + iconKey)}" />`
  }
  return '·'
}

function renderEffectText(eff) {
  const lang = isZh.value ? 'zh' : 'en'
  let text = eff['text_' + lang] || eff.text_en || ''
  if (!text) return `${eff.value} ${statTr(eff.key)}`
  text = text.replace(/<span class="g">/g, '<span style="color:#22c55e">')
    .replace(/<span class="r">/g, '<span style="color:#ef4444">')
    .replace(/<span class="p">/g, '<span style="color:#a855f7">')
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

const availableSets = computed(() => {
  const seen = new Set(); const result = []
  for (const w of rawData.value.weapons) {
    for (const s of (w.sets || [])) {
      if (!seen.has(s)) { seen.add(s); result.push({ key: s, label: setTr(s) }) }
    }
  }
  result.sort((a, b) => a.label.localeCompare(b.label))
  return result
})

// ---- All unique tags ----
const allTags = computed(() => {
  const tagSet = new Set()
  if (activeTab.value === 'items') {
    for (const item of rawData.value.items) { for (const t of (item.tags || [])) tagSet.add(t) }
  } else if (activeTab.value === 'characters') {
    for (const c of rawData.value.characters) { for (const t of (c.wanted_tags || [])) tagSet.add(t) }
  }
  return [...tagSet].sort((a, b) => tagTr(a).localeCompare(tagTr(b)))
})

// ---- Display list ----
const currentDisplayList = computed(() => {
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
  if (sortBy.value === 'price') list.sort((a, b) => (a.value || 0) - (b.value || 0))
  else if (activeTab.value === 'weapons' || activeTab.value === 'items') list.sort(byTierThenName)
  return list
})

// ---- Character ordering ----
const CHAR_BASE_ORDER = [
  'character_well_rounded','character_brawler','character_crazy','character_ranger',
  'character_mage','character_chunky','character_old','character_lucky',
  'character_mutant','character_generalist','character_loud','character_multitasker',
  'character_wildling','character_pacifist','character_gladiator','character_saver',
  'character_sick','character_farmer','character_ghost','character_speedy',
  'character_entrepreneur','character_engineer','character_explorer','character_doctor',
  'character_hunter','character_artificer','character_arms_dealer','character_streamer',
  'character_cyborg','character_glutton','character_jack','character_lich',
  'character_apprentice','character_cryptid','character_fisherman','character_golem',
  'character_king','character_renegade','character_one_arm','character_bull',
  'character_soldier','character_masochist','character_knight','character_demon',
  'character_baby','character_vagabond','character_technomage','character_vampire',
  'character_beast_master','character_wounded',
]
const CHAR_DLC_ORDER = [
  'character_sailor','character_curious','character_builder','character_captain',
  'character_creature','character_chef','character_druid','character_dwarf',
  'character_gangster','character_diver','character_hiker','character_buccaneer',
  'character_ogre','character_romantic',
]
const CHAR_ORDER_MAP = {}
CHAR_BASE_ORDER.forEach((id, i) => { CHAR_ORDER_MAP[id] = i })
CHAR_DLC_ORDER.forEach((id, i) => { CHAR_ORDER_MAP[id] = i + CHAR_BASE_ORDER.length })
function sortCharacters(chars) {
  return chars.sort((a, b) => (CHAR_ORDER_MAP[a.id] ?? 9999) - (CHAR_ORDER_MAP[b.id] ?? 9999))
}

// ---- Active weapon ----
const activeTierWeapons = computed(() => {
  if (activeTab.value !== 'weapons' || !selectedItem.value) return []
  const f = weaponFamilies.value.find(f => f.id === selectedItem.value.id)
  return f ? f.tiers : []
})

const activeWeaponData = computed(() => {
  if (activeTierWeapons.value.length === 0) return selectedItem.value || {}
  return activeTierWeapons.value.find(tw => tw.tier === currentTierIndex.value) || activeTierWeapons.value[0]
})

const activeWeaponTier = computed(() => activeWeaponData.value.tier || 0)

const allFourTierSlots = computed(() => {
  const slots = [null, null, null, null]
  for (const tw of activeTierWeapons.value) slots[tw.tier] = tw
  return slots
})

// ---- Shared computed: effects source ----
const currentEffects = computed(() => {
  if (activeTab.value === 'weapons') return activeWeaponData.value?.effects
  if (activeTab.value === 'items' || activeTab.value === 'characters') return selectedItem.value?.effects
  return null
})

const meleeAttackTypeText = computed(() => {
  const stats = activeWeaponData.value?.stats
  if (!stats || activeWeaponData.value?.type !== 'melee') return ''
  if (stats.attack_type === 0) return isZh.value ? '(突刺)' : '(Thrust)'
  if (stats.attack_type === 1) return isZh.value ? '(横扫)' : '(Sweep)'
  return ''
})

// ---- Price calculation ----
function getBasePrice() {
  if (activeTab.value === 'weapons') return activeWeaponData.value?.value || 0
  if (activeTab.value === 'items') return selectedItem.value?.value || 0
  return 0
}

function getListPrice(item) {
  return item?.value || 0
}

function shouldShowCardPrice(item) {
  if (!showPriceEnabled.value) return false
  if (activeTab.value !== 'weapons' && activeTab.value !== 'items') return false
  return getListPrice(item) > 1
}

function priceAtWave(wave) {
  const bp = getBasePrice()
  return Math.floor(bp + wave + (bp * wave * 0.1))
}

const computedPrice = computed(() => priceAtWave(waveSlider.value))
const showPriceSection = computed(() => (activeTab.value === 'weapons' || activeTab.value === 'items') && getBasePrice() > 1)

function getWaveIncrement() { return getBasePrice() * 0.1 + 1 }

function getCurrentTier() {
  if (activeTab.value === 'weapons') return activeWeaponData.value?.tier ?? 0
  if (activeTab.value === 'items') return selectedItem.value?.tier ?? 0
  return 0
}

function showPriceCell(wave) {
  const tier = getCurrentTier()
  if (tier >= 3 && wave < 8) return false
  if (tier >= 2 && wave < 4) return false
  return true
}

const waveSliderMarks = computed(() => ({ 1:'1', 4:'4', 8:'8', 14:'14', 19:'19' }))

// ---- Selection ----
function selectItem(item) {
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

// ---- Keyboard navigation ----
function getGridColumns() {
  const gridEl = mainContentRef.value?.querySelector('.grid-panel')
  if (!gridEl) return 4
  const colTemplate = getComputedStyle(gridEl).gridTemplateColumns
  return colTemplate.split(' ').length || 4
}

function onKeyDown(e) {
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

function onFilterChange() {}
const pendingNavigate = ref(false)

function onTabChange() {
  filterType.value = null; filterSet.value = null; filterTag.value = null
  sortBy.value = 'default'; searchText.value = ''; filterTier.value = null; filterDlc.value = null
  if (!pendingNavigate.value) {
    selectedItem.value = null
    setTimeout(() => {
      if (currentDisplayList.value.length > 0) selectItem(currentDisplayList.value[0])
    }, 50)
  }
  pendingNavigate.value = false
}

onMounted(async () => {
  const resp = await fetch(BASE + 'data/brotato_data.json')
  rawData.value = await resp.json()
})
</script>

<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
html { background: #1a1d28; }
body { background: #1a1d28; color: #ccc; font-family: 'Segoe UI', system-ui, sans-serif; transition: background .2s, color .2s; }

.app-container { max-width: 1400px; margin: 0 auto; min-height: 100vh; display: flex; flex-direction: column; }

/* Header */
.header { display: flex; align-items: center; justify-content: space-between; padding: 10px 24px; background: #151822; border-bottom: 2px solid #ff3d3d; }
.title { font-size: 22px; font-weight: 800; color: #ff3d3d; letter-spacing: 2px; text-shadow: 0 0 20px rgba(255,61,61,0.15); }
.author-link { font-size: 12px; font-weight: 500; color: #bbb; margin-left: 8px; }
.header-actions { display: flex; gap: 8px; align-items: center; }
.header-btn { background: #252836 !important; border: 1px solid #3a3d4e !important; color: #ccc !important; font-size: 13px; transition: all .2s; }
.header-btn:hover { background: #333648 !important; color: #fff !important; border-color: #5a5d6e !important; }
.lang-btn { font-weight: 700; font-size: 14px; min-width: 36px; }

/* Tabs — card style */
.main-tabs { background: #151822; padding: 0 24px; }
.main-tabs :deep(.el-tabs__header) { margin: 0; }
.main-tabs :deep(.el-tabs__nav-wrap::after) { display: none; }
.el-tabs--card > .el-tabs__header { border-bottom: 1px solid #2a2d3a; background: #151822; }
.el-tabs--card > .el-tabs__header .el-tabs__nav { border: none; }
.el-tabs--card > .el-tabs__header .el-tabs__item {
  color: #bbb !important; height: 42px; line-height: 42px; font-size: 14px;
  background: #22253a; border: 1px solid #3a3d4e; border-bottom: none;
  margin-right: 2px; border-radius: 8px 8px 0 0; padding: 0 18px;
  transition: background .15s, color .15s, border-color .15s;
}
.el-tabs--card > .el-tabs__header .el-tabs__item:first-child { border-left: 1px solid #3a3d4e !important; }
.el-tabs--card > .el-tabs__header .el-tabs__item:hover { color: #eee !important; background: #393d58; border-color: #4a4d5e; }
.el-tabs--card > .el-tabs__header .el-tabs__item.is-active { color: #ff3d3d !important; background: #1a1d28; border-color: #5a5d6e; }
.el-tabs--card > .el-tabs__header .el-tabs__active-bar { background: #ff3d3d; }

/* Filters */
.filters { display: flex; gap: 10px; padding: 10px 24px; background: #1a1d28; border-bottom: 1px solid #2a2d3a; flex-wrap: wrap; align-items: center; }
.search-input { flex: 1; max-width: 280px; }

/* Filter dropdown buttons */
.filter-btn {
  background: #22253a !important; border: 1px solid #3a3d4e !important; color: #bbb !important;
  font-size: 13px !important; height: 32px !important; padding: 0 10px !important;
  min-width: 110px; justify-content: center; gap: 6px;
  border-radius: 6px !important;
  transition: all .15s !important;
}
.filter-btn:hover { background: #2a2d3a !important; border-color: #5a5d6e !important; color: #fff !important; }
.filter-btn.has-value { color: #eae2b0 !important; }
.sort-btn {
  gap: 8px;
  min-width: 122px;
  border-style: solid !important;
  border-color: #43485b !important;
  background: linear-gradient(180deg, #25283a 0%, #1e2131 100%) !important;
  color: #cfd5e3 !important;
  font-weight: 700;
  box-shadow: 0 0 0 1px rgba(255, 255, 255, 0.03), 0 6px 14px rgba(0, 0, 0, 0.16);
  position: relative;
}
.sort-btn:not(.has-value) {
  color: #9da5b7 !important;
  border-color: #363b4d !important;
  background: linear-gradient(180deg, #1f2230 0%, #181b28 100%) !important;
  box-shadow: 0 0 0 1px rgba(255, 255, 255, 0.02), 0 4px 10px rgba(0, 0, 0, 0.14);
}
.sort-btn.has-value {
  color: #fff4cf !important;
  border-color: #d2a64a !important;
  background: linear-gradient(180deg, #4a3815 0%, #2d2412 100%) !important;
  box-shadow: 0 0 0 1px rgba(255, 196, 74, 0.12), 0 0 18px rgba(255, 196, 74, 0.16), 0 6px 14px rgba(0, 0, 0, 0.18);
}
.sort-btn:hover { border-color: #8f97ad !important; }
.sort-btn:not(.has-value):hover {
  background: linear-gradient(180deg, #262b3b 0%, #1e2230 100%) !important;
  color: #c5ccda !important;
}
.sort-btn.has-value:hover {
  background: linear-gradient(180deg, #5a461a 0%, #382b14 100%) !important;
  color: #fff7dd !important;
  border-color: #e0b152 !important;
}
.sort-btn :deep(.el-icon) { color: inherit; }
.price-toggle-btn {
  gap: 8px;
  min-width: 124px;
  border-style: solid !important;
  border-color: #4a4f63 !important;
  font-weight: 700;
  box-shadow: 0 0 0 1px rgba(255, 255, 255, 0.04), 0 6px 14px rgba(0, 0, 0, 0.18);
}
.price-toggle-btn.has-value {
  background: linear-gradient(180deg, #3b4e2f 0%, #273522 100%) !important;
  color: #e8ffd1 !important;
  border-color: #5d8a4b !important;
  box-shadow: 0 0 0 1px rgba(110, 255, 130, 0.12), 0 0 18px rgba(110, 255, 130, 0.18), 0 6px 14px rgba(0, 0, 0, 0.18);
}
.price-toggle-btn:not(.has-value) {
  background: linear-gradient(180deg, #1c1e28 0%, #161821 100%) !important;
  color: #9197aa !important;
  border-color: #2f3445 !important;
  box-shadow: 0 0 0 1px rgba(255, 255, 255, 0.02), 0 4px 10px rgba(0, 0, 0, 0.14);
}
.price-toggle-btn:hover { border-color: #7a8099 !important; }
.price-toggle-btn.has-value:hover {
  background: linear-gradient(180deg, #466038 0%, #314128 100%) !important;
  color: #f5ffd8 !important;
}
.price-toggle-btn:not(.has-value):hover {
  background: linear-gradient(180deg, #242838 0%, #1b1e2b 100%) !important;
  color: #c1c7d8 !important;
}

/* Main */
.main-content { position: relative; height: calc(100vh - 160px); overflow: hidden; }

/* Grid */
.grid-panel {
  position: absolute; left: 0; top: 0; bottom: 0; width: 50%; overflow-y: auto; padding: 10px;
  display: grid; grid-template-columns: repeat(auto-fill, minmax(90px, 1fr));
  gap: 5px; align-content: start; background: #1a1d28;
}
.grid-item {
  background: #22253a; border-radius: 8px; padding: 8px 4px; cursor: pointer;
  transition: all .2s ease; display: flex; flex-direction: column; align-items: center; gap: 4px; position: relative;
  border: 2px solid transparent;
}
.grid-item:hover { transform: translateY(-2px); box-shadow: 0 4px 16px rgba(0,0,0,.35); border-color: #3a3d4e; }
.grid-item.selected { box-shadow: 0 0 16px rgba(255,255,255,0.12); transform: translateY(-1px); }
.item-icon {
  width: 52px; height: 52px; display: flex; align-items: center; justify-content: center;
  background: #1e2030; border-radius: 8px; overflow: hidden; border: 2px solid #3a3d4e;
  transition: border-color .2s;
}
.item-icon img { max-width: 44px; max-height: 44px; image-rendering: pixelated; }
.item-name-text { font-size: 12px; font-weight: 600; text-align: center; max-width: 80px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.item-price-badge {
  position: absolute; top: 3px; left: 3px; font-size: 9px; line-height: 1;
  padding: 2px 5px; border-radius: 4px; font-weight: 500; z-index: 1;
  background: #3a3d4e; color: #fff;
  box-shadow: 0 1px 3px rgba(0,0,0,.35); pointer-events: none;
}
.item-dlc-badge { position: absolute; top: 3px; right: 3px; font-size: 8px; padding: 1px 3px; border-radius: 3px; background: #a855f7; color: #fff; font-weight: bold; }

/* Detail Panel */
.detail-panel {
  position: absolute; right: 0; top: 0; bottom: 0; left: 50%; overflow-y: auto; padding: 20px;
  background: #1e2030; border-left: 2px solid #2a2d3a;
}
.empty-panel { display: flex; align-items: center; justify-content: center; }
.detail-header { display: flex; gap: 14px; align-items: center; margin-bottom: 14px; padding-bottom: 14px; border-bottom: 1px solid #2a2d3a; }
.detail-icon-wrap {
  width: 68px; height: 68px; border-radius: 12px; display: flex; align-items: center; justify-content: center;
  background: #1e2030; border: 2px solid #3a3d4e; overflow: hidden; flex-shrink: 0;
}
.detail-icon-wrap img { max-width: 56px; max-height: 56px; image-rendering: pixelated; }
.detail-title-wrap { flex: 1; min-width: 0; }
.detail-title-wrap h2 { font-size: 20px; margin-bottom: 4px; }
.detail-badges { display: flex; gap: 6px; flex-wrap: wrap; align-items: center; margin-bottom: 2px; }
.type-badge { font-size: 11px; padding: 3px 8px; border-radius: 4px; color: #fff; line-height: 1.4; font-weight: 600; }
.type-badge.melee { background: #c0392b; }
.type-badge.ranged { background: #2980b9; }
.dlc-badge { font-size: 11px; padding: 3px 8px; border-radius: 4px; background: #a855f7; color: #fff; font-weight: 600; }
.set-badge { font-size: 11px; padding: 3px 8px; border-radius: 4px; background: #3a3d4e; color: #ccc; cursor: help; font-weight: 600; transition: background .15s; }
.set-badge:hover { background: #4a4d5e; }

/* Tier Tabs */
.tier-tabs { display: flex; gap: 4px; margin-bottom: 12px; }
.tier-tab { flex: 1; padding: 8px 0; border: 2px solid #444; background: #22253a; color: #888; border-radius: 6px; cursor: pointer; font-size: 13px; font-weight: 700; transition: all .2s; }
.tier-tab:hover:not(.disabled) { color: #fff; border-color: #555; }
.tier-tab.active { color: #fff !important; }
.tier-tab.disabled { opacity: 0.25; cursor: default; border-color: #2a2d3a !important; background: #22253a !important; color: #444 !important; }

/* Set tooltip */
.set-tooltip-content { font-size: 12px; line-height: 1.6; }
.set-tooltip-name { font-weight: bold; margin-bottom: 4px; color: #fff; }
.set-tooltip-line { color: #ccc; }

/* Weapon Stat Rows */
.detail-section { margin-top: 10px; }
.section-title { font-size: 12px; color: #ff3d3d; margin-bottom: 8px; text-transform: uppercase; letter-spacing: 1px; font-weight: 700; }
.weapon-stat-row { display: flex; align-items: center; gap: 8px; padding: 7px 12px; background: #22253a; border-radius: 6px; margin-bottom: 4px; transition: background .15s; }
.weapon-stat-row:hover { background: #282c44; }
.ws-label { font-size: 14px; color: #bbb; min-width: 70px; }
.ws-val { font-size: 15px; color: #eee; font-weight: 600; }
.crit-dmg { color: #f39c12; font-size: 14px; }
.ws-scaling { font-size: 15px; color: #eae2b0; }
.ws-scaling-pct { color: #ddd; }
.ws-attack-type { font-size: 13px; color: #bbb; font-weight: 400; margin-left: 4px; }
.stat-inline-icon { width: 16px; height: 16px; vertical-align: middle; image-rendering: pixelated; margin: 0 1px; }
.stat-prefix-icon { width: 13px; height: 13px; vertical-align: middle; image-rendering: pixelated; }

/* Price Section */
.price-section { margin-top: 12px; padding: 14px 16px; background: #22253a; border-radius: 8px; border: 1px solid #2a2d3a; display: flex; flex-wrap: wrap; gap: 10px 14px; align-items: flex-start; }
.price-formula { display: flex; align-items: baseline; gap: 4px; flex-wrap: wrap; flex: 1 1 320px; min-width: 0; margin-bottom: 0; }
.price-label { font-size: 13px; margin-right: 8px; color: #bbb; }
.price-base { font-size: 16px; font-weight: 700; color: #fff; }
.price-final { font-size: 16px; font-weight: 700; color: #eae2b0; }
.price-incr { font-size: 13px; color: #ccc; }
.price-op { font-size: 13px; color: #888; }
.price-icon { width: 18px; height: 18px; image-rendering: pixelated; vertical-align: middle; }

.price-table { width: 100%; max-width: 50%; flex: 1 1 280px; border-collapse: collapse; margin-bottom: 0; font-size: 13px; }
.price-table th, .price-table td { padding: 5px 8px; text-align: center; border: 1px solid #2a2d3a; }
.price-table th { color: #888; font-weight: 600; }
.price-table td { color: #ddd; }

.price-slider-row { display: flex; align-items: center; gap: 12px; width: 100%; }
.price-label { flex-shrink: 0; white-space: nowrap; }
.price-slider { --el-slider-height: 4px; flex: 1; min-width: 0; }
.price-slider :deep(.el-slider__runway) { background: #2a2d3a; margin: 0; }
.price-slider :deep(.el-slider__bar) { background: #ff3d3d; }
.price-slider :deep(.el-slider__button) { width: 14px; height: 14px; border-color: #ff3d3d; }
.price-slider :deep(.el-slider__marks-text) { font-size: 10px; color: #888; margin-top: 6px; }
.price-slider :deep(.el-slider__input) { display: none; }
.price-slider :deep(.el-slider__stop) { width: 6px; height: 6px; border-radius: 50%; background: #5a5d6e; }

/* Effects */
.effects-list { display: flex; flex-direction: column; gap: 4px; }
.effect-item { padding: 7px 10px; border-radius: 6px; font-size: 13px; background: #22253a; color: #ddd; line-height: 1.5; display: flex; align-items: baseline; gap: 6px; transition: background .15s; }
.effect-item:hover { background: #282c44; }
.eff-prefix { flex-shrink: 0; width: 8px; text-align: center; color: #777; display: flex; align-items: center; justify-content: center; line-height: 1; }
.eff-text { flex: 1; min-width: 0; }

/* Starting Weapons Grid */
.starting-weapons-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(80px, 1fr)); gap: 5px; }
.starting-weapon-card { cursor: pointer; }

/* Tags */
.tags-wrap { display: flex; flex-wrap: wrap; gap: 5px; }
.tag-badge { font-size: 11px; padding: 4px 10px; border-radius: 4px; background: #2a2d44; color: #bbb; font-weight: 600; line-height: 1.4; display: inline-block; transition: all .15s; }
.tag-badge.clickable { cursor: pointer; }
.tag-badge.clickable:hover { background: #3a3d58; color: #fff; }
.limit-badge { font-size: 11px; padding: 4px 10px; border-radius: 4px; color: #fff; font-weight: 600; line-height: 1.4; }
.limit-badge.unique { background: #c0392b; }
.limit-badge.limited { background: #d35400; }
.tag-pet { background: #1e3a1e; color: #6ee76e; }
.tag-pet:hover { background: #2a4a2a !important; color: #9ef79e !important; }
.tag-structure { background: #3a2a1a; color: #ffb74d; }
.tag-structure:hover { background: #4a3520 !important; color: #ffcc80 !important; }
.tag-tooltip-content { font-size: 12px; line-height: 1.6; max-width: 320px; }
.tag-tooltip-name { font-weight: bold; margin-bottom: 2px; color: #fff; }
.tag-tooltip-line { color: #aaa; word-break: break-all; }

/* ---- Element Plus Dark Overrides ---- */
.el-input__wrapper { background-color: #22253a !important; border-color: #3a3d4e !important; box-shadow: none !important; }
.el-input__wrapper:hover { border-color: #5a5d6e !important; }
.el-input.is-focus .el-input__wrapper { border-color: #ff3d3d !important; box-shadow: 0 0 0 1px #ff3d3d inset !important; }
.el-input__inner { color: #ccc !important; }
.el-input__inner::placeholder { color: #777 !important; }
.el-select .el-select__caret { color: #888 !important; }
.el-select .el-input .el-input__suffix .el-icon { color: #888 !important; }
.el-select .el-input__wrapper { background-color: #22253a !important; border-color: #3a3d4e !important; }
.el-select .el-tag { background-color: #2a2d3a !important; border-color: #444 !important; color: #ccc !important; }
.el-input__inner:-webkit-autofill,
.el-input__inner:-webkit-autofill:hover,
.el-input__inner:-webkit-autofill:focus { -webkit-box-shadow: 0 0 0 30px #22253a inset !important; -webkit-text-fill-color: #ccc !important; transition: background-color 5000s ease-in-out 0s; }

/* Dropdown popper */
.dark-dropdown, .dark-dropdown.el-popper { background-color: #22253a !important; border: 1px solid #3a3d4e !important; border-radius: 6px !important; box-shadow: 0 4px 12px rgba(0,0,0,.4) !important; }
.dark-dropdown .el-select-dropdown, .dark-dropdown .el-scrollbar, .dark-dropdown .el-scrollbar__wrap, .dark-dropdown .el-scrollbar__view,
.dark-dropdown .el-select-dropdown__list, .dark-dropdown .el-dropdown-menu { background-color: #22253a !important; }
.dark-dropdown .el-popper__arrow::before { background: #22253a !important; border-color: #3a3d4e !important; }
.dark-dropdown .el-select-dropdown__item { color: #bbb !important; padding: 8px 14px !important; font-size: 13px; transition: background .12s, color .12s; display: flex; align-items: center; min-height: 32px; line-height: 1.2; }
.dark-dropdown .el-select-dropdown__item:hover { background-color: #2e3148 !important; color: #fff !important; }
.dark-dropdown .el-select-dropdown__item.is-selected, .dark-dropdown .el-select-dropdown__item.selected { color: #ff3d3d !important; font-weight: 600; }
.dark-dropdown .el-select-dropdown__item.is-hovering { background-color: #2e3148 !important; }
.dark-dropdown .el-select-dropdown__empty { color: #777 !important; padding: 10px; }
.dark-dropdown .el-dropdown-menu__item {
  color: #bbb !important;
  padding: 8px 14px !important;
  font-size: 13px;
  background-color: transparent !important;
  transition: background-color .18s ease, color .18s ease, box-shadow .18s ease, transform .18s ease;
  line-height: 1.2;
}
.dark-dropdown .el-dropdown-menu__item:hover,
.dark-dropdown .el-dropdown-menu__item:focus,
.dark-dropdown .el-dropdown-menu__item:active {
  background-color: #2e3148 !important;
  color: #fff !important;
}
.dark-dropdown .el-dropdown-menu__item.is-active-opt {
  background-color: rgba(255, 61, 61, 0.08) !important;
  color: #ff3d3d !important;
  font-weight: 600;
}
.el-popper.is-dark { background: #22253a !important; border: 1px solid #3a3d4e !important; color: #ccc !important; }
.is-active-lang { color: #ff3d3d !important; font-weight: 600; }

/* Scrollbar */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: #1a1d28; }
::-webkit-scrollbar-thumb { background: #3a3d4e; border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: #5a5d6e; }

/* ==================== Light Theme ==================== */
html.light-theme { background: #f0f2f5; }
body.light-theme { background: #f0f2f5; color: #222; }
body.light-theme .header { background: #fff; border-bottom-color: #ff3d3d; }
body.light-theme .title { color: #ff3d3d; text-shadow: none; }
body.light-theme .header-btn { background: #e8eaed !important; border-color: #bbb !important; color: #333 !important; }
body.light-theme .header-btn:hover { background: #d8dade !important; color: #111 !important; }
body.light-theme .main-tabs { background: #fff; }
body.light-theme .el-tabs--card > .el-tabs__header { border-bottom-color: #ccc; background: #fff; }
body.light-theme .el-tabs--card > .el-tabs__header .el-tabs__item { color: #444 !important; background: #e8eaed; border-color: #ccc; }
body.light-theme .el-tabs--card > .el-tabs__header .el-tabs__item:first-child { border-left: 1px solid #ccc !important; }
body.light-theme .el-tabs--card > .el-tabs__header .el-tabs__item:hover { color: #222 !important; background: #d5d8de; border-color: #aaa; }
body.light-theme .el-tabs--card > .el-tabs__header .el-tabs__item.is-active { color: #ff3d3d !important; background: #f0f2f5; border-color: #bbb; }
body.light-theme .filters { background: #f0f2f5; border-bottom-color: #ccc; }
body.light-theme .filter-btn { background: #fff !important; border-color: #bbb !important; color: #444 !important; }
body.light-theme .filter-btn:hover { background: #f0f2f5 !important; border-color: #999 !important; color: #222 !important; }
body.light-theme .filter-btn.has-value { color: #111 !important; }
body.light-theme .sort-btn { border-color: #c3c8d4 !important; }
body.light-theme .sort-btn:not(.has-value) { background: linear-gradient(180deg, #eef2f7 0%, #dfe4ec 100%) !important; color: #697080 !important; box-shadow: 0 0 0 1px rgba(0, 0, 0, 0.03), 0 4px 10px rgba(0, 0, 0, 0.08); }
body.light-theme .sort-btn.has-value { background: linear-gradient(180deg, #fff1c8 0%, #ead79a 100%) !important; border-color: #c59c43 !important; color: #755200 !important; box-shadow: 0 0 0 1px rgba(205, 155, 44, 0.1), 0 0 18px rgba(205, 155, 44, 0.12), 0 6px 14px rgba(0, 0, 0, 0.08); }
body.light-theme .sort-btn:hover { border-color: #9ca3b4 !important; }
body.light-theme .sort-btn:not(.has-value):hover { background: linear-gradient(180deg, #e6ebf2 0%, #d6dce7 100%) !important; color: #4b5568 !important; }
body.light-theme .sort-btn.has-value:hover { background: linear-gradient(180deg, #ffe7ae 0%, #e2cc82 100%) !important; color: #5e4100 !important; border-color: #b88b2d !important; }
body.light-theme .price-toggle-btn { border-color: #b5b9c7 !important; }
body.light-theme .price-toggle-btn.has-value { background: linear-gradient(180deg, #d6f2c8 0%, #bfe5ab 100%) !important; border-color: #7aa95d !important; color: #214010 !important; box-shadow: 0 0 0 1px rgba(93, 168, 75, 0.12), 0 0 18px rgba(93, 168, 75, 0.12), 0 6px 14px rgba(0, 0, 0, 0.08); }
body.light-theme .price-toggle-btn:not(.has-value) { background: linear-gradient(180deg, #eef1f5 0%, #dde2ea 100%) !important; border-color: #b4bac5 !important; color: #6b7280 !important; }
body.light-theme .price-toggle-btn.has-value:hover { background: linear-gradient(180deg, #cbe9b8 0%, #b0d99d 100%) !important; color: #17330a !important; }
body.light-theme .price-toggle-btn:not(.has-value):hover { background: linear-gradient(180deg, #e6ebf1 0%, #d8dfe8 100%) !important; color: #4f5664 !important; }
body.light-theme .item-price-badge { box-shadow: 0 1px 3px rgba(0,0,0,.15); background: #ddd; color: #000; }
body.light-theme .el-input__wrapper { background-color: #fff !important; border-color: #bbb !important; }
body.light-theme .el-input__wrapper:hover { border-color: #999 !important; }
body.light-theme .el-input__inner { color: #222 !important; }
body.light-theme .el-input__inner::placeholder { color: #666 !important; }
body.light-theme .el-select .el-input__wrapper { background-color: #fff !important; border-color: #bbb !important; }
body.light-theme .el-input__inner:-webkit-autofill,
body.light-theme .el-input__inner:-webkit-autofill:hover,
body.light-theme .el-input__inner:-webkit-autofill:focus { -webkit-box-shadow: 0 0 0 30px #fff inset !important; -webkit-text-fill-color: #222 !important; }
body.light-theme .grid-panel { background: #f0f2f5; }
body.light-theme .grid-item { background: #fff; border-color: transparent; }
body.light-theme .grid-item:hover { box-shadow: 0 4px 16px rgba(0,0,0,.08); border-color: #ccc; }
body.light-theme .grid-item.selected { box-shadow: 0 0 12px rgba(0,0,0,.10); }
body.light-theme .item-icon { background: #f5f6f8; border-color: #ccc; }
body.light-theme .detail-panel { background: #fff; border-left-color: #ccc; }
body.light-theme .detail-header { border-bottom-color: #ddd; }
body.light-theme .detail-icon-wrap { background: #f5f6f8; border-color: #ccc; }
body.light-theme .set-badge { background: #ddd; color: #333; }
body.light-theme .set-badge:hover { background: #ccc; }
body.light-theme .weapon-stat-row { background: #f0f2f5; }
body.light-theme .weapon-stat-row:hover { background: #e8eaed; }
body.light-theme .ws-label { color: #444; }
body.light-theme .ws-val { color: #111; }
body.light-theme .price-section { background: #f0f2f5; border-color: #ccc; }
body.light-theme .price-label { color: #444; }
body.light-theme .price-base { color: #111; }
body.light-theme .price-final { color: #b45309; }
body.light-theme .price-incr { color: #444; }
body.light-theme .price-op { color: #777; }
body.light-theme .price-table th, body.light-theme .price-table td { border-color: #ccc; }
body.light-theme .price-table th { color: #777; }
body.light-theme .price-table td { color: #222; }
body.light-theme .price-slider :deep(.el-slider__runway) { background: #ccc; }
body.light-theme .price-slider :deep(.el-slider__marks-text) { color: #888; }
body.light-theme .price-slider :deep(.el-slider__stop) { background: #aaa; }
body.light-theme .effect-item { background: #f0f2f5; color: #222; }
body.light-theme .effect-item:hover { background: #e8eaed; }
body.light-theme .eff-prefix { color: #777; }
body.light-theme .starting-weapon-card { background: #fff; }
body.light-theme .starting-weapon-card:hover { box-shadow: 0 4px 12px rgba(0,0,0,.08); }
body.light-theme .item-name-text { color: #222; }
body.light-theme .tag-badge { background: #ddd; color: #333; }
body.light-theme .tag-badge.clickable:hover { background: #ccc; color: #111; }
body.light-theme .section-title { color: #ff3d3d; font-weight: 700; }
body.light-theme ::-webkit-scrollbar-track { background: #f0f2f5; }
body.light-theme ::-webkit-scrollbar-thumb { background: #bbb; }
body.light-theme ::-webkit-scrollbar-thumb:hover { background: #999; }
body.light-theme .tag-tooltip-line { color: #555; }
body.light-theme .set-tooltip-line { color: #555; }
body.light-theme .set-tooltip-name { color: #111; }
body.light-theme .ws-scaling { color: #333; }
body.light-theme .ws-scaling-pct { color: #333; }
body.light-theme .crit-dmg { color: #c0392b; }
body.light-theme .ws-attack-type { color: #666; }
body.light-theme .tier-tab { background: #e2e4e8; border-color: #bbb; color: #666; }
body.light-theme .tier-tab:not(.disabled):hover { background: #d5d8de; color: #333; }
body.light-theme .tier-tab.disabled { border-color: #ccc !important; background: #eee !important; color: #ccc !important; }
body.light-theme .tier-tab.active { color: #fff !important; }
body.light-theme .tag-pet { background: #c8e6c9; color: #1b5e20; }
body.light-theme .tag-pet:hover { background: #a5d6a7 !important; color: #0d3b0d !important; }
body.light-theme .tag-structure { background: #fff3e0; color: #e65100; }
body.light-theme .tag-structure:hover { background: #ffe0b2 !important; color: #bf360c !important; }
body.light-theme .el-input.is-focus .el-input__wrapper { border-color: #ff3d3d !important; box-shadow: 0 0 0 1px #ff3d3d inset !important; }
body.light-theme .el-select .el-select__caret { color: #555 !important; }
body.light-theme .el-select .el-tag { background-color: #e8eaed !important; border-color: #ccc !important; color: #333 !important; }
body.light-theme .dark-dropdown, body.light-theme .dark-dropdown.el-popper { background-color: #fff !important; border-color: #ccc !important; box-shadow: 0 2px 8px rgba(0,0,0,.08) !important; }
body.light-theme .dark-dropdown .el-select-dropdown, body.light-theme .dark-dropdown .el-scrollbar, body.light-theme .dark-dropdown .el-dropdown-menu, body.light-theme .dark-dropdown .el-dropdown-menu__item { background-color: #fff !important; }
body.light-theme .dark-dropdown .el-dropdown-menu__item { color: #222 !important; }
body.light-theme .dark-dropdown .el-dropdown-menu__item:hover { background-color: #f0f2f5 !important; color: #111 !important; }
body.light-theme .dark-dropdown .el-dropdown-menu__item.is-active-opt { color: #ff3d3d !important; }
body.light-theme .dark-dropdown .el-popper__arrow::before { background: #fff !important; border-color: #ccc !important; }
body.light-theme .dark-dropdown .el-select-dropdown__item { color: #222 !important; }
body.light-theme .dark-dropdown .el-select-dropdown__item:hover { background-color: #f0f2f5 !important; color: #111 !important; }
body.light-theme .dark-dropdown .el-select-dropdown__item.is-selected { color: #ff3d3d !important; }
body.light-theme .dark-dropdown .el-select-dropdown__item.is-hovering { background-color: #f0f2f5 !important; }
body.light-theme .el-popper.is-dark { background: #fff !important; border-color: #ccc !important; color: #222 !important; }
</style>
