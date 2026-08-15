<template>
  <div class="grid-panel">
    <GridCard v-for="item in currentDisplayList" :key="item.id" :item="item"
      :selected="selectedItem?.id === item.id"
      :ref="el => { const node = el?.$el ?? el; if (node) gridItemRefs[item.id] = node }" @select="selectItem" />
  </div>
</template>

<script setup>
import GridCard from './GridCard.vue'
import { currentDisplayList, selectedItem, gridItemRefs, selectItem } from '../store/codexStore'
</script>
