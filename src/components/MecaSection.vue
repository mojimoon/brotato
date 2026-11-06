<template>
  <div class="detail-section curse-section">
    <div class="curse-row">
      <el-button class="curse-toggle-btn meca-toggle-btn" :class="{ 'meca-active': mecaEnabled }"
        @click="mecaEnabled = !mecaEnabled" size="small">{{ S.mecha }}</el-button>
      <el-slider v-if="mecaEnabled" v-model="mecaSlider" :min="1" :max="20" :step="1" show-input
        class="curse-slider meca-slider" size="small" input-size="small" />
    </div>
  </div>
</template>

<script setup>
import { mecaEnabled, mecaSlider, S } from '../store/codexStore'
</script>
