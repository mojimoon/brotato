<template>
  <div v-if="displayStats" class="detail-section">
    <div class="weapon-stat-row">
      <span class="ws-label">{{ S.damage }}</span>
      <span class="ws-val" :class="{ 'curse-modified': curseEnabled }">{{ displayStats.damage }}</span>
      <span v-if="displayStats.scaling_stats?.length" class="ws-scaling">
        (<template v-for="(ss, i) in displayStats.scaling_stats" :key="i">
          <span v-if="i > 0 && ss[1] > 0">+</span><span class="ws-scaling-pct">{{ (ss[1] * 100).toFixed(0)
          }}%</span>
          <img v-if="getStatIcon(ss[0])" :src="getStatIcon(ss[0])" class="stat-inline-icon" />
          <span v-else>{{ statTr(ss[0]) }}</span>
        </template>)
      </span>
      <span v-if="displayStats.nb_projectiles > 1" class="ws-projectiles">x{{ displayStats.nb_projectiles }}</span>
    </div>

    <div class="weapon-stat-row">
      <span class="ws-label">{{ S.crit }}</span>
      <span class="ws-val">{{ (activeWeaponData.stats.crit_chance * 100).toFixed(0) }}%</span>
      <span class="ws-val crit-dmg" :class="{ 'curse-modified': curseEnabled }">x{{ displayStats.crit_damage
      }}</span>
    </div>

    <div class="weapon-stat-row">
      <span class="ws-label">{{ S.cooldown }}</span>
      <span class="ws-val">{{ formatCooldown(displayCooldown) }}</span>
      <span class="calc-reload">({{ S.tooltip }})</span>
      <span class="calc-reload-separator">/</span>
      <span class="ws-val">{{ formatCooldownFixed(totalCooldown) }}</span>
      <span class="calc-reload">({{ S.actual }})</span>
    </div>

    <div v-if="addlCooldownInfo" class="weapon-stat-row cooldown-row">
      <span class="ws-label">{{ S.cooldown }}</span>
      <template v-for="(seg, i) in addlCooldownInfo" :key="i">
        <span :class="seg.cls">{{ seg.text }}</span>
      </template>
    </div>

    <div v-if="displayStats.knockback !== 0" class="weapon-stat-row">
      <span class="ws-label">{{ S.knockback }}</span>
      <span class="ws-val">{{ displayStats.knockback }}</span>
    </div>

    <div class="weapon-stat-row">
      <span class="ws-label">{{ S.range }}</span>
      <span class="ws-val">{{ displayStats.max_range }}
        <span v-if="activeWeaponData.type === 'melee'" class="ws-attack-type">{{ meleeAttackTypeText }}</span>
      </span>
    </div>

    <div v-if="(displayStats.accuracy * 100) < 100" class="weapon-stat-row">
      <span class="ws-label">{{ S.accuracy }}</span>
      <span class="ws-val">{{ (displayStats.accuracy * 100).toFixed(0) }}%</span>
    </div>

    <div v-if="displayStats.lifesteal > 0" class="weapon-stat-row">
      <span class="ws-label">{{ S.lifesteal }}</span>
      <span class="ws-val" :class="{ 'curse-modified': curseEnabled }">{{ (displayStats.lifesteal *
        100).toFixed(0)
        }}%</span>
    </div>

    <div v-if="activeWeaponData.type === 'ranged' && displayStats.piercing > 0" class="weapon-stat-row">
      <span class="ws-label">{{ S.piercing }}</span>
      <span class="ws-val" :class="{ 'curse-modified': curseEnabled }">{{ displayStats.piercing }}
        <span v-if="displayStats.piercing_dmg_reduction > 0" class="ws-attack-type"> (-{{
          (displayStats.piercing_dmg_reduction * 100).toFixed(0) }}% {{ S.dmg }})</span>
      </span>
    </div>

    <div v-if="activeWeaponData.type === 'ranged' && displayStats.bounce > 0" class="weapon-stat-row">
      <span class="ws-label">{{ S.bounce }}</span>
      <span class="ws-val" :class="{ 'curse-modified': curseEnabled }">{{ displayStats.bounce }}</span>
    </div>

    <div v-if="dpsData" class="weapon-stat-row">
      <span class="ws-label">DPS</span>
      <span class="ws-val" :class="{ 'curse-modified': curseEnabled }">{{ dpsData.dmg.toFixed(2) }}</span>
      <span v-if="dpsData.scaling.length" class="ws-scaling">
        (<template v-for="(ss, i) in dpsData.scaling" :key="i">
          <span v-if="i > 0 && ss[1] > 0">+</span><span class="ws-scaling-pct">{{ ss[1].toFixed(1)
          }}%</span>
          <img v-if="getStatIcon(ss[0])" :src="getStatIcon(ss[0])" class="stat-inline-icon" />
          <span v-else>{{ statTr(ss[0]) }}</span>
        </template>)/s
      </span>
    </div>
  </div>
</template>

<script setup>
import {
  displayStats, curseEnabled, activeWeaponData, displayCooldown, totalCooldown,
  formatCooldown, formatCooldownFixed, addlCooldownInfo, dpsData, meleeAttackTypeText,
  S, getStatIcon, statTr,
} from '../store/codexStore'
</script>
