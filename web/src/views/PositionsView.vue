<template>
  <div>
    <n-card title="新增岗位" style="margin-bottom:16px">
      <n-space align="end" style="flex-wrap:wrap">
        <n-form-item label="岗位名称" style="min-width:220px">
          <n-input v-model:value="newName" placeholder="如：机器人焊接工程师" />
        </n-form-item>
        <n-form-item label="岗位要求" style="min-width:260px">
          <n-input v-model:value="newRequirement" placeholder="选填，岗位职责/要求" />
        </n-form-item>
        <n-button type="primary" @click="addPosition">添加岗位</n-button>
      </n-space>
    </n-card>

    <n-card title="Excel 导入岗位" style="margin-bottom:16px">
      <template #header-extra>
        <span style="font-size:12px;color:#94a3b8">识别表头「岗位名称 / 岗位要求」（支持别名），上传 .xlsx</span>
      </template>
      <n-space>
        <n-upload :show-file-list="false" :custom-request="handleImport">
          <n-button>选择 Excel 文件</n-button>
        </n-upload>
        <span v-if="importStatus" style="color:#94a3b8;font-size:13px">{{ importStatus }}</span>
      </n-space>
    </n-card>

    <n-card :title="`岗位列表（${positions.length}）`">
      <n-data-table :columns="columns" :data="positions" :loading="loading" :bordered="false" />
      <n-empty v-if="!positions.length" description="暂无岗位，请先添加或导入" style="padding:24px" />
    </n-card>
  </div>
</template>

<script setup>
import { ref, h, onMounted } from 'vue'
import { NButton, NSpace, useDialog, useMessage } from 'naive-ui'
import { api } from '../api'

const message = useMessage()
const dialog = useDialog()

const positions = ref([])
const loading = ref(false)
const newName = ref('')
const newRequirement = ref('')
const importStatus = ref('')

const columns = [
  { title: 'ID', key: 'id', width: 60 },
  { title: '岗位名称', key: 'name', width: 220 },
  { title: '岗位要求', key: 'requirement' },
  {
    title: '操作', key: 'actions', width: 150,
    render(row) {
      return h(NSpace, { size: 6 }, {
        default: () => [
          h(NButton, { size: 'small', onClick: () => openEdit(row) }, { default: () => '编辑' }),
          h(NButton, { size: 'small', type: 'error', onClick: () => removePosition(row) }, { default: () => '删除' })
        ]
      })
    }
  }
]

async function loadPositions() {
  loading.value = true
  try {
    positions.value = await api.listPositions()
  } catch (e) { message.error(e.message) } finally { loading.value = false }
}

async function addPosition() {
  const name = newName.value.trim()
  if (!name) { message.warning('请填写岗位名称'); return }
  try {
    await api.addPosition(name, newRequirement.value.trim())
    message.success('岗位已添加')
    newName.value = ''
    newRequirement.value = ''
    loadPositions()
  } catch (e) { message.error(e.message) }
}

function removePosition(row) {
  dialog.warning({
    title: '删除岗位',
    content: `确定删除岗位「${row.name}」？`,
    positiveText: '删除',
    negativeText: '取消',
    onPositiveClick: async () => {
      try {
        await api.deletePosition(row.id)
        message.success('已删除')
        loadPositions()
      } catch (e) { message.error(e.message) }
    }
  })
}

function openEdit(row) {
  dialog.info({
    title: '编辑岗位',
    showIcon: false,
    content: () => h('div', { style: 'display:flex;flex-direction:column;gap:12px' }, [
      h('input', {
        value: row.name,
        style: 'padding:8px 12px;border:1px solid #d1d5db;border-radius:8px;font-size:14px',
        onInput: e => row._name = e.target.value,
        placeholder: '岗位名称'
      }),
      h('input', {
        value: row.requirement || '',
        style: 'padding:8px 12px;border:1px solid #d1d5db;border-radius:8px;font-size:14px',
        onInput: e => row._req = e.target.value,
        placeholder: '岗位要求（选填）'
      })
    ]),
    positiveText: '保存',
    negativeText: '取消',
    onPositiveClick: async () => {
      try {
        await api.updatePosition(row.id, row._name || row.name, row._req || row.requirement || '')
        message.success('已更新')
        loadPositions()
      } catch (e) { message.error(e.message) }
    }
  })
}

async function handleImport({ file }) {
  const fd = new FormData()
  fd.append('file', file.file)
  importStatus.value = '导入中…'
  try {
    const res = await fetch('/api/positions/import', { method: 'POST', body: fd })
    const d = await res.json()
    if (!res.ok) throw new Error(d.detail || '导入失败')
    importStatus.value = `新增 ${d.created} 条，跳过空行 ${d.skipped}，重复 ${d.duplicates.length} 条`
    message.success(`导入完成：新增 ${d.created} 个岗位`)
    loadPositions()
  } catch (e) {
    message.error(e.message)
    importStatus.value = ''
  }
}

onMounted(loadPositions)
</script>
