<template>
  <div class="detail-section curse-section" :class="{ 'meca-section': mutEnabled }">
    <div class="curse-row">
      <el-button class="curse-toggle-btn mut-toggle-btn" :class="{ 'mut-active': mutEnabled }"
        @click="mutEnabled = !mutEnabled" size="small">{{ S.mutation }}</el-button>
      <el-slider v-if="mutEnabled" v-model="mutSlider" :min="1" :max="150" :step="1" :marks="marks" show-input
        class="curse-slider mut-slider" size="small" input-size="small" />
    </div>
  </div>
</template>

<script setup>
import { mutEnabled, mutSlider, S } from '../store/codexStore'

// 67: mutation scale reaches 0.7 (pets / structures / some effects become copyable); 150: full scale
const marks = { 67: '67', 100: '100', 150: '150' }
</script>
