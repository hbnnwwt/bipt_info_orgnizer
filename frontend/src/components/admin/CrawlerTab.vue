<template>
  <div class="crawler-tab">
    <!-- ── Toolbar: KPI stats + actions ── -->
    <div class="crawler-toolbar">
      <div class="toolbar-left">
        <!-- KPI row -->
        <div class="kpi-row">
          <div class="kpi-stat" :class="crawlStatus.running ? 'kpi-active' : 'kpi-idle'">
            <span class="kpi-dot"></span>
            <span class="kpi-label">{{ crawlStatus.running ? '爬取中' : '空闲' }}</span>
          </div>
          <div class="kpi-divider"></div>
          <div class="kpi-stat">
            <span class="kpi-num">{{ stats.total }}</span>
            <span class="kpi-sub">总配置</span>
          </div>
          <div class="kpi-divider"></div>
          <div class="kpi-stat">
            <span class="kpi-num">{{ stats.enabled }}</span>
            <span class="kpi-sub">已启用</span>
          </div>
          <div class="kpi-divider"></div>
          <div class="kpi-stat">
            <span class="kpi-num">{{ stats.crawled }}</span>
            <span class="kpi-sub">已爬取</span>
          </div>
        </div>

        <!-- Overall progress (only when running) -->
        <div v-if="crawlStatus.running && crawlProgress.total_configs > 0" class="crawl-overall-progress">
          <div class="overall-top">
            <span class="overall-label">整体进度 · {{ crawlProgress.config_index }}/{{ crawlProgress.total_configs }} 配置</span>
            <span v-if="currentConfigSpeed > 0" class="speed-label">{{ currentConfigSpeed }} 篇/秒</span>
          </div>
          <div class="overall-track">
            <div class="overall-fill" :style="{ width: overallPercent + '%' }"></div>
          </div>
        </div>
      </div>

      <div class="toolbar-actions">
        <button v-if="!crawlStatus.running" @click="showTriggerModal = true" class="btn-primary btn-sm" :disabled="crawlLoading">
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="5 3 19 12 5 21 5 3"/></svg>
          手动触发爬取
        </button>
        <button v-else @click="stopCrawl" class="btn-danger btn-sm">
          <svg width="13" height="13" viewBox="0 0 24 24" fill="currentColor"><rect x="6" y="6" width="12" height="12" rx="1"/></svg>
          停止爬取
        </button>
        <button @click="importNavigation" class="btn-outline btn-sm" :disabled="navLoading">
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
          {{ navLoading ? '导入中…' : '从首页导入导航' }}
        </button>
        <button @click="showLogs = !showLogs" class="btn-outline btn-sm">
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/></svg>
          {{ showLogs ? '隐藏日志' : '显示日志' }}
        </button>
        <button @click="showAddForm = !showAddForm" class="btn-outline btn-sm" :class="{ 'btn-active': showAddForm }">
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
          {{ showAddForm ? '收起' : '添加配置' }}
        </button>
      </div>
    </div>

    <!-- ── Trigger Crawl Modal ── -->
    <div v-if="showTriggerModal" class="modal-overlay" @click.self="showTriggerModal = false">
      <div class="modal-content">
        <div class="modal-header">
          <span class="modal-title">选择要爬取的配置</span>
          <button class="modal-close" @click="showTriggerModal = false" aria-label="关闭">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
          </button>
        </div>
        <div class="modal-search">
          <svg class="modal-search-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/></svg>
          <input v-model="modalSearch" type="search" placeholder="搜索配置…" class="modal-search-input" />
        </div>
        <div class="modal-body">
          <div class="select-all-row">
            <label class="checkbox-label">
              <input type="checkbox" v-model="selectAllConfigs" @change="toggleSelectAll" />
              <span>全选</span>
            </label>
            <span class="selected-count">{{ selectedConfigIds.length }} 已选</span>
          </div>
          <div class="config-select-list">
            <label
              v-for="c in filteredModalConfigs"
              :key="c.id"
              class="config-select-item"
            >
              <input type="checkbox" :value="c.id" v-model="selectedConfigIds" />
              <span class="config-select-name">{{ c.name }}</span>
              <span class="config-select-meta">{{ c.parent_category || '' }}</span>
            </label>
            <div v-if="filteredModalConfigs.length === 0" class="modal-empty">无匹配配置</div>
          </div>
        </div>
        <div class="modal-footer">
          <button @click="showTriggerModal = false" class="btn-outline btn-sm">取消</button>
          <button @click="triggerCrawl" class="btn-primary btn-sm" :disabled="selectedConfigIds.length === 0">
            爬取 {{ selectedConfigIds.length > 0 ? selectedConfigIds.length + ' 个' : '所选' }}
          </button>
        </div>
      </div>
    </div>

    <!-- ── Add config form (collapsible) ── -->
    <transition name="adv-fade">
      <div v-if="showAddForm" class="config-form">
        <div class="config-form-header">
          <span class="config-form-title">添加新配置</span>
          <button @click="showAdvanced = !showAdvanced" class="btn-ghost-xs toggle-advanced">
            {{ showAdvanced ? '收起高级' : '展开高级' }}
            <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" :style="{ transform: showAdvanced ? 'rotate(180deg)' : '' }">
              <path d="m6 9 6 6 6-6"/>
            </svg>
          </button>
        </div>
        <div class="config-form-grid">
          <input v-model="newConfig.name" type="text" placeholder="配置名称 *" class="input" />
          <input v-model="newConfig.url" type="url" placeholder="列表页URL *" class="input input-full" />
          <input v-model="newConfig.category" type="text" placeholder="分类标签" class="input" />
          <input v-model="newConfig.parent_category" type="text" placeholder="大类" class="input" />
          <input v-model="newConfig.sub_category" type="text" placeholder="小类" class="input" />
        </div>
        <transition name="adv-fade">
          <div v-if="showAdvanced" class="advanced-fields">
            <div class="config-form-grid">
              <label class="checkbox-label">
                <input type="checkbox" v-model="newConfig.is_list_page" />
                <span>列表页模式</span>
              </label>
              <input v-model="newConfig.article_selector" type="text" placeholder="文章链接选择器" class="input" />
              <input v-model="newConfig.link_prefix" type="text" placeholder="链接前缀" class="input" />
              <input v-model="newConfig.pagination_selector" type="text" placeholder="分页选择器" class="input" />
              <input v-model.number="newConfig.pagination_max" type="number" placeholder="最大页数" class="input" style="width:130px" />
              <input v-model="newConfig.selector" type="text" placeholder="内容CSS选择器" class="input" />
            </div>
          </div>
        </transition>
        <div class="config-form-actions">
          <button @click="addConfig" class="btn-primary btn-sm">添加配置</button>
          <button @click="loadPreset" class="btn-outline btn-sm">加载BIPT预设</button>
          <button @click="clearForm" class="btn-ghost-xs" style="margin-left:auto">清空</button>
        </div>
      </div>
    </transition>

    <!-- ── Config list ── -->
    <div class="config-list">
      <!-- Filter bar -->
      <div class="config-filters">
        <div class="filter-search-wrap">
          <svg class="filter-icon" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/></svg>
          <input v-model.lazy="filterSearch" type="search" placeholder="搜索配置…" class="filter-input" />
        </div>
        <select v-model="filterParent" class="filter-select">
          <option value="">全部大类</option>
          <option v-for="p in parentOptions" :key="p" :value="p">{{ p }}</option>
        </select>
        <select v-model="filterSub" class="filter-select" :disabled="!filterParent">
          <option value="">全部分类</option>
          <option v-for="s in subOptions" :key="s" :value="s">{{ s }}</option>
        </select>
        <span class="filter-count">{{ filteredConfigs.length }} / {{ configs.length }}</span>
      </div>

      <!-- Table or skeleton or empty -->
      <div class="table-wrapper">
        <table class="data-table">
          <thead>
            <tr>
              <th scope="col">名称</th>
              <th scope="col">大类</th>
              <th scope="col">小类</th>
              <th scope="col">模式</th>
              <th scope="col">间隔</th>
              <th scope="col">进度</th>
              <th scope="col">状态</th>
              <th scope="col">上次爬取</th>
              <th scope="col">操作</th>
            </tr>
          </thead>
          <tbody>
            <!-- Skeleton loading -->
            <template v-if="loading">
              <tr v-for="i in 4" :key="'sk-' + i" class="skeleton-row">
                <td><div class="sk sk-text sk-name"></div></td>
                <td><div class="sk sk-tag"></div></td>
                <td><div class="sk sk-tag"></div></td>
                <td><div class="sk sk-badge"></div></td>
                <td><div class="sk sk-select"></div></td>
                <td><div class="sk sk-progress"></div></td>
                <td><div class="sk sk-badge"></div></td>
                <td><div class="sk sk-time"></div></td>
                <td><div class="sk sk-actions"></div></td>
              </tr>
            </template>
            <!-- Config rows -->
            <template v-else>
              <tr v-for="c in filteredConfigs" :key="c.id">
                <td>
                  <a :href="c.url" target="_blank" class="link">{{ c.name }}</a>
                  <div class="cell-url">{{ c.url }}</div>
                </td>
                <td><span class="cell-tag">{{ c.parent_category || '—' }}</span></td>
                <td><span class="cell-tag">{{ c.sub_category || '—' }}</span></td>
                <td>
                  <span class="mode-badge" :class="c.initialized ? 'mode-incremental' : 'mode-full'">
                    {{ c.initialized ? '增量' : '全量' }}
                  </span>
                </td>
                <td class="cell-interval">
                  <select class="interval-select" :value="c.auto_interval_hours || 0" @change="updateInterval(c.id, Number($event.target.value))">
                    <option value="0">关闭</option>
                    <option value="4">4小时</option>
                    <option value="8">8小时</option>
                    <option value="12">12小时</option>
                    <option value="24">24小时</option>
                  </select>
                </td>
                <td class="cell-progress">
                  <template v-if="getConfigProgressStatus(c.id) === 'running'">
                    <div class="row-progress">
                      <div class="row-progress-track">
                        <div class="row-progress-fill" :style="{ width: getRowProgress(c.id) + '%' }"></div>
                      </div>
                      <span class="row-progress-label">
                        {{ getConfigProgress(c.id).page }}/{{ getConfigProgress(c.id).total_pages || '?' }}页 ·
                        {{ getConfigProgress(c.id).articles_crawled }}{{ getConfigProgress(c.id).articles_total > 0 ? '/' + getConfigProgress(c.id).articles_total : '' }}篇
                      </span>
                    </div>
                  </template>
                  <template v-else-if="c.last_crawl">
                    <span class="crawled-check">
                      <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"><polyline points="20 6 9 17 4 13"/></svg>
                      已爬
                    </span>
                  </template>
                  <template v-else>
                    <span class="not-crawled">—</span>
                  </template>
                </td>
                <td>
                  <span class="state-badge" :class="c.enabled ? 'state-on' : 'state-off'">
                    <span class="state-dot"></span>
                    {{ c.enabled ? '启用' : '禁用' }}
                  </span>
                </td>
                <td class="cell-time">{{ c.last_crawl?.slice(0, 16) || '—' }}</td>
                <td class="cell-actions">
                  <!-- Inline confirm delete -->
                  <template v-if="confirmingDelete === c.id">
                    <span class="inline-confirm">
                      <span class="inline-confirm-q">确认?</span>
                      <button @click="doDelete(c.id)" class="btn-confirm-yes btn-ghost-xs">是</button>
                      <button @click="confirmingDelete = null" class="btn-ghost-xs">否</button>
                    </span>
                  </template>
                  <template v-else>
                    <button @click="toggleConfig(c)" class="btn-ghost-xs">{{ c.enabled ? '禁用' : '启用' }}</button>
                    <button v-if="c.initialized" @click="confirmingReset === c.id ? doReset(c) : confirmingReset = c.id" class="btn-ghost-xs" :class="{ 'btn-danger-active': confirmingReset === c.id }">重置</button>
                    <button @click="confirmingDelete = c.id" class="btn-ghost-xs btn-text-danger">删除</button>
                  </template>
                </td>
              </tr>
              <!-- Empty state -->
              <tr v-if="configs.length > 0 && filteredConfigs.length === 0">
                <td colspan="9" class="cell-empty">
                  <div class="empty-state">
                    <svg class="empty-icon" width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.2"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/><line x1="8" y1="11" x2="14" y2="11"/></svg>
                    <span>没有匹配的过滤结果</span>
                    <button @click="clearFilters" class="btn-ghost-xs">清除过滤</button>
                  </div>
                </td>
              </tr>
            </template>
            <!-- Global empty -->
            <tr v-if="!loading && configs.length === 0">
              <td colspan="9" class="cell-empty">
                <div class="empty-state">
                  <svg class="empty-icon" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.2"><rect x="2" y="3" width="20" height="14" rx="2"/><line x1="8" y1="21" x2="16" y2="21"/><line x1="12" y1="17" x2="12" y2="21"/></svg>
                  <span class="empty-title">暂无爬虫配置</span>
                  <span class="empty-sub">点击上方的"添加配置"或"从首页导入导航"开始</span>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- ── Log panel ── -->
    <transition name="log-slide">
      <div v-if="showLogs" class="log-panel">
        <div class="log-panel-header">
          <span class="log-panel-title">爬虫日志</span>
          <div class="log-panel-actions">
            <button @click="loadLogs" class="btn-ghost-xs">刷新</button>
            <button @click="clearLogs" class="btn-ghost-xs">清空</button>
          </div>
        </div>
        <div class="log-box" ref="logBox">
          <div v-if="logs.length === 0" class="log-empty">暂无日志</div>
          <div v-for="(log, i) in logs" :key="i" class="log-line" :class="'log-' + log.level.toLowerCase()">
            <span class="log-time">{{ log.time }}</span>
            <span class="log-level">{{ log.level }}</span>
            <span class="log-msg">{{ log.message }}</span>
          </div>
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch, nextTick } from 'vue'
import api, { crawlerApi } from '../../api'
import { useToast } from '../../composables/toast'

const props = defineProps(['tab'])
const { success, error, info } = useToast()

const configs = ref([])
const loading = ref(false)
const showAdvanced = ref(false)
const showLogs = ref(false)
const showTriggerModal = ref(false)
const showAddForm = ref(false)
const selectedConfigIds = ref([])
const modalSearch = ref('')
const confirmingDelete = ref(null)
const confirmingReset = ref(null)
const logs = ref([])
const logBox = ref(null)
const crawlStatus = ref({ running: false })
const crawlProgress = ref({ phase: 'idle', configs: [], current_config: '', current_config_id: null, config_index: 0, total_configs: 0, page: 0, total_pages: 0, articles_crawled: 0, articles_total: 0 })
const crawlLoading = ref(false)
const navLoading = ref(false)
const filterSearch = ref('')
const filterParent = ref('')
const filterSub = ref('')
let logTimer = null
let statusTimer = null

// KPI stats
const stats = computed(() => {
  const total = configs.value.length
  const enabled = configs.value.filter(c => c.enabled).length
  const crawled = configs.value.filter(c => c.last_crawl).length
  return { total, enabled, crawled }
})

// Overall progress
const overallPercent = computed(() => {
  const { phase, configs } = crawlProgress.value
  if (phase !== 'running' || !configs?.length) return 0
  const doneCount = configs.filter(c => c.status === 'done' || c.status === 'stopped').length
  const runningIdx = configs.findIndex(c => c.status === 'running')
  if (runningIdx < 0) return Math.round(doneCount / configs.length * 100)
  const running = configs[runningIdx]
  const baseFrac = doneCount / configs.length
  const runningFrac = running.articles_total > 0
    ? (running.articles_crawled / running.articles_total) / configs.length
    : running.total_pages > 0
    ? (running.page / running.total_pages) / configs.length
    : 0
  return Math.round((baseFrac + runningFrac) * 100)
})

const currentConfigSpeed = computed(() => {
  const { phase, configs } = crawlProgress.value
  if (phase !== 'running' || !configs?.length) return 0
  const running = configs.find(c => c.status === 'running')
  if (!running) return 0
  const elapsed = running.elapsed_seconds || 0
  if (elapsed < 1) return 0
  const diff = running.articles_crawled - (running.articles_crawled_at_start || 0)
  if (diff <= 0) return 0
  return Math.round(diff / elapsed * 10) / 10
})

function getRowProgress(configId) {
  const cfg = crawlProgress.value.configs?.find(c => c.id === configId)
  if (!cfg) return 0
  if (cfg.status === 'done' || cfg.status === 'stopped') return 100
  if (cfg.status === 'running') {
    if (cfg.articles_total > 0) return Math.round(cfg.articles_crawled / cfg.articles_total * 100)
    if (cfg.total_pages > 0) return Math.round(cfg.page / cfg.total_pages * 100)
    return 5
  }
  return 0
}

function getConfigProgressStatus(configId) {
  return crawlProgress.value.configs?.find(c => c.id === configId)?.status || 'pending'
}

function getConfigProgress(configId) {
  return crawlProgress.value.configs?.find(c => c.id === configId) || { page: 0, total_pages: 0, articles_crawled: 0, articles_total: 0 }
}

// Filters
const parentOptions = computed(() => [...new Set(configs.value.map(c => c.parent_category).filter(Boolean))])
const subOptions = computed(() => {
  if (!filterParent.value) return [...new Set(configs.value.map(c => c.sub_category).filter(Boolean))]
  return [...new Set(configs.value.filter(c => c.parent_category === filterParent.value).map(c => c.sub_category).filter(Boolean))]
})
const filteredConfigs = computed(() => {
  let list = configs.value
  if (filterSearch.value) list = list.filter(c => c.name.toLowerCase().includes(filterSearch.value.toLowerCase()))
  if (filterParent.value) list = list.filter(c => c.parent_category === filterParent.value)
  if (filterSub.value) list = list.filter(c => c.sub_category === filterSub.value)
  return list
})

const filteredModalConfigs = computed(() => {
  if (!modalSearch.value) return configs.value
  const q = modalSearch.value.toLowerCase()
  return configs.value.filter(c => c.name.toLowerCase().includes(q) || (c.parent_category || '').toLowerCase().includes(q))
})

const selectAllConfigs = computed({
  get: () => configs.value.length > 0 && selectedConfigIds.value.length === configs.value.length,
  set: () => {}
})

function clearFilters() {
  filterSearch.value = ''
  filterParent.value = ''
  filterSub.value = ''
}

// New config
const newConfig = ref({
  name: '', url: '', selector: 'body', category: '',
  parent_category: '', sub_category: '',
  is_list_page: true, article_selector: 'ul.sub_list li a',
  link_prefix: '', pagination_selector: 'a[href*="index"]:has(img)', pagination_max: 0,
})

function clearForm() {
  newConfig.value = { name: '', url: '', selector: 'body', category: '', parent_category: '', sub_category: '', is_list_page: true, article_selector: 'ul.sub_list li a', link_prefix: '', pagination_selector: 'a[href*="index"]:has(img)', pagination_max: 0 }
  showAdvanced.value = false
}

function loadPreset() {
  newConfig.value = {
    name: '通知公告', url: 'https://info.bipt.edu.cn/jgjf/bctzgg/index.htm',
    selector: 'body', category: '通知公告', parent_category: '机关教辅', sub_category: '通知公告',
    is_list_page: true,
    article_selector: 'ul.sub_list li a', link_prefix: 'https://info.bipt.edu.cn/jgjf/bctzgg/',
    pagination_selector: 'a[href*="index"]:has(img)', pagination_max: 0,
  }
}

// Data loading
async function loadConfigs() {
  loading.value = true
  try {
    const { data } = await crawlerApi.get('/configs')
    configs.value = data.configs
  } catch (e) { error('加载爬虫配置失败') }
  finally { loading.value = false }
}

function validateUrl(url) {
  try { const u = new URL(url); return u.protocol === 'http:' || u.protocol === 'https:' } catch { return false }
}
function validateSelector(sel) {
  if (!sel || !sel.trim()) return false
  const dangerous = ['<script', 'javascript:', 'onerror', 'onclick', 'onload']
  return !dangerous.some(d => sel.toLowerCase().includes(d))
}

async function addConfig() {
  if (!newConfig.value.name.trim()) { error('请输入配置名称'); return }
  if (!newConfig.value.url.trim()) { error('请输入列表页URL'); return }
  if (!validateUrl(newConfig.value.url)) { error('URL 格式无效'); return }
  if (!newConfig.value.selector.trim()) { error('请输入内容CSS选择器'); return }
  if (!validateSelector(newConfig.value.selector)) { error('CSS选择器包含危险内容'); return }
  if (newConfig.value.is_list_page && !newConfig.value.article_selector.trim()) { error('列表页模式请输入文章链接选择器'); return }
  try {
    await crawlerApi.post('/configs', null, { params: { ...newConfig.value } })
    clearForm()
    showAddForm.value = false
    await loadConfigs()
    success('配置已添加')
  } catch (e) { error(e.response?.data?.detail || '添加失败') }
}

async function toggleConfig(c) {
  try {
    await crawlerApi.put(`/configs/${c.id}`, null, { params: { enabled: !c.enabled } })
    await loadConfigs()
  } catch (e) { error('更新失败') }
}

async function doDelete(id) {
  confirmingDelete.value = null
  try {
    await crawlerApi.delete(`/configs/${id}`)
    await loadConfigs()
    success('配置已删除')
  } catch (e) { error('删除失败') }
}

async function doReset(c) {
  confirmingReset.value = null
  try {
    await crawlerApi.put(`/configs/${c.id}`, null, { params: { initialized: false, pagination_max: 0 } })
    await loadConfigs()
    success(`已重置"${c.name}"`)
  } catch (e) { error('重置失败') }
}

async function updateInterval(configId, hours) {
  try {
    await crawlerApi.put(`/configs/${configId}`, null, { params: { auto_interval_hours: hours } })
    await loadConfigs()
  } catch (e) { error('更新失败') }
}

// Modal actions
function toggleSelectAll() {
  selectedConfigIds.value = selectAllConfigs.value ? configs.value.map(c => c.id) : []
}

async function triggerCrawl() {
  try {
    crawlLoading.value = true
    showTriggerModal.value = false
    const params = selectedConfigIds.value.length > 0 ? { config_ids: selectedConfigIds.value.join(',') } : {}
    await crawlerApi.post('/crawl/trigger', {}, { params })
    success('爬取已触发')
    loadCrawlStatus()
    loadCrawlProgress()
  } catch (e) { error('触发失败') }
  finally { crawlLoading.value = false }
}

async function importNavigation() {
  if (!confirm('将从首页抓取导航结构并批量创建配置，是否继续？')) return
  navLoading.value = true
  try {
    const { data: navData } = await crawlerApi.get('/crawl/navigation')
    const { data: batchData } = await crawlerApi.post('/crawl/configs/batch', { navigation: navData.navigation })
    await loadConfigs()
    success(`成功导入 ${batchData.count} 个配置`)
  } catch (e) { error('导入失败：' + (e.response?.data?.detail || e.message)) }
  finally { navLoading.value = false }
}

async function stopCrawl() {
  try {
    await crawlerApi.post('/crawl/stop')
    info('已请求停止爬取')
    loadCrawlStatus()
  } catch (e) { error('停止失败') }
}

// Logs
function toggleLogs() {
  showLogs.value = !showLogs.value
  if (showLogs.value) { loadLogs(); logTimer = setInterval(loadLogs, 3000) }
  else { clearInterval(logTimer); logTimer = null }
}

async function loadLogs() {
  try {
    const { data } = await api.get('/admin/logs')
    logs.value = data.logs
    await nextTick()
    if (logBox.value) logBox.value.scrollTop = logBox.value.scrollHeight
  } catch (e) { /* silent */ }
}

async function clearLogs() {
  try { await api.delete('/admin/logs'); logs.value = []; success('日志已清空') } catch (e) { error('清空失败') }
}

// Crawl status
async function loadCrawlStatus() {
  try {
    const { data } = await crawlerApi.get('/crawl/status')
    crawlStatus.value = data
    loadCrawlProgress()
  } catch (e) { /* silent */ }
}

async function loadCrawlProgress() {
  try {
    const { data } = await crawlerApi.get('/crawl/progress')
    crawlProgress.value = data
  } catch (e) { /* silent */ }
}

// Lifecycle
onMounted(() => { loadConfigs(); loadCrawlStatus() })

watch(() => props.tab, (newTab) => {
  if (newTab !== 'crawler') {
    clearInterval(logTimer); logTimer = null
    clearInterval(statusTimer); statusTimer = null
    showLogs.value = false
  } else {
    loadCrawlStatus()
    loadCrawlProgress()
    statusTimer = setInterval(() => { loadCrawlStatus(); loadCrawlProgress() }, 2000)
  }
})
</script>

<style scoped>
@import '../../assets/admin-shared.css';

.crawler-tab { --ease-out: cubic-bezier(0.16, 1, 0.3, 1); }

/* ── Toolbar ── */
.crawler-toolbar {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--space-4);
  margin-bottom: var(--space-3);
  flex-wrap: wrap;
}
.toolbar-left {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  min-width: 0;
  flex: 1;
}
.toolbar-actions {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  flex-wrap: wrap;
  flex-shrink: 0;
}
.toolbar-actions .btn-outline.btn-active {
  background: var(--color-primary-muted);
  color: var(--color-primary);
}

/* ── KPI row ── */
.kpi-row {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  flex-wrap: wrap;
}
.kpi-stat {
  display: flex;
  align-items: center;
  gap: 0.35rem;
}
.kpi-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}
.kpi-active .kpi-dot { background: var(--color-success); animation: badge-pulse 1.5s ease-in-out infinite; }
.kpi-idle .kpi-dot { background: var(--color-text-faint); }
@media (prefers-reduced-motion: reduce) { .kpi-active .kpi-dot { animation: none; } }
.kpi-label { font-size: 0.8125rem; font-weight: 600; }
.kpi-idle .kpi-label { color: var(--color-text-muted); }
.kpi-active .kpi-label { color: var(--color-success); }
.kpi-divider { width: 1px; height: 16px; background: var(--color-border); flex-shrink: 0; }
.kpi-num { font-size: 1rem; font-weight: 700; color: var(--color-text); font-variant-numeric: tabular-nums; }
.kpi-sub { font-size: 0.75rem; color: var(--color-text-muted); }

/* ── Overall progress ── */
.crawl-overall-progress { min-width: 200px; max-width: 320px; }
.overall-top { display: flex; align-items: center; justify-content: space-between; margin-bottom: 0.3rem; }
.overall-label { font-size: 0.75rem; color: var(--color-text-muted); font-variant-numeric: tabular-nums; }
.speed-label { font-size: 0.75rem; color: var(--color-success); font-weight: 600; font-variant-numeric: tabular-nums; }
.overall-track { height: 6px; background: var(--color-border); border-radius: 3px; overflow: hidden; }
.overall-fill { height: 100%; background: var(--color-success); border-radius: 3px; transition: width 0.4s var(--ease-out); }

/* ── Overall progress animation ── */
@keyframes badge-pulse {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.5; transform: scale(0.85); }
}

/* ── Config form ── */
.config-form {
  background: var(--color-bg);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: var(--space-3) var(--space-4);
  margin-bottom: var(--space-3);
}
.config-form-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--space-3);
}
.config-form-title { font-size: 0.875rem; font-weight: 700; color: var(--color-text); }
.toggle-advanced { display: inline-flex; align-items: center; gap: 0.25rem; font-size: 0.8125rem; }
.toggle-advanced svg { transition: transform 200ms var(--ease-out); }
.config-form-grid { display: flex; gap: var(--space-2); flex-wrap: wrap; align-items: center; }
.config-form-grid .input { min-width: 130px; }
.advanced-fields { margin-top: var(--space-3); padding-top: var(--space-3); border-top: 1px solid var(--color-border); }
.config-form-actions { display: flex; gap: var(--space-2); margin-top: var(--space-3); align-items: center; }

/* ── Config list ── */
.config-list-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: var(--space-2); }
.config-list-count { font-size: 0.8125rem; font-weight: 600; color: var(--color-text-muted); }

/* ── Filter bar ── */
.config-filters { display: flex; align-items: center; gap: var(--space-2); margin-bottom: var(--space-3); flex-wrap: wrap; }
.filter-search-wrap { position: relative; display: flex; align-items: center; }
.filter-icon { position: absolute; left: 0.6rem; color: var(--color-text-faint); pointer-events: none; }
.filter-input { padding: 0.5rem 0.75rem 0.5rem 2rem; border: 1px solid var(--color-border); border-radius: var(--radius); font-size: 0.875rem; color: var(--color-text); background: var(--color-bg); font-family: var(--font-sans); outline: none; width: 180px; transition: border-color 200ms; }
.filter-input:focus { border-color: var(--color-primary); }
.filter-input::placeholder { color: var(--color-text-faint); }
.filter-select { padding: 0.5rem 0.75rem; border: 1px solid var(--color-border); border-radius: var(--radius); font-size: 0.875rem; background: var(--color-bg); color: var(--color-text); font-family: var(--font-sans); cursor: pointer; transition: border-color 200ms; }
.filter-select:focus { border-color: var(--color-primary); outline: none; }
.filter-count { font-size: 0.75rem; color: var(--color-text-muted); white-space: nowrap; margin-left: auto; }

/* ── Table wrapper ── */
.table-wrapper { background: var(--color-bg); border: 1px solid var(--color-border); border-radius: var(--radius-lg); overflow: hidden; }
.data-table { font-size: 0.875rem; width: 100%; }
.data-table th { text-align: left; padding: 0.55rem 0.875rem; font-size: 0.6875rem; font-weight: 700; color: var(--color-text-muted); letter-spacing: 0.08em; text-transform: uppercase; background: var(--color-surface); border-bottom: 1px solid var(--color-border); }
.data-table td { padding: 0.65rem 0.875rem; border-bottom: 1px solid var(--color-border); vertical-align: middle; font-size: 0.8125rem; }
.data-table tr:last-child td { border-bottom: none; }
.data-table tr:hover td { background: var(--color-surface); }

/* ── Cells ── */
.cell-url { font-size: 0.6875rem; color: var(--color-text-faint); word-break: break-all; margin-top: 2px; max-width: 260px; }
.cell-time { color: var(--color-text-muted); font-size: 0.8125rem; font-variant-numeric: tabular-nums; white-space: nowrap; }
.cell-empty { text-align: center; padding: var(--space-6) !important; }
.cell-actions { display: flex; gap: 2px; align-items: center; white-space: nowrap; }
.cell-tag { display: inline-block; font-size: 0.75rem; color: var(--color-text-secondary); }
.cell-interval { min-width: 90px; }
.cell-progress { min-width: 140px; max-width: 200px; }

/* ── Row progress ── */
.row-progress { display: flex; flex-direction: column; gap: 0.2rem; }
.row-progress-track { height: 5px; background: var(--color-border); border-radius: 3px; overflow: hidden; }
.row-progress-fill { height: 100%; background: var(--color-success); border-radius: 3px; transition: width 0.4s var(--ease-out); }
.row-progress-label { font-size: 0.6875rem; color: var(--color-text-muted); font-variant-numeric: tabular-nums; white-space: nowrap; }
.crawled-check { display: inline-flex; align-items: center; gap: 0.25rem; font-size: 0.75rem; color: var(--color-success); font-weight: 600; }
.not-crawled { color: var(--color-text-faint); }

/* ── Mode / State badges ── */
.mode-badge { display: inline-block; padding: 0.125rem 0.45rem; border-radius: var(--radius-sm); font-size: 0.75rem; font-weight: 600; }
.mode-incremental { background: var(--color-success-bg); color: var(--color-success-text); }
.mode-full { background: var(--color-warning-bg); color: var(--color-warning-text); }
.state-badge { display: inline-flex; align-items: center; gap: 0.35rem; font-size: 0.8125rem; font-weight: 600; }
.state-on { color: var(--color-success); }
.state-off { color: var(--color-text-muted); }
.state-dot { display: inline-block; width: 6px; height: 6px; border-radius: 50%; flex-shrink: 0; }
.state-on .state-dot { background: var(--color-success); }
.state-off .state-dot { background: var(--color-border-strong); }

/* ── Interval select ── */
.interval-select { font-size: 0.75rem; padding: 0.2rem 0.4rem; border: 1px solid var(--color-border); border-radius: var(--radius-sm); background: var(--color-bg); color: var(--color-text); cursor: pointer; }
.interval-select:hover { border-color: var(--color-primary); }

/* ── Link ── */
.link { color: var(--color-primary); font-weight: 500; text-decoration: none; font-size: 0.875rem; }
.link:hover { text-decoration: underline; }

/* ── Inline confirm ── */
.inline-confirm { display: flex; align-items: center; gap: 2px; }
.inline-confirm-q { font-size: 0.75rem; color: var(--color-error); font-weight: 600; padding: 0 0.25rem; }
.btn-confirm-yes { color: var(--color-error) !important; font-weight: 600; }
.btn-danger-active { background: var(--color-danger-bg); color: var(--color-error); }

/* ── Empty state ── */
.empty-state { display: flex; flex-direction: column; align-items: center; gap: var(--space-2); padding: var(--space-6) 0; color: var(--color-text-muted); }
.empty-icon { color: var(--color-border-strong); margin-bottom: var(--space-1); }
.empty-title { font-size: 0.9375rem; font-weight: 600; color: var(--color-text-secondary); }
.empty-sub { font-size: 0.8125rem; color: var(--color-text-muted); }
.modal-empty { text-align: center; color: var(--color-text-muted); font-size: 0.875rem; padding: var(--space-5); }

/* ── Skeleton loading ── */
.skeleton-row td { padding: 0.7rem 0.875rem; }
.sk { background: var(--color-surface); border-radius: var(--radius-sm); display: block; }
.sk-text { height: 14px; width: 80%; }
.sk-name { height: 14px; width: 70%; }
.sk-tag { height: 12px; width: 48px; }
.sk-badge { height: 16px; width: 40px; border-radius: var(--radius-sm); }
.sk-select { height: 22px; width: 70px; border-radius: var(--radius-sm); }
.sk-progress { height: 14px; width: 90%; }
.sk-time { height: 12px; width: 70px; }
.sk-actions { height: 20px; width: 80px; }

/* ── Modal ── */
.modal-overlay { position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.5); display: flex; align-items: center; justify-content: center; z-index: 1000; }
.modal-content { background: var(--color-bg); border-radius: var(--radius-lg); width: 90%; max-width: 480px; max-height: 80vh; display: flex; flex-direction: column; box-shadow: 0 4px 24px rgba(0,0,0,0.2); }
.modal-header { display: flex; align-items: center; justify-content: space-between; padding: var(--space-3) var(--space-4); border-bottom: 1px solid var(--color-border); }
.modal-title { font-size: 0.9375rem; font-weight: 700; color: var(--color-text); }
.modal-close { background: none; border: none; cursor: pointer; color: var(--color-text-muted); padding: 0.25rem; border-radius: var(--radius-sm); display: flex; align-items: center; transition: color var(--transition-fast), background var(--transition-fast); }
.modal-close:hover { color: var(--color-text); background: var(--color-surface); }
.modal-search { padding: var(--space-2) var(--space-4); border-bottom: 1px solid var(--color-border); display: flex; align-items: center; gap: var(--space-2); }
.modal-search-icon { color: var(--color-text-faint); flex-shrink: 0; }
.modal-search-input { flex: 1; border: none; background: transparent; font-size: 0.875rem; color: var(--color-text); outline: none; font-family: var(--font-sans); }
.modal-search-input::placeholder { color: var(--color-text-faint); }
.modal-body { padding: var(--space-3) var(--space-4); overflow-y: auto; flex: 1; }
.modal-footer { display: flex; align-items: center; justify-content: flex-end; gap: var(--space-2); padding: var(--space-3) var(--space-4); border-top: 1px solid var(--color-border); }
.select-all-row { display: flex; align-items: center; justify-content: space-between; margin-bottom: var(--space-2); padding-bottom: var(--space-2); border-bottom: 1px solid var(--color-border); }
.selected-count { font-size: 0.8125rem; color: var(--color-text-muted); font-variant-numeric: tabular-nums; }
.config-select-list { display: flex; flex-direction: column; gap: 2px; max-height: 280px; overflow-y: auto; }
.config-select-item { display: flex; align-items: center; gap: 0.5rem; padding: 0.4rem 0.5rem; border-radius: var(--radius-sm); cursor: pointer; }
.config-select-item:hover { background: var(--color-surface); }
.config-select-item input[type="checkbox"] { width: 16px; height: 16px; cursor: pointer; }
.config-select-name { font-size: 0.8125rem; color: var(--color-text); flex: 1; }
.config-select-meta { font-size: 0.6875rem; color: var(--color-text-muted); }

/* ── Log panel ── */
.log-panel { background: var(--color-bg); border: 1px solid var(--color-border); border-radius: var(--radius-lg); overflow: hidden; }
.log-panel-header { display: flex; align-items: center; justify-content: space-between; padding: var(--space-3) var(--space-4); border-bottom: 1px solid var(--color-border); background: var(--color-surface); }
.log-panel-title { font-size: 0.875rem; font-weight: 700; color: var(--color-text); }
.log-panel-actions { display: flex; gap: 2px; }
.log-box { background: var(--log-bg, #1e1e1e); color: var(--log-text, #d4d4d4); padding: var(--space-3) var(--space-4); max-height: 280px; overflow-y: auto; font-family: var(--font-mono); font-size: 0.75rem; line-height: 1.7; }
.log-empty { color: var(--log-empty, #555); text-align: center; padding: var(--space-4); }
.log-line { display: flex; gap: var(--space-2); align-items: baseline; }
.log-time { color: var(--log-time, #666); white-space: nowrap; flex-shrink: 0; font-size: 0.6875rem; }
.log-level { font-weight: 700; white-space: nowrap; width: 52px; text-align: center; flex-shrink: 0; font-size: 0.6875rem; }
.log-info .log-level { color: var(--log-info, #4fc3f7); }
.log-warning .log-level { color: var(--log-warning, #ffb74d); }
.log-error .log-level { color: var(--log-error, #f87171); }
.log-success .log-level { color: var(--log-success, #81c784); }
.log-debug .log-level { color: var(--log-debug, #888); }
.log-msg { word-break: break-all; }

/* ── Transitions ── */
.log-slide-enter-active, .log-slide-leave-active { transition: opacity 200ms var(--ease-out), transform 200ms var(--ease-out); }
.log-slide-enter-from, .log-slide-leave-to { opacity: 0; transform: translateY(-6px); }
.adv-fade-enter-active, .adv-fade-leave-active { transition: opacity 180ms var(--ease-out), max-height 200ms var(--ease-out); max-height: 400px; overflow: hidden; }
.adv-fade-enter-from, .adv-fade-leave-to { opacity: 0; max-height: 0; }

/* ── Responsive ── */
@media (max-width: 768px) {
  .crawler-toolbar { flex-direction: column; align-items: flex-start; }
  .toolbar-actions { width: 100%; flex-wrap: wrap; }
  .config-form-grid { flex-direction: column; }
  .config-form-grid .input { min-width: 100%; }
  .data-table { display: block; overflow-x: auto; }
  .cell-url { max-width: 160px; }
  .crawl-overall-progress { min-width: 0; width: 100%; }
  .cell-progress { min-width: 120px; }
  .data-table input[type="checkbox"] { min-width: 44px; min-height: 44px; }
  .cell-actions { min-height: 44px; }
  .btn-ghost-xs { min-height: 44px; min-width: 44px; }
}
</style>
