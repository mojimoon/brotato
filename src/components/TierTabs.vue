<template>
  <div class="tier-tabs" v-if="activeTierWeapons.length > 1">
    <button v-for="(tw, idx) in allFourTierSlots" :key="idx" class="tier-tab"
      :class="{ active: currentTierIndex === idx && tw !== null, disabled: tw === null }" :disabled="tw === null"
      :style="tw !== null ? { background: currentTierIndex === idx ? tierColor(idx) : tierBgColor(idx), borderColor: tierColor(idx), color: currentTierIndex === idx ? '#fff' : tierColor(idx) } : {}"
      @click="tw !== null && (currentTierIndex = idx, stickyTierIndex = idx)">
      T{{ idx + 1 }}
    </button>
  </div>
</template>

<script setup>
import {
  activeTierWeapons, allFourTierSlots, currentTierIndex, stickyTierIndex, tierColor, tierBgColor,
} from '../store/codexStore'
</script>
