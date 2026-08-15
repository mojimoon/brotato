<template>
  <div class="detail-section">
    <h3 class="section-title">{{ S.effects }}</h3>
    <div class="effects-list">
      <template v-for="(eff, idx) in currentEffects" :key="idx">
        <div class="effect-item">
          <span class="eff-prefix" v-html="renderEffectPrefix(eff)"></span>
          <span class="eff-text" v-html="renderEffectText(eff)"></span>
        </div>
        <div v-if="curseEnabled && eff.text?.extra_effects" v-for="(extra, ei) in eff.text.extra_effects"
          :key="'x' + idx + '_' + ei" class="effect-item curse-extra-effect">
          <span class="eff-prefix" v-html="renderEffectPrefix(extra)"></span>
          <span class="eff-text" v-html="renderEffectText(extra)"></span>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup>
import { currentEffects, curseEnabled, renderEffectPrefix, renderEffectText, S } from '../store/codexStore'
</script>
