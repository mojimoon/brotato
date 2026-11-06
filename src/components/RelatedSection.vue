<template>
  <div v-if="list.length" class="detail-section">
    <h3 class="section-title">{{ title || S.related }}</h3>
    <div class="starting-weapons-grid">
      <div v-for="r in list" :key="r.kind + r.id" class="grid-item starting-weapon-card"
        :class="{ selected: r.current, 'related-current': r.current }"
        :style="r.current ? { background: tierSelectedBg(r.data.tier), borderColor: tierColor(r.data.tier) } : {}"
        @click="openRelated(r)">
        <div v-if="!r.current && r.data.value > 1 && showingPrice" class="item-price-badge">{{ r.data.value }}</div>
        <div class="item-icon" :style="{ borderColor: tierColor(r.data.tier), background: tierBgColor(r.data.tier) }">
          <img :src="getIconSrc(r.data.icon)" />
        </div>
        <div class="item-name-text">{{ itemName(r.data) + (r.kind === 'weapon' ? tierSuffix(r.data.tier) : '') }}</div>
        <div v-if="itemSetBadge(r.data)" class="item-dlc-badge" :class="itemSetBadge(r.data).cls">
          <img v-for="(src, i) in itemSetBadge(r.data).icons || []" :key="i" :src="src" class="badge-icon" />{{ itemSetBadge(r.data).text }}
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import {
  S, tierColor, tierBgColor, tierSelectedBg, getIconSrc, itemName, tierSuffix, itemSetBadge, showingPrice,
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
