<template>
  <div class="main-content" tabindex="0" @keydown="onKeyDown" ref="mainContentRef">
    <ItemGrid />
    <DetailPanel />
  </div>
</template>

<script setup>
import ItemGrid from './ItemGrid.vue'
import DetailPanel from './DetailPanel.vue'
import { mainContentRef, onKeyDown } from '../store/codexStore'
</script>
