<template>
  <div>
    <!-- 招聘会设置 -->
    <n-card title="招聘会设置" style="margin-bottom:16px">
      <n-space align="end" style="flex-wrap:wrap">
        <n-form-item label="招聘会名称" style="min-width:260px">
          <n-input v-model:value="eventName" placeholder="如：2026 招聘会" />
        </n-form-item>
        <n-form-item label="简历保存目录" style="min-width:260px">
          <n-input v-model:value="saveDir" placeholder="如：D:\招聘会\2026" />
        </n-form-item>
        <n-button type="primary" size="large" @click="saveConfig">保存</n-button>
        <n-button type="error" size="large" ghost @click="resetEvent">开始新一场</n-button>
      </n-space>
      <div style="color:#94a3b8;font-size:12px;margin-top:8px">当前保存目录：{{ saveDir }}</div>
    </n-card>

    <!-- 现场扫码 -->
    <n-card title="现场扫码上传">
      <div style="display:flex;gap:28px;flex-wrap:wrap">
        <!-- 二维码 -->
        <div style="flex:0 0 300px;text-align:center;padding:16px;border:1px solid #e2e8f0;border-radius:12px">
          <div style="color:#94a3b8;font-size:13px;margin-bottom:6px">当前招聘学校</div>
          <div style="font-size:22px;font-weight:700;color:#d97706;min-height:32px">{{ activeSchoolName }}</div>
          <n-image :src="qrSrc" width="220" height="220" style="margin:10px auto;display:block;border:1px solid #e2e8f0;border-radius:10px" />
          <div style="font-size:13px;color:#475569">📱 手机扫码上传简历</div>
          <div style="font-size:12px;color:#94a3b8;word-break:break-all;margin-top:4px">{{ qrUrl }}</div>
        </div>

        <!-- 右栏 -->
        <div style="flex:1;min-width:280px">
          <div style="display:flex;align-items:center;gap:12px;padding:10px 14px;background:#f8fafc;border-radius:10px;margin-bottom:16px">
            <span style="color:#64748b;font-size:13px">切换学校</span>
            <n-select v-model:value="activeSchool" :options="schoolOptions" style="flex:1" @update:value="switchActiveSchool" />
          </div>
          <n-grid :cols="2" :x-gap="12" style="margin-bottom:16px">
            <n-grid-item>
              <n-card embedded size="small" style="text-align:center">
                <div style="font-size:32px;font-weight:700;color:#2563eb">{{ statCount }}</div>
                <div style="font-size:13px;color:#64748b">已收简历</div>
              </n-card>
            </n-grid-item>
            <n-grid-item>
              <n-card embedded size="small" style="text-align:center">
                <div style="font-size:32px;font-weight:700;color:#2563eb">{{ statCount }}</div>
                <div style="font-size:13px;color:#64748b">本场新增</div>
              </n-card>
            </n-grid-item>
          </n-grid>
          <div style="font-weight:600;color:#1e293b;margin-bottom:8px">最近上传</div>
          <div style="max-height:320px;overflow-y:auto;border:1px solid #e2e8f0;border-radius:10px;padding:4px 12px">
            <n-empty v-if="!recent.length" description="暂无上传记录" style="padding:20px 0" />
            <div v-for="item in recent" :key="item.id" style="display:flex;align-items:center;gap:10px;padding:10px 0;border-bottom:1px solid #f1f5f9;font-size:14px">
              <span style="width:8px;height:8px;border-radius:50%;background:#22c55e;flex-shrink:0"></span>
              <span style="flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">📄 {{ item.original }}</span>
              <span style="color:#94a3b8;font-size:12px">{{ item.upload_time.slice(11,16) }} · {{ item.name || '未留名' }}{{ item.school_name ? ' · ' + item.school_name : '' }}</span>
            </div>
          </div>
        </div>
      </div>
    </n-card>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { api } from '../api'

const eventName = ref('')
const saveDir = ref('')
const activeSchoolName = ref('未指定学校')
const activeSchool = ref(null)
const schoolOptions = ref([])
const qrSrc = ref('/api/qrcode?t=1')
const qrUrl = ref('')
const statCount = ref(0)
const recent = ref([])
let timer = null
let lastMaxId = 0

async function loadConfig() {
  try {
    const cfg = await api.getConfig()
    eventName.value = cfg.event_name
    saveDir.value = cfg.save_dir
    activeSchoolName.value = cfg.active_school || '未指定学校'
    activeSchool.value = cfg.active_school || null
    qrUrl.value = cfg.active_school
      ? `手机访问：http://${cfg.host_ip}:${cfg.port}/upload?event=${cfg.event_id}&school=${encodeURIComponent(cfg.active_school)}`
      : `手机访问：http://${cfg.host_ip}:${cfg.port}/upload?event=${cfg.event_id}`
    refreshQr(cfg.active_school)
    const schools = await api.listSchools()
    schoolOptions.value = schools.map(s => ({ label: s.name, value: s.name }))
  } catch (e) { console.error(e) }
}

function refreshQr(school) {
  qrSrc.value = school
    ? `/api/qrcode?school=${encodeURIComponent(school)}&t=${Date.now()}`
    : '/api/qrcode?t=' + Date.now()
}

async function saveConfig() {
  try {
    await api.saveConfig({ event_name: eventName.value, save_dir: saveDir.value })
    await loadConfig()
  } catch (e) { console.error(e) }
}

async function resetEvent() {
  if (!confirm('确定开始新一场招聘会？将生成新二维码，已收简历不删除。')) return
  await api.resetEvent()
  await loadConfig()
}

async function switchActiveSchool(name) {
  if (!name) return
  const schools = await api.listSchools()
  const school = schools.find(s => s.name === name)
  if (!school) return
  await api.activateSchool(school.id)
  activeSchoolName.value = name
  refreshQr(name)
}

async function loadStats() {
  try {
    const d = await api.getStats()
    statCount.value = d.count
    recent.value = d.recent || []
    if (d.recent && d.recent.length) {
      const newMax = d.recent[0].id
      if (lastMaxId && newMax > lastMaxId) {
        // 新简历到达横幅
      }
      lastMaxId = newMax
    }
  } catch (e) {}
}

onMounted(async () => {
  await loadConfig()
  loadStats()
  timer = setInterval(loadStats, 3000)
})
onUnmounted(() => { if (timer) clearInterval(timer) })
</script>
