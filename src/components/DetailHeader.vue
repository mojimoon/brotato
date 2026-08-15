<template>
  <div class="detail-header">
    <div class="detail-icon-wrap" :style="{ borderColor: color, background: bg }">
      <img :src="getIconSrc(item.icon)" />
    </div>
    <div class="detail-title-wrap">
      <h2 :style="{ color }">{{ title }}</h2>
      <div class="detail-badges">
        <slot name="badges" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { getIconSrc } from '../store/codexStore'

defineProps({
  item: { type: Object, required: true },
  title: { type: String, default: '' },
  color: { type: String, default: 'var(--text-strong)' },
  bg: { type: String, default: 'var(--bg-icon)' },
})
</script>
