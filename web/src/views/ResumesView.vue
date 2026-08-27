<template>
  <div class="resumes-layout">
    <!-- 左栏：筛选 + 列表（懒加载） -->
    <div class="left-pane">
      <n-card size="small" title="筛选" style="margin-bottom:12px">
        <n-space vertical size="small">
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px">
            <n-select v-model:value="filter.school" :options="schoolOptions" clearable placeholder="全部学校" size="small" />
            <n-select v-model:value="filter.position" :options="positionOptions" clearable placeholder="全部岗位" size="small" />
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

      <n-card size="small" class="list-card">
        <template #header>
          <div style="display:flex;align-items:center;justify-content:space-between">
            <span>简历列表（{{ total }}）</span>
            <n-space size="4">
              <n-button size="tiny" @click="downloadFiltered">⬇ 导出</n-button>
            </n-space>
          </div>
        </template>

        <div class="list-body" ref="listBody" @scroll="onListScroll">
          <n-empty v-if="!items.length && !loading" description="暂无简历" style="padding:30px 0" />
          <div
            v-for="row in items"
            :key="row.id"
            class="resume-item"
            :class="{ active: row.id === currentId }"
            @click="selectRow(row)"
          >
            <span class="item-dot" :class="{ 'dot-on': row.id === currentId }"></span>
            <div class="item-content">
              <div class="item-line1">
                <span class="item-name">{{ row.name || '未留名' }}</span>
                <span class="item-pos">{{ row.position_name || row.position }}</span>
              </div>
              <div class="item-line2">{{ row.original }}</div>
            </div>
            <div class="item-right">
              <span class="item-meta">{{ (row.upload_time || '').slice(0, 16) }} · {{ row.school_name || '—' }}</span>
              <span class="item-del" @click.stop="deleteOne(row)" title="删除">🗑</span>
            </div>
          </div>
          <div v-if="loading" style="text-align:center;padding:12px;color:#94a3b8;font-size:13px">加载中…</div>
          <div v-if="!loading && hasMore" style="text-align:center;padding:8px;color:#94a3b8;font-size:12px">下滑加载更多</div>
          <div v-if="!loading && !hasMore && items.length" style="text-align:center;padding:8px;color:#cbd5e1;font-size:12px">已加载全部</div>
        </div>
      </n-card>
    </div>

    <!-- 右栏：PDF 查看器 -->
    <div class="right-pane">
      <template v-if="current">
        <div class="preview-head">
          <div>
            <div style="font-weight:600;color:#1e293b">{{ current.name || '未留名' }} · {{ current.position_name || current.position }}</div>
            <div style="font-size:12px;color:#94a3b8">{{ current.school_name || '—' }} · {{ current.original }}</div>
          </div>
          <n-button size="small" @click="downloadOne(current.id)">下载</n-button>
        </div>
        <pdf-viewer :source="api.resumePreviewUrl(current.id)" />
      </template>
      <div v-else class="preview-empty">
        <div style="font-size:40px;margin-bottom:10px">📄</div>
        <div style="color:#94a3b8">从左侧选择一条简历，在此查看</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onBeforeUnmount } from 'vue'
import { useDialog, useMessage } from 'naive-ui'
import { api } from '../api'
import PdfViewer from '../components/PdfViewer.vue'

const message = useMessage()
const dialog = useDialog()

const PAGE_SIZE = 50
const page = ref(0)          // 已加载页数（0 表示还没加载）
const total = ref(0)
const items = ref([])
const loading = ref(false)
const currentId = ref(null)
const listBody = ref(null)

const filter = reactive({ school: null, position: null, dateStart: null, dateEnd: null, keyword: '' })
const schoolOptions = ref([])
const positionOptions = ref([])

const hasMore = computed(() => items.value.length < total.value)
const current = computed(() => items.value.find(i => i.id === currentId.value) || null)

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

async function loadMore() {
  if (loading.value) return
  loading.value = true
  try {
    const offset = page.value * PAGE_SIZE
    const d = await api.listResumes(buildParams(offset))
    if (page.value === 0) {
      // 首次加载：全新列表
      items.value = d.items
      currentId.value = d.items.length ? d.items[0].id : null
    } else {
      // 追加
      const known = new Set(items.value.map(i => i.id))
      items.value = [...items.value, ...d.items.filter(i => !known.has(i.id))]
    }
    total.value = d.total
    page.value++
  } catch (e) {
    message.error(e.message)
  } finally {
    loading.value = false
  }
}

function onListScroll() {
  const el = listBody.value
  if (!el) return
  // 滚动到接近底部 80px 时加载更多
  if (el.scrollTop + el.clientHeight >= el.scrollHeight - 80) {
    if (hasMore.value) loadMore()
  }
}

function selectRow(row) {
  currentId.value = row.id
}

function doSearch() {
  page.value = 0
  items.value = []
  loadMore()
}
function resetFilter() {
  filter.school = null
  filter.position = null
  filter.dateStart = null
  filter.dateEnd = null
  filter.keyword = ''
  page.value = 0
  items.value = []
  loadMore()
}

async function loadFilters() {
  try {
    const [schools, positions] = await Promise.all([api.listSchools(), api.listPositions()])
    schoolOptions.value = schools.map(s => ({ label: s.name, value: s.name }))
    positionOptions.value = positions.map(p => ({ label: p.name, value: p.name }))
  } catch (e) {}
  loadMore()
}

// ============ 操作 ============
function downloadOne(id) {
  window.location.href = api.resumeDownloadUrl(id)
}
function downloadFiltered() {
  const p = buildParams(0)
  delete p.limit
  delete p.offset
  window.location.href = api.exportZipUrl(p)
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
      } catch (e) { message.error(e.message) }
    }
  })
}

onMounted(loadFilters)
onBeforeUnmount(() => {})
</script>

<style scoped>
.resumes-layout {
  display: flex;
  gap: 16px;
  height: 100%;
  min-height: 0;
}
.left-pane {
  flex: 0 0 46%;
  max-width: 520px;
  min-width: 340px;
  display: flex;
  flex-direction: column;
  min-height: 0;
}
.list-card {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
}
.list-card :deep(.n-card__content) {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
  padding: 0 12px 12px;
  overflow: hidden;
}
.list-body {
  flex: 1;
  overflow-y: auto;
  min-height: 0;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  padding: 4px 14px;
  box-sizing: border-box;
}
.resume-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 4px;
  border-bottom: 1px solid #f1f5f9;
  cursor: pointer;
  font-size: 14px;
}
.resume-item:last-child { border-bottom: none; }
.resume-item:hover { background: #f8fafc; }
.resume-item.active { background: #eff6ff; }
.item-dot {
  width: 8px; height: 8px; border-radius: 50%;
  background: #d1d5db; flex-shrink: 0;
  transition: background .15s;
}
.item-dot.dot-on { background: #22c55e; }
.item-content { flex: 1; min-width: 0; }
.item-line1 { display: flex; align-items: center; gap: 8px; }
.item-name { font-weight: 600; color: #1e293b; font-size: 14px; }
.item-pos {
  font-size: 12px; color: #2563eb; background: #eff6ff;
  padding: 1px 8px; border-radius: 10px; overflow: hidden;
  text-overflow: ellipsis; white-space: nowrap; max-width: 130px;
}
.item-line2 {
  font-size: 12px; color: #94a3b8; margin-top: 2px;
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}
.item-right {
  display: flex; align-items: center; gap: 10px; flex-shrink: 0;
}
.item-meta { color: #94a3b8; font-size: 12px; white-space: nowrap; }
.item-del {
  cursor: pointer; font-size: 14px; opacity: 0.5; transition: opacity .15s;
}
.item-del:hover { opacity: 1; }

.right-pane {
  flex: 1;
  min-width: 0;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  background: #fff;
  display: flex;
  flex-direction: column;
  min-height: 0;
}
.preview-empty {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #94a3b8;
}
.preview-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 12px 16px;
  border-bottom: 1px solid #e2e8f0;
  flex-shrink: 0;
}
</style>
