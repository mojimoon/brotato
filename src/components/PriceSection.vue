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
            <th>5</th>
            <th>10</th>
            <th>15</th>
            <th>19</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td>{{ isMobile ? S.belowNightmareShort : S.belowNightmare }}</td>
            <td>+{{ formatIncr(getWaveIncrement()) }}</td>
            <td class="price-base price-final">{{ waveSlider > 0 ? computedPrice : getBasePrice() }}</td>
            <td>{{ showPriceCell(1) ? priceAtWave(1) : '' }}</td>
            <td>{{ showPriceCell(5) ? priceAtWave(5) : '' }}</td>
            <td>{{ priceAtWave(10) }}</td>
            <td>{{ priceAtWave(15) }}</td>
            <td>{{ priceAtWave(19) }}</td>
          </tr>
          <tr>
            <td>{{ isMobile ? S.nightmareShort : S.nightmare }}</td>
            <td>+{{ formatIncr(getWaveIncrementNM()) }}</td>
            <td class="price-base price-final-nightmare">{{ waveSlider > 0 ? computedPriceNM : getBasePrice() }}
            </td>
            <td>{{ showPriceCell(1) ? priceAtWaveNM(1) : '' }}</td>
            <td>{{ showPriceCell(5) ? priceAtWaveNM(5) : '' }}</td>
            <td>{{ priceAtWaveNM(10) }}</td>
            <td>{{ priceAtWaveNM(15) }}</td>
            <td>{{ priceAtWaveNM(19) }}</td>
          </tr>
        </tbody>
      </table>
      <div class="price-slider-row">
        <span class="wave-label">{{ S.wave }}</span>
        <el-slider v-model="waveSlider" :min="0" :max="19" :step="1" :marks="waveSliderMarks" class="price-slider"
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
