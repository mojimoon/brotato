<template>
  <div class="detail-section curse-section" :class="{ 'meca-section': curseEnabled }">
    <div class="curse-row">
      <el-button class="curse-toggle-btn" :class="{ 'curse-active': curseEnabled }"
        @click="curseEnabled = !curseEnabled" size="small">{{ S.curse }}</el-button>
      <el-slider v-if="curseEnabled" v-model="curseSlider" :min="10" :max="110" :step="1" :marks="marks" show-input
        class="curse-slider" size="small" input-size="small" />
    </div>
  </div>
</template>

<script setup>
import { curseEnabled, curseSlider, S } from '../store/codexStore'
const marks = { 10: '10', 40: '40', 70: '70', 100: '100', 110: '110' }
</script>
