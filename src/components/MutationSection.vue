<template>
  <div class="detail-section curse-section" :class="{ 'meca-section': mutEnabled }">
    <div class="curse-row">
      <el-button class="curse-toggle-btn mut-toggle-btn" :class="{ 'mut-active': mutEnabled }"
        @click="mutEnabled = !mutEnabled" size="small">{{ S.mutation }}</el-button>
      <el-slider v-if="mutEnabled" v-model="mutSlider" :min="1" :max="mutCurve.max" :step="1" :marks="marks" show-input
        class="curse-slider mut-slider" size="small" input-size="small" />
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { mutEnabled, mutSlider, mutCurve, S } from '../store/codexStore'

// min_evo: mutation scale reaches 0.7 (pets / structures / some effects become copyable); max: full scale
const marks = computed(() => ({ [mutCurve.value.min_evo]: String(mutCurve.value.min_evo), [mutCurve.value.max]: String(mutCurve.value.max) }))
</script>
