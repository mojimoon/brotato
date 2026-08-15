<template>
  <div class="detail-panel" v-if="selectedItem">
    <WeaponDetail v-if="activeTab === 'weapons'" />
    <ItemDetail v-else-if="activeTab === 'items'" />
    <CharacterDetail v-else />
  </div>
  <div class="detail-panel empty-panel" v-else>
    <el-empty :description="S.clickToSee" />
  </div>
</template>

<script setup>
import WeaponDetail from './WeaponDetail.vue'
import ItemDetail from './ItemDetail.vue'
import CharacterDetail from './CharacterDetail.vue'
import { selectedItem, activeTab, S } from '../store/codexStore'
</script>
