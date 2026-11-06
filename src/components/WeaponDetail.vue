<template>
  <div>
    <DetailHeader :item="selectedItem" :title="weaponTitle" :color="weaponColor" :bg="weaponBg" :id-text="activeWeaponData.id">
      <template #badges>
        <span class="type-badge" :class="selectedItem.type">{{ S[selectedItem.type] }}</span>
        <span v-if="selectedItem.set && selectedItem.set !== 'base'" class="dlc-badge" :class="'badge-set-' + selectedItem.set">{{ itemSetName(selectedItem.set) }}</span>
        <el-tooltip v-for="(setNameKey, si) in (selectedItem.sets || [])" :key="si" placement="top"
          effect="dark" :hide-after="0">
          <template #content>
            <div class="set-tooltip-content">
              <div class="set-tooltip-name">{{ setTr(setNameKey) }}</div>
              <div v-for="(bonus, bi) in (getSetBonuses(setNameKey) || [])" :key="bi" class="set-tooltip-line">
                ({{ bi + 2 }}) <span v-html="setBonusText(bonus)"></span>
              </div>
            </div>
          </template>
          <span class="set-badge">{{ setTr(setNameKey) }}</span>
        </el-tooltip>
      </template>
    </DetailHeader>

    <TierTabs />

    <WeaponStatRows />

    <CurseSection />
    <MecaSection />
    <AttackSpeedCalculator />
    <PriceSection />
    <EffectsList />
  </div>
</template>

<script setup>
import { computed } from 'vue'
import DetailHeader from './DetailHeader.vue'
import TierTabs from './TierTabs.vue'
import WeaponStatRows from './WeaponStatRows.vue'
import CurseSection from './CurseSection.vue'
import MecaSection from './MecaSection.vue'
import AttackSpeedCalculator from './AttackSpeedCalculator.vue'
import PriceSection from './PriceSection.vue'
import EffectsList from './EffectsList.vue'
import {
  selectedItem, S, itemName, activeWeaponTier, activeWeaponData, tierSuffix, tierColor, tierBgColor,
  setTr, getSetBonuses, setBonusText, itemSetName,
} from '../store/codexStore'

const weaponTitle = computed(() => itemName(selectedItem.value) + tierSuffix(activeWeaponTier.value))
const weaponColor = computed(() => tierColor(activeWeaponTier.value))
const weaponBg = computed(() => tierBgColor(activeWeaponTier.value))
</script>
