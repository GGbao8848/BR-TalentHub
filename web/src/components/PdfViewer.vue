<template>
  <div class="pdf-viewer">
    <!-- 工具栏 -->
    <div class="pdf-toolbar">
      <n-space align="center" size="8">
        <n-button size="tiny" :disabled="page <= 1" @click="prevPage">‹ 上一页</n-button>
        <span class="page-info">{{ page }} / {{ numPages }}</span>
        <n-button size="tiny" :disabled="page >= numPages" @click="nextPage">下一页 ›</n-button>
      </n-space>
      <n-space align="center" size="8">
        <n-button size="tiny" @click="zoomOut">−</n-button>
        <span class="zoom-info">{{ Math.round(scale * 100) }}%</span>
        <n-button size="tiny" @click="zoomIn">+</n-button>
        <n-button size="tiny" @click="fitWidth">适应宽度</n-button>
      </n-space>
    </div>

    <!-- 渲染区 -->
    <div class="pdf-scroll" ref="scrollEl" @scroll="onScroll">
      <canvas ref="canvasEl"></canvas>
      <div v-if="loading" class="pdf-loading">加载中…</div>
      <div v-if="error" class="pdf-error">{{ error }}</div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, onBeforeUnmount, nextTick } from 'vue'
import * as pdfjsLib from 'pdfjs-dist'
import workerSrc from 'pdfjs-dist/build/pdf.worker.min.mjs?url'

pdfjsLib.GlobalWorkerOptions.workerSrc = workerSrc

const props = defineProps({
  source: { type: String, required: true }
})

const canvasEl = ref(null)
const scrollEl = ref(null)
const page = ref(1)
const numPages = ref(0)
const scale = ref(1.0)
const loading = ref(false)
const error = ref('')
let pdfDoc = null
let renderTask = null

async function loadPdf() {
  loading.value = true
  error.value = ''
  page.value = 1
  numPages.value = 0
  scale.value = 1.0
  try {
    if (pdfDoc) { pdfDoc.destroy(); pdfDoc = null }
    pdfDoc = await pdfjsLib.getDocument(props.source).promise
    numPages.value = pdfDoc.numPages
    await renderPage()
  } catch (e) {
    console.error('PDF 加载失败', e)
    error.value = '无法预览该简历（文件可能不是有效的 PDF）'
  } finally {
    loading.value = false
  }
}

async function renderPage() {
  if (!pdfDoc || !canvasEl.value) return
  const p = Math.min(Math.max(1, page.value), numPages.value)
  const pdfPage = await pdfDoc.getPage(p)
  const viewport = pdfPage.getViewport({ scale: scale.value })
  const canvas = canvasEl.value
  canvas.width = viewport.width
  canvas.height = viewport.height
  canvas.style.width = viewport.width + 'px'
  canvas.style.height = viewport.height + 'px'
  if (renderTask) { renderTask.cancel(); renderTask = null }
  const ctx = canvas.getContext('2d')
  renderTask = pdfPage.render({ canvasContext: ctx, viewport })
  await renderTask.promise
}

function prevPage() { if (page.value > 1) { page.value--; renderPage() } }
function nextPage() { if (page.value < numPages.value) { page.value++; renderPage() } }
function zoomIn() { scale.value = Math.min(3, scale.value + 0.25); renderPage() }
function zoomOut() { scale.value = Math.max(0.5, scale.value - 0.25); renderPage() }
async function fitWidth() {
  const w = scrollEl.value ? scrollEl.value.clientWidth - 16 : 800
  const p = await pdfDoc.getPage(page.value)
  const vp = p.getViewport({ scale: 1 })
  scale.value = Math.max(0.5, Math.min(3, w / vp.width))
  renderPage()
}
function onScroll() { renderPage() }

watch(() => props.source, () => { loadPdf() })

onBeforeUnmount(() => {
  if (pdfDoc) pdfDoc.destroy()
})

loadPdf()
</script>

<style scoped>
.pdf-viewer { display: flex; flex-direction: column; height: 100%; min-height: 0; }
.pdf-toolbar {
  display: flex; align-items: center; justify-content: space-between; gap: 12px;
  padding: 8px 12px; border-bottom: 1px solid #e2e8f0; flex-shrink: 0; background: #f8fafc;
}
.page-info, .zoom-info { font-size: 13px; color: #475569; min-width: 48px; text-align: center; }
.pdf-scroll {
  flex: 1; overflow: auto; min-height: 0; padding: 12px; display: flex; flex-direction: column;
  align-items: center; background: #eef1f5;
}
.pdf-scroll canvas { box-shadow: 0 2px 12px rgba(0,0,0,0.15); background: #fff; }
.pdf-loading, .pdf-error { padding: 40px 20px; color: #94a3b8; font-size: 14px; text-align: center; }
.pdf-error { color: #dc2626; }
</style>
