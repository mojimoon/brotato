<template>
  <div class="resources-panel">
    <div class="resources-inner">
      <!-- Left column -->
      <div class="res-col">
        <!-- About -->
        <section class="res-section">
          <div class="res-section-head">
            <el-icon class="res-section-icon"><InfoFilled /></el-icon>
            <span class="res-section-title">{{ isZh ? '关于' : 'About' }}</span>
          </div>
          <p class="res-about-text">
            {{ isZh
              ? '如果你觉得这个有帮助，请考虑在 GitHub 上给我点个 star！谢谢！'
              : 'If you find this helpful, please consider giving me a star on GitHub! Thank you!' }}
          </p>
          <a class="res-link" :href="githubUrl" target="_blank" rel="noopener noreferrer">
            <BrandIcon name="github" class="res-link-icon" />
            <span class="res-link-label">GitHub · mojimoon/brotato</span>
            <el-icon class="res-link-ext"><TopRight /></el-icon>
          </a>
          <p class="res-about-text res-about-sub">
            {{ isZh ? '试试我的 Brotato 模组：' : 'Try out my Brotato mods:' }}
          </p>
          <a class="res-link" :href="modCurseUrl" target="_blank" rel="noopener noreferrer">
            <BrandIcon name="steam" class="res-link-icon" />
            <span class="res-link-label">{{ isZh ? '诅咒和双面升级 [DoubleSidedUpgrades]' : 'Cursed & Double Sided Upgrades' }}</span>
            <el-icon class="res-link-ext"><TopRight /></el-icon>
          </a>
          <a class="res-link" :href="modOneItemUrl" target="_blank" rel="noopener noreferrer">
            <BrandIcon name="steam" class="res-link-icon" />
            <span class="res-link-label">{{ isZh ? '所有物品变为同一个 [OneItemToRuleThemAll]' : 'One Item to Rule Them All' }}</span>
            <el-icon class="res-link-ext"><TopRight /></el-icon>
          </a>
        </section>

        <!-- Left dynamic sections (Special Thanks) -->
        <section v-for="sec in leftSections" :key="sec.key" class="res-section">
          <div class="res-section-head">
            <el-icon class="res-section-icon"><component :is="sec.icon" /></el-icon>
            <span class="res-section-title">{{ isZh ? sec.title.zh : sec.title.en }}</span>
          </div>
          <div v-for="(item, i) in sec.items" :key="i" class="res-item">
            <a class="res-link" :href="item.url" target="_blank" rel="noopener noreferrer">
              <BrandIcon :name="item.brand" class="res-link-icon" />
              <span class="res-link-label">{{ isZh ? item.label.zh : item.label.en }}</span>
              <span v-if="item.by" class="res-by">{{ item.by }}</span>
              <el-icon class="res-link-ext"><TopRight /></el-icon>
            </a>
            <div v-if="item.sub && item.sub.length" class="res-sub">
              <a v-for="(sub, j) in item.sub" :key="j" class="res-link res-sub-link"
                :href="sub.url" target="_blank" rel="noopener noreferrer">
                <BrandIcon :name="sub.icon || item.subBrand || item.brand" class="res-link-icon" />
                <span class="res-link-label">{{ isZh ? sub.label.zh : sub.label.en }}</span>
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
            <span class="res-section-title">{{ isZh ? sec.title.zh : sec.title.en }}</span>
          </div>
          <div v-for="(item, i) in sec.items" :key="i" class="res-item">
            <a class="res-link" :href="item.url" target="_blank" rel="noopener noreferrer">
              <BrandIcon :name="item.brand" class="res-link-icon" />
              <span class="res-link-label">{{ isZh ? item.label.zh : item.label.en }}</span>
              <span v-if="item.by" class="res-by">{{ item.by }}</span>
              <el-icon class="res-link-ext"><TopRight /></el-icon>
            </a>
            <div v-if="item.sub && item.sub.length" class="res-sub">
              <a v-for="(sub, j) in item.sub" :key="j" class="res-link res-sub-link"
                :href="sub.url" target="_blank" rel="noopener noreferrer">
                <BrandIcon :name="sub.icon || item.subBrand || item.brand" class="res-link-icon" />
                <span class="res-link-label">{{ isZh ? sub.label.zh : sub.label.en }}</span>
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
import { isZh } from '../store/codexStore'
import BrandIcon from './BrandIcon.vue'

const githubUrl = 'https://github.com/mojimoon/brotato'
const modCurseUrl = 'https://steamcommunity.com/sharedfiles/filedetails/?id=3671945570'
const modOneItemUrl = 'https://steamcommunity.com/sharedfiles/filedetails/?id=3757246252'

const sheetsBase = 'https://docs.google.com/spreadsheets/d/1qi_KWBH_fQlrXJioDGJQScuRbwfndHzLu4Zj5Ek0Aso/edit'
const wikiBase = 'https://brotato.wiki.spellsandguns.com'

const sections = [
  {
    key: 'thanks',
    icon: markRaw(Star),
    title: { en: 'Special Thanks', zh: '特别感谢' },
    items: [
      {
        brand: 'sheets', subBrand: 'sheets',
        label: { en: 'Brotato MultiTool', zh: 'Brotato MultiTool' }, by: 'AroRIsing',
        url: `${sheetsBase}?gid=1643867668`,
        sub: [
          { icon: 'sheets', label: { en: 'DPS Calculator', zh: 'DPS 计算器' }, url: `${sheetsBase}?gid=1374380662` },
          { icon: 'sheets', label: { en: 'Item Efficiency', zh: '物品性价比' }, url: `${sheetsBase}?gid=743336370` },
          { icon: 'sheets', label: { en: 'Misc Calculators', zh: '杂项计算器' }, url: `${sheetsBase}?gid=1779030030` },
          { icon: 'sheets', label: { en: 'Enemy Calculator', zh: '敌人计算器' }, url: `${sheetsBase}?gid=647636409` },
          { icon: 'sheets', label: { en: 'Endless Mode', zh: '无尽模式' }, url: `${sheetsBase}?gid=1720835033` },
        ],
      },
      {
        brand: 'steam',
        label: { en: 'Improved Tooltip', zh: 'Improved Tooltip' }, by: 'WL',
        url: 'https://steamcommunity.com/sharedfiles/filedetails/?id=3019195689',
      },
    ],
  },
  {
    key: 'resources',
    icon: markRaw(Files),
    title: { en: 'Resources', zh: '资源' },
    items: [
      {
        brand: 'wiki', subBrand: 'wiki',
        label: { en: 'Wiki', zh: 'Wiki' },
        url: `${wikiBase}/Brotato_Wiki`,
        sub: [
          { icon: 'weapon', label: { en: 'Weapons', zh: '武器' }, url: `${wikiBase}/Weapons` },
          { icon: 'character', label: { en: 'Characters', zh: '角色' }, url: `${wikiBase}/Characters` },
          { icon: 'item', label: { en: 'Items', zh: '物品' }, url: `${wikiBase}/Items` },
          { icon: 'stat', label: { en: 'Stats', zh: '属性' }, url: `${wikiBase}/Stats` },
          { icon: 'enemy', label: { en: 'Enemies', zh: '敌人' }, url: `${wikiBase}/Enemies` },
          { icon: 'community', label: { en: 'Community', zh: '社区' }, url: `${wikiBase}/Community` },
        ],
      },
    ],
  },
  {
    key: 'community',
    icon: markRaw(ChatDotRound),
    title: { en: 'Community', zh: '社区' },
    items: [
      { brand: 'discord', label: { en: 'Discord', zh: 'Discord' }, url: 'https://discord.com/invite/j39jE6k' },
      { brand: 'reddit', label: { en: 'Reddit', zh: 'Reddit' }, url: 'https://www.reddit.com/r/Brotato' },
    ],
  },
  {
    key: 'official',
    icon: markRaw(OfficeBuilding),
    title: { en: 'Official', zh: '官方' },
    items: [
      { brand: 'steam', label: { en: 'Steam', zh: 'Steam' }, url: 'https://store.steampowered.com/app/1942280/Brotato' },
      { brand: 'x', label: { en: 'X', zh: 'X' }, url: 'https://x.com/Studio_Evil' },
      { brand: 'bilibili', label: { en: 'Bilibili', zh: 'Bilibili' }, url: 'https://space.bilibili.com/3546576049932887' },
    ],
  },
]

const leftSections = computed(() => sections.filter((s) => s.key === 'thanks'))
const rightSections = computed(() => sections.filter((s) => ['resources', 'community', 'official'].includes(s.key)))
</script>
