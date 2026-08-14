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

      <el-button v-if="activeTab === 'weapons'" class="filter-btn frames-toggle-btn"
        :class="{ 'frames-active': showFrames }" @click="showFrames = !showFrames">
        {{ S.frames }}
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
                  <span v-if="i > 0 && ss[1] > 0">+</span><span class="ws-scaling-pct">{{ (ss[1] * 100).toFixed(0)
                  }}%</span>
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
              <span class="ws-val">{{ formatCooldown(displayCooldown) }}</span>
              <span class="calc-reload">({{ S.tooltip }})</span>
              <span class="calc-reload-separator">/</span>
              <span class="ws-val">{{ formatCooldownFixed(totalCooldown, true) }}</span>
              <span class="calc-reload">({{ S.actual }})</span>
            </div>

            <div v-if="addlCooldownInfo" class="weapon-stat-row cooldown-row">
              <span class="ws-label">{{ S.cooldown }}</span>
              <template v-for="(seg, i) in addlCooldownInfo" :key="i">
                <span :class="seg.cls">{{ seg.text }}</span>
              </template>
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

            <div v-if="dpsData" class="weapon-stat-row">
              <span class="ws-label">DPS</span>
              <span class="ws-val" :class="{ 'curse-modified': curseEnabled }">{{ dpsData.dmg.toFixed(2) }}</span>
              <span v-if="dpsData.scaling.length" class="ws-scaling">
                (<template v-for="(ss, i) in dpsData.scaling" :key="i">
                  <span v-if="i > 0 && ss[1] > 0">+</span><span class="ws-scaling-pct">{{ ss[1].toFixed(1)
                  }}%</span>
                  <img v-if="getStatIcon(ss[0])" :src="getStatIcon(ss[0])" class="stat-inline-icon" />
                  <span v-else>{{ statTr(ss[0]) }}</span>
                </template>)/s
              </span>
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
              <div class="calc-line">
                <span class="calc-label">{{ S.tooltipCooldown }}:</span>
                <span class="calc-value">{{ formatCooldown(calculatedTooltipCooldown) }}</span>
                <template v-for="(seg, i) in cooldownSegments('tooltip')" :key="i">
                  <span :class="seg.cls">{{ seg.text }}</span>
                </template>
              </div>
              <div class="calc-line">
                <span class="calc-label">{{ S.actualCooldown }}:</span>
                <span class="calc-value">{{ formatCooldownFixed(calculatedCooldown, true) }}</span>
                <template v-for="(seg, i) in cooldownSegments('actual')" :key="i">
                  <span :class="seg.cls">{{ seg.text }}</span>
                </template>
                <span class="calc-pct"
                  :class="cooldownChangePct < 0 ? 'pct-neg' : cooldownChangePct > 0 ? 'pct-pos' : ''">(DPS
                  {{
                    cooldownChangePct >= 0 ? '+' : '' }}{{ cooldownChangePct.toFixed(0) }}%)</span>
              </div>
            </div>
            <div class="cooldown-chart-wrapper">
              <Line :data="chartData" :options="chartOptions" :plugins="[baseCooldownLinePlugin, currentPointPlugin]" />
            </div>
            <div class="slider-row">
              <label class="slider-label">{{ S.attackSpeed }}</label>
              <el-slider v-model="attackSpeedSlider" :min="-200" :max="500" :step="1" :marks="atkSpeedMarks"
                show-input />
            </div>
            <div v-if="activeWeaponData.type === 'melee'" class="slider-row">
              <label class="slider-label">{{ S.statRange }}
                <el-tooltip :content="S.rangeInfo" placement="top" :show-after="200">
                  <el-icon class="range-help-icon">
                    <QuestionFilled />
                  </el-icon>
                </el-tooltip>
              </label>
              <el-slider v-model="statRangeSlider" :min="-200" :max="200" :step="1" :marks="rangeMarks" show-input />
            </div>
            <div class="slider-row">
              <label class="slider-label">{{ S.weaponCount }}</label>
              <el-slider v-model="weaponCountSlider" :min="1" :max="6" :step="1" :marks="weaponCountMarks" show-input />
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
import { Search, Sort, User, Sunny, Moon, Box, Aim, ArrowDown, View, Hide, Close, QuestionFilled } from '@element-plus/icons-vue'
import { Line } from 'vue-chartjs'
import { Chart as ChartJS, LinearScale, PointElement, LineElement, Tooltip } from 'chart.js'

ChartJS.register(LinearScale, PointElement, LineElement, Tooltip)

const BASE = import.meta.env.MODE === 'production'
  ? 'https://cdn.jsdmirror.com/gh/mojimoon/brotato@v1.4.3/public/'
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
  bounce: '反弹', projectiles: '投射物', dmg: '伤害', dps: 'DPS',
  basePrice: '基础价格', perWave: '每波', wave: '波次',
  effects: '效果', startingWeapons: '起始武器', preferredTags: '偏好标签',
  unique: '独特', limited: '限制', clickToSee: '点击左侧查看详情',
  belowNightmare: '难5', nightmare: '噩梦', basePriceShort: '价格', 
  belowNightmareShort: '难5', nightmareShort: '噩梦',
  attackSpeedCalc: '攻速计算器', attackSpeed: '攻速', statRange: '范围', weaponCount: '武器数量', frames: '帧数',
  curse: '诅咒', clear: '清除筛选',
  tooltipCooldown: '显示冷却', actualCooldown: '实际冷却', tooltip: '显示', actual: '实际',
  rangeInfo: '玩家范围属性。实际加成减半（例如，150基础范围 + 100范围属性 → 200武器范围）'
} : {
  weapons: 'Weapons', items: 'Items', characters: 'Characters',
  search: 'Search...', all: 'All', tier: 'Rarity', type: 'Type',
  melee: 'Melee', ranged: 'Ranged', set: 'Set', source: 'Source',
  base: 'Base', baseGame: 'Base Game', tag: 'Tag', sort: 'Sort',
  default: 'Default', price: 'Price', showPrice: 'Show Price', on: 'On', off: 'Off',
  damage: 'Damage', crit: 'Crit', cooldown: 'Cooldown', knockback: 'Knockback',
  range: 'Range', accuracy: 'Accuracy', lifesteal: 'Lifesteal', piercing: 'Piercing',
  bounce: 'Bounce', projectiles: 'Projectiles', dmg: 'dmg', dps: 'DPS',
  basePrice: 'Base Price', perWave: '/wave', wave: 'Wave',
  effects: 'Effects', startingWeapons: 'Starting Weapons', preferredTags: 'Preferred Tags',
  unique: 'Unique', limited: 'Limited', clickToSee: 'Click to see details',
  belowNightmare: 'Danger 5', nightmare: 'Nightmare', basePriceShort: 'Price', 
  belowNightmareShort: 'D5', nightmareShort: 'NM',
  attackSpeedCalc: 'Attack Speed Calculator', attackSpeed: 'A.Spd', statRange: 'Range', weaponCount: 'Weapon Count', frames: 'Frames',
  curse: 'Curse', clear: 'Clear Filters',
  tooltipCooldown: 'Tooltip Cooldown', actualCooldown: 'Actual Cooldown', tooltip: 'Tooltip', actual: 'Actual',
  rangeInfo: 'Player range stat. Actual bonus is halved (e.g. 150 base range + 100 range stat → 200 weapon range)'
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
const weaponCountSlider = ref(6)
const showFrames = ref(false)

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
  const maxAtkSpd = 202
  const hasRange = activeWeaponData.value?.type === 'melee' && statRangeSlider.value !== 0
  const mainPoints = []
  const basePoints = []

  for (let atkSpd = minAtkSpd; atkSpd <= maxAtkSpd; atkSpd += 1) {
    mainPoints.push({ x: atkSpd, y: calculateCooldownWithAttackSpeed(stats, atkSpd, statRangeSlider.value, weaponCountSlider.value) })
    if (hasRange) {
      basePoints.push({ x: atkSpd, y: calculateCooldownWithAttackSpeed(stats, atkSpd, 0) })
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
    ctx.arc(x, y, 4, 0, Math.PI * 2)
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
        max: 202,
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

watch([showAttackSpeedCalc, attackSpeedSlider, statRangeSlider, weaponCountSlider, isDark], () => {
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

// Additional cooldown info for weapons with a reload, shown in the weapon
// panel's stats list. Composed as styled segments (mirrors cooldownSegments)
// so the parts break to a new line instead of squeezing on narrow screens.
const addlCooldownInfo = computed(() => {
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

// DPS = weapon panel (incl. scaling) divided by the actual attack cooldown.
// Weapons with a reload use an equivalent per-shot cooldown:
//   actual cooldown + (actual reload cooldown - actual cooldown) / shots
const dpsData = computed(() => {
  if (!displayStats.value) return null
  const stats = activeWeaponData.value?.stats
  const base = totalCooldown.value
  if (!base || base <= 0) return null
  let cd = base
  const reload = getReloadCooldowns(stats, 0)
  if (reload && reload.shots > 0) {
    cd = base + (reload.actual - base) / reload.shots
  }
  const dmg = displayStats.value.damage / cd
  const scaling = (displayStats.value.scaling_stats || []).map(([k, v]) => [k, (v * 100) / cd])
  return { dmg, cd, scaling }
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
const COOLDOWN_FPS = 60
const MIN_WEAPON_COOLDOWN_FRAMES = 2
const BASE_MELEE_ATTACK_DURATION = 0.2
// The reference workbook defaults to six equipped weapons for its cooldown
// randomization correction. Keep this explicit so a loadout setting can be
// threaded through later without changing the core formula.
const DEFAULT_WEAPON_COUNT = 6

const totalCooldown = computed(() => {
  const stats = activeWeaponData.value?.stats
  if (!stats) return 0
  return calculateCooldownWithAttackSpeed(stats, 0, 0, weaponCountSlider.value)
})

const displayCooldown = computed(() => {
  const stats = displayStats.value
  if (!stats) return 0
  return calculateTooltipCooldown(stats, 0, 0)
})

function formatCooldown(seconds) {
  if (seconds < 0.1) return seconds.toFixed(3) + 's'
  return seconds.toFixed(2) + 's'
}

function formatCooldownFixed(seconds, frameRange = false) {
  return seconds.toFixed(3) + 's' + (frameRange ? frameRangeSuffix() : '')
}

// Appends a frame-range suffix (e.g. " (7-15f)") to a cooldown value when the
// "Frames" toggle is on. The range is the true per-shot attack-interval spread
// from the game's cooldown randomization: rand_range(max(1, base - max_rand),
// base + max_rand) on the weapon-cooldown frames, plus the deterministic
// recoil/melee idle frames. max_rand = min(weaponCount * base / 5, weaponCount * 5).
function frameRangeSuffix() {
  if (!showFrames.value) return ''
  const wcf = currentWeaponCooldownFrames.value
  const count = weaponCountSlider.value
  const idle = currentRecoilIdleFrames.value
  const maxRand = Math.min((count * wcf) / 5.0, count * 5.0)
  const minF = Math.round(Math.max(1, wcf - maxRand) + idle)
  const maxF = Math.round(wcf + maxRand + idle)
  return ` (${minF}-${maxF}f)`
}

function getAttackSpeedFactor(attackSpeed) {
  const value = Number(attackSpeed)
  return Number.isFinite(value) ? value / 100 : 0
}

function getBaseRecoilDuration(stats) {
  const recoilDuration = Number(stats?.recoil_duration)
  return Number.isFinite(recoilDuration) ? recoilDuration : 0.1
}

// Matches DPS Calculator!D31: the game applies attack speed to the weapon
// cooldown in frames, truncates it, and never lets it go below two frames.
function getWeaponCooldownFrames(baseCooldownFrames, atkSpd) {
  const base = Number(baseCooldownFrames)
  if (!Number.isFinite(base)) return MIN_WEAPON_COOLDOWN_FRAMES

  const modified = atkSpd >= 0
    ? base / (1 + atkSpd)
    : base * (1 + Math.abs(atkSpd))
  return Math.max(MIN_WEAPON_COOLDOWN_FRAMES, Math.floor(modified))
}

function getRecoilDuration(stats, atkSpd) {
  const baseRecoil = getBaseRecoilDuration(stats)
  return atkSpd >= 0
    ? baseRecoil / (1 + atkSpd)
    : baseRecoil
}

// Matches DPS Calculator!U8/V8 for weapons with a reload cooldown.
function getReloadCooldowns(stats, attackSpeed) {
  const shots = Number(stats?.additional_cooldown_every_x_shots)
  const multiplier = Number(stats?.additional_cooldown_multiplier)
  if (!Number.isFinite(shots) || shots <= 0 || !Number.isFinite(multiplier) || multiplier <= 0) return null

  const atkSpd = getAttackSpeedFactor(attackSpeed)
  const weaponCooldownFrames = getWeaponCooldownFrames(stats.cooldown, atkSpd)
  const recoilDuration = getRecoilDuration(stats, atkSpd)
  const reloadWeaponCooldownFrames = weaponCooldownFrames * multiplier
  const tooltipRecoilFrames = Math.floor(recoilDuration * COOLDOWN_FPS)
  // ROUND here to match calculateCooldownWithAttackSpeed: the old
  // Math.floor(x * 60 + 1) over-counted exactly-integer recoil and skewed the
  // reload breakpoint the same way the main cooldown did.
  const trueRecoilFrames = Math.round(recoilDuration * COOLDOWN_FPS)

  return {
    shots,
    tooltip: reloadWeaponCooldownFrames / COOLDOWN_FPS + (tooltipRecoilFrames / COOLDOWN_FPS) * 2,
    actual: (reloadWeaponCooldownFrames + 1) / COOLDOWN_FPS + (trueRecoilFrames / COOLDOWN_FPS) * 2,
  }
}

// Matches DPS Calculator!F33. Range affects melee animation time only.
function getMeleeTiming(stats, atkSpd, statRange) {
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

function getMeleeAttackType(stats) {
  if (stats?.alternate_attack_type) return 'Swing/Thrust'
  if (stats?.attack_type === 1 || stats?.attack_type === 'Swing' || stats?.attack_type === 'sweep') return 'Swing'
  return 'Thrust'
}

function getMeleeAttackTypeFrameBonus(stats) {
  const attackType = getMeleeAttackType(stats)
  if (attackType === 'Swing') return 1
  if (attackType === 'Swing/Thrust') return 0.5
  return 0
}

// DPS Calculator!W36. This is the workbook's average correction for the
// randomized starting cooldown of a six-weapon loadout, expressed in frames.
function getWeaponRandomizationFrames(weaponCooldownFrames, weaponCount = DEFAULT_WEAPON_COUNT) {
  const count = Math.max(0, Number(weaponCount) || 0)
  const randomPercent = Math.min(0.2 * count, 1.2)
  if (randomPercent === 0) return 0

  const frameInterval = Math.min(randomPercent * weaponCooldownFrames, 5 * count)
  const rangeMin = Math.max(1, weaponCooldownFrames - frameInterval)
  const rangeMax = weaponCooldownFrames + frameInterval
  const average = (rangeMin + rangeMax) / 2
  const averageRounding = 0.5
  return average + averageRounding - weaponCooldownFrames
}

// Matches DPS Calculator!N6 (the value shown in the game's tooltip).
function calculateTooltipCooldown(stats, attackSpeed, statRange = 0) {
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

// Matches DPS Calculator!M6 (the true, frame-rounded attack cooldown).
function calculateCooldownWithAttackSpeed(stats, attackSpeed, statRange = 0, weaponCount = DEFAULT_WEAPON_COUNT) {
  if (!stats) return 0

  const atkSpd = getAttackSpeedFactor(attackSpeed)
  const weaponCooldownFrames = getWeaponCooldownFrames(stats.cooldown, atkSpd)
  // Recoil frames are ROUNDED, not floored after adding 1. The old
  // Math.floor(x * 60 + 1) added the buffer before rounding, which
  // over-counts exactly-integer recoil (0.05s -> 3.0 frames becomes 4) and
  // makes a 1% attack-speed gain look like a 3-frame breakpoint on SMG
  // instead of the true 1 frame (0.0495s -> 2.97 rounds back to 3).
  const recoilFrames = Math.round(getRecoilDuration(stats, atkSpd) * COOLDOWN_FPS)
  let trueCooldownFrames

  if (activeWeaponData.value?.type === 'melee') {
    const { attackDuration, backDuration } = getMeleeTiming(stats, atkSpd, statRange)
    // Same ROUND (not floor(x*60+1)) fix as the recoil frames: the workbook's
    // melee branch (DPS Calculator!M6) also applies ROUNDDOWN(Atk_Dur/2*60+1)
    // and ROUNDDOWN(Back_Dur*60+1); the +1 before rounding over-counts exactly.
    const attackDurationFrames = Math.round(attackDuration / 2 * COOLDOWN_FPS)
    const backDurationFrames = Math.round(backDuration * COOLDOWN_FPS)

    trueCooldownFrames = Math.floor(
      (weaponCooldownFrames + 1)
      + recoilFrames
      + attackDurationFrames
      + backDurationFrames
      + 1,
    )
    trueCooldownFrames += getMeleeAttackTypeFrameBonus(stats)
  } else {
    trueCooldownFrames = (weaponCooldownFrames + 1) + recoilFrames * 2
  }

  trueCooldownFrames += getWeaponRandomizationFrames(weaponCooldownFrames, weaponCount)
  return trueCooldownFrames / COOLDOWN_FPS
}

const calculatedCooldown = computed(() => {
  const stats = activeWeaponData.value?.stats
  if (!stats) return 0
  return calculateCooldownWithAttackSpeed(
    stats,
    attackSpeedSlider.value,
    statRangeSlider.value,
    weaponCountSlider.value
  )
})

const calculatedTooltipCooldown = computed(() => {
  const stats = activeWeaponData.value?.stats
  if (!stats) return 0
  return calculateTooltipCooldown(
    stats,
    attackSpeedSlider.value,
    statRangeSlider.value,
  )
})

const calculatedReloadCooldowns = computed(() => {
  const stats = activeWeaponData.value?.stats
  if (!stats) return null
  return getReloadCooldowns(stats, attackSpeedSlider.value)
})

// Frame components of the *current* weapon + sliders, used by frameRangeSuffix
// to build the true per-shot attack-interval spread.
const currentWeaponCooldownFrames = computed(() => {
  const stats = activeWeaponData.value?.stats
  if (!stats) return 0
  return getWeaponCooldownFrames(stats.cooldown, getAttackSpeedFactor(attackSpeedSlider.value))
})

const currentRecoilIdleFrames = computed(() => {
  const stats = activeWeaponData.value?.stats
  if (!stats) return 0
  const atkSpd = getAttackSpeedFactor(attackSpeedSlider.value)
  if (activeWeaponData.value?.type === 'melee') {
    const { attackDuration, backDuration } = getMeleeTiming(stats, atkSpd, statRangeSlider.value)
    return (
      Math.round(attackDuration / 2 * COOLDOWN_FPS) +
      Math.round(backDuration * COOLDOWN_FPS) +
      getMeleeAttackTypeFrameBonus(stats)
    )
  }
  return Math.round(getRecoilDuration(stats, atkSpd) * COOLDOWN_FPS) * 2
})

// Build the trailing segments for a cooldown line so each piece can be
// styled independently (mirrors how addlCooldownInfo composes its parts).
// kind: 'tooltip' | 'actual'. Returns [{ text, cls }, ...] for concatenation.
function cooldownSegments(kind) {
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
    const equiv = calculatedCooldown.value + (reload.actual - calculatedCooldown.value) / reload.shots
    segs.push({ text: '/', cls: 'calc-reload-separator' })
    segs.push({ text: isZh.value ? '等效' : 'equiv', cls: 'calc-reload' })
    segs.push({ text: formatCooldownFixed(equiv), cls: 'calc-value' })
  }
  return segs
}

const cooldownChangePct = computed(() => {
  if (totalCooldown.value === 0 || calculatedCooldown.value === 0) return 0
  return (totalCooldown.value / calculatedCooldown.value - 1) * 100
})

// const atkSpeedMarks = { [-200]: '-200', [-100]: '-100', [0]: '0', [100]: '100', [200]: '200', [300]: '300', [400]: '400', [500]: '500' }
const atkSpeedMarks = computed(() => isMobile.value ? { [-200]: '-200', [0]: '0', [100]: '100', [300]: '300', [500]: '500' } : { [-200]: '-200', [-100]: '-100', [0]: '0', [100]: '100', [200]: '200', [300]: '300', [400]: '400', [500]: '500' })
const rangeMarks = { [-200]: '-200', [-100]: '-100', [0]: '0', [100]: '100', [200]: '200' }
const weaponCountMarks = { 1: '1', 2: '2', 3: '3', 4: '4', 5: '5', 6: '6' }

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

/* ===================================================================
   Theme tokens (dark = defaults). Light theme only overrides values.
   Identical colors across the app are merged into one token.
   =================================================================== */
:root {
  /* page & layout */
  --bg-app: #1a1d28;
  --bg-header: #151822;
  /* surfaces */
  --bg-card: #22253a;
  --bg-row: #22253a;
  --bg-alt: #22253a;
  --bg-inset: #1e2030;
  --bg-icon: #1e2030;
  --bg-table-head: #1e2030;
  --bg-hover: #282c44;
  --bg-alt-hover: #282c44;
  --bg-dropdown-hover: #2e3148;
  --bg-tabs-hover: #393d58;
  --bg-filter-hover: #2a2d3a;
  --bg-btn: #252836;
  --bg-btn-hover: #333648;
  --bg-tag: #2a2d44;
  --bg-tag-hover: #3a3d58;
  --bg-tier: #22253a;
  --bg-tier-disabled: #22253a;
  /* badges */
  --badge-bg: #3a3d4e;
  --badge-fg: #fff;
  /* borders */
  --border: #3a3d4e;
  --border-input: #3a3d4e;
  --border-subtle: #2a2d3a;
  --border-soft: #2a2d3a;
  --border-strong: #444;
  --border-hover: #5a5d6e;
  --border-tabs-hover: #4a4d5e;
  --border-active: #5a5d6e;
  /* text */
  --text: #ccc;
  --text-strong: #eee;
  --text-muted: #bbb;
  --text-faint: #888;
  --text-fainter: #777;
  --text-bright: #fff;
  --text-btn: #ccc;
  /* accents (same in both themes unless noted) */
  --accent: #ff3d3d;
  --accent-gold: #f39c12;
  --accent-green: #4ade80;
  --accent-red: #f87171;
  --accent-blue: #2980b9;
  --accent-purple: #a855f7;
  --curse: #c084fc;
  --curse-deep: #7b3fa3;
  --nightmare: #ff3d3d;
  --price-final: #f39c12;
  --badge-red: #c0392b;
  --badge-orange: #d35400;
  /* value-state (gold) shared by filter/sort buttons */
  --val-text: #fff4cf;
  --val-border: #d2a64a;
  --val-shadow: 0 0 0 1px rgba(255, 196, 74, 0.12);
  /* misc semantic text */
  --tag-fg: #bbb;
  --tag-tooltip-line: #aaa;
  --set-tooltip-line: #ccc;
  --set-badge-fg: #ccc;
  --set-badge-hover-bg: #4a4d5e;
  --attack-type-fg: #bbb;
  --tier-fg: #888;
  --tier-hover-bg: transparent;
  --tier-hover-fg: #fff;
  --tier-hover-border: #555;
  --tier-active-fg: #fff;
  --eff-prefix: #777;
  --marks-text: #888;
  --slider-marks: #888;
  --stop-bg: #5a5d6e;
  --scrollbar-thumb: #3a3d4e;
  --scrollbar-thumb-hover: #5a5d6e;
  --caret: #888;
  --range-icon: #888;
  --dropdown-empty: #777;
  --dropdown-item-fg: #bbb;
  --el-tag-bg: #2a2d3a;
  --dropdown-shadow: 0 4px 12px rgba(0, 0, 0, 0.4);
  /* tags (pet / structure) */
  --tag-pet-bg: #1e3a1e; --tag-pet-fg: #6ee76e;
  --tag-pet-bg-hover: #2a4a2a; --tag-pet-fg-hover: #9ef79e;
  --tag-struct-bg: #3a2a1a; --tag-struct-fg: #ffb74d;
  --tag-struct-bg-hover: #4a3520; --tag-struct-fg-hover: #ffcc80;
  /* effect markers */
  --mark-green: #22c55e; --mark-red: #ef4444; --mark-purple: #a855f7;
  /* weapon scaling text */
  --scaling: #eae2b0; --scaling-pct: #ddd;
  /* curse toggle (off / active) */
  --curse-off-bg: #2a2d3a; --curse-off-border: #3a3d4e; --curse-off-fg: #888;
  --curse-active-bg: #3d1f5e; --curse-active-border: #7b3fa3; --curse-active-fg: #c084fc;
}

html { background: var(--bg-app); }
body { background: var(--bg-app); color: var(--text); font-family: 'Segoe UI', system-ui, sans-serif; transition: background .2s, color .2s; }

.app-container { max-width: 1400px; margin: 0 auto; height: 100vh; overflow: hidden; display: flex; flex-direction: column; }

/* Header */
.header { display: flex; align-items: center; justify-content: space-between; padding: 10px 24px; background: var(--bg-header); border-bottom: 2px solid var(--accent); }
.title { font-size: 22px; font-weight: 800; color: var(--accent); letter-spacing: 2px; text-shadow: 0 0 20px rgba(255, 61, 61, 0.15); }
.author-link { font-size: 12px; font-weight: 500; color: var(--text-muted); margin-left: 8px; }
.header-actions { display: flex; gap: 8px; align-items: center; }
.header-btn { background: var(--bg-btn) !important; border: 1px solid var(--border-input) !important; color: var(--text-btn) !important; font-size: 13px; transition: all .2s; }
.header-btn:hover { background: var(--bg-btn-hover) !important; color: var(--text-bright) !important; border-color: var(--border-hover) !important; }
.lang-btn { font-weight: 700; font-size: 14px; min-width: 36px; }

/* Tabs — card style */
.main-tabs { background: var(--bg-header); padding: 0 24px; }
.main-tabs :deep(.el-tabs__header) { margin: 0; }
.main-tabs :deep(.el-tabs__nav-wrap::after) { display: none; }
.el-tabs--card > .el-tabs__header { border-bottom: 1px solid var(--border-subtle); background: var(--bg-header); }
.el-tabs--card > .el-tabs__header .el-tabs__nav { border: none; }
.el-tabs--card > .el-tabs__header .el-tabs__item {
  color: var(--text-muted) !important; height: 42px; line-height: 42px; font-size: 14px;
  background: var(--bg-card); border: 1px solid var(--border); border-bottom: none;
  margin-right: 2px; border-radius: 8px 8px 0 0; padding: 0 18px;
  transition: background .15s, color .15s, border-color .15s;
}
.el-tabs--card > .el-tabs__header .el-tabs__item:first-child { border-left: 1px solid var(--border) !important; }
.el-tabs--card > .el-tabs__header .el-tabs__item:hover { color: var(--text-strong) !important; background: var(--bg-tabs-hover); border-color: var(--border-tabs-hover); }
.el-tabs--card > .el-tabs__header .el-tabs__item.is-active { color: var(--accent) !important; background: var(--bg-app); border-color: var(--border-active); }
.el-tabs--card > .el-tabs__header .el-tabs__active-bar { background: var(--accent); }

/* Filters */
.filters { display: flex; gap: 10px; padding: 10px 24px; background: var(--bg-app); border-bottom: 1px solid var(--border-subtle); flex-wrap: wrap; align-items: center; }
.search-input { flex: 1; max-width: 280px; }

/* Filter dropdown buttons */
.filter-btn {
  background: var(--bg-card) !important; border: 1px solid var(--border-input) !important; color: var(--text-muted) !important;
  font-size: 13px !important; height: 32px !important; padding: 0 10px !important;
  min-width: 110px; justify-content: center; gap: 6px;
  border-radius: 6px !important;
  transition: all .15s !important;
}
.filter-btn:hover { background: var(--bg-filter-hover) !important; border-color: var(--border-hover) !important; color: var(--text-bright) !important; }
.filter-btn.has-value {
  color: var(--val-text) !important;
  border-color: var(--val-border) !important;
  box-shadow: var(--val-shadow);
}
/* Fancy action buttons (sort / price toggle) — shared layout, colors via vars */
.sort-btn, .price-toggle-btn {
  gap: 8px; min-width: 122px; border-style: solid !important; font-weight: 700; position: relative;
  color: var(--btn-text) !important;
  border-color: var(--btn-border) !important;
  background: var(--btn-bg) !important;
  box-shadow: var(--btn-shadow);
}
.sort-btn:not(.has-value), .price-toggle-btn:not(.has-value) {
  color: var(--btn-text-off) !important;
  border-color: var(--btn-border-off) !important;
  background: var(--btn-bg-off) !important;
  box-shadow: var(--btn-shadow-off);
}
.sort-btn.has-value, .price-toggle-btn.has-value {
  color: var(--btn-text-val) !important;
  border-color: var(--btn-border-val) !important;
  box-shadow: var(--btn-shadow-val);
}
.sort-btn:hover, .price-toggle-btn:hover { border-color: var(--btn-border-hover) !important; }
.sort-btn:not(.has-value):hover, .price-toggle-btn:not(.has-value):hover {
  background: var(--btn-bg-hover) !important; color: var(--btn-text-hover) !important;
}
.sort-btn.has-value:hover, .price-toggle-btn.has-value:hover {
  color: var(--btn-text-val-hover) !important;
  border-color: var(--btn-border-val-hover) !important;
  box-shadow: var(--btn-shadow-val-hover);
}
.sort-btn :deep(.el-icon) { color: inherit; }
.sort-dropdown { margin-left: auto; }
.clear-btn { color: var(--text-faint); padding: 8px !important; min-width: 0; }
.clear-btn:hover { color: var(--badge-red) !important; border-color: var(--badge-red) !important; }

/* Sort button — amber/gold palette */
.sort-btn {
  --btn-text: #cfd5e3; --btn-border: #43485b; --btn-bg: linear-gradient(180deg,#25283a 0%,#1e2131 100%);
  --btn-shadow: 0 0 0 1px rgba(255,255,255,.03), 0 6px 14px rgba(0,0,0,.16);
  --btn-text-off: #9da5b7; --btn-border-off: #363b4d; --btn-bg-off: linear-gradient(180deg,#1f2230 0%,#181b28 100%);
  --btn-shadow-off: 0 0 0 1px rgba(255,255,255,.02), 0 4px 10px rgba(0,0,0,.14);
  --btn-border-hover: #8f97ad;
  --btn-bg-hover: linear-gradient(180deg,#262b3b 0%,#1e2230 100%); --btn-text-hover: #c5ccda;
  --btn-text-val: #fff4cf; --btn-border-val: #d2a64a;
  --btn-shadow-val: 0 0 0 1px rgba(255,196,74,.12), 0 0 0 1px rgba(255,196,74,.08) inset;
  --btn-text-val-hover: #fff7dd; --btn-border-val-hover: #e0b152;
  --btn-shadow-val-hover: 0 0 0 1px rgba(255,196,74,.16), 0 0 0 1px rgba(255,196,74,.12) inset;
}
/* Price toggle button — green palette */
.price-toggle-btn {
  --btn-text: #cfd5e3; --btn-border: #4a4f63; --btn-bg: linear-gradient(180deg,#25283a 0%,#1e2131 100%);
  --btn-shadow: 0 0 0 1px rgba(255,255,255,.04), 0 6px 14px rgba(0,0,0,.18);
  --btn-text-off: #9197aa; --btn-border-off: #2f3445; --btn-bg-off: linear-gradient(180deg,#1c1e28 0%,#161821 100%);
  --btn-shadow-off: 0 0 0 1px rgba(255,255,255,.02), 0 4px 10px rgba(0,0,0,.14);
  --btn-border-hover: #7a8099;
  --btn-bg-hover: linear-gradient(180deg,#242838 0%,#1b1e2b 100%); --btn-text-hover: #c1c7d8;
  --btn-text-val: #e8ffd1; --btn-border-val: #5d8a4b;
  --btn-shadow-val: 0 0 0 1px rgba(110,255,130,.12), 0 0 0 1px rgba(110,255,130,.08) inset;
  --btn-text-val-hover: #f5ffd8; --btn-border-val-hover: #6ea054;
  --btn-shadow-val-hover: 0 0 0 1px rgba(110,255,130,.16), 0 0 0 1px rgba(110,255,130,.1) inset;
}

/* Main */
.main-content { position: relative; flex: 1 1 auto; min-height: 0; overflow: hidden; }

/* Grid */
.grid-panel {
  position: absolute; left: 0; top: 0; bottom: 0; width: 50%; overflow-y: auto; padding: 10px;
  display: grid; grid-template-columns: repeat(auto-fill, minmax(90px, 1fr));
  gap: 5px; align-content: start; background: var(--bg-app);
}
.grid-item {
  background: var(--bg-card); border-radius: 8px; padding: 8px 4px; cursor: pointer;
  transition: all .2s ease; display: flex; flex-direction: column; align-items: center; gap: 4px; position: relative;
  border: 2px solid transparent;
}
.grid-item:hover { transform: translateY(-2px); box-shadow: 0 4px 16px rgba(0,0,0,.35); border-color: var(--border); }
.grid-item.selected { box-shadow: 0 0 16px rgba(255,255,255,0.12); transform: translateY(-1px); }
.item-icon {
  width: 52px; height: 52px; display: flex; align-items: center; justify-content: center;
  background: var(--bg-icon); border-radius: 8px; overflow: hidden; border: 2px solid var(--border);
  transition: border-color .2s;
}
.item-icon img { max-width: 44px; max-height: 44px; image-rendering: pixelated; }
.item-name-text { font-size: 12px; font-weight: 600; text-align: center; max-width: 80px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.item-price-badge {
  position: absolute; top: 3px; left: 3px; font-size: 12px; line-height: 1;
  padding: 2px 5px; border-radius: 4px; font-weight: 500; z-index: 1;
  background: var(--badge-bg); color: var(--badge-fg);
  box-shadow: 0 1px 3px rgba(0,0,0,.35); pointer-events: none;
}
.item-dlc-badge { position: absolute; top: 3px; right: 3px; font-size: 11px; padding: 1px 3px; border-radius: 3px; background: var(--accent-purple); color: #fff; font-weight: 500; }

/* Detail Panel */
.detail-panel {
  position: absolute; right: 0; top: 0; bottom: 0; left: 50%; overflow-y: auto; padding: 20px;
  background: var(--bg-inset); border-left: 2px solid var(--border-subtle);
}
.empty-panel { display: flex; align-items: center; justify-content: center; }
.detail-header { display: flex; gap: 14px; align-items: center; margin-bottom: 14px; padding-bottom: 14px; border-bottom: 1px solid var(--border-soft); }
.detail-icon-wrap {
  width: 68px; height: 68px; border-radius: 12px; display: flex; align-items: center; justify-content: center;
  background: var(--bg-icon); border: 2px solid var(--border); overflow: hidden; flex-shrink: 0;
}
.detail-icon-wrap img { max-width: 56px; max-height: 56px; image-rendering: pixelated; }
.detail-title-wrap { flex: 1; min-width: 0; }
.detail-title-wrap h2 { font-size: 20px; margin-bottom: 4px; }
.detail-badges { display: flex; gap: 6px; flex-wrap: wrap; align-items: center; margin-bottom: 2px; }
.type-badge { font-size: 11px; padding: 3px 8px; border-radius: 4px; color: #fff; line-height: 1.4; font-weight: 600; }
.type-badge.melee { background: var(--badge-red); }
.type-badge.ranged { background: var(--accent-blue); }
.dlc-badge { font-size: 11px; padding: 3px 8px; border-radius: 4px; background: var(--accent-purple); color: #fff; font-weight: 600; }
.set-badge { font-size: 11px; padding: 3px 8px; border-radius: 4px; background: var(--badge-bg); color: var(--set-badge-fg); cursor: help; font-weight: 600; transition: background .15s; }
.set-badge:hover { background: var(--set-badge-hover-bg); }

/* Tier Tabs */
.tier-tabs { display: flex; gap: 4px; margin-bottom: 12px; }
.tier-tab { flex: 1; padding: 8px 0; border: 2px solid var(--border-strong); background: var(--bg-tier); color: var(--tier-fg); border-radius: 6px; cursor: pointer; font-size: 13px; font-weight: 700; transition: all .2s; }
.tier-tab:hover:not(.disabled) { color: var(--tier-hover-fg); border-color: var(--tier-hover-border); background: var(--tier-hover-bg); }
.tier-tab.active { color: var(--tier-active-fg) !important; }
.tier-tab.disabled { opacity: 0.25; cursor: default; border-color: var(--border-subtle) !important; background: var(--bg-tier-disabled) !important; color: var(--tier-fg) !important; }

/* Set tooltip */
.set-tooltip-content { font-size: 12px; line-height: 1.6; }
.set-tooltip-name { font-weight: bold; margin-bottom: 4px; color: var(--text-bright); }
.set-tooltip-line { color: var(--set-tooltip-line); }

/* Weapon Stat Rows */
.detail-section { margin-top: 10px; }
.section-title { font-size: 12px; color: var(--accent); margin-bottom: 8px; text-transform: uppercase; letter-spacing: 1px; font-weight: 700; }
.weapon-stat-row { display: flex; flex-wrap: wrap; align-items: center; gap: 8px; padding: 7px 12px; background: var(--bg-row); border-radius: 6px; margin-bottom: 4px; transition: background .15s; }
.cooldown-row { gap: 6px; }
.weapon-stat-row:hover { background: var(--bg-hover); }
.ws-label { font-size: 14px; color: var(--text-muted); min-width: 70px; }
.ws-val { font-size: 15px; color: var(--text-strong); font-weight: 600; }
.ws-val.curse-modified { color: var(--curse); text-shadow: 0 0 6px rgba(139, 92, 246, 0.3); }
.crit-dmg { color: var(--accent-gold); font-size: 14px; }
.ws-scaling { font-size: 15px; color: var(--scaling); }
.ws-scaling-pct { color: var(--scaling-pct); }
.ws-attack-type { font-size: 13px; color: var(--attack-type-fg); font-weight: 400; margin-left: 4px; }
.stat-inline-icon { width: 16px; height: 16px; vertical-align: middle; image-rendering: pixelated; margin: 0 1px; }
.stat-prefix-icon { width: 13px; height: 13px; vertical-align: middle; image-rendering: pixelated; }

/* Curse Section */
.curse-section { margin-top: 12px; padding: 12px 16px; background: var(--bg-row); border-radius: 8px; border: 1px solid var(--border-subtle); }
.curse-row { display: flex; align-items: center; gap: 12px; }
.curse-toggle-btn {
  font-size: 15px; font-weight: 600;
  background: var(--curse-off-bg) !important; border: 1px solid var(--curse-off-border) !important; color: var(--curse-off-fg) !important;
  transition: all 0.2s;
}
.curse-toggle-btn.curse-active {
  background: var(--curse-active-bg) !important; border-color: var(--curse-active-border) !important; color: var(--curse-active-fg) !important;
  box-shadow: 0 0 8px rgba(139, 92, 246, 0.3);
}
.curse-slider { flex: 1; min-width: 150px; --el-slider-height: 4px; }
.curse-slider :deep(.el-slider__runway) { background: var(--curse-off-bg); }
.curse-slider :deep(.el-slider__bar) { background: var(--curse-deep); }
.curse-slider :deep(.el-slider__button) { width: 14px; height: 14px; border-color: var(--curse-deep); }
.curse-slider :deep(.el-input-number) { width: 80px; }

.frames-toggle-btn {
  font-weight: 700; min-width: 72px;
  background: var(--bg-alt) !important; border: 1px solid var(--border-hover) !important; color: var(--text) !important;
  transition: all 0.2s;
}
.frames-toggle-btn.frames-active {
  background: rgba(34, 197, 94, 0.15) !important;
  border-color: #22c55e !important; color: #22c55e !important;
  box-shadow: 0 0 8px rgba(34, 197, 94, 0.3);
}
body.light-theme .frames-toggle-btn.frames-active {
  background: #ecfdf3 !important; color: #15803d !important; border-color: #16a34a !important;
}

/* Price Section */
.price-section { margin-top: 12px; padding: 14px 16px; background: var(--bg-row); border-radius: 8px; border: 1px solid var(--border-subtle); }
.price-toggle { display: flex; align-items: center; gap: 8px; padding: 10px 12px; background: var(--bg-alt); border-radius: 6px; cursor: pointer; font-size: 14px; color: var(--accent-gold); transition: background .15s; }
.price-toggle:hover { background: var(--bg-alt-hover); }
.price-table { width: 100%; border-collapse: collapse; margin-bottom: 12px; font-size: 13px; margin-top: 12px; }
.price-table th, .price-table td { padding: 6px 10px; text-align: center; border: 1px solid var(--border-subtle); }
.price-table th { color: var(--text-faint); font-weight: 600; background: var(--bg-table-head); }
.price-table td { color: var(--text); }
.price-table .price-bold { font-weight: 700; color: var(--text-bright); }
.price-base { font-size: 16px; font-weight: 700; color: var(--text-bright); }
.price-final { color: var(--price-final) !important; }
.price-final-nightmare { color: var(--nightmare) !important; }
.price-icon { width: 18px; height: 18px; image-rendering: pixelated; vertical-align: middle; }
.price-label { font-size: 13px; color: var(--text-muted); }

.price-slider-row { display: flex; align-items: center; gap: 12px; }
.wave-label { flex-shrink: 0; white-space: nowrap; font-size: 13px; color: var(--text-muted); margin-right: 8px; }
.price-slider { --el-slider-height: 4px; flex: 1; min-width: 0; }
.price-slider :deep(.el-slider__runway) { background: var(--border-subtle); margin: 0; }
.price-slider :deep(.el-slider__bar) { background: var(--accent); }
.price-slider :deep(.el-slider__button) { width: 14px; height: 14px; border-color: var(--accent); }
.price-slider :deep(.el-slider__marks-text) { font-size: 10px; color: var(--marks-text); margin-top: 6px; }
.price-slider :deep(.el-slider__input) { display: none; }
.price-slider :deep(.el-slider__stop) { width: 6px; height: 6px; border-radius: 50%; background: var(--stop-bg); }

/* Effects */
.effects-list { display: flex; flex-direction: column; gap: 4px; }
.effect-item { padding: 7px 10px; border-radius: 6px; font-size: 13px; background: var(--bg-row); color: var(--text); line-height: 1.5; display: flex; align-items: baseline; gap: 6px; transition: background .15s; }
.curse-extra-effect { border-left: 3px solid var(--curse); padding-left: 8px; }
.curse-extra-effect .eff-prefix { color: var(--curse); }
.effect-item:hover { background: var(--bg-hover); }
.eff-prefix { flex-shrink: 0; width: 8px; text-align: center; color: var(--eff-prefix); display: flex; align-items: center; justify-content: center; line-height: 1; }
.eff-text { flex: 1; min-width: 0; }

/* Starting Weapons Grid */
.starting-weapons-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(80px, 1fr)); gap: 5px; }
.starting-weapon-card { cursor: pointer; }

/* Tags */
.tags-wrap { display: flex; flex-wrap: wrap; gap: 5px; }
.tag-badge { font-size: 11px; padding: 4px 10px; border-radius: 4px; background: var(--bg-tag); color: var(--tag-fg); font-weight: 600; line-height: 1.4; display: inline-block; transition: all .15s; }
.tag-badge.clickable { cursor: pointer; }
.tag-badge.clickable:hover { background: var(--bg-tag-hover); color: var(--text-bright); }
.limit-badge { font-size: 11px; padding: 4px 10px; border-radius: 4px; color: #fff; font-weight: 600; line-height: 1.4; }
.limit-badge.unique { background: var(--badge-red); }
.limit-badge.limited { background: var(--badge-orange); }
.tag-pet { background: var(--tag-pet-bg); color: var(--tag-pet-fg); }
.tag-pet:hover { background: var(--tag-pet-bg-hover) !important; color: var(--tag-pet-fg-hover) !important; }
.tag-structure_real { background: var(--tag-struct-bg); color: var(--tag-struct-fg); }
.tag-structure_real:hover { background: var(--tag-struct-bg-hover) !important; color: var(--tag-struct-fg-hover) !important; }
.tag-tooltip-content { font-size: 12px; line-height: 1.6; max-width: 320px; }
.tag-tooltip-name { font-weight: bold; margin-bottom: 2px; color: var(--text-bright); }
.tag-tooltip-line { color: var(--tag-tooltip-line); word-break: break-all; }

/* ---- Element Plus Dark Overrides ---- */
.el-input__wrapper { background-color: var(--bg-card) !important; border-color: var(--border-input) !important; box-shadow: none !important; }
.el-input__wrapper:hover { border-color: var(--border-hover) !important; }
.el-input.is-focus .el-input__wrapper { border-color: var(--accent) !important; box-shadow: 0 0 0 1px var(--accent) inset !important; }
.el-input__inner { color: var(--text) !important; }
.el-input__inner::placeholder { color: var(--text-fainter) !important; }
.el-select .el-select__caret { color: var(--caret) !important; }
.el-select .el-input .el-input__suffix .el-icon { color: var(--caret) !important; }
.el-select .el-input__wrapper { background-color: var(--bg-card) !important; border-color: var(--border-input) !important; }
.el-select .el-tag { background-color: var(--el-tag-bg) !important; border-color: var(--border) !important; color: var(--text-muted) !important; }
.el-input__inner:-webkit-autofill,
.el-input__inner:-webkit-autofill:hover,
.el-input__inner:-webkit-autofill:focus { -webkit-box-shadow: 0 0 0 30px var(--bg-card) inset !important; -webkit-text-fill-color: var(--text) !important; transition: background-color 5000s ease-in-out 0s; }

/* Dropdown popper */
.dark-dropdown, .dark-dropdown.el-popper { background-color: var(--bg-card) !important; border: 1px solid var(--border-input) !important; border-radius: 6px !important; box-shadow: var(--dropdown-shadow) !important; }
.dark-dropdown .el-select-dropdown, .dark-dropdown .el-scrollbar, .dark-dropdown .el-scrollbar__wrap, .dark-dropdown .el-scrollbar__view,
.dark-dropdown .el-select-dropdown__list, .dark-dropdown .el-dropdown-menu { background-color: var(--bg-card) !important; max-height: 540px; overflow-y: auto; }
.dark-dropdown .el-popper__arrow::before { background: var(--bg-card) !important; border-color: var(--border-input) !important; }
.dark-dropdown .el-select-dropdown__item { color: var(--dropdown-item-fg) !important; padding: 8px 14px !important; font-size: 13px; transition: background .12s, color .12s; display: flex; align-items: center; min-height: 32px; line-height: 1.2; }
.dark-dropdown .el-select-dropdown__item:hover { background-color: var(--bg-dropdown-hover) !important; color: var(--text-bright) !important; }
.dark-dropdown .el-select-dropdown__item.is-selected, .dark-dropdown .el-select-dropdown__item.selected { color: var(--accent) !important; font-weight: 600; }
.dark-dropdown .el-select-dropdown__item.is-hovering { background-color: var(--bg-dropdown-hover) !important; }
.dark-dropdown .el-select-dropdown__empty { color: var(--dropdown-empty) !important; padding: 10px; }
.dark-dropdown .el-dropdown-menu__item {
  color: var(--dropdown-item-fg) !important;
  padding: 8px 14px !important;
  font-size: 13px;
  background-color: transparent !important;
  transition: background-color .18s ease, color .18s ease, box-shadow .18s ease, transform .18s ease;
  line-height: 1.2;
}
.dark-dropdown .el-dropdown-menu__item:hover,
.dark-dropdown .el-dropdown-menu__item:focus,
.dark-dropdown .el-dropdown-menu__item:active {
  background-color: var(--bg-dropdown-hover) !important;
  color: var(--text-bright) !important;
}
.dark-dropdown .el-dropdown-menu__item.is-active-opt {
  background-color: rgba(255, 61, 61, 0.08) !important;
  color: var(--accent) !important;
  font-weight: 600;
}
.el-popper.is-dark { background: var(--bg-card) !important; border: 1px solid var(--border-input) !important; color: var(--text) !important; }
.is-active-lang { color: var(--accent) !important; font-weight: 600; }

/* Scrollbar */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: var(--bg-app); }
::-webkit-scrollbar-thumb { background: var(--scrollbar-thumb); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: var(--scrollbar-thumb-hover); }

/* ==================== Light Theme ==================== */
html.light-theme, body.light-theme {
  --bg-app: #f0f2f5;
  --bg-header: #fff;
  --bg-card: #fff;
  --bg-row: #f0f2f5;
  --bg-alt: #f5f5f5;
  --bg-inset: #fff;
  --bg-icon: #f5f6f8;
  --bg-table-head: #e8eaed;
  --bg-hover: #e8eaed;
  --bg-alt-hover: #e8e8e8;
  --bg-dropdown-hover: #f0f2f5;
  --bg-tabs-hover: #d5d8de;
  --bg-filter-hover: #f0f2f5;
  --bg-btn: #e8eaed;
  --bg-btn-hover: #d8dade;
  --bg-tag: #ddd;
  --bg-tag-hover: #ccc;
  --bg-tier: #e2e4e8;
  --bg-tier-disabled: #eee;
  --badge-bg: #ddd;
  --badge-fg: #000;
  --border: #ccc;
  --border-input: #bbb;
  --border-subtle: #ccc;
  --border-soft: #ddd;
  --border-strong: #bbb;
  --border-hover: #999;
  --border-tabs-hover: #aaa;
  --border-active: #bbb;
  --text: #222;
  --text-strong: #111;
  --text-muted: #444;
  --text-faint: #777;
  --text-fainter: #666;
  --text-bright: #111;
  --text-btn: #333;
  --accent: #ff3d3d;
  --accent-gold: #c0392b;
  --accent-green: #107535;
  --accent-red: #dc2626;
  --accent-blue: #2980b9;
  --accent-purple: #9333ea;
  --curse: #7c3aed;
  --curse-deep: #a78bfa;
  --nightmare: #e53935;
  --price-final: #1e88e5;
  --badge-red: #c0392b;
  --badge-orange: #e65100;
  --val-text: #7c5a06;
  --val-border: #c59c43;
  --val-shadow: 0 0 0 1px rgba(205, 155, 44, 0.14);
  --tag-fg: #333;
  --tag-tooltip-line: #555;
  --set-tooltip-line: #555;
  --set-badge-fg: #333;
  --set-badge-hover-bg: #ccc;
  --attack-type-fg: #666;
  --tier-fg: #666;
  --tier-hover-bg: #d5d8de;
  --tier-hover-fg: #333;
  --tier-hover-border: #aaa;
  --tier-active-fg: #fff;
  --eff-prefix: #777;
  --marks-text: #888;
  --slider-marks: #999;
  --stop-bg: #aaa;
  --scrollbar-thumb: #bbb;
  --scrollbar-thumb-hover: #999;
  --caret: #555;
  --range-icon: #aaa;
  --dropdown-empty: #777;
  --dropdown-item-fg: #222;
  --el-tag-bg: #e8eaed;
  --dropdown-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  --tag-pet-bg: #c8e6c9; --tag-pet-fg: #1b5e20;
  --tag-pet-bg-hover: #a5d6a7; --tag-pet-fg-hover: #0d3b0d;
  --tag-struct-bg: #fff3e0; --tag-struct-fg: #e65100;
  --tag-struct-bg-hover: #ffe0b2; --tag-struct-fg-hover: #bf360c;
  --mark-green: #107535; --mark-red: #dc2626; --mark-purple: #9333ea;
  --scaling: #333; --scaling-pct: #333;
  --curse-off-bg: #fff7ed; --curse-off-border: #f59e0b; --curse-off-fg: #b45309;
  --curse-active-bg: #ede9fe; --curse-active-border: #a78bfa; --curse-active-fg: #7c3aed;
  --curse-active-shadow: 0 0 6px rgba(245, 158, 11, 0.2);
}
/* a few Element-internal light overrides whose dark side is Element's default */
body.light-theme .el-slider__tooltip { background: #fff !important; border: 1px solid #ddd !important; color: #222 !important; }
body.light-theme .el-slider__tooltip::after { border-top-color: #fff !important; }
body.light-theme .el-popper .el-popper__arrow::before { background: #fff !important; border-color: #ccc !important; }

/* ==================== Responsive ==================== */
@media (max-width: 768px) {
  .app-container { height: auto; min-height: 100vh; overflow: visible; }
  .main-content {
    position: relative; height: auto; overflow: visible;
    display: flex; flex-direction: column; gap: 0;
  }
  .grid-panel {
    position: static; width: 100%; height: 40vh; overflow-y: auto;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    border-right: none; border-bottom: 2px solid var(--border-subtle);
  }
  .detail-panel {
    position: static; left: auto; width: 100%; flex: 1; min-height: 0;
    overflow-y: auto; border-left: none;
  }
  body.light-theme .grid-panel { border-bottom-color: var(--border-subtle); }
  body.light-theme .detail-panel { border-left: none; }
  .empty-panel { min-height: 20vh; }
  .filters { padding: 6px 12px; gap: 6px; }
  .search-input { flex: 0 0 100%; max-width: none; }
  .filter-btn { min-width: 0; flex: 1 1 auto; }
  .sort-dropdown { margin-left: 0 !important; order: 2; flex: 1 1 auto; }
  .price-toggle-btn { order: 2; flex: 1 1 auto; }
  .filters::after { content: ""; order: 1; flex-basis: 100%; height: 0; }
  .header { padding: 8px 12px; flex-wrap: wrap; gap: 6px 10px; }
  .header h1 { display: flex; align-items: baseline; flex-wrap: wrap; gap: 2px 8px; min-width: 0; }
  .header-actions { flex-wrap: wrap; margin-left: auto; }
  .title { font-size: 18px; }
  .main-tabs { padding: 0 12px; }
  .main-tabs :deep(.el-tabs__item) { padding: 0 12px; font-size: 13px; }
}

/* Attack Speed Calculator */
.attack-speed-toggle {
  display: flex; align-items: center; gap: 8px; padding: 10px 12px;
  background: var(--bg-alt); border-radius: 6px; cursor: pointer;
  font-size: 14px; color: var(--accent-gold); transition: background .15s;
}
.attack-speed-toggle:hover { background: var(--bg-alt-hover); }
.toggle-icon { font-size: 10px; color: var(--text-faint); }
.attack-speed-calc {
  margin-top: 8px; padding: 12px; background: var(--bg-alt);
  border-radius: 6px; border: 1px solid var(--border-soft);
}
.calc-result {
  display: flex; flex-direction: column; gap: 6px;
  margin-bottom: 12px; padding: 8px 12px;
  background: var(--bg-inset); border-radius: 6px;
}
.calc-line { display: flex; flex-wrap: wrap; align-items: center; gap: 8px; }
.calc-label { font-size: 14px; color: var(--text-muted); }
.calc-value { font-size: 18px; font-weight: 700; color: var(--accent-green); }
.calc-pct { font-size: 14px; font-weight: 600; margin-left: 4px; }
.pct-pos { color: var(--accent-green); }
.pct-neg { color: var(--accent-red); }
.calc-reload { font-size: 13px; color: var(--text-muted);  }
.calc-reload-separator { margin: 0 2px; color: var(--text-faint); }
.slider-row {
  display: flex; align-items: center; gap: 12px; margin-bottom: 12px;
}
.slider-label {
  flex-shrink: 0; width: 60px; font-size: 13px; color: var(--text-muted); text-align: right;
}
.range-help-icon { margin-left: 4px; font-size: 14px; color: var(--range-icon); cursor: help; vertical-align: middle; }
.slider-row .el-slider { flex: 1; --el-slider-height: 4px; }
.slider-row .el-slider :deep(.el-slider__runway) { background: var(--border-soft); }
.slider-row .el-slider :deep(.el-slider__bar) { background: var(--accent-green); }
.slider-row .el-slider :deep(.el-slider__button) {
  width: 14px; height: 14px; border-color: var(--accent-green);
}
.cooldown-chart-wrapper {
  margin-top: 12px; background: var(--bg-inset); border-radius: 6px; padding: 8px;
}

/* Effect text color markers */
.zvg { color: var(--mark-green); }
.zvr { color: var(--mark-red); }
.zvp { color: var(--mark-purple); }
</style>
