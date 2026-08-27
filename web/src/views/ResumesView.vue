<template>
  <div class="resumes-layout">
    <!-- 左栏：筛选 + 列表 -->
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
              <n-button size="tiny" :disabled="!selectedIds.length" @click="downloadSelected">⬇ 所选</n-button>
              <n-button size="tiny" @click="downloadFiltered">⬇ 全部</n-button>
              <n-button size="tiny" type="error" :disabled="!selectedIds.length" @click="deleteSelected">删除所选</n-button>
            </n-space>
          </div>
        </template>

        <div class="list-body">
          <n-empty v-if="!items.length && !loading" description="暂无简历" style="padding:30px 0" />
          <div
            v-for="row in items"
            :key="row.id"
            class="resume-item"
            :class="{ active: row.id === currentId }"
            @click="selectRow(row)"
          >
            <div class="item-main">
              <span class="item-name">{{ row.name || '未留名' }}</span>
              <span class="item-pos">{{ row.position_name || row.position }}</span>
            </div>
            <div class="item-sub">
              <span>{{ row.school_name || '—' }}</span>
              <span class="item-time">{{ (row.upload_time || '').slice(0, 16) }}</span>
            </div>
          </div>
        </div>

        <n-pagination
          v-if="total > PAGE_SIZE"
          size="small"
          :page="page"
          :page-count="totalPages"
          @update:page="onPageChange"
          style="justify-content:center;margin-top:10px"
        />
      </n-card>
    </div>

    <!-- 右栏：简历预览 -->
    <div class="right-pane">
      <div v-if="!current" class="preview-empty">
        <div style="font-size:40px;margin-bottom:10px">📄</div>
        <div style="color:#94a3b8">从左侧选择一条简历，在此预览</div>
      </div>
      <template v-else>
        <div class="preview-head">
          <div>
            <div style="font-weight:600;color:#1e293b">{{ current.name || '未留名' }} · {{ current.position_name || current.position }}</div>
            <div style="font-size:12px;color:#94a3b8">{{ current.school_name || '—' }} · {{ current.original }}</div>
          </div>
          <n-space size="8">
            <n-button size="small" @click="downloadOne(current.id)">下载</n-button>
            <n-button size="small" type="error" @click="deleteOne(current)">删除</n-button>
          </n-space>
        </div>
        <iframe
          v-if="current"
          :key="'pdf-' + current.id"
          class="preview-frame"
          :src="api.resumePreviewUrl(current.id)"
        />
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useDialog, useMessage } from 'naive-ui'
import { api } from '../api'

const message = useMessage()
const dialog = useDialog()

const PAGE_SIZE = 20
const page = ref(1)
const total = ref(0)
const items = ref([])
const loading = ref(false)
const currentId = ref(null)
const checkedRowKeys = ref([])
const selectedIds = ref([])

const filter = reactive({ school: null, position: null, dateStart: null, dateEnd: null, keyword: '' })
const schoolOptions = ref([])
const positionOptions = ref([])

const totalPages = computed(() => Math.max(1, Math.ceil(total.value / PAGE_SIZE)))
const current = computed(() => items.value.find(i => i.id === currentId.value) || null)

function fmtDate(v) {
  if (!v) return ''
  const d = new Date(v)
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

function buildParams() {
  const p = {}
  if (filter.school) p.school = filter.school
  if (filter.position) p.position = filter.position
  if (filter.dateStart) p.date_start = fmtDate(filter.dateStart)
  if (filter.dateEnd) p.date_end = fmtDate(filter.dateEnd)
  if (filter.keyword) p.keyword = filter.keyword
  p.limit = PAGE_SIZE
  p.offset = (page.value - 1) * PAGE_SIZE
  return p
}

async function loadResumes() {
  loading.value = true
  try {
    const d = await api.listResumes(buildParams())
    items.value = d.items
    total.value = d.total
    // 若当前选中的行被翻页过滤掉，清空选中
    if (currentId.value && !items.value.find(i => i.id === currentId.value)) {
      currentId.value = null
    }
    if (!currentId.value && items.value.length) {
      currentId.value = items.value[0].id
    }
  } catch (e) {
    message.error(e.message)
  } finally {
    loading.value = false
  }
}

async function loadFilters() {
  try {
    const [schools, positions] = await Promise.all([api.listSchools(), api.listPositions()])
    schoolOptions.value = schools.map(s => ({ label: s.name, value: s.name }))
    positionOptions.value = positions.map(p => ({ label: p.name, value: p.name }))
  } catch (e) {}
  loadResumes()
}

function selectRow(row) {
  currentId.value = row.id
}

function doSearch() { page.value = 1; loadResumes() }
function resetFilter() {
  filter.school = null
  filter.position = null
  filter.dateStart = null
  filter.dateEnd = null
  filter.keyword = ''
  page.value = 1
  loadResumes()
}
function onPageChange(p) {
  page.value = p
  loadResumes()
}

// ============ 操作 ============
function downloadOne(id) {
  window.location.href = api.resumeDownloadUrl(id)
}
function downloadSelected() {
  if (!selectedIds.value.length) { message.warning('请先勾选简历'); return }
  window.location.href = api.exportZipUrl({ ids: selectedIds.value.join(',') })
}
function downloadFiltered() {
  const p = buildParams()
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
        loadResumes()
      } catch (e) { message.error(e.message) }
    }
  })
}
function deleteSelected() {
  const ids = selectedIds.value
  if (!ids.length) { message.warning('请先勾选简历'); return }
  dialog.warning({
    title: '批量删除',
    content: `确定删除所选 ${ids.length} 条简历及文件？`,
    positiveText: '删除',
    negativeText: '取消',
    onPositiveClick: async () => {
      try {
        for (const id of ids) await api.deleteResume(id)
        message.success('已删除所选简历')
        loadResumes()
      } catch (e) { message.error(e.message) }
    }
  })
}

onMounted(loadFilters)
</script>

<style scoped>
.resumes-layout {
  display: flex;
  gap: 16px;
  height: calc(100vh - 56px - 48px);
  min-height: 480px;
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
  padding-top: 8px;
}
.list-body {
  flex: 1;
  overflow-y: auto;
  min-height: 0;
  margin: 0 -4px;
  padding: 0 4px;
}
.resume-item {
  padding: 10px 12px;
  border-radius: 8px;
  cursor: pointer;
  border: 1px solid transparent;
  transition: background .15s, border-color .15s;
  margin-bottom: 6px;
}
.resume-item:hover { background: #f1f5f9; }
.resume-item.active {
  background: #eff6ff;
  border-color: #bfdbfe;
}
.item-main { display: flex; align-items: center; gap: 8px; }
.item-name { font-weight: 600; color: #1e293b; font-size: 14px; }
.item-pos {
  font-size: 12px; color: #2563eb; background: #eff6ff;
  padding: 2px 8px; border-radius: 10px; overflow: hidden;
  text-overflow: ellipsis; white-space: nowrap; max-width: 140px;
}
.item-sub { display: flex; justify-content: space-between; align-items: center; margin-top: 4px; }
.item-sub span { font-size: 12px; color: #94a3b8; }
.item-time { flex-shrink: 0; }

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
.preview-frame {
  flex: 1;
  width: 100%;
  border: none;
  min-height: 0;
  background: #fff;
}
</style>
