<template>
  <div class="resumes-layout">
    <!-- 左栏：筛选 + 无限滚动列表 -->
    <div class="left-pane">
      <n-card size="small" title="筛选" style="margin-bottom:12px;flex-shrink:0">
        <n-space vertical size="small">
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px">
            <n-popselect v-model:value="filter.school" :options="schoolOptions" size="small" scrollable clearable>
              <n-button size="small" quaternary style="width:100%">
                {{ filter.school || '全部学校' }}
              </n-button>
            </n-popselect>
            <n-popselect v-model:value="filter.position" :options="positionOptions" size="small" scrollable clearable>
              <n-button size="small" quaternary style="width:100%">
                {{ filter.position || '全部岗位' }}
              </n-button>
            </n-popselect>
          </div>
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px">
            <n-date-picker v-model:value="filter.dateStart" type="date" clearable size="small" placeholder="开始日期" />
            <n-date-picker v-model:value="filter.dateEnd" type="date" clearable size="small" placeholder="结束日期" />
          </div>
          <n-input v-model:value="filter.keyword" placeholder="姓名 / 手机 / 文件名" clearable size="small" @keyup.enter="doSearch" />
          <n-space>
            <n-button size="small" type="primary" block @click="doSearch">查询</n-button>
            <n-button size="small" @click="resetFilter">重置</n-button>
          </n-space>
        </n-space>
      </n-card>

      <div class="left-title">简历列表</div>
      <n-infinite-scroll class="resume-scroll" :distance="10" @load="handleLoad">
        <div
          v-for="row in items"
          :key="row.id"
          class="resume-item"
          :class="{ 'item-active': row.id === currentId }"
          @click="selectRow(row)"
        >
          <div class="item-info">
            <div class="item-line1">{{ row.name || '未留名' }} · {{ row.position_name || row.position }}</div>
            <div class="item-line2">{{ row.school_name || '—' }} · {{ (row.upload_time || '').slice(0, 16) }}</div>
          </div>
          <div class="item-actions">
            <n-button size="tiny" type="error" quaternary @click.stop="deleteOne(row)">删除</n-button>
          </div>
        </div>
        <div v-if="loading" class="list-hint">加载中…</div>
        <div v-else-if="finished" class="list-hint">已加载全部</div>
      </n-infinite-scroll>
    </div>

    <!-- 右栏：简历查看器（仅在查看器内滚动） -->
    <div class="right-pane">
      <div class="preview-nav">
        <n-space align="center" size="8">
          <n-button size="small" :disabled="!hasPrev" @click="goPrev">‹ 上一份</n-button>
          <n-button size="small" :disabled="!hasNext" @click="goNext">下一份 ›</n-button>
          <n-popselect
            v-model:value="currentId"
            :options="popOptions"
            size="medium"
            scrollable
            trigger="click"
          >
            <n-button size="small" style="margin-right: 8px">
              {{ currentLabel }}
            </n-button>
          </n-popselect>
        </n-space>
      </div>
      <template v-if="current">
        <div class="preview-filebar">
          <div class="file-name" :title="current.original">📄 {{ current.original }}</div>
          <n-button size="tiny" type="primary" @click="downloadOne(current.id)">⬇ 下载</n-button>
        </div>
        <file-viewer :source="api.resumePreviewUrl(current.id)" :filename="current.original" :resume-id="current.id" />
      </template>
      <div v-else class="preview-empty">
        <div style="font-size:40px;margin-bottom:10px">📄</div>
        <div style="color:#94a3b8">从左侧选择一条简历，在此查看</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useDialog, useMessage } from 'naive-ui'
import { api } from '../api'
import FileViewer from '../components/FileViewer.vue'

const message = useMessage()
const dialog = useDialog()

const PAGE_SIZE = 20
const page = ref(0)
const total = ref(0)
const items = ref([])
const loading = ref(false)
const finished = ref(false)
const currentId = ref(null)

const filter = reactive({ school: null, position: null, dateStart: null, dateEnd: null, keyword: '' })
const schoolOptions = ref([])
const positionOptions = ref([])

const hasMore = computed(() => items.value.length < total.value)
const current = computed(() => items.value.find(i => i.id === currentId.value) || null)

// 查看器上一份/下一份 定位
const currentIdx = computed(() => items.value.findIndex(i => i.id === currentId.value))
const hasPrev = computed(() => currentIdx.value > 0)
const hasNext = computed(() => currentIdx.value >= 0 && currentIdx.value < items.value.length - 1)
const currentLabel = computed(() => {
  if (!current.value) return '选择简历'
  return `${current.value.name || '未留名'} · ${current.value.position_name || current.value.position}`
})
// popselect 跳转选项（label 姓名·岗位，value id）
const popOptions = computed(() =>
  items.value.map(i => ({ label: `${i.name || '未留名'} · ${i.position_name || i.position}`, value: i.id }))
)

function goPrev() {
  if (hasPrev.value) currentId.value = items.value[currentIdx.value - 1].id
}
function goNext() {
  if (hasNext.value) currentId.value = items.value[currentIdx.value + 1].id
}

function fmtDate(v) {
  if (!v) return ''
  const d = new Date(v)
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

function buildParams(offset) {
  const p = {}
  if (filter.school) p.school = filter.school
  if (filter.position) p.position = filter.position
  if (filter.dateStart) p.date_start = fmtDate(filter.dateStart)
  if (filter.dateEnd) p.date_end = fmtDate(filter.dateEnd)
  if (filter.keyword) p.keyword = filter.keyword
  p.limit = PAGE_SIZE
  p.offset = offset
  return p
}

async function handleLoad() {
  if (loading.value || finished.value) return
  loading.value = true
  try {
    const offset = page.value * PAGE_SIZE
    const d = await api.listResumes(buildParams(offset))
    if (page.value === 0) {
      items.value = d.items
      currentId.value = d.items.length ? d.items[0].id : null
    } else {
      const known = new Set(items.value.map(i => i.id))
      items.value = [...items.value, ...d.items.filter(i => !known.has(i.id))]
    }
    total.value = d.total
    page.value++
    if (items.value.length >= total.value) finished.value = true
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

function selectRow(row) {
  currentId.value = row.id
}

function downloadOne(id) {
  window.location.href = api.resumeDownloadUrl(id)
}

function deleteOne(row) {
  dialog.warning({
    title: '删除简历',
    content: `确定删除「${row.name || row.original}」这条简历及文件？`,
    positiveText: '删除',
    negativeText: '取消',
    onPositiveClick: async () => {
      try {
        await api.deleteResume(row.id)
        message.success('已删除')
        if (currentId.value === row.id) currentId.value = null
        items.value = items.value.filter(i => i.id !== row.id)
        total.value--
      } catch (e) {
        message.error(e.message)
      }
    }
  })
}

function doSearch() {
  page.value = 0
  items.value = []
  finished.value = false
  currentId.value = null
  handleLoad()
}
function resetFilter() {
  filter.school = null
  filter.position = null
  filter.dateStart = null
  filter.dateEnd = null
  filter.keyword = ''
  doSearch()
}

async function loadFilters() {
  try {
    const [schools, positions] = await Promise.all([api.listSchools(), api.listPositions()])
    schoolOptions.value = schools.map(s => ({ label: s.name, value: s.name }))
    positionOptions.value = positions.map(p => ({ label: p.name, value: p.name }))
  } catch (e) {
    console.error(e)
  }
}

onMounted(() => {
  loadFilters()
  handleLoad()
})
</script>

<style scoped>
.resumes-layout {
  display: flex;
  gap: 16px;
  flex: 1;
  min-height: 0;
}
.left-pane {
  flex: 0 0 40%;
  max-width: 440px;
  min-width: 300px;
  display: flex;
  flex-direction: column;
  min-height: 0;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  background: #fff;
  padding: 12px;
}
.left-title {
  font-weight: 600;
  color: #1e293b;
  margin-bottom: 10px;
  flex-shrink: 0;
}
.resume-scroll {
  flex: 1;
  min-height: 0;
  height: 0;  /* flex:1 时用 height:0 + min-height:0，让父级 flex 拉伸决定实际高度，同时使内部 .n-scrollbar 的 height:100% 可解析 */
}
.resume-scroll :deep(.n-scrollbar) {
  height: 100%;
}
.resume-item {
  display: flex;
  align-items: center;
  gap: 8px;
  height: 52px;
  padding: 0 12px;
  margin-bottom: 8px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  background-color: #fff;
  cursor: pointer;
  transition: border-color .2s, background-color .2s, box-shadow .2s;
}
.resume-item:last-child {
  margin-bottom: 0;
}
.resume-item:hover {
  border-color: #bfdbfe;
  background-color: #f0f7ff;
}
.resume-item.item-active {
  border-color: #2563eb;
  background-color: #eff6ff;
  box-shadow: 0 0 0 1px #2563eb inset;
}
.item-info {
  flex: 1;
  min-width: 0;
}
.item-actions {
  flex-shrink: 0;
}
.item-line1 {
  font-size: 14px;
  font-weight: 600;
  color: #1e293b;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.item-line2 {
  font-size: 12px;
  color: #64748b;
  margin-top: 2px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.list-hint {
  text-align: center;
  padding: 8px 0;
  color: #94a3b8;
  font-size: 12px;
}

.right-pane {
  flex: 1;
  min-width: 0;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  background: #fff;
  display: flex;
  flex-direction: column;
  min-height: 0;
  overflow: hidden;
}
.preview-nav {
  display: flex;
  align-items: center;
  padding: 8px 12px;
  border-bottom: 1px solid #e2e8f0;
  background: #f8fafc;
  flex-shrink: 0;
}
.preview-filebar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 8px 12px;
  border-bottom: 1px solid #e2e8f0;
  background: #fff;
  flex-shrink: 0;
}
.file-name {
  flex: 1;
  min-width: 0;
  font-size: 13px;
  color: #475569;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.preview-empty {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #94a3b8;
}
</style>
