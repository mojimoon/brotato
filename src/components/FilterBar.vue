<template>
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
        {{ filterSet !== null ? ((availableSets.find(s => s.key === filterSet) || {}).label || filterSet) : S.set }}
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

    <el-dropdown trigger="click" popper-class="dark-dropdown" @command="(v) => { filterDlc = v; onFilterChange(); }">
      <el-button class="filter-btn" :class="{ 'has-value': filterDlc !== null }">
        {{ filterDlc === 0 ? S.base : filterDlc === 1 ? 'DLC1' : S.source }}
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
          <el-dropdown-item :command="1" :class="{ 'is-active-opt': filterDlc === 1 }">DLC1</el-dropdown-item>
        </el-dropdown-menu>
      </template>
    </el-dropdown>

    <el-button v-if="hasActiveFilter" class="filter-btn clear-btn" @click="clearAllFilters">
      <el-icon>
        <Close />
      </el-icon>
    </el-button>

    <div class="filter-cluster">
      <el-dropdown v-if="activeTab === 'weapons' || activeTab === 'items'" trigger="click"
        popper-class="dark-dropdown" @command="(v) => { sortBy = v; onFilterChange(); }" class="sort-dropdown">
        <el-button class="filter-btn sort-btn" :class="{ 'has-value': sortBy !== 'default' }">
          <el-icon style="margin-right:4px">
            <Sort />
          </el-icon>
          {{ currentSortLabel }}
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
            <template v-if="activeTab === 'weapons'">
              <el-dropdown-item command="damage" :class="{ 'is-active-opt': sortBy === 'damage' }">{{ S.sortDamage
              }}</el-dropdown-item>
              <el-dropdown-item command="crit" :class="{ 'is-active-opt': sortBy === 'crit' }">{{ S.sortCrit
              }}</el-dropdown-item>
              <el-dropdown-item command="cooldown" :class="{ 'is-active-opt': sortBy === 'cooldown' }">{{
              S.sortCooldown }}</el-dropdown-item>
              <el-dropdown-item command="range" :class="{ 'is-active-opt': sortBy === 'range' }">{{ S.sortRange
              }}</el-dropdown-item>
            </template>
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

      <el-button v-if="activeTab === 'weapons'" class="filter-btn price-toggle-btn frames-toggle-btn"
        :class="{ 'has-value': showFrames }" @click="showFrames = !showFrames">
        <el-icon style="margin-right:4px">
          <MoreFilled v-if="showFrames" />
          <More v-else />
        </el-icon>
        {{ S.frames }}
      </el-button>
    </div>
  </div>
</template>

<script setup>
import { Search, Sort, ArrowDown, View, Hide, Close, More, MoreFilled } from '@element-plus/icons-vue'
import {
  searchText, activeTab, S, filterTier, tierDisplayName, onFilterChange, filterType,
  filterSet, availableSets, filterTag, allTags, tagTr, filterDlc, hasActiveFilter,
  clearAllFilters, sortBy, currentSortLabel, showingPrice, showFrames,
} from '../store/codexStore'
</script>
