<template>
  <div v-if="activeTab === 'weapons' && activeWeaponData.stats" class="detail-section">
    <div class="attack-speed-toggle" @click="showAttackSpeedCalc = !showAttackSpeedCalc">
      <span class="toggle-icon">{{ showAttackSpeedCalc ? '▼' : '▶' }}</span>
      <span>{{ S.attackSpeedCalc }}</span>
    </div>
    <div v-if="showAttackSpeedCalc" class="attack-speed-calc">
      <div class="calc-result">
        <div class="calc-line">
          <span class="calc-label">{{ S.tooltipCooldown }}:</span>
          <span class="calc-value">{{ formatCooldown(calculatedTooltipCooldown) }}</span>
          <template v-for="(seg, i) in cooldownSegments('tooltip')" :key="i">
            <span :class="seg.cls">{{ seg.text }}</span>
          </template>
        </div>
        <div class="calc-line">
          <span class="calc-label">{{ S.actualCooldown }}:</span>
          <span class="calc-value">{{ formatCooldownFixed(calculatedCooldown) }}
            <span v-if="showFrames">
              {{ frameRange() }}
            </span>
          </span>
          <template v-for="(seg, i) in cooldownSegments('actual')" :key="i">
            <span :class="seg.cls">{{ seg.text }}</span>
          </template>
          <span class="calc-pct"
            :class="cooldownChangePct < 0 ? 'pct-neg' : cooldownChangePct > 0 ? 'pct-pos' : ''">(DPS
            {{
              cooldownChangePct >= 0 ? '+' : '' }}{{ cooldownChangePct.toFixed(1) }}%)</span>
        </div>
        <div v-if="attackSpeedBreakpoints.length" class="calc-line breakpoint-line">
          <span class="calc-label">{{ S.attackSpeedBreakpoints }}:</span>
          <span class="calc-value breakpoint-list">
            <template v-for="(bp, i) in attackSpeedBreakpoints" :key="i">
              <span v-if="i > 0" class="bp-sep">,</span><span class="bp-item">{{ bp.aspd }}: +{{
                bp.dpsPct.toFixed(1) }}%</span>
            </template>
          </span>
        </div>
      </div>
      <div class="cooldown-chart-wrapper">
        <Line :data="chartData" :options="chartOptions" :plugins="[baseCooldownLinePlugin, currentPointPlugin]" />
      </div>
      <div class="slider-row">
        <label class="slider-label">{{ S.attackSpeed }}</label>
        <el-slider v-model="attackSpeedSlider" :min="-200" :max="500" :step="1" :marks="atkSpeedMarks" show-input
          size="small" />
      </div>
      <div v-if="activeWeaponData.type === 'melee'" class="slider-row">
        <label class="slider-label">
          <el-tooltip :content="S.rangeInfo" placement="top" :show-after="200">
            <el-icon class="range-help-icon">
              <QuestionFilled />
            </el-icon>
          </el-tooltip>
          {{ S.statRange }}
        </label>
        <el-slider v-model="statRangeSlider" :min="-200" :max="200" :step="1" :marks="rangeMarks" show-input
          size="small" />
      </div>
      <div class="slider-row">
        <label class="slider-label">{{ S.weaponCount }}</label>
        <el-slider v-model="weaponCountSlider" :min="1" :max="6" :step="1" :marks="weaponCountMarks" show-input
          size="small" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { QuestionFilled } from '@element-plus/icons-vue'
import { Line } from 'vue-chartjs'
import { Chart as ChartJS, LinearScale, PointElement, LineElement, Tooltip } from 'chart.js'

import {
  activeTab, activeWeaponData, attackSpeedSlider, statRangeSlider, weaponCountSlider, isDark,
  totalCooldown, calculatedCooldown, calculatedTooltipCooldown, calculatedReloadCooldowns,
  showAttackSpeedCalc, cooldownSegments, showFrames, frameRange, cooldownChangePct,
  attackSpeedBreakpoints, atkSpeedMarks, rangeMarks, weaponCountMarks, S,
  formatCooldown, formatCooldownFixed, calculateCooldownWithAttackSpeed,
} from '../store/codexStore'

ChartJS.register(LinearScale, PointElement, LineElement, Tooltip)

const chartData = computed(() => {
  const stats = activeWeaponData.value?.stats
  if (!stats) return { datasets: [] }

  const minAtkSpd = -100
  const maxAtkSpd = 202
  const hasRange = activeWeaponData.value?.type === 'melee' && statRangeSlider.value !== 0
  const mainPoints = []
  const basePoints = []

  for (let atkSpd = minAtkSpd; atkSpd <= maxAtkSpd; atkSpd += 1) {
    mainPoints.push({ x: atkSpd, y: calculateCooldownWithAttackSpeed(stats, atkSpd, statRangeSlider.value, weaponCountSlider.value) })
    if (hasRange) {
      basePoints.push({ x: atkSpd, y: calculateCooldownWithAttackSpeed(stats, atkSpd, 0) })
    }
  }

  const dark = isDark.value
  const datasets = []
  if (hasRange) {
    datasets.push({
      data: basePoints,
      borderColor: dark ? '#888' : '#bbb',
      borderWidth: 1.5,
      pointRadius: 0,
      tension: 0.3,
    })
  }
  datasets.push({
    data: mainPoints,
    borderColor: dark ? '#4ade80' : '#22c55e',
    borderWidth: 2,
    pointRadius: 0,
    tension: 0.3,
  })

  return { datasets }
})

const baseCooldownLinePlugin = {
  id: 'baseCooldownLine',
  afterDraw(chart) {
    const baseCd = totalCooldown.value
    if (!baseCd) return
    const yScale = chart.scales.y
    const y = yScale.getPixelForValue(baseCd)
    if (y < yScale.top || y > yScale.bottom) return
    const ctx = chart.ctx
    ctx.save()
    ctx.beginPath()
    ctx.setLineDash([6, 3])
    ctx.strokeStyle = isDark.value ? '#f87171' : '#ef4444'
    ctx.lineWidth = 1
    ctx.moveTo(chart.chartArea.left, y)
    ctx.lineTo(chart.chartArea.right, y)
    ctx.stroke()
    ctx.restore()
  }
}

const currentPointPlugin = {
  id: 'currentPoint',
  afterDraw(chart) {
    const xScale = chart.scales.x
    const yScale = chart.scales.y
    if (!xScale || !yScale || !chart.chartArea) return

    const val = attackSpeedSlider.value
    const datasets = chart.data.datasets
    if (!datasets.length) return

    const lastDs = datasets[datasets.length - 1].data
    if (!lastDs || !lastDs.length) return

    let closest = lastDs[0]
    let minDist = Infinity
    lastDs.forEach(pt => {
      const d = Math.abs(pt.x - val)
      if (d < minDist) { minDist = d; closest = pt }
    })
    if (!closest) return

    const x = xScale.getPixelForValue(closest.x)
    const y = yScale.getPixelForValue(closest.y)
    const ctx = chart.ctx
    ctx.save()
    ctx.beginPath()
    ctx.arc(x, y, 4, 0, Math.PI * 2)
    ctx.fillStyle = isDark.value ? '#f87171' : '#ef4444'
    ctx.fill()
    ctx.restore()
  }
}

const chartOptions = computed(() => {
  const dark = isDark.value
  const _atkSpd = attackSpeedSlider.value // dependency so chart re-renders on slider change
  return {
    responsive: true,
    maintainAspectRatio: true,
    aspectRatio: 3,
    animation: false,
    plugins: {
      legend: { display: false },
      tooltip: {
        mode: 'index',
        intersect: false,
        callbacks: {
          label: (ctx) => ctx.parsed.y.toFixed(3),
        },
      },
    },
    scales: {
      x: {
        type: 'linear',
        min: -100,
        max: 202,
        grid: { color: dark ? '#333' : '#e5e5e5' },
        ticks: { color: dark ? '#aaa' : '#666', font: { size: 10 }, stepSize: 25 },
      },
      y: {
        min: 0,
        grid: { color: dark ? '#333' : '#e5e5e5' },
        ticks: { color: dark ? '#aaa' : '#666', font: { size: 10 }, callback: (v) => v.toFixed(2) },
      },
    },
  }
})
</script>
