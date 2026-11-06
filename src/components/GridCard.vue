<template>
  <div class="grid-item" :class="{ selected }"
    :style="selected ? { background: tierSelectedBg(item.tier), borderColor: tierColor(item.tier) } : {}"
    @click="$emit('select', item)">
    <div v-if="shouldShowCardPrice(item)" class="item-price-badge">{{ getListPrice(item) }}</div>
    <div class="item-icon" :style="{ borderColor: tierColor(item.tier), background: tierBgColor(item.tier) }">
      <img :src="getIconSrc(item.icon)" />
    </div>
    <div class="item-name-text">{{ itemName(item) }}</div>
    <div v-if="badge" class="item-dlc-badge" :class="badge.cls"><img v-for="(src, i) in badge.icons || []" :key="i" :src="src" class="badge-icon" />{{ badge.text }}</div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { tierColor, tierBgColor, tierSelectedBg, getIconSrc, itemName, shouldShowCardPrice, getListPrice, itemSetBadge } from '../store/codexStore'

const props = defineProps({
  item: { type: Object, required: true },
  selected: { type: Boolean, default: false },
})
defineEmits(['select'])
const badge = computed(() => itemSetBadge(props.item))
</script>
