<template>
  <div v-if="list.length" class="detail-section">
    <h3 class="section-title">{{ S.history }}</h3>
    <HistoryList :list="list" />
  </div>
</template>

<script setup>
import { computed } from 'vue'
import HistoryList from './HistoryList.vue'
import { S, historyFor } from '../store/codexStore'

// entryId: item / character id, or weapon family id (weapon_id)
const props = defineProps({ entryId: { type: String, default: '' } })
const list = computed(() => historyFor(props.entryId))
</script>
