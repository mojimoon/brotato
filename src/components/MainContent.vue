<template>
  <div class="main-content" tabindex="0" @keydown="onKeyDown" ref="mainContentRef">
    <ItemGrid />
    <DetailPanel v-if="!isMobile" />
    <el-drawer v-else v-model="mobileDetailOpen" direction="btt" size="85%" :with-header="false"
      class="mobile-detail-drawer" append-to-body>
      <button class="mobile-detail-close" @click="mobileDetailOpen = false" aria-label="close">
        <el-icon><Close /></el-icon>
      </button>
      <DetailPanel />
    </el-drawer>
  </div>
</template>

<script setup>
import ItemGrid from './ItemGrid.vue'
import DetailPanel from './DetailPanel.vue'
import { Close } from '@element-plus/icons-vue'
import { mainContentRef, onKeyDown, isMobile, mobileDetailOpen } from '../store/codexStore'
</script>
