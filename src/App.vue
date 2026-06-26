<template>
  <div class="app-container">
    <!-- Header -->
    <header class="header">
      <h1>
        <span class="title">Brotato Codex</span>
        <a href="https://github.com/mojimoon/" target="_blank" rel="noopener noreferrer"
          class="author-link">@mojimoon</a>
      </h1>
      <div class="header-actions">
        <span>
          V 1.1.15.4
        </span>
        <!-- [![](https://img.shields.io/github/stars/mojimoon/brotato)](https://github.com/mojimoon/brotato) -->
        <a href="https://github.com/mojimoon/brotato" target="_blank" rel="noopener noreferrer">
          <img src="https://img.shields.io/github/stars/mojimoon/brotato?style=social" alt="GitHub stars"
            style="height: 20px;" />
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
      <el-tab-pane name="weapons"><template #label><el-icon style="vertical-align:middle;margin-right:4px">
            <Aim />
          </el-icon>{{ S.weapons }}</template></el-tab-pane>
      <el-tab-pane name="items"><template #label><el-icon style="vertical-align:middle;margin-right:4px">
            <Box />
          </el-icon>{{ S.items }}</template></el-tab-pane>
      <el-tab-pane name="characters"><template #label><el-icon style="vertical-align:middle;margin-right:4px">
            <User />
          </el-icon>{{ S.characters }}</template></el-tab-pane>
    </el-tabs>

    <!-- Filters -->
    <div class="filters">
      <el-input v-model="searchText" :placeholder="S.search" clearable class="search-input" @input="onFilterChange">
        <template #prefix><el-icon>
            <Search />
          </el-icon></template>
      </el-input>

      <el-dropdown v-if="activeTab !== 'characters'" trigger="click" popper-class="dark-dropdown"
        @command="(v) => { filterTier = v; onFilterChange(); }">
        <el-button class="filter-btn" :class="{ 'has-value': filterTier !== null }">
          {{ filterTier !== null ? tierDisplayName(filterTier) : S.tier }}
          <el-icon class="el-icon--right">
            <ArrowDown />
          </el-icon>
        </el-button>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item :command="null" :class="{ 'is-active-opt': filterTier === null }">{{ S.all
            }}</el-dropdown-item>
            <el-dropdown-item v-for="n in 4" :key="n - 1" :command="n - 1"
              :class="{ 'is-active-opt': filterTier === n - 1 }">{{ tierDisplayName(n - 1) }}</el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>

      <el-dropdown v-if="activeTab === 'weapons'" trigger="click" popper-class="dark-dropdown"
        @command="(v) => { filterType = v; onFilterChange(); }">
        <el-button class="filter-btn" :class="{ 'has-value': !!filterType }">
          {{ filterType ? S[filterType] : S.type }}
          <el-icon class="el-icon--right">
            <ArrowDown />
          </el-icon>
        </el-button>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item :command="null" :class="{ 'is-active-opt': !filterType }">{{ S.all }}</el-dropdown-item>
            <el-dropdown-item command="melee" :class="{ 'is-active-opt': filterType === 'melee' }">{{ S.melee
            }}</el-dropdown-item>
            <el-dropdown-item command="ranged" :class="{ 'is-active-opt': filterType === 'ranged' }">{{ S.ranged
            }}</el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>

      <el-dropdown v-if="activeTab === 'weapons'" trigger="click" popper-class="dark-dropdown"
        @command="(v) => { filterSet = v; onFilterChange(); }">
        <el-button class="filter-btn" :class="{ 'has-value': filterSet !== null }">
          {{filterSet !== null ? ((availableSets.find(s => s.key === filterSet) || {}).label || filterSet) : S.set}}
          <el-icon class="el-icon--right">
            <ArrowDown />
          </el-icon>
        </el-button>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item :command="null" :class="{ 'is-active-opt': filterSet === null }">{{ S.all
            }}</el-dropdown-item>
            <el-dropdown-item v-for="s in availableSets" :key="s.key" :command="s.key"
              :class="{ 'is-active-opt': filterSet === s.key }">{{ s.label }}</el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>

      <el-dropdown trigger="click" popper-class="dark-dropdown" @command="(v) => { filterDlc = v; onFilterChange(); }">
        <el-button class="filter-btn" :class="{ 'has-value': filterDlc !== null }">
          {{ filterDlc === 0 ? S.base : filterDlc === 1 ? 'DLC' : S.source }}
          <el-icon class="el-icon--right">
            <ArrowDown />
          </el-icon>
        </el-button>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item :command="null" :class="{ 'is-active-opt': filterDlc === null }">{{ S.all
            }}</el-dropdown-item>
            <el-dropdown-item :command="0" :class="{ 'is-active-opt': filterDlc === 0 }">{{ S.baseGame
            }}</el-dropdown-item>
            <el-dropdown-item :command="1" :class="{ 'is-active-opt': filterDlc === 1 }">DLC</el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>

      <el-dropdown v-if="activeTab === 'items' || activeTab === 'characters'" trigger="click"
        popper-class="dark-dropdown" @command="(v) => { filterTag = v; onFilterChange(); }">
        <el-button class="filter-btn" :class="{ 'has-value': filterTag !== null }">
          {{ filterTag !== null ? tagTr(filterTag) : S.tag }}
          <el-icon class="el-icon--right">
            <ArrowDown />
          </el-icon>
        </el-button>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item :command="null" :class="{ 'is-active-opt': filterTag === null }">{{ S.all
            }}</el-dropdown-item>
            <el-dropdown-item v-for="t in allTags" :key="t" :command="t"
              :class="{ 'is-active-opt': filterTag === t }">{{ tagTr(t) }}</el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>

      <el-button v-if="hasActiveFilter" class="filter-btn clear-btn" @click="clearAllFilters">
        <el-icon>
          <Close />
        </el-icon>
      </el-button>

      <el-dropdown v-if="activeTab === 'weapons' || activeTab === 'items'" trigger="click" popper-class="dark-dropdown"
        @command="(v) => { sortBy = v; onFilterChange(); }" class="sort-dropdown">
        <el-button class="filter-btn sort-btn" :class="{ 'has-value': sortBy !== 'default' }">
          <el-icon style="margin-right:4px">
            <Sort />
          </el-icon>
          {{ sortBy === 'price' ? S.price : S.default }}
          <el-icon class="el-icon--right">
            <ArrowDown />
          </el-icon>
        </el-button>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item command="default" :class="{ 'is-active-opt': sortBy === 'default' }">{{ S.default
            }}</el-dropdown-item>
            <el-dropdown-item command="price" :class="{ 'is-active-opt': sortBy === 'price' }">{{ S.price
            }}</el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>

      <el-button v-if="activeTab === 'weapons' || activeTab === 'items'" class="filter-btn price-toggle-btn"
        :class="{ 'has-value': showingPrice }" @click="showingPrice = !showingPrice">
        <el-icon style="margin-right:4px">
          <View v-if="showingPrice" />
          <Hide v-else />
        </el-icon>
        {{ S.price }}
      </el-button>
    </div>

    <!-- Main Content -->
    <div class="main-content" tabindex="0" @keydown="onKeyDown" ref="mainContentRef">
      <!-- Left: Grid -->
      <div class="grid-panel">
        <div v-for="item in currentDisplayList" :key="item.id" :ref="el => { if (el) gridItemRefs[item.id] = el }"
          class="grid-item" :class="{ selected: selectedItem?.id === item.id }"
          :style="selectedItem?.id === item.id ? { background: tierSelectedBg(item.tier), borderColor: tierColor(item.tier) } : {}"
          @click="selectItem(item)">
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
            <div class="detail-icon-wrap"
              :style="{ borderColor: tierColor(activeWeaponTier), background: tierBgColor(activeWeaponTier) }">
              <img :src="getIconSrc(selectedItem.icon)" />
            </div>
            <div class="detail-title-wrap">
              <h2 :style="{ color: tierColor(activeWeaponTier) }">{{ itemName(selectedItem) }}</h2>
              <div class="detail-badges">
                <span class="type-badge" :class="selectedItem.type">{{ S[selectedItem.type] }}</span>
                <span v-if="selectedItem.dlc" class="dlc-badge">DLC</span>
                <el-tooltip v-for="(setNameKey, si) in (selectedItem.sets || [])" :key="si" placement="top"
                  effect="dark" :hide-after="0">
                  <template #content>
                    <div class="set-tooltip-content">
                      <div class="set-tooltip-name">{{ setTr(setNameKey) }}</div>
                      <div v-for="(bonus, bi) in (getSetBonuses(setNameKey) || [])" :key="bi" class="set-tooltip-line">
                        ({{ bi + 2 }}) <span v-html="setBonusText(bonus)"></span>
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

          <div v-if="displayStats" class="detail-section">
            <div class="weapon-stat-row">
              <span class="ws-label">{{ S.damage }}</span>
              <span class="ws-val" :class="{ 'curse-modified': curseEnabled }">{{ displayStats.damage }}</span>
              <span v-if="displayStats.scaling_stats?.length" class="ws-scaling">
                (<template v-for="(ss, i) in displayStats.scaling_stats" :key="i">
                  <span v-if="i > 0">+</span><span class="ws-scaling-pct">{{ (ss[1] * 100).toFixed(0) }}%</span>
                  <img v-if="getStatIcon(ss[0])" :src="getStatIcon(ss[0])" class="stat-inline-icon" />
                  <span v-else>{{ statTr(ss[0]) }}</span>
                </template>)
              </span>
            </div>

            <div class="weapon-stat-row">
              <span class="ws-label">{{ S.crit }}</span>
              <span class="ws-val">{{ (activeWeaponData.stats.crit_chance * 100).toFixed(0) }}%</span>
              <span class="ws-val crit-dmg" :class="{ 'curse-modified': curseEnabled }">x{{ displayStats.crit_damage
              }}</span>
            </div>

            <div class="weapon-stat-row">
              <span class="ws-label">{{ S.cooldown }}</span>
              <span class="ws-val">
                {{ formatCooldown(displayCooldown) }}
                <span class="ws-attack-type">({{ formatCooldown(displayStats.cooldown / 60) }}+{{
                  formatCooldown(displayStats.animation_cooldown || 0) }})</span>
              </span>
            </div>

            <div v-if="addlCooldownInfo" class="weapon-stat-row">
              <span class="ws-label">{{ S.cooldown }}</span>
              <span class="ws-val">{{ addlCooldownInfo }}</span>
            </div>

            <div v-if="displayStats.knockback !== 0" class="weapon-stat-row">
              <span class="ws-label">{{ S.knockback }}</span>
              <span class="ws-val">{{ displayStats.knockback }}</span>
            </div>

            <div class="weapon-stat-row">
              <span class="ws-label">{{ S.range }}</span>
              <span class="ws-val">{{ displayStats.max_range }}
                <span v-if="activeWeaponData.type === 'melee'" class="ws-attack-type">{{ meleeAttackTypeText }}</span>
              </span>
            </div>

            <div v-if="(displayStats.accuracy * 100) < 100" class="weapon-stat-row">
              <span class="ws-label">{{ S.accuracy }}</span>
              <span class="ws-val">{{ (displayStats.accuracy * 100).toFixed(0) }}%</span>
            </div>

            <div v-if="displayStats.lifesteal > 0" class="weapon-stat-row">
              <span class="ws-label">{{ S.lifesteal }}</span>
              <span class="ws-val" :class="{ 'curse-modified': curseEnabled }">{{ (displayStats.lifesteal *
                100).toFixed(0)
              }}%</span>
            </div>

            <div v-if="activeWeaponData.type === 'ranged' && displayStats.piercing > 0" class="weapon-stat-row">
              <span class="ws-label">{{ S.piercing }}</span>
              <span class="ws-val" :class="{ 'curse-modified': curseEnabled }">{{ displayStats.piercing }}
                <span v-if="displayStats.piercing_dmg_reduction > 0" class="ws-attack-type"> (-{{
                  (displayStats.piercing_dmg_reduction * 100).toFixed(0) }}% {{ S.dmg }})</span>
              </span>
            </div>

            <div v-if="activeWeaponData.type === 'ranged' && displayStats.bounce > 0" class="weapon-stat-row">
              <span class="ws-label">{{ S.bounce }}</span>
              <span class="ws-val" :class="{ 'curse-modified': curseEnabled }">{{ displayStats.bounce }}</span>
            </div>

            <div v-if="activeWeaponData.type === 'ranged' && activeWeaponData.stats.nb_projectiles > 1"
              class="weapon-stat-row">
              <span class="ws-label">{{ S.projectiles }}</span>
              <span class="ws-val">{{ activeWeaponData.stats.nb_projectiles }}</span>
            </div>
          </div>
        </template>

        <!-- Item Detail -->
        <template v-else-if="activeTab === 'items'">
          <div class="detail-header">
            <div class="detail-icon-wrap"
              :style="{ borderColor: tierColor(selectedItem.tier), background: tierBgColor(selectedItem.tier) }">
              <img :src="getIconSrc(selectedItem.icon)" />
            </div>
            <div class="detail-title-wrap">
              <h2 :style="{ color: tierColor(selectedItem.tier) }">{{ itemName(selectedItem) }}</h2>
              <div class="detail-badges">
                <span v-if="selectedItem.dlc" class="dlc-badge">DLC</span>
                <span v-if="isUniqueItem(selectedItem)" class="limit-badge unique">{{ S.unique }}</span>
                <span v-else-if="isLimitedItem(selectedItem)" class="limit-badge limited">{{ S.limited }}({{
                  selectedItem.max_nb }})</span>
                <span v-for="tag in sortedItemTags(selectedItem)" :key="tag" class="tag-badge clickable"
                  :class="specialTagClass(tag)" @click.stop="onTagClick(tag)">
                  <el-tooltip placement="top" effect="dark" :hide-after="0">
                    <template #content>
                      <div class="tag-tooltip-content">
                        <div class="tag-tooltip-name">{{ tagTr(tag) }}</div>
                        <div v-if="tagItems(tag).length" class="tag-tooltip-line">{{ S.items }}：{{
                          tagItems(tag).join(' ,') }}</div>
                        <div v-if="tagCharacters(tag).length" class="tag-tooltip-line">{{ S.characters }}：{{
                          tagCharacters(tag).join(', ') }}</div>
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
            <div class="detail-icon-wrap"
              :style="{ borderColor: tierColor(selectedItem.tier), background: tierBgColor(selectedItem.tier) }">
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
              <div v-for="wid in selectedItem.starting_weapons" :key="wid" class="grid-item starting-weapon-card"
                @click="navigateToWeapon(wid)">
                <div class="item-icon"
                  :style="{ borderColor: tierColor(getWeaponById(wid)?.tier ?? 0), background: tierBgColor(getWeaponById(wid)?.tier ?? 0) }">
                  <img :src="getIconSrc(getWeaponById(wid)?.icon)" />
                </div>
                <div class="item-name-text">{{ getWeaponById(wid) ? itemName(getWeaponById(wid), true) : wid }}</div>
              </div>
            </div>
          </div>
          <div v-if="(selectedItem.wanted_tags || []).length" class="detail-section">
            <h3 class="section-title">{{ S.preferredTags }}</h3>
            <div class="tags-wrap">
              <span v-for="tag in selectedItem.wanted_tags" :key="tag" class="tag-badge clickable"
                @click.stop="onTagClick(tag)">
                <el-tooltip placement="top" effect="dark" :hide-after="0">
                  <template #content>
                    <div class="tag-tooltip-content">
                      <div class="tag-tooltip-name">{{ tagTr(tag) }}</div>
                      <div v-if="tagItems(tag).length" class="tag-tooltip-line">{{ S.items }}：
                        {{ tagItems(tag).join(', ') }}</div>
                      <div v-if="tagCharacters(tag).length" class="tag-tooltip-line">{{ S.characters }}：{{
                        tagCharacters(tag).join(', ') }}</div>
                    </div>
                  </template>
                  {{ tagTr(tag) }}
                </el-tooltip>
              </span>
            </div>
          </div>
        </template>

        <!-- Curse Preview (weapons & items) -->
        <div v-if="activeTab === 'weapons' || activeTab === 'items'" class="detail-section curse-section">
          <div class="curse-row">
            <el-button class="curse-toggle-btn" :class="{ 'curse-active': curseEnabled }"
              @click="curseEnabled = !curseEnabled" size="small">{{ S.curse }}</el-button>
            <el-slider v-if="curseEnabled" v-model="curseSlider" :min="10" :max="110" :step="1" show-input
              class="curse-slider" />
          </div>
        </div>

        <!-- Attack Speed Calculator (weapons only) -->
        <div v-if="activeTab === 'weapons' && activeWeaponData.stats" class="detail-section">
          <div class="attack-speed-toggle" @click="showAttackSpeedCalc = !showAttackSpeedCalc">
            <span class="toggle-icon">{{ showAttackSpeedCalc ? '▼' : '▶' }}</span>
            <span>{{ S.attackSpeedCalc }}</span>
          </div>
          <div v-if="showAttackSpeedCalc" class="attack-speed-calc">
            <div class="calc-result">
              <span class="calc-label">{{ S.finalCooldown }}:</span>
              <span class="calc-value">{{ formatCooldown(calculatedCooldown) }}</span>
              <span class="calc-pct"
                :class="cooldownChangePct < 0 ? 'pct-neg' : cooldownChangePct > 0 ? 'pct-pos' : ''">({{
                  S.attackSpeed }} {{ cooldownChangePct > 0 ? '+' : '' }}{{ cooldownChangePct.toFixed(0) }}%)</span>
            </div>
            <div class="slider-row">
              <label class="slider-label">{{ S.attackSpeed }}</label>
              <el-slider v-model="attackSpeedSlider" :min="-200" :max="500" :step="1" :marks="atkSpeedMarks"
                show-input />
            </div>
            <div v-if="activeWeaponData.type === 'melee'" class="slider-row">
              <label class="slider-label">{{ S.statRange }}</label>
              <el-slider v-model="statRangeSlider" :min="-200" :max="200" :step="1" :marks="rangeMarks" show-input />
            </div>
            <div class="cooldown-chart-wrapper">
              <Line :data="chartData" :options="chartOptions" :plugins="[baseCooldownLinePlugin, currentPointPlugin]" />
            </div>
          </div>
        </div>

        <!-- Shared: Price Section (weapons & items) -->
        <div v-if="showPriceSection" class="detail-section">
          <div class="price-toggle" @click="showPriceDetail = !showPriceDetail">
            <span class="toggle-icon">{{ showPriceDetail ? '▼' : '▶' }}</span>
            <span>{{ S.basePrice }}</span>
            <span class="price-base">{{ getBasePrice() }}
              <img :src="priceIconSrc" class="price-icon" />
            </span>
          </div>
          <div v-if="showPriceDetail" class="price-section">
            <table class="price-table">
              <thead>
                <tr>
                  <th></th>
                  <th>{{ S.perWave }}</th>
                  <th>{{ S.wave }} {{ waveSlider }}</th>
                  <th>1</th>
                  <th>4</th>
                  <th>8</th>
                  <th>14</th>
                  <th>19</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td>{{ isMobile ? S.belowNightmareShort : S.belowNightmare }}</td>
                  <td>+{{ formatIncr(getWaveIncrement()) }}</td>
                  <td class="price-base price-final">{{ waveSlider > 0 ? computedPrice : getBasePrice() }}</td>
                  <td>{{ showPriceCell(1) ? priceAtWave(1) : '' }}</td>
                  <td>{{ showPriceCell(4) ? priceAtWave(4) : '' }}</td>
                  <td>{{ priceAtWave(8) }}</td>
                  <td>{{ priceAtWave(14) }}</td>
                  <td>{{ priceAtWave(19) }}</td>
                </tr>
                <tr>
                  <td>{{ isMobile ? S.nightmareShort : S.nightmare }}</td>
                  <td>+{{ formatIncr(getWaveIncrementNM()) }}</td>
                  <td class="price-base price-final-nightmare">{{ waveSlider > 0 ? computedPriceNM : getBasePrice() }}
                  </td>
                  <td>{{ showPriceCell(1) ? priceAtWaveNM(1) : '' }}</td>
                  <td>{{ showPriceCell(4) ? priceAtWaveNM(4) : '' }}</td>
                  <td>{{ priceAtWaveNM(8) }}</td>
                  <td>{{ priceAtWaveNM(14) }}</td>
                  <td>{{ priceAtWaveNM(19) }}</td>
                </tr>
              </tbody>
            </table>
            <div class="price-slider-row">
              <span class="wave-label">{{ S.wave }}</span>
              <el-slider v-model="waveSlider" :min="0" :max="20" :step="1" :marks="waveSliderMarks" class="price-slider"
                placement="bottom" />
            </div>
          </div>
        </div>

        <!-- Shared: Effects Section -->
        <div v-if="currentEffects?.length" class="detail-section">
          <h3 class="section-title">{{ S.effects }}</h3>
          <div class="effects-list">
            <template v-for="(eff, idx) in currentEffects" :key="idx">
              <div class="effect-item">
                <span class="eff-prefix" v-html="renderEffectPrefix(eff)"></span>
                <span class="eff-text" v-html="renderEffectText(eff)"></span>
              </div>
              <!-- Extra effects only when cursed -->
              <div v-if="curseEnabled && eff.text?.extra_effects" v-for="(extra, ei) in eff.text.extra_effects"
                :key="'x' + idx + '_' + ei" class="effect-item curse-extra-effect">
                <span class="eff-prefix" v-html="renderEffectPrefix(extra)"></span>
                <span class="eff-text" v-html="renderEffectText(extra)"></span>
              </div>
            </template>
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
import { Search, Sort, User, Sunny, Moon, Box, Aim, ArrowDown, View, Hide, Close } from '@element-plus/icons-vue'
import { Line } from 'vue-chartjs'
import { Chart as ChartJS, LinearScale, PointElement, LineElement, Tooltip } from 'chart.js'

ChartJS.register(LinearScale, PointElement, LineElement, Tooltip)

const BASE = import.meta.env.MODE === 'production'
  ? 'https://cdn.jsdmirror.com/gh/mojimoon/brotato@v1.4.1/public/'
  : import.meta.env.BASE_URL

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
  unique: '独特', limited: '限制', clickToSee: '点击左侧查看详情',
  belowNightmare: '难度0-5', nightmare: '噩梦',
  basePriceShort: '价格', belowNightmareShort: '难5', nightmareShort: '噩梦',
  attackSpeedCalc: '攻速计算器', attackSpeed: '攻速', statRange: '范围',
  curse: '诅咒', finalCooldown: '最终冷却', clear: '清除筛选'
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
  unique: 'Unique', limited: 'Limited', clickToSee: 'Click to see details',
  belowNightmare: 'Danger 0-5', nightmare: 'Nightmare',
  basePriceShort: 'Price', belowNightmareShort: 'D5', nightmareShort: 'NM',
  attackSpeedCalc: 'Attack Speed Calculator', attackSpeed: 'A.Spd', statRange: 'Range',
  curse: 'Curse', finalCooldown: 'Final Cooldown', clear: 'Clear Filters'
})

// ---- Reactivity ----
const rawData = ref({ weapons: [], items: [], characters: [], translations: {}, stat_icons: {}, sets: {} })
const mainContentRef = ref(null)
const gridItemRefs = ref({})
const activeTab = ref('weapons')
const lsGet = (k, d) => { try { const v = localStorage.getItem(k); return v !== null ? JSON.parse(v) : d } catch { return d } }
const isZh = ref(lsGet('brotato_isZh', navigator.language.startsWith('zh')))
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
const sortBy = ref(lsGet('brotato_sortBy', 'default'))
const showingPrice = ref(lsGet('brotato_showingPrice', true))
const isDark = ref(lsGet('brotato_isDark', true))
const isMobile = ref(window.innerWidth < 768)
const priceIconSrc = computed(() => `${BASE}icons/items/materials/harvesting_icon.png`)

// ---- Attack Speed Calculator ----
const showAttackSpeedCalc = ref(lsGet('brotato_showAtkCalc', false))
const showPriceDetail = ref(lsGet('brotato_showPriceDetail', false))
const attackSpeedSlider = ref(0)
const statRangeSlider = ref(0)

// ---- Curse System ----
const curseEnabled = ref(false)
const curseSlider = ref(110)

// Persist curse state (similar to other UI state)
const CURSE_STORAGE_KEY = 'brotato_curse'
const CURSE_ENABLED_KEY = 'brotato_curse_enabled'

function loadCurseState() {
  try {
    const saved = localStorage.getItem(CURSE_STORAGE_KEY)
    if (saved !== null) curseSlider.value = parseInt(saved) || 110
    const savedEnabled = localStorage.getItem(CURSE_ENABLED_KEY)
    if (savedEnabled !== null) curseEnabled.value = savedEnabled === 'true'
  } catch (e) { /* localStorage not available */ }
}

watch(curseSlider, (v) => {
  try { localStorage.setItem(CURSE_STORAGE_KEY, String(v)) } catch (e) {}
})
watch(curseEnabled, (v) => {
  try { localStorage.setItem(CURSE_ENABLED_KEY, String(v)) } catch (e) {}
})

// Curse value as a fraction: slider value / 100
const curseFactor = computed(() => curseEnabled.value ? curseSlider.value / 100 : 0)

function applyCurse(curseArg, effectSign, originalValue) {
  // curseArg: {value, type, mult?, ceil?, curse_value?, curse_min?, curse_max?, linked_mult?, max_val?}
  // type: default|positive|negative|random|fixed|linked|none
  const cv = curseFactor.value
  if (cv <= 0) return Math.round(curseArg.value)
  
  const type = curseArg.type || 'default'
  const absV = Math.abs(curseArg.value)
  const sign = curseArg.value < 0 ? -1 : 1
  const mult = curseArg.mult ?? 1.0
  const useCeil = curseArg.ceil ?? true
  const effMod = cv * mult
  
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
      // Show range: 72~76
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

const chartData = computed(() => {
  const stats = activeWeaponData.value?.stats
  if (!stats) return { datasets: [] }

  const minAtkSpd = -100
  const maxAtkSpd = 200
  const hasRange = activeWeaponData.value?.type === 'melee' && statRangeSlider.value !== 0
  const mainPoints = []
  const basePoints = []

  for (let atkSpd = minAtkSpd; atkSpd <= maxAtkSpd; atkSpd += 1) {
    mainPoints.push({ x: atkSpd, y: calculateCooldownWithAttackSpeed(stats.cooldown, stats.animation_cooldown || 0, atkSpd, statRangeSlider.value) })
    if (hasRange) {
      basePoints.push({ x: atkSpd, y: calculateCooldownWithAttackSpeed(stats.cooldown, stats.animation_cooldown || 0, atkSpd, 0) })
    }
  }

  const dark = isDark.value
  const datasets = []
  if (hasRange) {
    datasets.push({
      data: basePoints,
      borderColor: dark ? '#888' : '#bbb',
      borderWidth: 1.5,
      pointRadius: 0,
      tension: 0.3,
    })
  }
  datasets.push({
    data: mainPoints,
    borderColor: dark ? '#4ade80' : '#22c55e',
    borderWidth: 2,
    pointRadius: 0,
    tension: 0.3,
  })

  return { datasets }
})

const baseCooldownLinePlugin = {
  id: 'baseCooldownLine',
  afterDraw(chart) {
    const baseCd = totalCooldown.value
    if (!baseCd) return
    const yScale = chart.scales.y
    const y = yScale.getPixelForValue(baseCd)
    if (y < yScale.top || y > yScale.bottom) return
    const ctx = chart.ctx
    ctx.save()
    ctx.beginPath()
    ctx.setLineDash([6, 3])
    ctx.strokeStyle = isDark.value ? '#f87171' : '#ef4444'
    ctx.lineWidth = 1
    ctx.moveTo(chart.chartArea.left, y)
    ctx.lineTo(chart.chartArea.right, y)
    ctx.stroke()
    ctx.restore()
  }
}

const currentPointPlugin = {
  id: 'currentPoint',
  afterDraw(chart) {
    const xScale = chart.scales.x
    const yScale = chart.scales.y
    if (!xScale || !yScale || !chart.chartArea) return

    const val = attackSpeedSlider.value
    const datasets = chart.data.datasets
    if (!datasets.length) return

    const lastDs = datasets[datasets.length - 1].data
    if (!lastDs || !lastDs.length) return

    let closest = lastDs[0]
    let minDist = Infinity
    lastDs.forEach(pt => {
      const d = Math.abs(pt.x - val)
      if (d < minDist) { minDist = d; closest = pt }
    })
    if (!closest) return

    const x = xScale.getPixelForValue(closest.x)
    const y = yScale.getPixelForValue(closest.y)
    const ctx = chart.ctx
    ctx.save()
    ctx.beginPath()
    ctx.arc(x, y, 5, 0, Math.PI * 2)
    ctx.fillStyle = isDark.value ? '#f87171' : '#ef4444'
    ctx.fill()
    ctx.restore()
  }
}

const chartOptions = computed(() => {
  const dark = isDark.value
  const _atkSpd = attackSpeedSlider.value // dependency so chart re-renders on slider change
  return {
    responsive: true,
    maintainAspectRatio: true,
    aspectRatio: 3,
    animation: false,
    plugins: {
      legend: { display: false },
      tooltip: {
        mode: 'index',
        intersect: false,
        callbacks: {
          label: (ctx) => ctx.parsed.y.toFixed(3),
        },
      },
    },
    scales: {
      x: {
        type: 'linear',
        min: -100,
        max: 200,
        grid: { color: dark ? '#333' : '#e5e5e5' },
        ticks: { color: dark ? '#aaa' : '#666', font: { size: 10 }, stepSize: 25 },
      },
      y: {
        min: 0,
        grid: { color: dark ? '#333' : '#e5e5e5' },
        ticks: { color: dark ? '#aaa' : '#666', font: { size: 10 }, callback: (v) => v.toFixed(2) },
      },
    },
  }
})

watch([showAttackSpeedCalc, attackSpeedSlider, statRangeSlider, isDark], () => {
  // Chart.js is reactive via computed, no manual redraw needed
})

watch(isDark, (v) => {
  document.documentElement.classList.toggle('light-theme', !v)
  document.body.classList.toggle('light-theme', !v)
}, { immediate: true })

watch(isZh, v => localStorage.setItem('brotato_isZh', JSON.stringify(v)))
watch(sortBy, v => localStorage.setItem('brotato_sortBy', JSON.stringify(v)))
watch(showingPrice, v => localStorage.setItem('brotato_showingPrice', JSON.stringify(v)))
watch(isDark, v => localStorage.setItem('brotato_isDark', JSON.stringify(v)))
watch(showAttackSpeedCalc, v => localStorage.setItem('brotato_showAtkCalc', JSON.stringify(v)))
watch(showPriceDetail, v => localStorage.setItem('brotato_showPriceDetail', JSON.stringify(v)))

// ---- Tier colors ----
const TIER_COLORS = ['#aaaaaa', '#5cc4ff', '#b75cff', '#ff3d3d']
const TIER_BG_COLORS = ['rgba(170,170,170,0.15)', 'rgba(92,196,255,0.12)', 'rgba(183,92,255,0.12)', 'rgba(255,61,61,0.12)']

function tierColor(tier) { return TIER_COLORS[tier] || '#aaaaaa' }
function tierBgColor(tier) { return TIER_BG_COLORS[tier] || 'rgba(170,170,170,0.1)' }
const TIER_SELECTED_BG = ['rgba(170,170,170,0.35)', 'rgba(92,196,255,0.30)', 'rgba(183,92,255,0.30)', 'rgba(255,61,61,0.30)']
function tierSelectedBg(tier) { return TIER_SELECTED_BG[tier] || TIER_SELECTED_BG[0] }
function tierDisplayName(tier) { return ['T1','T2','T3','T4'][tier] || 'T1' }
function tierSuffix(tier) { return ['',' Ⅱ',' Ⅲ',' Ⅳ'][tier] || '' }
function tierTagType(tier) { return ['info','','warning','danger'][tier] || 'info' }

function itemName(item, showWeaponTier = false) { 
  if (showWeaponTier) {
    const tier = activeWeaponData.value?.tier ?? 0
    const suffix = tierSuffix(tier)
    return isZh.value ? `${item.name_zh}${suffix}` : `${item.name_en}${suffix}`
  }
  return isZh.value ? item.name_zh : item.name_en 
}
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
  return bonus.map(e => (e.text && e.text[lang]) || '').join(' / ')
}

// function renderSetBonusHtml(bonus) {
//   const raw = setBonusText(bonus)
//   if (!raw) return ''
//   return raw.replace(/<span class="g">/g, '<span style="color:#22c55e">')
//     .replace(/<span class="r">/g, '<span style="color:#ef4444">')
//     .replace(/<span class="p">/g, '<span style="color:#a855f7">')
// }

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
  structure: { en: 'Structure (Preference)', zh: '构筑物(偏好)' }, structure_real: { en: 'Structure', zh: '构筑物' }, xp_gain: { en: 'XP Gain', zh: '经验获取' },
}

function tagTr(tag) {
  const t = TAG_TRANSLATIONS[tag]
  if (!t) return tag.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())
  return isZh.value ? t.zh : t.en
}

const SPECIAL_TAGS = ['pet', 'structure_real']
function specialTagClass(tag) { return SPECIAL_TAGS.includes(tag) ? 'tag-' + tag : '' }

function isUniqueItem(item) { return item && item.max_nb === 1 }
function isLimitedItem(item) { return item && item.max_nb > 1 }

const TAG_SORT_ORDER = { pet: 0, structure_real: 1, structure: 2 }
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
  return (rawData.value.items || []).filter(i => (i.tags || []).includes(tag)).map(i => itemName(i))
}
function tagCharacters(tag) {
  return (rawData.value.characters || []).filter(c => (c.wanted_tags || []).includes(tag) || (c.tags || []).includes(tag)).map(c => itemName(c))
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
    // Old format fallback
    text = eff.text?.[lang] || ''
    curseArgs = []
    useCurseData = false
  }
  
  if (!text) return `${eff.value} ${statTr(eff.key)}`
  
  const effectSign = eff.effect_sign ?? 3
  const origValue = eff.value
  
  // Apply curse to placeholders
  if (curseArgs.length > 0) {
    // Pre-compute linked parent value (always curseArgs[0])
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
          return dp != null ? val.toFixed(dp) : String(Math.round(val))
        }
        let rawValue = curseEnabled.value
          ? applyCurse(arg, effectSign, origValue)
          : (arg.decimalPlaces != null ? arg.value.toFixed(arg.decimalPlaces) : Math.round(arg.value))
        if (arg.decimalPlaces != null && curseEnabled.value) {
          rawValue = parseFloat(rawValue).toFixed(arg.decimalPlaces)
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
        // Weapon: fixed base_value - 1, no curse scaling
        effectiveVal = Math.max(1, (special.base_value ?? origValue) - 1)
      } else {
        // Item: negative curse type, value scales with curse
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
// ]
// const CHAR_DLC_ORDER = [
  'character_sailor','character_curious','character_builder','character_captain',
  'character_creature','character_chef','character_druid','character_dwarf',
  'character_gangster','character_diver','character_hiker','character_buccaneer',
  'character_ogre','character_romantic',
]
const CHAR_ORDER_MAP = {}
CHAR_BASE_ORDER.forEach((id, i) => { CHAR_ORDER_MAP[id] = i })
// CHAR_DLC_ORDER.forEach((id, i) => { CHAR_ORDER_MAP[id] = i + CHAR_BASE_ORDER.length })
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

// Cursed weapon stats for display
const displayStats = computed(() => {
  const stats = activeWeaponData.value?.stats
  if (!stats) return null
  const cv = curseFactor.value
  if (cv <= 0) return stats
  return {
    ...stats,
    damage: Math.ceil(stats.damage * (1 + cv)),
    crit_damage: Math.round(stats.crit_damage * (1 + cv / 5) * 10) / 10,
    // NOTE: cooldown(attack speed) is NOT modified by curse (per _boost_weapon_stats_damage)
    lifesteal: stats.lifesteal > 0 ? Math.round(stats.lifesteal * (1 + cv) * 100) / 100 : stats.lifesteal,
    piercing: stats.piercing > 0 ? Math.min(stats.piercing + 1, Math.ceil(stats.piercing * (1 + cv / 5))) : stats.piercing,
    bounce: stats.bounce > 0 ? Math.min(stats.bounce + 1, Math.ceil(stats.bounce * (1 + cv / 5))) : stats.bounce,
    scaling_stats: (stats.scaling_stats || []).map(([k, v]) => [k, v * (1 + cv)]),
  }
})

const allFourTierSlots = computed(() => {
  const slots = [null, null, null, null]
  for (const tw of activeTierWeapons.value) slots[tw.tier] = tw
  return slots
})

// Additional cooldown every X shots (e.g. revolver, grenade launcher, chain gun)
const addlCooldownInfo = computed(() => {
  const stats = activeWeaponData.value?.stats
  if (!stats || stats.additional_cooldown_every_x_shots <= 0) return ''
  const shots = stats.additional_cooldown_every_x_shots
  const mult = stats.additional_cooldown_multiplier
  const baseCd = stats.cooldown / 60
  const effectiveCd = baseCd * mult
  const cdStr = formatCooldown(effectiveCd)
  if (isZh.value) return `每发射${shots}次冷却增加至${cdStr}`
  return `Cooldown is ${cdStr} every ${shots} shots`
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

// ---- Cooldown calculation ----
const totalCooldown = computed(() => {
  const stats = activeWeaponData.value?.stats
  if (!stats) return 0
  const attackCooldown = stats.cooldown / 60
  const animationCooldown = stats.animation_cooldown || 0
  return attackCooldown + animationCooldown
})

const displayCooldown = computed(() => {
  const stats = displayStats.value
  if (!stats) return 0
  const attackCooldown = stats.cooldown / 60
  const animationCooldown = stats.animation_cooldown || 0
  return attackCooldown + animationCooldown
})

function formatCooldown(seconds) {
  if (seconds < 0.1) return seconds.toFixed(3) + 's'
  return seconds.toFixed(2) + 's'
}

function calculateCooldownWithAttackSpeed(baseCooldownFrames, animationCooldown, attackSpeed, statRange, rangeOverride) {
  const atkSpd = attackSpeed / 100
  const MIN_CD = 2

  let attackCooldownFrames
  if (atkSpd < 0) {
    attackCooldownFrames = Math.trunc(baseCooldownFrames * (1 + Math.abs(atkSpd)))
  } else {
    attackCooldownFrames = Math.trunc(baseCooldownFrames / (1 + atkSpd))
  }
  attackCooldownFrames = Math.max(MIN_CD, attackCooldownFrames)
  const attackCooldown = attackCooldownFrames / 60

  let animCooldown = animationCooldown || 0
  if (animCooldown > 0) {
    const BASE_ATK_DURATION = 0.2
    const stats = activeWeaponData.value?.stats
    if (stats && activeWeaponData.value?.type === 'melee') {
      const baseRange = stats.max_range || 150
      const effectiveRange = rangeOverride !== undefined ? rangeOverride : baseRange + statRange / 2
      const rangeFactor = Math.max(0, effectiveRange / Math.max(70 * (1 + (atkSpd / 3)), 70))
      const atkDuration = Math.max(0.01, BASE_ATK_DURATION - (atkSpd / 10)) + rangeFactor * 0.15
      const backDuration = atkSpd > 0 ? BASE_ATK_DURATION / (1 + (atkSpd * 3)) : BASE_ATK_DURATION
      const recoilDuration = stats.recoil_duration || 0.1
      animCooldown = atkDuration / 2 + backDuration + recoilDuration
    }
  }

  return attackCooldown + animCooldown
}

const calculatedCooldown = computed(() => {
  const stats = activeWeaponData.value?.stats
  if (!stats) return 0
  return calculateCooldownWithAttackSpeed(
    stats.cooldown,
    stats.animation_cooldown || 0,
    attackSpeedSlider.value,
    statRangeSlider.value
  )
})

const cooldownChangePct = computed(() => {
  if (totalCooldown.value === 0 || calculatedCooldown.value === 0) return 0
  return (totalCooldown.value / calculatedCooldown.value - 1) * 100
})

// const atkSpeedMarks = { [-200]: '-200', [-100]: '-100', [0]: '0', [100]: '100', [200]: '200', [300]: '300', [400]: '400', [500]: '500' }
const atkSpeedMarks = computed(() => isMobile.value ? { [-200]: '-200', [0]: '0', [100]: '100', [300]: '300', [500]: '500' } : { [-200]: '-200', [-100]: '-100', [0]: '0', [100]: '100', [200]: '200', [300]: '300', [400]: '400', [500]: '500' })
const rangeMarks = { [-200]: '-200', [-100]: '-100', [0]: '0', [100]: '100', [200]: '200' }

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
  if (!showingPrice.value) return false
  if (activeTab.value !== 'weapons' && activeTab.value !== 'items') return false
  return getListPrice(item) > 1
}

function priceAtWave(wave) {
  const bp = getBasePrice()
  return Math.floor(bp + wave + (bp * wave * 0.1))
}

function priceAtWaveNM(wave) {
  const bp = getBasePrice()
  return Math.floor(bp + wave + (bp * wave * 0.11))
}

const computedPrice = computed(() => priceAtWave(waveSlider.value))
const computedPriceNM = computed(() => priceAtWaveNM(waveSlider.value))
const showPriceSection = computed(() => (activeTab.value === 'weapons' || activeTab.value === 'items') && getBasePrice() > 1)

function getWaveIncrement() { return getBasePrice() * 0.1 + 1 }

function getWaveIncrementNM() { return getBasePrice() * 0.11 + 1 }

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

function formatIncr(v) {
  // up to 2 decimal places, remove trailing zeros
  return v.toFixed(2).replace(/\.?0+$/, '')
}

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
const hasActiveFilter = computed(() => searchText.value || filterTier.value !== null || filterType.value || filterSet.value !== null || filterDlc.value !== null || filterTag.value !== null)
function clearAllFilters() {
  searchText.value = ''
  filterTier.value = null
  filterType.value = null
  filterSet.value = null
  filterDlc.value = null
  filterTag.value = null
}
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
  loadCurseState()
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
.filter-btn.has-value {
  color: #fff4cf !important;
  border-color: #d2a64a !important;
  box-shadow: 0 0 0 1px rgba(255, 196, 74, 0.12);
}
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
  box-shadow: 0 0 0 1px rgba(255, 196, 74, 0.12), 0 0 0 1px rgba(255, 196, 74, 0.08) inset;
}
.sort-btn:hover { border-color: #8f97ad !important; }
.sort-btn:not(.has-value):hover {
  background: linear-gradient(180deg, #262b3b 0%, #1e2230 100%) !important;
  color: #c5ccda !important;
}
.sort-btn.has-value:hover {
  color: #fff7dd !important;
  border-color: #e0b152 !important;
  box-shadow: 0 0 0 1px rgba(255, 196, 74, 0.16), 0 0 0 1px rgba(255, 196, 74, 0.12) inset;
}
.sort-btn :deep(.el-icon) { color: inherit; }
.sort-dropdown { margin-left: auto; }
.clear-btn { color: #888; padding: 8px !important; min-width: 0; }
.clear-btn:hover { color: #f39c12 !important; border-color: #f39c12 !important; }
.price-toggle-btn {
  gap: 8px;
  min-width: 124px;
  border-style: solid !important;
  border-color: #4a4f63 !important;
  font-weight: 700;
  box-shadow: 0 0 0 1px rgba(255, 255, 255, 0.04), 0 6px 14px rgba(0, 0, 0, 0.18);
}
.price-toggle-btn.has-value {
  color: #e8ffd1 !important;
  border-color: #5d8a4b !important;
  box-shadow: 0 0 0 1px rgba(110, 255, 130, 0.12), 0 0 0 1px rgba(110, 255, 130, 0.08) inset;
}
.price-toggle-btn:not(.has-value) {
  background: linear-gradient(180deg, #1c1e28 0%, #161821 100%) !important;
  color: #9197aa !important;
  border-color: #2f3445 !important;
  box-shadow: 0 0 0 1px rgba(255, 255, 255, 0.02), 0 4px 10px rgba(0, 0, 0, 0.14);
}
.price-toggle-btn:hover { border-color: #7a8099 !important; }
.price-toggle-btn.has-value:hover {
  color: #f5ffd8 !important;
  border-color: #6ea054 !important;
  box-shadow: 0 0 0 1px rgba(110, 255, 130, 0.16), 0 0 0 1px rgba(110, 255, 130, 0.1) inset;
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
  position: absolute; top: 3px; left: 3px; font-size: 12px; line-height: 1;
  padding: 2px 5px; border-radius: 4px; font-weight: 500; z-index: 1;
  background: #3a3d4e; color: #fff;
  box-shadow: 0 1px 3px rgba(0,0,0,.35); pointer-events: none;
}
.item-dlc-badge { position: absolute; top: 3px; right: 3px; font-size: 11px; padding: 1px 3px; border-radius: 3px; background: #a855f7; color: #fff; font-weight: 500; }

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
.ws-val.curse-modified { color: #c084fc; text-shadow: 0 0 6px rgba(139, 92, 246, 0.3); }
.crit-dmg { color: #f39c12; font-size: 14px; }
.ws-scaling { font-size: 15px; color: #eae2b0; }
.ws-scaling-pct { color: #ddd; }
.ws-attack-type { font-size: 13px; color: #bbb; font-weight: 400; margin-left: 4px; }
.stat-inline-icon { width: 16px; height: 16px; vertical-align: middle; image-rendering: pixelated; margin: 0 1px; }
.stat-prefix-icon { width: 13px; height: 13px; vertical-align: middle; image-rendering: pixelated; }

/* Curse Section */
.curse-section { margin-top: 12px; padding: 12px 16px; background: #22253a; border-radius: 8px; border: 1px solid #2a2d3a; }
.curse-row { display: flex; align-items: center; gap: 12px; }
.curse-toggle-btn { 
  font-size: 13px; font-weight: 600; 
  background: #2a2d3a !important; border: 1px solid #3a3d4e !important; color: #888 !important;
  transition: all 0.2s;
}
.curse-toggle-btn.curse-active {
  background: #3d1f5e !important; border-color: #7b3fa3 !important; color: #c084fc !important;
  box-shadow: 0 0 8px rgba(139, 92, 246, 0.3);
}
.curse-slider { flex: 1; min-width: 150px; --el-slider-height: 4px; }
.curse-slider :deep(.el-slider__runway) { background: #2a2d3a; }
.curse-slider :deep(.el-slider__bar) { background: #7b3fa3; }
.curse-slider :deep(.el-slider__button) { width: 14px; height: 14px; border-color: #7b3fa3; }
.curse-slider :deep(.el-input-number) { width: 80px; }

/* Price Section */
.price-section { margin-top: 12px; padding: 14px 16px; background: #22253a; border-radius: 8px; border: 1px solid #2a2d3a; }
.price-toggle { display: flex; align-items: center; gap: 8px; padding: 10px 12px; background: #22253a; border-radius: 6px; cursor: pointer; font-size: 14px; color: #f39c12; transition: background .15s; }
.price-toggle:hover { background: #282c44; }
.price-table { width: 100%; border-collapse: collapse; margin-bottom: 12px; font-size: 13px; margin-top: 12px; }
.price-table th, .price-table td { padding: 6px 10px; text-align: center; border: 1px solid #2a2d3a; }
.price-table th { color: #888; font-weight: 600; background: #1e2030; }
.price-table td { color: #ddd; }
.price-table .price-bold { font-weight: 700; color: #fff; }
.price-base { font-size: 16px; font-weight: 700; color: #fff; }
.price-final { color: #f39c12 !important; }
.price-final-nightmare { color: #ff3d3d !important; }
.price-icon { width: 18px; height: 18px; image-rendering: pixelated; vertical-align: middle; }
.price-label { font-size: 13px; color: #bbb; }

.price-slider-row { display: flex; align-items: center; gap: 12px; }
.wave-label { flex-shrink: 0; white-space: nowrap; font-size: 13px; color: #bbb; margin-right: 8px; }
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
.curse-extra-effect { border-left: 3px solid #c084fc; padding-left: 8px; }
.curse-extra-effect .eff-prefix { color: #c084fc; }
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
.tag-structure_real { background: #3a2a1a; color: #ffb74d; }
.tag-structure_real:hover { background: #4a3520 !important; color: #ffcc80 !important; }
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
.dark-dropdown .el-select-dropdown__list, .dark-dropdown .el-dropdown-menu { background-color: #22253a !important; max-height: 540px; overflow-y: auto; }
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
body.light-theme .filter-btn.has-value {
  color: #7c5a06 !important;
  border-color: #c59c43 !important;
  box-shadow: 0 0 0 1px rgba(205, 155, 44, 0.14);
}
body.light-theme .sort-btn { border-color: #c3c8d4 !important; }
body.light-theme .sort-btn:not(.has-value) { background: linear-gradient(180deg, #eef2f7 0%, #dfe4ec 100%) !important; color: #697080 !important; box-shadow: 0 0 0 1px rgba(0, 0, 0, 0.03), 0 4px 10px rgba(0, 0, 0, 0.08); }
body.light-theme .sort-btn.has-value { border-color: #c59c43 !important; color: #755200 !important; box-shadow: 0 0 0 1px rgba(205, 155, 44, 0.1), 0 0 0 1px rgba(205, 155, 44, 0.08) inset; }
body.light-theme .sort-btn:hover { border-color: #9ca3b4 !important; }
body.light-theme .sort-btn:not(.has-value):hover { background: linear-gradient(180deg, #e6ebf2 0%, #d6dce7 100%) !important; color: #4b5568 !important; }
body.light-theme .sort-btn.has-value:hover { color: #5e4100 !important; border-color: #b88b2d !important; box-shadow: 0 0 0 1px rgba(205, 155, 44, 0.14), 0 0 0 1px rgba(205, 155, 44, 0.1) inset; }
body.light-theme .clear-btn { color: #999; }
body.light-theme .clear-btn:hover { color: #c0392b !important; border-color: #c0392b !important; }
body.light-theme .price-toggle-btn { border-color: #b5b9c7 !important; }
body.light-theme .price-toggle-btn.has-value { border-color: #7aa95d !important; color: #214010 !important; box-shadow: 0 0 0 1px rgba(93, 168, 75, 0.12), 0 0 0 1px rgba(93, 168, 75, 0.08) inset; }
body.light-theme .price-toggle-btn:not(.has-value) { background: linear-gradient(180deg, #eef1f5 0%, #dde2ea 100%) !important; border-color: #b4bac5 !important; color: #6b7280 !important; }
body.light-theme .price-toggle-btn.has-value:hover { color: #17330a !important; border-color: #6f9f56 !important; box-shadow: 0 0 0 1px rgba(93, 168, 75, 0.16), 0 0 0 1px rgba(93, 168, 75, 0.1) inset; }
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
body.light-theme .curse-section { background: #f0f2f5; border-color: #ccc; }
body.light-theme .curse-toggle-btn { background: #e8eaed !important; border-color: #ccc !important; color: #777 !important; }
body.light-theme .curse-toggle-btn.curse-active { background: #ede9fe !important; border-color: #a78bfa !important; color: #7c3aed !important; }
body.light-theme .curse-modified { color: #7c3aed !important; }
body.light-theme .price-section { background: #f0f2f5; border-color: #ccc; }
body.light-theme .price-toggle { background: #f5f5f5; color: #c0392b; }
body.light-theme .price-toggle:hover { background: #e8e8e8; }
body.light-theme .wave-label { color: #444; }
body.light-theme .price-base { color: #111; }
body.light-theme .price-final { color: #1e88e5 !important; }
body.light-theme .price-final-nightmare { color: #e53935 !important; }
body.light-theme .price-table th, body.light-theme .price-table td { border-color: #ccc; }
body.light-theme .price-table th { color: #777; background: #e8eaed; }
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
body.light-theme .tag-structure_real { background: #fff3e0; color: #e65100; }
body.light-theme .tag-structure_real:hover { background: #ffe0b2 !important; color: #bf360c !important; }
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
body.light-theme .el-slider__tooltip { background: #fff !important; border: 1px solid #ddd !important; color: #222 !important; }
body.light-theme .el-slider__tooltip::after { border-top-color: #fff !important; }
body.light-theme .el-popper .el-popper__arrow::before { background: #fff !important; border-color: #ccc !important; }

/* ==================== Responsive ==================== */
@media (max-width: 768px) {
  .main-content {
    position: relative; height: auto; overflow: visible;
    display: flex; flex-direction: column; gap: 0;
  }
  .grid-panel {
    position: static; width: 100%; height: 40vh; overflow-y: auto;
    border-right: none; border-bottom: 2px solid #2a2d3a;
  }
  .detail-panel {
    position: static; left: auto; width: 100%; flex: 1; min-height: 0;
    overflow-y: auto; border-left: none;
  }
  body.light-theme .grid-panel { border-bottom-color: #ccc; }
  body.light-theme .detail-panel { border-left: none; }
  .empty-panel { min-height: 20vh; }
  .filters { padding: 6px 12px; gap: 6px; }
  .sort-dropdown { margin-left: 0 !important; flex-basis: 100%; }
  .sort-dropdown + .price-toggle-btn { flex-basis: auto; }
  .filter-select { width: 110px; }
  .sort-select { width: 100px; }
  .search-input { max-width: 200px; }
  .header { padding: 8px 12px; }
  .title { font-size: 18px; }
  .main-tabs { padding: 0 12px; }
  .main-tabs :deep(.el-tabs__item) { padding: 0 12px; font-size: 13px; }
}

/* Attack Speed Calculator */
.attack-speed-toggle {
  display: flex; align-items: center; gap: 8px; padding: 10px 12px;
  background: #22253a; border-radius: 6px; cursor: pointer;
  font-size: 14px; color: #f39c12; transition: background .15s;
}
.attack-speed-toggle:hover { background: #282c44; }
.toggle-icon { font-size: 10px; color: #888; }
.attack-speed-calc {
  margin-top: 8px; padding: 12px; background: #22253a;
  border-radius: 6px; border: 1px solid #2a2d3a;
}
.calc-result {
  display: flex; align-items: center; gap: 8px;
  margin-bottom: 12px; padding: 8px 12px;
  background: #1e2030; border-radius: 6px;
}
.calc-label { font-size: 14px; color: #bbb; }
.calc-value { font-size: 18px; font-weight: 700; color: #4ade80; }
.calc-pct { font-size: 14px; font-weight: 600; margin-left: 4px; }
.pct-pos { color: #4ade80; }
.pct-neg { color: #f87171; }
.slider-row {
  display: flex; align-items: center; gap: 12px; margin-bottom: 12px;
}
.slider-label {
  flex-shrink: 0; width: 60px; font-size: 13px; color: #bbb; text-align: right;
}
.slider-row .el-slider { flex: 1; --el-slider-height: 4px; }
.slider-row .el-slider :deep(.el-slider__runway) { background: #2a2d3a; }
.slider-row .el-slider :deep(.el-slider__bar) { background: #4ade80; }
.slider-row .el-slider :deep(.el-slider__button) {
  width: 14px; height: 14px; border-color: #4ade80;
}
/* .slider-row .el-slider :deep(.el-slider__input) { width: 60px; }
.slider-row .el-slider :deep(.el-slider__input .el-input-number__decrease),
.slider-row .el-slider :deep(.el-slider__input .el-input-number__increase) { display: none; }
.slider-row .el-slider :deep(.el-slider__input .el-input__wrapper) { padding-left: 4px; padding-right: 4px; }
.slider-row .el-slider :deep(.el-slider__marks-text) { font-size: 10px; color: #888; } */
.cooldown-chart-wrapper {
  margin-top: 12px; background: #1e2030; border-radius: 6px; padding: 8px;
}

body.light-theme .attack-speed-toggle { background: #f5f5f5; color: #c0392b; }
body.light-theme .attack-speed-toggle:hover { background: #e8e8e8; }
body.light-theme .attack-speed-calc { background: #f5f5f5; border-color: #ddd; }
body.light-theme .calc-result { background: #fff; }
body.light-theme .calc-label { color: #666; }
body.light-theme .calc-value { color: #107535; }
body.light-theme .slider-label { color: #666; }
body.light-theme .slider-row .el-slider :deep(.el-slider__runway) { background: #ddd; }
body.light-theme .slider-row .el-slider :deep(.el-slider__marks-text) { color: #999; }
body.light-theme .cooldown-chart-wrapper { background: #fff; }
body.light-theme .pct-pos { color: #16a34a; }
body.light-theme .pct-neg { color: #dc2626; }

/* Effect text color markers */
.zvg { color: #22c55e; }
.zvr { color: #ef4444; }
.zvp { color: #a855f7; }
body.light-theme .zvg { color: #107535; }
body.light-theme .zvr { color: #dc2626; }
body.light-theme .zvp { color: #9333ea; }
</style>
