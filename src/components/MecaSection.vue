<template>
  <div class="detail-section curse-section" :class="{ 'meca-section': mecaEnabled }">
    <div class="curse-row">
      <el-button class="curse-toggle-btn meca-toggle-btn" :class="{ 'meca-active': mecaEnabled }"
        @click="mecaEnabled = !mecaEnabled" size="small">{{ S.mecha }}</el-button>
      <el-slider v-if="mecaEnabled" v-model="mecaSlider" :min="1" :max="MAX" :step="1" :marks="marks" show-input
        class="curse-slider meca-slider" size="small" input-size="small" />
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { mecaEnabled, mecaSlider, isMobile, S } from '../store/codexStore'

// Each mechanization adds (rank + 1) power, so a weapon upgraded n times has n(n+1)/2:
// 1, 3, 6, 10, 15, 21, 28, 36, 45, 55 (higher values only via combining weapons).
const MAX = computed(() => isMobile.value ? 55 : 80)
const marks = computed(() => isMobile.value ? { 3: '3', 10: '10', 21: '21', 36: '36', 55: '55' } : {3: '3', 6: '6', 10: '10', 15: '15', 21: '21', 28: '28', 36: '36', 45: '45', 55: '55', 66: '66', 78: '78' })
</script>
