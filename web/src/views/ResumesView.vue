<template>
  <div>
    <!-- 筛选 -->
    <n-card title="筛选" style="margin-bottom:16px">
      <n-space align="end" style="flex-wrap:wrap">
        <n-form-item label="学校" style="min-width:160px">
          <n-select v-model:value="filter.school" :options="schoolOptions" clearable placeholder="全部学校" />
        </n-form-item>
        <n-form-item label="岗位" style="min-width:160px">
          <n-select v-model:value="filter.position" :options="positionOptions" clearable placeholder="全部岗位" />
        </n-form-item>
        <n-form-item label="开始日期" style="min-width:150px">
          <n-date-picker v-model:value="filter.dateStart" type="date" clearable style="width:100%" />
        </n-form-item>
        <n-form-item label="结束日期" style="min-width:150px">
          <n-date-picker v-model:value="filter.dateEnd" type="date" clearable style="width:100%" />
        </n-form-item>
        <n-form-item label="关键词" style="min-width:160px">
          <n-input v-model:value="filter.keyword" placeholder="姓名 / 手机 / 文件名" clearable @keyup.enter="doSearch" />
        </n-form-item>
        <n-button type="primary" @click="doSearch">查询</n-button>
        <n-button @click="resetFilter">重置</n-button>
      </n-space>
    </n-card>

    <!-- 列表 -->
    <n-card>
      <template #header>
        <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:8px">
          <span>简历列表（{{ total }}）</span>
          <n-space>
            <n-button size="small" type="success" :disabled="!selectedIds.length" @click="downloadSelected">⬇ 下载所选（ZIP）</n-button>
            <n-button size="small" type="success" @click="downloadFiltered">⬇ 下载当前筛选全部</n-button>
            <n-button size="small" :disabled="!selectedIds.length" @click="deleteSelected">删除所选</n-button>
          </n-space>
        </div>
      </template>

      <n-data-table
        :columns="columns"
        :data="items"
        :pagination="pagination"
        :row-key="rowKey"
        :checked-row-keys="checkedRowKeys"
        @update:checked-row-keys="onChecked"
        @update:page="onPageChange"
        :loading="loading"
      />
    </n-card>

    <!-- 预览弹窗 -->
    <n-modal v-model:show="previewShow" preset="card" style="width:900px;max-width:95vw;height:90vh">
      <template #header>
        <div style="display:flex;align-items:center;justify-content:space-between">
          <span>{{ previewTitle }}</span>
        </div>
      </template>
      <iframe v-if="previewIsPdf" :src="previewUrl" style="width:100%;height:100%;border:none" />
      <n-empty v-else description="该文件不是 PDF，无法在线预览" style="padding:40px 0">
        <template #extra>
          <n-button type="primary" @click="downloadPreview">点击下载查看</n-button>
        </template>
      </n-empty>
    </n-modal>
  </div>
</template>

<script setup>
import { ref, reactive, computed, h, onMounted } from 'vue'
import { NButton, NTag, NSpace, useDialog, useMessage } from 'naive-ui'
import { api } from '../api'

const message = useMessage()
const dialog = useDialog()

const PAGE_SIZE = 20
const page = ref(1)
const total = ref(0)
const items = ref([])
const loading = ref(false)
const checkedRowKeys = ref([])
const selectedIds = ref([])

const filter = reactive({ school: null, position: null, dateStart: null, dateEnd: null, keyword: '' })
const schoolOptions = ref([])
const positionOptions = ref([])

// 预览
const previewShow = ref(false)
const previewUrl = ref('')
const previewIsPdf = ref(false)
const previewTitle = ref('')

function rowKey(row) { return row.id }

const columns = [
  { type: 'selection' },
  { title: 'ID', key: 'id', width: 60 },
  { title: '姓名', key: 'name', width: 100 },
  { title: '手机号', key: 'phone', width: 120 },
  { title: '学校', key: 'school_name', width: 120 },
  { title: '岗位', key: 'position_name', width: 130 },
  { title: '上传时间', key: 'upload_time', width: 160 },
  { title: '文件名', key: 'original', ellipsis: { tooltip: true } },
  {
    title: '操作', key: 'actions', width: 210,
    render(row) {
      return h(NSpace, { size: 6 }, {
        default: () => [
          h(NButton, { size: 'small', onClick: () => viewResume(row.id, row) }, { default: () => '查看' }),
          h(NButton, { size: 'small', onClick: () => downloadOne(row.id) }, { default: () => '下载' }),
          h(NButton, { size: 'small', type: 'error', onClick: () => deleteOne(row) }, { default: () => '删除' })
        ]
      })
    }
  }
]

const pagination = computed(() => ({
  pageSize: PAGE_SIZE,
  page: page.value,
  itemCount: total.value
}))

function fmtDate(v) {
  if (!v) return ''
  const d = new Date(v)
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${d.getFullYear()}-${m}-${day}`
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
    checkedRowKeys.value = []
    selectedIds.value = []
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
function onChecked(keys) {
  checkedRowKeys.value = keys
  selectedIds.value = keys
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

// ============ 查看（PDF 预览） ============
async function viewResume(id, row) {
  previewTitle.value = row ? `${row.name || ''} · ${row.original}` : '简历预览'
  previewShow.value = true
  // 用 fetch 探测类型
  try {
    const res = await fetch(api.resumeDownloadUrl(id))
    const ct = res.headers.get('content-type') || ''
    previewIsPdf.value = ct.includes('application/pdf')
  } catch (e) {
    previewIsPdf.value = true
  }
  previewUrl.value = api.resumeDownloadUrl(id)
}
function downloadPreview() {
  window.location.href = previewUrl.value
}

onMounted(loadFilters)
</script>
