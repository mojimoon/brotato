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
      <a href="https://brotato.wiki.spellsandguns.com/" target="_blank" rel="noopener noreferrer">
        <el-button class="header-btn" circle>Wiki</el-button>
      </a>
      <el-dropdown @command="(cmd) => { isZh = cmd === 'zh' }" trigger="click">
        <el-button class="header-btn lang-btn" circle>{{ isZh ? '中' : 'EN' }}</el-button>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item :command="'zh'" :class="{ 'is-active-lang': isZh }">中文</el-dropdown-item>
            <el-dropdown-item :command="'en'" :class="{ 'is-active-lang': !isZh }">English</el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
      <el-button class="header-btn" :icon="isDark ? Moon : Sunny" circle @click="isDark = !isDark" />
    </div>
  </header>
</template>

<script setup>
import { Moon, Sunny } from '@element-plus/icons-vue'
import { isZh, isDark } from '../store/codexStore'
</script>

<style scoped>
.header-logo {
  height: 24px; width: 24px; object-fit: contain; border-radius: 4px; flex-shrink: 0; margin-right: 8px;
}
@media (max-width: 768px) {
  .header-logo { margin-right: 0; }
}
</style>
