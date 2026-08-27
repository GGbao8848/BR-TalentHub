<template>
  <div>
    <n-grid :cols="3" :x-gap="16" style="margin-bottom:16px">
      <n-grid-item>
        <n-card embedded style="text-align:center">
          <div style="font-size:34px;font-weight:700;color:#2563eb">{{ dash.total }}</div>
          <div style="font-size:13px;color:#64748b">简历总数</div>
        </n-card>
      </n-grid-item>
      <n-grid-item>
        <n-card embedded style="text-align:center">
          <div style="font-size:34px;font-weight:700;color:#2563eb">{{ schoolCount }}</div>
          <div style="font-size:13px;color:#64748b">学校数</div>
        </n-card>
      </n-grid-item>
      <n-grid-item>
        <n-card embedded style="text-align:center">
          <div style="font-size:34px;font-weight:700;color:#2563eb">{{ positionCount }}</div>
          <div style="font-size:13px;color:#64748b">岗位数</div>
        </n-card>
      </n-grid-item>
    </n-grid>

    <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:16px">
      <n-card title="按学校统计">
        <div v-if="!dash.by_school || !dash.by_school.length" class="empty">暂无数据</div>
        <div v-else class="hbar-wrap">
          <div v-for="x in dash.by_school" :key="x.name" class="hbar-row" :title="`${x.name}: ${x.count}`">
            <div class="hbar-label">{{ x.name }}</div>
            <div class="hbar-track"><div class="hbar-fill" :style="{ width: pct(x.count) + '%' }"></div></div>
            <div class="hbar-val">{{ x.count }}</div>
          </div>
        </div>
      </n-card>

      <n-card title="按岗位统计">
        <div v-if="!dash.by_position || !dash.by_position.length" class="empty">暂无数据</div>
        <div v-else class="hbar-wrap">
          <div v-for="x in dash.by_position" :key="x.name" class="hbar-row" :title="`${x.name}: ${x.count}`">
            <div class="hbar-label">{{ x.name }}</div>
            <div class="hbar-track"><div class="hbar-fill" :style="{ width: pct(x.count) + '%' }"></div></div>
            <div class="hbar-val">{{ x.count }}</div>
          </div>
        </div>
      </n-card>

      <n-card title="近 14 日趋势">
        <div v-if="!dash.by_day || !dash.by_day.length" class="empty">暂无数据</div>
        <div v-else class="hbar-wrap">
          <div v-for="x in dash.by_day" :key="x.day" class="hbar-row" :title="`${x.day}: ${x.count}`">
            <div class="hbar-label">{{ x.day.slice(5) }}</div>
            <div class="hbar-track"><div class="hbar-fill" :style="{ width: pct(x.count) + '%' }"></div></div>
            <div class="hbar-val">{{ x.count }}</div>
          </div>
        </div>
      </n-card>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { api } from '../api'

const dash = ref({ total: 0, by_school: [], by_position: [], by_day: [] })
const schoolCount = ref(0)
const positionCount = ref(0)

function pct(n) {
  const max = maxCount()
  return max ? Math.round(n / max * 100) : 0
}
function maxCount() {
  const all = [...(dash.value.by_school || []), ...(dash.value.by_position || []), ...(dash.value.by_day || [])]
  return Math.max(0, ...all.map(x => x.count))
}

async function loadDashboard() {
  try {
    const [d, schools, positions] = await Promise.all([
      api.getDashboard(), api.listSchools(), api.listPositions()
    ])
    dash.value = d
    schoolCount.value = schools.length
    positionCount.value = positions.length
  } catch (e) { console.error(e) }
}

onMounted(loadDashboard)
</script>

<style scoped>
.empty { color: #94a3b8; text-align: center; padding: 24px 0; font-size: 14px; }
.hbar-wrap { min-height: 200px; max-height: 420px; overflow-y: auto; padding-right: 4px; }
.hbar-row { display: flex; align-items: center; gap: 10px; margin: 7px 0; }
.hbar-label { width: 150px; font-size: 13px; color: #475569; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; flex-shrink: 0; }
.hbar-track { flex: 1; height: 22px; background: #f1f5f9; border-radius: 6px; overflow: hidden; }
.hbar-fill { height: 100%; background: linear-gradient(90deg, #2563eb, #06b6d4); border-radius: 6px; min-width: 2px; transition: width .4s; }
.hbar-val { width: 44px; text-align: right; font-size: 13px; color: #2563eb; flex-shrink: 0; }
@media (max-width: 1100px) {
  .dash-cols { grid-template-columns: 1fr !important; }
}
</style>
