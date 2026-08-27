<template>
  <n-config-provider :theme-overrides="themeOverrides">
    <n-message-provider>
      <n-dialog-provider>
        <n-notification-provider>
          <message-bridge />
          <n-layout style="min-height:100vh">
            <n-layout-header bordered style="display:flex;align-items:center;justify-content:space-between;padding:0 24px;height:56px">
              <div style="font-size:18px;font-weight:700;color:#1e293b">
                BR <span style="color:#2563eb">Tech</span> · 招聘会管理
              </div>
              <div style="font-size:15px;color:#475569;font-weight:600">{{ eventName }}</div>
            </n-layout-header>
            <n-layout has-sider style="min-height:calc(100vh - 56px)">
              <n-layout-sider bordered :width="200" content-style="padding:16px 0">
                <n-menu
                  :value="activeKey"
                  :options="menuOptions"
                  @update:value="onMenuChange"
                />
              </n-layout-sider>
              <n-layout content-style="padding:24px;background:#f5f7fa">
                <router-view />
              </n-layout>
            </n-layout>
          </n-layout>
        </n-notification-provider>
      </n-dialog-provider>
    </n-message-provider>
  </n-config-provider>
</template>

<script setup>
import { ref, computed, h, defineComponent, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  NConfigProvider, NMessageProvider, NDialogProvider, NNotificationProvider,
  NLayout, NLayoutHeader, NLayoutSider, NMenu, useMessage
} from 'naive-ui'
import { themeOverrides } from '../theme'
import { api, setMessageApi } from '../api'

const route = useRoute()
const router = useRouter()
const eventName = ref('BR 招聘会')

// 桥接组件：在 provider 内取 message 实例注入 api 层
const MessageBridge = defineComponent({
  setup() {
    setMessageApi(useMessage())
    return () => null
  }
})

const menuOptions = [
  { label: '📺 现场大屏', key: 'screen' },
  { label: '📄 简历管理', key: 'resumes' },
  { label: '💼 岗位管理', key: 'positions' },
  { label: '🏫 学校管理', key: 'schools' },
  { label: '📊 数据看板', key: 'dashboard' }
]

const activeKey = computed(() => route.name)

function onMenuChange(key) {
  router.push('/' + key)
}

onMounted(async () => {
  try {
    const cfg = await api.getConfig()
    eventName.value = cfg.event_name
  } catch (e) {}
})
</script>
