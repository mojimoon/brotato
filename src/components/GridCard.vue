<template>
  <div class="grid-item" :class="{ selected }"
    :style="selected ? { background: tierSelectedBg(item.tier), borderColor: tierColor(item.tier) } : {}"
    @click="$emit('select', item)">
    <div v-if="shouldShowCardPrice(item)" class="item-price-badge">{{ getListPrice(item) }}</div>
    <div class="item-icon" :style="{ borderColor: tierColor(item.tier), background: tierBgColor(item.tier) }">
      <img :src="getIconSrc(item.icon)" />
    </div>
    <div class="item-name-text">{{ itemName(item) }}</div>
    <div v-if="item.dlc" class="item-dlc-badge">DLC1</div>
  </div>
</template>

<script setup>
import { tierColor, tierBgColor, tierSelectedBg, getIconSrc, itemName, shouldShowCardPrice, getListPrice } from '../store/codexStore'

defineProps({
  item: { type: Object, required: true },
  selected: { type: Boolean, default: false },
})
defineEmits(['select'])
</script>
