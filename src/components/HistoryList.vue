<template>
  <div class="hist-list">
    <div v-for="ver in list" :key="ver.v" class="hist-ver">
      <span class="hist-ver-tag">{{ ver.v }}</span>
      <ul class="hist-lines">
        <li v-for="(line, i) in ver.lines" :key="i" v-html="historyLineHtml(line)"></li>
      </ul>
    </div>
  </div>
</template>

<script setup>
import { historyLineHtml } from '../store/codexStore'

defineProps({ list: { type: Array, default: () => [] } })
</script>
