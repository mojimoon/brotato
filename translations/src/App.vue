<template>
  <div class="app-container">
    <!-- 头部 -->
    <header class="app-header">
      <div class="header-title">
        <h1>Brotato 翻译键值修复</h1>
        <span class="subtitle">从候选字符串池中匹配缺失的 effect 键值</span>
      </div>
      <div class="header-actions">
        <el-button @click="handleImport" :icon="Upload">导入</el-button>
        <el-button type="success" @click="handleExport" :icon="Download" :disabled="doneCount === 0">
          导出 JSON ({{ doneCount }}/{{ totalMissing }})
        </el-button>
        <input ref="fileInput" type="file" accept=".json" style="display:none" @change="onFileSelected" />
      </div>
    </header>

    <!-- 统计概览 -->
    <div v-if="mergedData" class="stats-overview">
      <div class="stat-item">
        <span class="stat-num">{{ mergedData.stats.total_effects }}</span>
        <span class="stat-label">effect 文件</span>
      </div>
      <div class="stat-item">
        <span class="stat-num">{{ mergedData.stats.unique_keys }}</span>
        <span class="stat-label">唯一键</span>
      </div>
      <div class="stat-item">
        <span class="stat-num green">{{ mergedData.stats.known_count }}</span>
        <span class="stat-label">已知</span>
      </div>
      <div class="stat-item">
        <span class="stat-num red">{{ mergedData.stats.missing_count }}</span>
        <span class="stat-label">缺失</span>
      </div>
      <el-divider direction="vertical" />
      <div class="stat-item">
        <span class="stat-num blue">{{ matchedCount }}</span>
        <span class="stat-label">已匹配</span>
      </div>
      <div class="stat-item">
        <span class="stat-num orange">{{ manualCount }}</span>
        <span class="stat-label">手动</span>
      </div>
      <div class="stat-item">
        <span class="stat-num gray">{{ skippedCount }}</span>
        <span class="stat-label">跳过</span>
      </div>
      <el-progress
        :percentage="progressPercent"
        :stroke-width="6"
        :show-text="false"
        class="progress-bar"
        :color="progressColor"
      />
      <span class="progress-text">{{ progressPercent }}%</span>
    </div>

    <!-- 筛选栏 -->
    <div v-if="mergedData" class="filter-bar">
      <el-input
        v-model="searchQuery"
        placeholder="搜索键名或来源..."
        :prefix-icon="Search"
        clearable
        class="search-input"
      />
      <el-radio-group v-model="categoryFilter" class="cat-filter">
        <el-radio-button value="all">全部 ({{ mergedData.stats.missing_count }})</el-radio-button>
        <el-radio-button value="effect">effect ({{ mergedData.stats.by_category.effect }})</el-radio-button>
        <el-radio-button value="stat">stat ({{ mergedData.stats.by_category.stat }})</el-radio-button>
        <el-radio-button value="other">other ({{ mergedData.stats.by_category.other }})</el-radio-button>
      </el-radio-group>
      <el-radio-group v-model="sourceFilter" class="source-filter">
        <el-radio-button value="all">全部</el-radio-button>
        <el-radio-button value="base">Base</el-radio-button>
        <el-radio-button value="dlc1">DLC1</el-radio-button>
        <el-radio-button value="both">共有</el-radio-button>
      </el-radio-group>
      <el-radio-group v-model="statusFilter" class="status-filter">
        <el-radio-button value="all">全部</el-radio-button>
        <el-radio-button value="unmatched">未处理</el-radio-button>
        <el-radio-button value="done">已处理</el-radio-button>
        <el-radio-button value="skipped">已跳过</el-radio-button>
      </el-radio-group>
    </div>

    <!-- 加载状态 -->
    <div v-if="loading" class="loading">
      <el-icon class="is-loading"><Loading /></el-icon>
      加载数据中...
    </div>

    <!-- 缺失键列表 -->
    <div v-else-if="mergedData && filteredKeys.length" class="key-list">
      <KeyCard
        v-for="entry in filteredKeys"
        :key="entry.final_key"
        :entry="entry"
        :saved="getSaved(entry.final_key)"
        :candidates="mergedData.csv_missing_keys"
        :used-map="usedMap"
        @update="(val) => onUpdate(entry.final_key, val)"
      />
    </div>

    <!-- 空状态 -->
    <el-empty v-else-if="mergedData" description="没有匹配的缺失键" />
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Search, Upload, Download, Loading } from '@element-plus/icons-vue'
import KeyCard from './components/KeyCard.vue'

const loading = ref(true)
const searchQuery = ref('')
const categoryFilter = ref('all')
const sourceFilter = ref('all')
const statusFilter = ref('all')
const fileInput = ref(null)

const mergedData = ref(null)

// 用户匹配状态: { KEY: { status, matchedN, en, zh } }
const saved = reactive({})

const totalMissing = computed(() => mergedData.value?.stats.missing_count || 0)

// 各状态计数
const matchedCount = computed(() => Object.values(saved).filter(v => v.status === 'matched').length)
const manualCount = computed(() => Object.values(saved).filter(v => v.status === 'manual').length)
const skippedCount = computed(() => Object.values(saved).filter(v => v.status === 'skipped').length)
const doneCount = computed(() => matchedCount.value + manualCount.value)

const progressPercent = computed(() => {
  if (totalMissing.value === 0) return 0
  return Math.round(((doneCount.value + skippedCount.value) / totalMissing.value) * 100)
})

const progressColor = computed(() => {
  if (progressPercent.value === 100) return '#67c23a'
  if (progressPercent.value >= 50) return '#409eff'
  return '#e6a23c'
})

// 候选使用映射: { id: keyName }
const usedMap = computed(() => {
  const m = {}
  for (const [key, val] of Object.entries(saved)) {
    if (val.status === 'matched' && val.matchedN != null) {
      m[val.matchedN] = key
    }
  }
  return m
})

// 筛选后的缺失键
const filteredKeys = computed(() => {
  if (!mergedData.value) return []
  let keys = [...mergedData.value.missing_keys]

  if (categoryFilter.value !== 'all') {
    keys = keys.filter(k => k.category === categoryFilter.value)
  }

  if (sourceFilter.value === 'base') {
    keys = keys.filter(k => k.sources.includes('base'))
  } else if (sourceFilter.value === 'dlc1') {
    keys = keys.filter(k => k.sources.includes('dlc1'))
  } else if (sourceFilter.value === 'both') {
    keys = keys.filter(k => k.sources.length >= 2)
  }

  if (searchQuery.value.trim()) {
    const q = searchQuery.value.toLowerCase()
    keys = keys.filter(k =>
      k.final_key.toLowerCase().includes(q) ||
      k.key.toLowerCase().includes(q) ||
      k.text_key.toLowerCase().includes(q) ||
      k.source_names.some(n => n.toLowerCase().includes(q))
    )
  }

  if (statusFilter.value === 'unmatched') {
    keys = keys.filter(k => {
      const s = saved[k.final_key]
      return !s || s.status === 'unmatched'
    })
  } else if (statusFilter.value === 'done') {
    keys = keys.filter(k => {
      const s = saved[k.final_key]
      return s && (s.status === 'matched' || s.status === 'manual')
    })
  } else if (statusFilter.value === 'skipped') {
    keys = keys.filter(k => {
      const s = saved[k.final_key]
      return s && s.status === 'skipped'
    })
  }

  return keys
})

function getSaved(key) {
  return saved[key] || null
}

function onUpdate(key, val) {
  saved[key] = {
    status: val.status,
    matchedN: val.matchedN,
    en: val.en,
    zh: val.zh
  }
  saveToStorage()
}

// localStorage 持久化
const STORAGE_KEY = 'brotato-translations-fix-merged-v1'

function saveToStorage() {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(saved))
  } catch (e) {
    console.warn('保存失败', e)
  }
}

function loadFromStorage() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (raw) {
      const parsed = JSON.parse(raw)
      Object.assign(saved, parsed || {})
    }
  } catch (e) {
    console.warn('加载失败', e)
  }
}

// 导出 JSON
function handleExport() {
  const missingKeys = mergedData.value.missing_keys

  const entries = missingKeys.map(k => {
    const sv = saved[k.final_key] || { status: 'unmatched', matchedN: null, en: '', zh: '' }
    return {
      key: k.final_key,
      category: k.category,
      original_key: k.key,
      text_key: k.text_key,
      sources: k.sources,
      status: sv.status,
      matched_missing_key_id: sv.matchedN,
      en: sv.en || '',
      zh: sv.zh || '',
      source_names: k.source_names,
      occurrence_count: k.occurrence_count
    }
  })

  const result = {
    label: 'merged',
    exported_at: new Date().toISOString(),
    total: entries.length,
    matched: entries.filter(e => e.status === 'matched').length,
    manual: entries.filter(e => e.status === 'manual').length,
    skipped: entries.filter(e => e.status === 'skipped').length,
    unmatched: entries.filter(e => e.status === 'unmatched').length,
    entries
  }

  const blob = new Blob([JSON.stringify(result, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `translations_merged_${new Date().toISOString().slice(0, 10)}.json`
  a.click()
  URL.revokeObjectURL(url)

  ElMessage.success(`已导出（匹配 ${result.matched}，手动 ${result.manual}，跳过 ${result.skipped}，未处理 ${result.unmatched}）`)
}

// 导入 JSON（兼容旧格式 base/dlc1 + 新格式 merged）
function handleImport() {
  fileInput.value.click()
}

function onFileSelected(e) {
  const file = e.target.files[0]
  if (!file) return

  const reader = new FileReader()
  reader.onload = (ev) => {
    try {
      const result = JSON.parse(ev.target.result)
      if (!result.entries || !Array.isArray(result.entries)) {
        ElMessage.error('JSON 格式不正确')
        return
      }

      let count = 0
      for (const entry of result.entries) {
        if (!entry.key) continue

        // 兼容旧格式：matched_missing_key_n (旧) vs matched_missing_key_id (新)
        let matchedN = entry.matched_missing_key_id ?? entry.matched_missing_key_n ?? entry.matchedN ?? null

        // 旧格式候选 N 是纯数字（base 的 MissingKey N），
        // 新格式是 "B_{n}" / "D_{n}"。
        // 旧导入只有 base 数据，将纯数字转为 "B_{n}"
        if (matchedN != null && typeof matchedN === 'number') {
          matchedN = `B_${matchedN}`
        }

        saved[entry.key] = {
          status: entry.status || 'unmatched',
          matchedN: matchedN,
          en: entry.en || '',
          zh: entry.zh || ''
        }
        count++
      }
      saveToStorage()
      ElMessage.success(`已导入 ${count} 条记录`)
    } catch (err) {
      ElMessage.error('解析 JSON 失败: ' + err.message)
    }
  }
  reader.readAsText(file)
  e.target.value = ''
}

// 加载数据
async function loadData() {
  loading.value = true
  try {
    const res = await fetch('./merged_analysis.json')
    mergedData.value = await res.json()
    loadFromStorage()
  } catch (e) {
    ElMessage.error('加载数据失败: ' + e.message)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  document.documentElement.classList.add('dark')
  loadData()
})
</script>

<style scoped>
.app-container {
  max-width: 1100px;
  margin: 0 auto;
  padding: 20px;
  min-height: 100vh;
}

.app-header {
  display: flex; justify-content: space-between; align-items: center;
  margin-bottom: 16px; padding-bottom: 12px;
  border-bottom: 1px solid #2a2a44;
}
.header-title h1 { font-size: 22px; color: #e0e0f0; }
.subtitle { font-size: 12px; color: #666688; margin-left: 8px; }
.header-actions { display: flex; gap: 8px; }

.stats-overview {
  display: flex; align-items: center; gap: 18px;
  padding: 10px 0; flex-wrap: wrap;
}
.stat-item { display: flex; flex-direction: column; align-items: center; }
.stat-num { font-size: 20px; font-weight: 700; color: #e0e0f0; }
.stat-num.green { color: #67c23a; }
.stat-num.red { color: #f56c6c; }
.stat-num.blue { color: #409eff; }
.stat-num.orange { color: #e6a23c; }
.stat-num.gray { color: #909399; }
.stat-label { font-size: 11px; color: #666688; margin-top: 2px; }
.progress-bar { flex: 1; min-width: 80px; max-width: 160px; }
.progress-text { font-size: 12px; color: #8888aa; }

.filter-bar {
  display: flex; gap: 12px; margin-bottom: 16px;
  flex-wrap: wrap; align-items: center;
}
.search-input { width: 240px; }
.cat-filter, .source-filter, .status-filter { flex-shrink: 0; }

.loading { text-align: center; padding: 60px; color: #666688; font-size: 14px; }
.loading .el-icon { margin-right: 6px; }

.key-list { padding-bottom: 40px; }
</style>
