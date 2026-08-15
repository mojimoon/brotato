<template>
  <div>
    <DetailHeader :item="selectedItem" :title="itemName(selectedItem)" :color="charColor" :bg="charBg">
      <template #badges>
        <span v-if="selectedItem.dlc" class="dlc-badge">DLC</span>
      </template>
    </DetailHeader>

    <EffectsList />

    <div v-if="(selectedItem.wanted_tags || []).length" class="detail-section">
      <h3 class="section-title">{{ S.preferredTags }}</h3>
      <div class="tags-wrap">
        <TagBadge v-for="tag in selectedItem.wanted_tags" :key="tag" :tag="tag" />
      </div>
    </div>

    <div v-if="selectedItem.starting_weapons?.length" class="detail-section">
      <h3 class="section-title">{{ S.startingWeapons }}</h3>
      <div class="starting-weapons-grid">
        <div v-for="wid in selectedItem.starting_weapons" :key="wid" class="grid-item starting-weapon-card"
          @click="navigateToWeapon(wid)">
          <div class="item-icon"
            :style="{ borderColor: tierColor(getWeaponById(wid)?.tier ?? 0), background: tierBgColor(getWeaponById(wid)?.tier ?? 0) }">
            <img :src="getIconSrc(getWeaponById(wid)?.icon)" />
          </div>
          <div class="item-name-text">{{ getWeaponById(wid) ? itemName(getWeaponById(wid), true) : wid }}</div>
        </div>
      </div>
    </div>
    
    <CurseSection />
  </div>
</template>

<script setup>
import { computed } from 'vue'
import DetailHeader from './DetailHeader.vue'
import TagBadge from './TagBadge.vue'
import EffectsList from './EffectsList.vue'
import CurseSection from './CurseSection.vue'
import {
  selectedItem, S, itemName, tierColor, tierBgColor, getWeaponById, getIconSrc, navigateToWeapon,
} from '../store/codexStore'

const charColor = computed(() => tierColor(selectedItem.value?.tier ?? 0))
const charBg = computed(() => tierBgColor(selectedItem.value?.tier ?? 0))
</script>
