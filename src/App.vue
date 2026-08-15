<template>
  <div class="app-container">
    <!-- Header -->
    <AppHeader />

    <!-- Tabs -->
    <el-tabs v-model="activeTab" type="card" class="main-tabs" @tab-change="onTabChange">
      <el-tab-pane name="weapons"><template #label><el-icon style="vertical-align:middle;margin-right:4px">
            <Aim />
          </el-icon>{{ S.weapons }}</template></el-tab-pane>
      <el-tab-pane name="items"><template #label><el-icon style="vertical-align:middle;margin-right:4px">
            <Box />
          </el-icon>{{ S.items }}</template></el-tab-pane>
      <el-tab-pane name="characters"><template #label><el-icon style="vertical-align:middle;margin-right:4px">
            <User />
          </el-icon>{{ S.characters }}</template></el-tab-pane>
    </el-tabs>

    <!-- Filters -->
    <FilterBar />

    <!-- Main Content -->
    <MainContent />
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { Aim, Box, User } from '@element-plus/icons-vue'
import AppHeader from './components/AppHeader.vue'
import FilterBar from './components/FilterBar.vue'
import MainContent from './components/MainContent.vue'
import { activeTab, S, onTabChange, initCodex } from './store/codexStore'

onMounted(initCodex)
</script>
