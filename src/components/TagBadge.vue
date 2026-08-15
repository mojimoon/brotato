<template>
  <span class="tag-badge clickable" :class="specialTagClass(tag)" @click.stop="onTagClick(tag)">
    <el-tooltip placement="top" effect="dark" :hide-after="0">
      <template #content>
        <div class="tag-tooltip-content">
          <div class="tag-tooltip-name">{{ tagTr(tag) }}</div>
          <div v-if="tagItems(tag).length" class="tag-tooltip-line">{{ S.items }}：{{ tagItems(tag).join(' ,') }}</div>
          <div v-if="tagCharacters(tag).length" class="tag-tooltip-line">{{ S.characters }}：{{
            tagCharacters(tag).join(', ') }}</div>
        </div>
      </template>
      {{ tagTr(tag) }}
    </el-tooltip>
  </span>
</template>

<script setup>
import { tagTr, specialTagClass, onTagClick, tagItems, tagCharacters, S } from '../store/codexStore'

defineProps({
  tag: { type: String, required: true },
})
</script>
