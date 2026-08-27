<template>
  <n-config-provider :theme-overrides="themeOverrides">
    <n-message-provider>
      <upload-bridge />
    </n-message-provider>
  </n-config-provider>
</template>

<script setup>
import { h, defineComponent } from 'vue'
import { NConfigProvider, NMessageProvider, useMessage } from 'naive-ui'
import { themeOverrides } from './theme'
import { setMessageApi } from './api'
import UploadView from './views/UploadView.vue'

// 桥接：在 provider 内取 message 实例注入 api 层
const UploadBridge = defineComponent({
  setup() {
    setMessageApi(useMessage())
    return () => h(UploadView)
  }
})
</script>
