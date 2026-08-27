<template>
  <n-config-provider :theme-overrides="themeOverrides">
    <n-message-provider>
      <n-dialog-provider>
        <n-notification-provider>
          <message-bridge />
          <n-layout style="height:100vh;overflow:hidden">
            <n-layout-header bordered style="display:flex;align-items:center;justify-content:space-between;padding:0 24px;height:56px;flex-shrink:0">
              <div style="font-size:18px;font-weight:700;color:#1e293b">
                BR <span style="color:#2563eb">Tech</span> · 招聘会管理
              </div>
              <div style="font-size:15px;color:#475569;font-weight:600">{{ eventName }}</div>
            </n-layout-header>
            <n-layout has-sider style="height:calc(100vh - 56px)">
              <n-layout-sider
                bordered
                :width="210"
                :collapsed-width="64"
                collapse-mode="width"
                :collapsed="siderCollapsed"
                :show-trigger="'bar'"
                @collapse="siderCollapsed = true"
                @expand="siderCollapsed = false"
                content-style="padding:12px 0;height:100%;overflow-y:auto"
              >
                <n-menu
                  :value="activeKey"
                  :options="menuOptions"
                  :collapsed="siderCollapsed"
                  :collapsed-width="64"
                  :collapsed-icon-size="20"
                  @update:value="onMenuChange"
                />
              </n-layout-sider>
              <n-layout content-style="padding:24px;background:#f5f7fa;height:100%;overflow:hidden;display:flex">
                <div style="flex:1;min-height:0;overflow-y:auto">
                  <router-view />
                </div>
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
const siderCollapsed = ref(false)

// 桥接组件：在 provider 内取 message 实例注入 api 层
const MessageBridge = defineComponent({
  setup() {
    setMessageApi(useMessage())
    return () => null
  }
})

const menuOptions = [
  { label: '现场大屏', key: 'screen', icon: () => h('span', { style: 'font-size:16px' }, '📺') },
  { label: '简历管理', key: 'resumes', icon: () => h('span', { style: 'font-size:16px' }, '📄') },
  { label: '岗位管理', key: 'positions', icon: () => h('span', { style: 'font-size:16px' }, '💼') },
  { label: '学校管理', key: 'schools', icon: () => h('span', { style: 'font-size:16px' }, '🏫') },
  { label: '数据看板', key: 'dashboard', icon: () => h('span', { style: 'font-size:16px' }, '📊') }
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
