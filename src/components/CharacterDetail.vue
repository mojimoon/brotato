<template>
  <div>
    <DetailHeader :item="selectedItem" :title="itemName(selectedItem)" :color="charColor" :bg="charBg">
      <template #badges>
        <span v-if="selectedItem.set && selectedItem.set !== 'base'" class="dlc-badge" :class="'badge-set-' + selectedItem.set">{{ itemSetName(selectedItem.set) }}</span>
      </template>
    </DetailHeader>

    <EffectsList />
    <RelatedSection :entry="selectedItem" />

    <div v-if="(selectedItem.wanted_tags || []).length" class="detail-section">
      <h3 class="section-title">{{ S.preferredTags }}</h3>
      <div class="tags-wrap">
        <TagBadge v-for="tag in selectedItem.wanted_tags" :key="tag" :tag="tag" />
      </div>
    </div>

    <RelatedSection :entry="selectedItem" :refs="startingRefs" :title="S.startingWeapons" />
    <RelatedSection :entry="selectedItem" :refs="bannedRefs" :title="S.bannedItems" />
  </div>
</template>

<script setup>
import { computed } from 'vue'
import DetailHeader from './DetailHeader.vue'
import TagBadge from './TagBadge.vue'
import EffectsList from './EffectsList.vue'
import RelatedSection from './RelatedSection.vue'
import {
  selectedItem, S, itemName, tierColor, tierBgColor, itemSetName,
} from '../store/codexStore'

// starting choices: weapons + pickable items (Beast Master's pets)
const startingRefs = computed(() => [
  ...(selectedItem.value?.starting_weapons || []).map(id => ({ kind: 'weapon', id })),
  ...(selectedItem.value?.starting_items || []).map(id => ({ kind: 'item', id })),
])
const bannedRefs = computed(() => (selectedItem.value?.banned || []).map(id => ({ kind: 'item', id })))
const charColor = computed(() => tierColor(selectedItem.value?.tier ?? 0))
const charBg = computed(() => tierBgColor(selectedItem.value?.tier ?? 0))
</script>
