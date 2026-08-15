<template>
  <div class="detail-section curse-section">
    <div class="curse-row">
      <el-button class="curse-toggle-btn" :class="{ 'curse-active': curseEnabled }"
        @click="curseEnabled = !curseEnabled" size="small">{{ S.curse }}</el-button>
      <el-slider v-if="curseEnabled" v-model="curseSlider" :min="10" :max="110" :step="1" show-input
        class="curse-slider" size="small" input-size="small" />
    </div>
  </div>
</template>

<script setup>
import { curseEnabled, curseSlider, S } from '../store/codexStore'
</script>
