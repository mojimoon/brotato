<template>
  <div v-if="showPriceSection" class="detail-section">
    <div class="price-toggle" @click="showPriceDetail = !showPriceDetail">
      <span class="toggle-icon">{{ showPriceDetail ? '▼' : '▶' }}</span>
      <span>{{ S.basePrice }}</span>
      <span class="price-base">{{ getBasePrice() }}
        <img :src="priceIconSrc" class="price-icon" />
      </span>
    </div>
    <div v-if="showPriceDetail" class="price-section">
      <table class="price-table">
        <thead>
          <tr>
            <th></th>
            <th>{{ S.perWave }}</th>
            <th>{{ S.wave }} {{ waveSlider }}</th>
            <th>1</th>
            <th>4</th>
            <th>8</th>
            <th>14</th>
            <th>19</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td>{{ isMobile ? S.belowNightmareShort : S.belowNightmare }}</td>
            <td>+{{ formatIncr(getWaveIncrement()) }}</td>
            <td class="price-base price-final">{{ waveSlider > 0 ? computedPrice : getBasePrice() }}</td>
            <td>{{ showPriceCell(1) ? priceAtWave(1) : '' }}</td>
            <td>{{ showPriceCell(4) ? priceAtWave(4) : '' }}</td>
            <td>{{ priceAtWave(8) }}</td>
            <td>{{ priceAtWave(14) }}</td>
            <td>{{ priceAtWave(19) }}</td>
          </tr>
          <tr>
            <td>{{ isMobile ? S.nightmareShort : S.nightmare }}</td>
            <td>+{{ formatIncr(getWaveIncrementNM()) }}</td>
            <td class="price-base price-final-nightmare">{{ waveSlider > 0 ? computedPriceNM : getBasePrice() }}
            </td>
            <td>{{ showPriceCell(1) ? priceAtWaveNM(1) : '' }}</td>
            <td>{{ showPriceCell(4) ? priceAtWaveNM(4) : '' }}</td>
            <td>{{ priceAtWaveNM(8) }}</td>
            <td>{{ priceAtWaveNM(14) }}</td>
            <td>{{ priceAtWaveNM(19) }}</td>
          </tr>
        </tbody>
      </table>
      <div class="price-slider-row">
        <span class="wave-label">{{ S.wave }}</span>
        <el-slider v-model="waveSlider" :min="0" :max="20" :step="1" :marks="waveSliderMarks" class="price-slider"
          placement="bottom" size="small" show-input />
      </div>
    </div>
  </div>
</template>

<script setup>
import {
  showPriceSection, showPriceDetail, S, getBasePrice, priceIconSrc, computedPrice, isMobile,
  waveSlider, showPriceCell, formatIncr, getWaveIncrement, getWaveIncrementNM, priceAtWave,
  priceAtWaveNM, computedPriceNM, waveSliderMarks,
} from '../store/codexStore'
</script>
