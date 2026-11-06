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
    <span class="detail-id" :title="idText || item.id">{{ idText || item.id }}</span>
  </div>
</template>

<script setup>
import { getIconSrc } from '../store/codexStore'

defineProps({
  item: { type: Object, required: true },
  title: { type: String, default: '' },
  color: { type: String, default: 'var(--text-strong)' },
  bg: { type: String, default: 'var(--bg-icon)' },
  idText: { type: String, default: '' },
})
</script>

<style scoped>
.detail-id {
  margin-left: auto; align-self: flex-start; font-family: ui-monospace, Consolas, monospace;
  font-size: 12px; color: var(--text-muted, #888); user-select: all; word-break: break-all; text-align: right;
}
</style>
