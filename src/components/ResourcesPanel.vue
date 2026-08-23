<template>
  <div class="resources-panel">
    <div class="resources-inner">
      <!-- Left column -->
      <div class="res-col">
        <!-- About -->
        <section class="res-section">
          <div class="res-section-head">
            <el-icon class="res-section-icon"><InfoFilled /></el-icon>
            <span class="res-section-title">{{ S.about }}</span>
          </div>
          <p class="res-about-text">
            {{ S.aboutText }}
          </p>
          <a class="res-link" :href="githubUrl" target="_blank" rel="noopener noreferrer">
            <BrandIcon name="github" class="res-link-icon" />
            <span class="res-link-label">GitHub · mojimoon/brotato</span>
            <el-icon class="res-link-ext"><TopRight /></el-icon>
          </a>
          <p class="res-about-text res-about-sub">
            {{ S.tryMods }}
          </p>
          <a class="res-link" :href="modCurseUrl" target="_blank" rel="noopener noreferrer">
            <BrandIcon name="steam" class="res-link-icon" />
            <span class="res-link-label">{{ S.modCurse }}</span>
            <el-icon class="res-link-ext"><TopRight /></el-icon>
          </a>
          <a class="res-link" :href="modOneItemUrl" target="_blank" rel="noopener noreferrer">
            <BrandIcon name="steam" class="res-link-icon" />
            <span class="res-link-label">{{ S.modOneItem }}</span>
            <el-icon class="res-link-ext"><TopRight /></el-icon>
          </a>
        </section>

        <!-- Left dynamic sections (Special Thanks) -->
        <section v-for="sec in leftSections" :key="sec.key" class="res-section">
          <div class="res-section-head">
            <el-icon class="res-section-icon"><component :is="sec.icon" /></el-icon>
            <span class="res-section-title">{{ sec.title }}</span>
          </div>
          <div v-for="(item, i) in sec.items" :key="i" class="res-item">
            <a class="res-link" :href="item.url" target="_blank" rel="noopener noreferrer">
              <BrandIcon :name="item.brand" class="res-link-icon" />
              <span class="res-link-label">{{ item.label }}</span>
              <span v-if="item.by" class="res-by">{{ item.by }}</span>
              <el-icon class="res-link-ext"><TopRight /></el-icon>
            </a>
            <div v-if="item.sub && item.sub.length" class="res-sub">
              <a v-for="(sub, j) in item.sub" :key="j" class="res-link res-sub-link"
                :href="sub.url" target="_blank" rel="noopener noreferrer">
                <BrandIcon :name="sub.icon || item.subBrand || item.brand" class="res-link-icon" />
                <span class="res-link-label">{{ sub.label }}</span>
                <el-icon class="res-link-ext"><TopRight /></el-icon>
              </a>
            </div>
          </div>
        </section>
      </div>

      <!-- Right column (Resources, Community, Official) -->
      <div class="res-col">
        <section v-for="sec in rightSections" :key="sec.key" class="res-section">
          <div class="res-section-head">
            <el-icon class="res-section-icon"><component :is="sec.icon" /></el-icon>
            <span class="res-section-title">{{ sec.title }}</span>
          </div>
          <div v-for="(item, i) in sec.items" :key="i" class="res-item">
            <a class="res-link" :href="item.url" target="_blank" rel="noopener noreferrer">
              <BrandIcon :name="item.brand" class="res-link-icon" />
              <span class="res-link-label">{{ item.label }}</span>
              <span v-if="item.by" class="res-by">{{ item.by }}</span>
              <el-icon class="res-link-ext"><TopRight /></el-icon>
            </a>
            <div v-if="item.sub && item.sub.length" class="res-sub">
              <a v-for="(sub, j) in item.sub" :key="j" class="res-link res-sub-link"
                :href="sub.url" target="_blank" rel="noopener noreferrer">
                <BrandIcon :name="sub.icon || item.subBrand || item.brand" class="res-link-icon" />
                <span class="res-link-label">{{ sub.label }}</span>
                <el-icon class="res-link-ext"><TopRight /></el-icon>
              </a>
            </div>
          </div>
        </section>
      </div>
    </div>
  </div>
</template>

<script setup>
import { markRaw, computed } from 'vue'
import { InfoFilled, Star, Files, ChatDotRound, OfficeBuilding, TopRight } from '@element-plus/icons-vue'
import { S, rawData } from '../store/codexStore'
import BrandIcon from './BrandIcon.vue'

const githubUrl = 'https://github.com/mojimoon/brotato'
const modCurseUrl = 'https://steamcommunity.com/sharedfiles/filedetails/?id=3671945570'
const modOneItemUrl = 'https://steamcommunity.com/sharedfiles/filedetails/?id=3757246252'

const sheetsBase = 'https://docs.google.com/spreadsheets/d/1qi_KWBH_fQlrXJioDGJQScuRbwfndHzLu4Zj5Ek0Aso/edit'
const wikiBase = 'https://brotato.wiki.spellsandguns.com'

// Structural template: icons (components), urls, brands, authors. The translated
// titles/labels come from rawData.value.ui.sections (generated per language).
const sectionStructure = [
  {
    key: 'thanks',
    icon: markRaw(Star),
    items: [
      {
        brand: 'sheets', subBrand: 'sheets',
        by: 'AroRIsing',
        url: `${sheetsBase}?gid=1643867668`,
        sub: [
          { icon: 'sheets', url: `${sheetsBase}?gid=1374380662` },
          { icon: 'sheets', url: `${sheetsBase}?gid=743336370` },
          { icon: 'sheets', url: `${sheetsBase}?gid=1779030030` },
          { icon: 'sheets', url: `${sheetsBase}?gid=647636409` },
          { icon: 'sheets', url: `${sheetsBase}?gid=1720835033` },
        ],
      },
      {
        brand: 'steam',
        by: 'WL',
        url: 'https://steamcommunity.com/sharedfiles/filedetails/?id=3019195689',
      },
    ],
  },
  {
    key: 'resources',
    icon: markRaw(Files),
    items: [
      {
        brand: 'wiki', subBrand: 'wiki',
        url: `${wikiBase}/Brotato_Wiki`,
        sub: [
          { icon: 'weapon', url: `${wikiBase}/Weapons` },
          { icon: 'character', url: `${wikiBase}/Characters` },
          { icon: 'item', url: `${wikiBase}/Items` },
          { icon: 'stat', url: `${wikiBase}/Stats` },
          { icon: 'enemy', url: `${wikiBase}/Enemies` },
          { icon: 'community', url: `${wikiBase}/Community` },
        ],
      },
    ],
  },
  {
    key: 'community',
    icon: markRaw(ChatDotRound),
    items: [
      { brand: 'discord', url: 'https://discord.com/invite/j39jE6k' },
      { brand: 'reddit', url: 'https://www.reddit.com/r/Brotato' },
    ],
  },
  {
    key: 'official',
    icon: markRaw(OfficeBuilding),
    items: [
      { brand: 'steam', url: 'https://store.steampowered.com/app/1942280/Brotato' },
      { brand: 'x', url: 'https://x.com/Studio_Evil' },
      { brand: 'bilibili', url: 'https://space.bilibili.com/3546576049932887' },
    ],
  },
]

const uiSections = computed(() => rawData.value.ui?.sections || [])

const sections = computed(() => sectionStructure.map(struct => {
  const ui = uiSections.value.find(s => s.key === struct.key) || {}
  return {
    key: struct.key,
    icon: struct.icon,
    title: ui.title || struct.key,
    items: struct.items.map((it, i) => {
      const uiIt = (ui.items || [])[i] || {}
      return {
        ...it,
        label: uiIt.label || it.brand || '',
        sub: (it.sub || []).map((s, j) => {
          const uiSub = (uiIt.sub || [])[j] || {}
          return { ...s, label: uiSub.label || s.icon || '' }
        }),
      }
    }),
  }
}))

const leftSections = computed(() => sections.value.filter((s) => s.key === 'thanks'))
const rightSections = computed(() => sections.value.filter((s) => ['resources', 'community', 'official'].includes(s.key)))
</script>
