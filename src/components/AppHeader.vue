<template>
  <header class="header">
    <h1>
      <img src="/brotato_icon.ico" class="header-logo" alt="Brotato" />
      <span class="title">Brotato Codex+</span>
      <a href="https://github.com/mojimoon/" target="_blank" rel="noopener noreferrer" class="author-link">@mojimoon</a>
    </h1>
    <div class="header-actions">
      <a href="https://github.com/mojimoon/brotato" target="_blank" rel="noopener noreferrer">
        <img src="https://img.shields.io/github/stars/mojimoon/brotato?style=social" alt="GitHub stars"
          style="height: 20px;" />
      </a>
      <span>V 1.1.15.4</span>
      <el-dropdown @command="(cmd) => { currentLang = cmd }" trigger="click" popper-class="dark-dropdown">
        <el-button class="header-btn lang-btn" round>{{ currentLangName }}</el-button>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item v-for="l in availableLangs" :key="l.code" :command="l.code"
              :class="{ 'is-active-lang': currentLang === l.code }">{{ l.name }}</el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
      <el-button class="header-btn" :icon="isDark ? Moon : Sunny" round @click="isDark = !isDark" />
    </div>
  </header>
</template>

<script setup>
import { computed } from 'vue'
import { Moon, Sunny } from '@element-plus/icons-vue'
import { currentLang, availableLangs, isDark } from '../store/codexStore'

const currentLangName = computed(() => {
  const found = availableLangs.value.find(l => l.code === currentLang.value)
  return found ? found.name : currentLang.value
})
</script>

<style scoped>
.header-logo {
  height: 24px; width: 24px; object-fit: contain; border-radius: 4px; flex-shrink: 0; margin-right: 8px;
}
.header-btn {
  border-radius: 999px;
}
.lang-btn {
  min-width: 64px;
  justify-content: center;
}
@media (max-width: 768px) {
  .header-logo { margin-right: 0; }
}
</style>
