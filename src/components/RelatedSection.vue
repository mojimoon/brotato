<template>
  <div v-if="list.length" class="detail-section">
    <h3 class="section-title">{{ title || S.related }}</h3>
    <div class="starting-weapons-grid">
      <div v-for="r in list" :key="r.kind + r.id" class="grid-item starting-weapon-card"
        :class="{ selected: r.current, 'related-current': r.current }" @click="openRelated(r)">
        <div class="item-icon-wrap">
          <div class="item-icon" :style="iconStyle(r.data.tier, r.current)">
            <img :src="getIconSrc(r.data.icon)" />
            <span v-if="!r.current && r.data.value > 1 && showBadges" class="corner-badge corner-tl item-price-badge">{{ r.data.value }}</span>
          </div>
          <span v-if="showBadges && itemSetBadge(r.data)" class="source-badge item-dlc-badge" :class="itemSetBadge(r.data).cls">
            <img v-for="(src, i) in itemSetBadge(r.data).icons || []" :key="i" :src="src" class="badge-icon" />{{ itemSetBadge(r.data).text }}
          </span>
        </div>
        <div class="item-name-text">{{ itemName(r.data) + (r.kind === 'weapon' ? tierSuffix(r.data.tier) : '') }}</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import {
  S, iconStyle, getIconSrc, itemName, tierSuffix, itemSetBadge, showBadges,
  relatedEntries, openRelated,
} from '../store/codexStore'

// refs: [{kind, id}]; defaults to entry.related
const props = defineProps({
  entry: { type: Object, default: null },
  refs: { type: Array, default: null },
  title: { type: String, default: '' },
})
const list = computed(() => relatedEntries(props.entry, props.refs || props.entry?.related))
</script>

<style scoped>
.related-current { cursor: default; }
</style>
