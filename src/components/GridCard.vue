<template>
  <div class="grid-item" :class="{ selected }" @click="$emit('select', item)">
    <div class="item-icon-wrap">
      <div class="item-icon" :style="iconStyle(item.tier, selected)">
        <img :src="getIconSrc(item.icon)" />
        <span v-if="shouldShowCardPrice(item)" class="corner-badge corner-tl item-price-badge">{{ getListPrice(item) }}</span>
        <span v-if="limit" class="corner-badge corner-tr item-limit-badge" :class="limit.cls" :title="limit.title">{{ item.max_nb }}</span>
      </div>
      <span v-if="badge" class="source-badge item-dlc-badge" :class="badge.cls"><img v-for="(src, i) in badge.icons || []" :key="i" :src="src" class="badge-icon" />{{ badge.text }}</span>
    </div>
    <div class="item-name-text">{{ itemName(item) }}</div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { iconStyle, getIconSrc, itemName, shouldShowCardPrice, getListPrice, itemSetBadge, isUniqueItem, isLimitedItem, showingPrice, S } from '../store/codexStore'

const props = defineProps({
  item: { type: Object, required: true },
  selected: { type: Boolean, default: false },
})
defineEmits(['select'])
const badge = computed(() => itemSetBadge(props.item))
// 道具数量上限（唯一 / 限定），配色与详情页的 limit-badge 一致；随「价格」开关一起显示 / 隐藏
const limit = computed(() => !showingPrice.value ? null : isUniqueItem(props.item) ? { cls: 'unique', title: S.value.unique }
  : isLimitedItem(props.item) ? { cls: 'limited', title: `${S.value.limited}(${props.item.max_nb})` } : null)
</script>
