<template>
  <div class="key-card" :class="statusClass">
    <!-- 卡片头部 -->
    <div class="card-header">
      <div class="header-left">
        <el-tag :type="categoryTag" size="small" effect="dark" class="cat-tag">
          {{ entry.category }}
        </el-tag>
        <!-- Base / DLC1 来源标签 -->
        <el-tag
          v-for="src in entry.sources"
          :key="src"
          size="small"
          effect="dark"
          :type="srcTagType(src)"
          class="src-tag"
        >
          {{ srcLabel(src) }}
        </el-tag>
        <span class="key-name mono">{{ entry.final_key }}</span>
        <el-tag v-if="status === 'matched'" type="success" size="small" effect="dark" round>已匹配 {{ matchedId }}</el-tag>
        <el-tag v-else-if="status === 'manual'" type="warning" size="small" effect="dark" round>手动输入</el-tag>
        <el-tag v-else-if="status === 'skipped'" type="info" size="small" effect="dark" round>已跳过</el-tag>
      </div>
      <div class="header-right">
        <el-tooltip :content="`出现 ${entry.occurrence_count} 次`" placement="top">
          <el-badge :value="entry.occurrence_count" type="primary" class="occ-badge">
            <el-icon><Histogram /></el-icon>
          </el-badge>
        </el-tooltip>
        <el-button text size="small" @click="showContext = !showContext">
          <el-icon><InfoFilled /></el-icon>
          {{ showContext ? '收起' : '上下文' }}
        </el-button>
      </div>
    </div>

    <!-- 来源信息 -->
    <div class="sources">
      <el-icon><Location /></el-icon>
      <el-tag
        v-for="name in displaySources"
        :key="name"
        size="small"
        type="info"
        effect="plain"
        class="source-tag"
      >
        {{ name }}
      </el-tag>
      <el-tooltip
        v-if="entry.source_names.length > maxSources"
        :content="entry.source_names.slice(maxSources).join(', ')"
        placement="top"
      >
        <el-tag size="small" type="info" effect="plain">+{{ entry.source_names.length - maxSources }}</el-tag>
      </el-tooltip>
      <span class="source-types">{{ entry.source_types.join(' / ') }}</span>
    </div>

    <!-- 上下文信息（展开） -->
    <el-collapse-transition>
      <div v-show="showContext" class="context-section">
        <div class="context-title">
          <el-icon><Document /></el-icon>
          原始数据（key / text_key / 出现位置）
        </div>
        <table class="context-table">
          <tbody>
            <tr>
              <td class="ctx-label">原始 key</td>
              <td class="mono">{{ entry.key || '(空)' }}</td>
            </tr>
            <tr>
              <td class="ctx-label">text_key</td>
              <td class="mono">{{ entry.text_key || '(空，使用 key)' }}</td>
            </tr>
          </tbody>
        </table>
        <div class="context-files">
          <div v-for="(ctx, i) in entry.sample_contexts" :key="i" class="context-file">
            <el-tag size="small" effect="dark" :type="srcTagType(ctx.source)" class="ctx-src-tag">{{ srcLabel(ctx.source) }}</el-tag>
            <span class="mono file-path">{{ ctx.path }}</span>
            <el-tag size="small" effect="plain">value={{ ctx.value }}</el-tag>
            <el-tag v-if="ctx.script" size="small" type="info" effect="plain">{{ shortScript(ctx.script) }}</el-tag>
          </div>
        </div>
      </div>
    </el-collapse-transition>

    <!-- ============ 已匹配/手动输入结果展示区 ============ -->
    <el-collapse-transition>
      <div v-if="status !== 'unmatched'" class="result-section">
        <div class="result-title">
          <el-icon><CircleCheckFilled v-if="status==='matched'" /><EditPen v-else-if="status==='manual'" /><RemoveFilled v-else /></el-icon>
          {{ status === 'matched' ? '已匹配的字符串' : status === 'manual' ? '手动输入' : '已跳过' }}
          <span v-if="status === 'matched' && usedElsewhere" class="warn-used">
            （该候选已被其他键使用：{{ usedElsewhere }}）
          </span>
        </div>
        <div v-if="status !== 'skipped'" class="result-rows">
          <div class="result-row">
            <label class="r-label">EN</label>
            <el-input v-model="editEn" type="textarea" :autosize="{ minRows: 1, maxRows: 3 }" @input="onManualEdit" />
          </div>
          <div class="result-row">
            <label class="r-label">ZH</label>
            <el-input v-model="editZh" type="textarea" :autosize="{ minRows: 1, maxRows: 3 }" @input="onManualEdit" />
          </div>
        </div>
        <div class="result-actions">
          <el-button size="small" @click="unmatch" v-if="status !== 'skipped'">取消匹配</el-button>
          <el-button size="small" @click="unskip" v-else>取消跳过</el-button>
          <el-button size="small" type="info" plain @click="skip" v-if="status !== 'skipped'">标记跳过</el-button>
        </div>
      </div>
    </el-collapse-transition>

    <!-- ============ 候选匹配区（未匹配时显示） ============ -->
    <div v-if="status === 'unmatched'" class="candidate-section">
      <div class="candidate-toolbar">
        <el-input
          v-model="searchInput"
          placeholder="搜索候选字符串（EN/ZH/编号）..."
          :prefix-icon="Search"
          clearable
          size="small"
          class="cand-search"
        />
        <el-tooltip content="用键名核心词自动搜索" placement="top">
          <el-button size="small" @click="autoSearch" :icon="MagicStick">自动推荐</el-button>
        </el-tooltip>
        <el-button size="small" text @click="switchToManual">
          <el-icon><EditPen /></el-icon> 手动输入
        </el-button>
      </div>

      <div class="candidate-list" v-if="filteredCandidates.length">
        <div
          v-for="cand in filteredCandidates"
          :key="cand.id"
          class="candidate-item"
          :class="{ recommended: cand.recommended, used: isUsed(cand.id) }"
          @click="selectCandidate(cand)"
        >
          <div class="cand-header">
            <span class="cand-n">{{ cand.id }}</span>
            <el-tag size="small" effect="dark" :type="srcTagType(cand.source)">{{ srcLabel(cand.source) }}</el-tag>
            <el-icon v-if="cand.recommended" class="rec-icon"><StarFilled /></el-icon>
            <el-tag v-if="isUsed(cand.id)" size="small" type="warning" effect="plain">已用于 {{ usedBy(cand.id) }}</el-tag>
            <el-tag v-if="cand.zh === cand.en" size="small" type="info" effect="plain">未翻译</el-tag>
          </div>
          <div class="cand-en">{{ cand.en }}</div>
          <div class="cand-zh">{{ cand.zh }}</div>
        </div>
      </div>
      <el-empty v-else description="无匹配候选" :image-size="50" />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { Search, MagicStick, EditPen } from '@element-plus/icons-vue'

const props = defineProps({
  entry: { type: Object, required: true },
  saved: { type: Object, default: null },
  candidates: { type: Array, default: () => [] },
  usedMap: { type: Object, default: () => ({}) }
})

const emit = defineEmits(['update'])

const showContext = ref(false)
const maxSources = 8
const searchInput = ref('')
const autoSearchInput = ref('')

// 本地状态
const status = ref(props.saved?.status || 'unmatched')
const matchedId = ref(props.saved?.matchedN ?? null) // 现在存的是 "B_123" / "D_45" 格式
const editEn = ref(props.saved?.en || '')
const editZh = ref(props.saved?.zh || '')

watch(() => props.saved, (val) => {
  if (val) {
    status.value = val.status || 'unmatched'
    matchedId.value = val.matchedN ?? null
    editEn.value = val.en || ''
    editZh.value = val.zh || ''
  } else {
    status.value = 'unmatched'
    matchedId.value = null
    editEn.value = ''
    editZh.value = ''
  }
}, { deep: true })

const statusClass = computed(() => ({
  matched: status.value === 'matched',
  manual: status.value === 'manual',
  skipped: status.value === 'skipped'
}))

const categoryTag = computed(() => {
  const map = { stat: 'warning', effect: 'primary', other: 'info' }
  return map[props.entry.category] || 'info'
})

const displaySources = computed(() => props.entry.source_names.slice(0, maxSources))

// 来源标签辅助函数
function srcLabel(src) {
  return src === 'dlc1' ? 'DLC1' : 'Base'
}
function srcTagType(src) {
  return src === 'dlc1' ? 'danger' : 'primary'
}

// 从键名提取核心搜索词
const coreKeywords = computed(() => {
  const key = props.entry.final_key.replace(/^(EFFECT_|STAT_)/, '')
  return key.toLowerCase().split('_').filter(w => w.length > 2 && !['the', 'and', 'for', 'with'].includes(w))
})

// 候选过滤 + 推荐
const filteredCandidates = computed(() => {
  let list = props.candidates
  const q = (searchInput.value.trim() || autoSearchInput.value.trim()).toLowerCase()

  if (q) {
    const tokens = q.split(/\s+/).filter(Boolean)
    list = list.filter(c => {
      const en = (c.en || '').toLowerCase()
      const zh = (c.zh || '').toLowerCase()
      const idStr = String(c.id || '').toLowerCase()
      return tokens.every(t => en.includes(t) || zh.includes(t) || idStr.includes(t))
    })
  }

  // 推荐排序：核心词命中越多越靠前
  const scored = list.map(c => {
    const en = (c.en || '').toLowerCase()
    let score = 0
    for (const kw of coreKeywords.value) {
      if (en.includes(kw)) score += 10
    }
    for (const src of props.entry.source_names) {
      if (en.includes(src.toLowerCase())) score += 5
    }
    return { ...c, _score: score, recommended: score >= 10 }
  })

  scored.sort((a, b) => b._score - a._score)
  return scored.slice(0, 30)
})

const isUsed = (id) => id in props.usedMap && props.usedMap[id] !== props.entry.final_key
const usedBy = (id) => props.usedMap[id]
const usedElsewhere = computed(() => {
  if (matchedId.value == null) return null
  const k = props.usedMap[matchedId.value]
  return k && k !== props.entry.final_key ? k : null
})

function autoSearch() {
  autoSearchInput.value = coreKeywords.value.slice(0, 3).join(' ')
}

function selectCandidate(cand) {
  status.value = 'matched'
  matchedId.value = cand.id
  editEn.value = cand.en
  editZh.value = cand.zh
  emitUpdate()
}

function switchToManual() {
  status.value = 'manual'
  matchedId.value = null
  if (!editEn.value) editEn.value = ''
  if (!editZh.value) editZh.value = ''
  emitUpdate()
}

function onManualEdit() {
  if (status.value === 'matched') {
    status.value = 'manual'
    matchedId.value = null
  }
  emitUpdate()
}

function unmatch() {
  status.value = 'unmatched'
  matchedId.value = null
  editEn.value = ''
  editZh.value = ''
  autoSearch()
  emitUpdate()
}

function unskip() {
  status.value = 'unmatched'
  autoSearch()
  emitUpdate()
}

function skip() {
  status.value = 'skipped'
  emitUpdate()
}

function emitUpdate() {
  emit('update', {
    key: props.entry.final_key,
    status: status.value,
    matchedN: matchedId.value,
    en: editEn.value,
    zh: editZh.value
  })
}

function shortScript(script) {
  return script.split('/').pop().replace('.gd', '')
}
</script>

<style scoped>
.key-card {
  background: #1e1e32;
  border: 1px solid #2a2a4a;
  border-radius: 8px;
  padding: 14px 16px;
  margin-bottom: 10px;
  transition: border-color 0.2s, box-shadow 0.2s;
}
.key-card:hover { border-color: #3a3a5a; }
.key-card.matched { border-left: 3px solid #67c23a; }
.key-card.manual { border-left: 3px solid #e6a23c; }
.key-card.skipped { opacity: 0.55; border-left: 3px solid #909399; }

.card-header {
  display: flex; justify-content: space-between; align-items: center;
  margin-bottom: 8px;
}
.header-left { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.header-right { display: flex; align-items: center; gap: 8px; }
.key-name { font-size: 15px; font-weight: 600; color: #e0e0f0; letter-spacing: 0.5px; }
.cat-tag { text-transform: uppercase; font-weight: 700; }
.src-tag { font-weight: 700; font-size: 11px; }
.occ-badge { margin-right: 4px; }

.sources {
  display: flex; align-items: center; flex-wrap: wrap; gap: 4px;
  margin-bottom: 8px; font-size: 12px; color: #8888aa;
}
.source-tag { font-size: 11px; }
.source-types { margin-left: 8px; color: #666688; font-style: italic; }

.context-section {
  margin: 8px 0; padding: 10px;
  background: #161628; border-radius: 6px; border: 1px solid #222238;
}
.context-title {
  display: flex; align-items: center; gap: 6px;
  font-size: 12px; color: #8888aa; margin-bottom: 6px;
  text-transform: uppercase; letter-spacing: 0.5px;
}
.context-table { width: 100%; font-size: 12px; margin-bottom: 8px; }
.context-table td { padding: 2px 8px 2px 0; color: #aaaacc; }
.ctx-label { color: #666688; white-space: nowrap; width: 80px; }
.context-files { display: flex; flex-direction: column; gap: 4px; }
.context-file { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.ctx-src-tag { font-size: 10px; }
.file-path { font-size: 11px; color: #7777aa; flex: 1; min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

/* 结果区 */
.result-section {
  margin-top: 10px; padding: 10px;
  background: #161628; border-radius: 6px; border: 1px solid #2a3a2a;
}
.key-card.manual .result-section { border-color: #3a3a1a; }
.key-card.skipped .result-section { border-color: #333340; }
.result-title {
  display: flex; align-items: center; gap: 6px;
  font-size: 12px; color: #67c23a; margin-bottom: 8px;
  text-transform: uppercase; letter-spacing: 0.5px;
}
.key-card.manual .result-title { color: #e6a23c; }
.key-card.skipped .result-title { color: #909399; }
.warn-used { color: #e6a23c; font-size: 11px; text-transform: none; }
.result-rows { display: flex; flex-direction: column; gap: 6px; }
.result-row { display: flex; align-items: flex-start; gap: 8px; }
.r-label { font-size: 12px; font-weight: 700; color: #6060a0; width: 24px; text-align: center; flex-shrink: 0; padding-top: 4px; }
.result-actions { display: flex; gap: 8px; margin-top: 8px; }

/* 候选区 */
.candidate-section { margin-top: 10px; }
.candidate-toolbar { display: flex; gap: 8px; margin-bottom: 8px; flex-wrap: wrap; align-items: center; }
.cand-search { flex: 1; min-width: 200px; }
.candidate-list {
  max-height: 340px; overflow-y: auto;
  border: 1px solid #2a2a44; border-radius: 6px;
  background: #161628;
}
.candidate-item {
  padding: 8px 12px; border-bottom: 1px solid #222238;
  cursor: pointer; transition: background 0.15s;
}
.candidate-item:last-child { border-bottom: none; }
.candidate-item:hover { background: #1e1e38; }
.candidate-item.recommended { background: #1a2a1a; border-left: 3px solid #67c23a; }
.candidate-item.recommended:hover { background: #223a22; }
.candidate-item.used { opacity: 0.6; }
.cand-header { display: flex; align-items: center; gap: 6px; margin-bottom: 3px; flex-wrap: wrap; }
.cand-n { font-size: 11px; font-weight: 700; color: #6060a0; font-family: monospace; }
.rec-icon { color: #e6a23c; font-size: 12px; }
.cand-en { font-size: 13px; color: #ccccee; line-height: 1.4; }
.cand-zh { font-size: 13px; color: #67c23a; line-height: 1.4; margin-top: 2px; }
</style>
