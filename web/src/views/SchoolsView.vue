<template>
  <div>
    <n-card title="新增学校" style="margin-bottom:16px">
      <n-form inline label-placement="left" :show-feedback="false" style="row-gap:12px">
        <n-form-item label="学校名称">
          <n-input v-model:value="newName" placeholder="如：北京大学" style="width:200px" />
        </n-form-item>
        <n-form-item label="绑定岗位（可多选）">
          <div style="display:flex;gap:8px;align-items:center">
            <n-select v-model:value="newPositions" multiple :options="positionOptions" placeholder="该校开放招聘的岗位" clearable style="width:280px" />
            <n-button size="small" @click="selectAllNewPositions">全部添加</n-button>
          </div>
        </n-form-item>
        <n-form-item>
          <n-button type="primary" @click="addSchool">添加学校</n-button>
        </n-form-item>
      </n-form>
    </n-card>

    <n-card :title="`学校列表（${schools.length}）· 每校独立二维码`">
      <n-empty v-if="!schools.length" description="暂无学校" style="padding:24px" />
      <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:16px">
        <n-card v-for="s in schools" :key="s.id" size="small" embedded style="text-align:center">
          <div style="font-size:15px;font-weight:600;color:#1e293b;margin-bottom:8px">{{ s.name }}</div>
          <n-image :src="api.schoolQrcode(s.id) + '?t=' + Date.now()" width="150" height="150" style="display:inline-block;border:1px solid #e2e8f0;border-radius:8px;padding:4px" />
          <div style="margin-top:8px">
            <n-tag v-for="p in s.positions" :key="p.id" size="small" style="margin:2px">{{ p.name }}</n-tag>
            <span v-if="!s.positions || !s.positions.length" style="color:#94a3b8;font-size:12px">未绑定岗位</span>
          </div>
          <div style="font-size:11px;color:#94a3b8;word-break:break-all;margin-top:6px">{{ uploadUrl(s.name) }}</div>
          <n-space style="margin-top:10px;justify-content:center">
            <n-button size="small" @click="openEditPositions(s)">改岗位</n-button>
            <n-button size="small" type="error" @click="removeSchool(s)">删除</n-button>
          </n-space>
        </n-card>
      </div>
    </n-card>
  </div>
</template>

<script setup>
import { ref, computed, h, onMounted } from 'vue'
import { useDialog, useMessage } from 'naive-ui'
import { api } from '../api'

const message = useMessage()
const dialog = useDialog()

const schools = ref([])
const positions = ref([])
const newName = ref('')
const newPositions = ref([])

const positionOptions = computed(() =>
  positions.value.map(p => ({ label: p.name, value: p.id }))
)

function uploadUrl(name) {
  return `/upload?school=${encodeURIComponent(name)}`
}

async function loadAll() {
  try {
    const [sList, pList] = await Promise.all([api.listSchools(), api.listPositions()])
    schools.value = sList
    positions.value = pList
  } catch (e) { message.error(e.message) }
}

function selectAllNewPositions() {
  // 全部添加：选中所有岗位
  if (newPositions.value.length === positionOptions.value.length) return
  newPositions.value = positionOptions.value.map(o => o.value)
}

async function addSchool() {
  const name = newName.value.trim()
  if (!name) { message.warning('请填写学校名称'); return }
  try {
    await api.addSchool(name, newPositions.value)
    message.success('学校已添加')
    newName.value = ''
    newPositions.value = []
    loadAll()
  } catch (e) { message.error(e.message) }
}

function removeSchool(s) {
  dialog.warning({
    title: '删除学校',
    content: `确定删除学校「${s.name}」？已收简历记录将保留。`,
    positiveText: '删除',
    negativeText: '取消',
    onPositiveClick: async () => {
      try {
        await api.deleteSchool(s.id)
        message.success('已删除')
        loadAll()
      } catch (e) { message.error(e.message) }
    }
  })
}

function openEditPositions(s) {
  let pids = s.position_ids || []
  const allIds = positions.value.map(p => p.id)
  let selectAll = allIds.length > 0 && allIds.every(id => pids.includes(id))
  dialog.info({
    title: `学校「${s.name}」绑定岗位`,
    showIcon: false,
    content: () => h('div', { style: 'width:100%' }, [
      h('div', { style: 'margin-bottom:8px;display:flex;align-items:center;gap:8px' }, [
        h('span', { style: 'color:#475569;font-size:13px' }, '选择该校开放招聘的岗位：'),
        h('label', {
          style: 'display:inline-flex;align-items:center;gap:4px;font-size:13px;cursor:pointer;color:#2563eb'
        }, [
          h('input', {
            type: 'checkbox',
            checked: selectAll,
            style: 'width:15px;height:15px;accent-color:#2563eb',
            onInput: e => {
              selectAll = e.target.checked
              pids = selectAll ? [...allIds] : []
              const root = e.target.closest('.n-dialog__content')
              if (root) {
                root.querySelectorAll('input[data-pos]').forEach(cb => {
                  cb.checked = selectAll
                })
              }
            }
          }),
          '全部添加'
        ])
      ]),
      ...positions.value.map(p => h('label', {
        style: 'display:inline-flex;align-items:center;gap:6px;margin:4px 12px 4px 0;font-size:14px;cursor:pointer'
      }, [
        h('input', {
          type: 'checkbox',
          'data-pos': true,
          checked: pids.includes(p.id),
          style: 'width:16px;height:16px;accent-color:#2563eb',
          onInput: e => {
            if (e.target.checked) { if (!pids.includes(p.id)) pids.push(p.id) }
            else pids = pids.filter(x => x !== p.id)
            selectAll = allIds.every(id => pids.includes(id))
          }
        }),
        p.name
      ]))
    ]),
    positiveText: '保存',
    negativeText: '取消',
    onPositiveClick: async () => {
      try {
        await api.updateSchoolPositions(s.id, pids)
        message.success('已更新岗位绑定')
        loadAll()
      } catch (e) { message.error(e.message) }
    }
  })
}

onMounted(loadAll)
</script>
