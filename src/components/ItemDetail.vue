<template>
  <div>
    <DetailHeader :item="selectedItem" :title="itemName(selectedItem)" :color="itemColor" :bg="itemBg">
      <template #badges>
        <span v-if="selectedItem.set && selectedItem.set !== 'base'" class="dlc-badge badge-lg" :class="'badge-set-' + selectedItem.set">{{ itemSetName(selectedItem.set) }}</span>
        <el-tooltip v-for="t in evolutionTags(selectedItem)" :key="t.key" :content="t.desc" placement="top"
          effect="dark" :hide-after="0" :disabled="!t.desc">
          <span class="dlc-badge badge-lg" :class="t.cls"><img :src="t.icon" class="badge-icon" />{{ t.label }}</span>
        </el-tooltip>
        <span v-if="isUniqueItem(selectedItem)" class="limit-badge unique">{{ S.unique }}</span>
        <span v-else-if="isLimitedItem(selectedItem)" class="limit-badge limited">{{ S.limited }}({{
          selectedItem.max_nb }})</span>
        <TagBadge v-for="tag in sortedItemTags(selectedItem)" :key="tag" :tag="tag" />
      </template>
    </DetailHeader>

    <CurseSection />
    <PriceSection />
    <EffectsList />
    <RelatedSection :entry="selectedItem" />
  </div>
</template>

<script setup>
import { computed } from 'vue'
import DetailHeader from './DetailHeader.vue'
import TagBadge from './TagBadge.vue'
import CurseSection from './CurseSection.vue'
import PriceSection from './PriceSection.vue'
import EffectsList from './EffectsList.vue'
import RelatedSection from './RelatedSection.vue'
import {
  selectedItem, S, itemName, isUniqueItem, isLimitedItem, sortedItemTags,
  tierColor, tierBgColor, itemSetName, evolutionTags,
} from '../store/codexStore'

const itemColor = computed(() => tierColor(selectedItem.value?.tier ?? 0))
const itemBg = computed(() => tierBgColor(selectedItem.value?.tier ?? 0))
</script>
