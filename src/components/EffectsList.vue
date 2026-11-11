<template>
  <div class="detail-section" v-if="currentEffects.length">
    <h3 class="section-title">{{ S.effects }}</h3>
    <div class="effects-list">
      <template v-for="(eff, idx) in currentEffects" :key="idx">
        <div class="effect-item" :class="{ 'mut-copy': mutCopyable(eff), 'mut-removed': mutActive && !curseEnabled && eff.mut === 'remove' }">
          <span class="eff-prefix" v-html="renderEffectPrefix(eff)"></span>
          <span class="eff-text" v-html="renderEffectText(eff)"></span>
          <span v-if="eff.mut === 'no_copy' || eff.mut === 'no_remove'" class="no-mut-copy">{{ eff.mut === 'no_remove' ? S.noMutRemove : S.noMutCopy }}</span>
          <span v-else-if="eff.mut_min" class="no-mut-copy">{{ S.mutNeed.replace('{0}', eff.mut_min) }}</span>
        </div>
        <div v-if="curseEnabled && eff.text?.extra_effects" v-for="(extra, ei) in eff.text.extra_effects"
          :key="'x' + idx + '_' + ei" class="effect-item curse-extra-effect" :class="{ 'mut-copy': mutCopyable(extra) }">
          <span class="eff-prefix" v-html="renderEffectPrefix(extra)"></span>
          <span class="eff-text" v-html="renderEffectText(extra)"></span>
          <span v-if="extra.mut === 'no_copy'" class="no-mut-copy">{{ S.noMutCopy }}</span>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup>
import { activeTab, mutActive, mutCopyable, currentEffects, curseEnabled, renderEffectPrefix, renderEffectText, S } from '../store/codexStore'
</script>
