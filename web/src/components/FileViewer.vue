<template>
  <div class="file-viewer">
    <!-- 图片 -->
    <div v-if="type === 'image'" class="image-body">
      <img :src="source" alt="预览" />
    </div>

    <!-- PDF：浏览器原生渲染 -->
    <iframe
      v-else-if="type === 'pdf'"
      :src="source"
      class="pdf-frame"
      title="PDF 预览"
    ></iframe>

    <!-- Markdown：渲染 HTML -->
    <div v-else-if="type === 'markdown'" class="md-body">
      <div v-if="loading" class="preview-hint">加载中…</div>
      <div v-else-if="error" class="preview-hint error">{{ error }}</div>
      <div v-else class="md-content" v-html="mdHtml"></div>
    </div>

    <!-- docx：mammoth 转 HTML（保留格式） -->
    <div v-else-if="type === 'docx'" class="word-body">
      <div v-if="loading" class="preview-hint">加载中…</div>
      <div v-else-if="error" class="preview-hint error">{{ error }}</div>
      <div v-else class="word-content" v-html="wordHtml"></div>
    </div>

    <!-- 文本 / doc：读取内容显示 -->
    <div v-else-if="type === 'text' || type === 'doc'" class="text-body">
      <div v-if="loading" class="preview-hint">加载中…</div>
      <div v-else-if="error" class="preview-hint error">{{ error }}</div>
      <pre v-else>{{ textContent }}</pre>
    </div>

    <!-- 不支持 -->
    <div v-else class="preview-empty">
      <div style="font-size:40px;margin-bottom:10px">📄</div>
      <div style="color:#94a3b8;margin-bottom:8px">暂不支持预览 {{ ext || '该格式' }} 文件</div>
      <n-button size="small" type="primary" @click="download">下载查看</n-button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onBeforeUnmount } from 'vue'
import { marked } from 'marked'
import mammoth from 'mammoth/mammoth.browser'
import { api } from '../api'

const props = defineProps({
  source: { type: String, required: true },
  filename: { type: String, default: '' },
  resumeId: { type: Number, default: 0 }
})

const textContent = ref('')
const mdHtml = ref('')
const wordHtml = ref('')
const loading = ref(false)
const error = ref('')

// 根据文件名扩展名判断渲染类型
const ext = computed(() => {
  const name = props.filename || props.source.split('?')[0]
  const dot = name.lastIndexOf('.')
  return dot >= 0 ? name.slice(dot + 1).toLowerCase() : ''
})
const type = computed(() => {
  const e = ext.value
  if (['png', 'jpg', 'jpeg', 'gif', 'webp', 'svg', 'bmp'].includes(e)) return 'image'
  if (e === 'pdf') return 'pdf'
  if (['md', 'markdown'].includes(e)) return 'markdown'
  if (['txt', 'text'].includes(e)) return 'text'
  if (e === 'docx') return 'docx'
  if (e === 'doc') return 'doc'
  return 'unsupported'
})

async function loadText() {
  if (type.value !== 'markdown' && type.value !== 'text' && type.value !== 'docx' && type.value !== 'doc') return
  loading.value = true
  error.value = ''
  try {
    if (type.value === 'docx') {
      // mammoth 解析 docx → HTML（保留标题/加粗/列表等格式）
      const res = await fetch(props.source)
      const buf = await res.arrayBuffer()
      const result = await mammoth.convertToHtml({ arrayBuffer: buf })
      wordHtml.value = result.value || '（未提取到内容）'
    } else if (type.value === 'doc') {
      const d = await api.resumeText(props.resumeId)
      textContent.value = d.text || '（未提取到文字内容）'
    } else {
      const res = await fetch(props.source)
      const raw = await res.text()
      if (type.value === 'markdown') {
        mdHtml.value = marked.parse(raw)
      } else {
        textContent.value = raw
      }
    }
  } catch (e) {
    error.value = '内容加载失败，可下载查看原文件'
  } finally {
    loading.value = false
  }
}

function download() {
  window.open(props.source, '_blank')
}

watch(() => [props.source, props.resumeId], () => { loadText() })
loadText()

onBeforeUnmount(() => {})
</script>

<style scoped>
.file-viewer {
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 0;
}
.pdf-frame {
  flex: 1;
  width: 100%;
  border: none;
  min-height: 0;
  background: #eef1f5;
}
.image-body {
  flex: 1;
  min-height: 0;
  overflow: auto;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #eef1f5;
  padding: 16px;
}
.image-body img {
  max-width: 100%;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.15);
  background: #fff;
}
.text-body {
  flex: 1;
  min-height: 0;
  overflow: auto;
  background: #fff;
  padding: 16px 20px;
}
.text-body pre {
  margin: 0;
  font-family: "PingFang SC", "Microsoft YaHei", system-ui, sans-serif;
  font-size: 14px;
  line-height: 1.7;
  white-space: pre-wrap;
  word-break: break-word;
  color: #1e293b;
}
.md-body {
  flex: 1;
  min-height: 0;
  overflow: auto;
  background: #fff;
  padding: 16px 24px;
}
.md-content {
  font-size: 14px;
  line-height: 1.8;
  color: #1e293b;
  word-break: break-word;
}
.md-content h1,
.md-content h2,
.md-content h3 {
  margin: 16px 0 8px;
  color: #1e293b;
  border-bottom: 1px solid #e5e7eb;
  padding-bottom: 6px;
}
.md-content h1 { font-size: 22px; }
.md-content h2 { font-size: 18px; }
.md-content h3 { font-size: 16px; }
.md-content p { margin: 8px 0; }
.md-content ul,
.md-content ol {
  margin: 8px 0;
  padding-left: 22px;
}
.md-content li { margin: 4px 0; }
.md-content code {
  background: #f1f5f9;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 13px;
  color: #dc2626;
}
.md-content blockquote {
  margin: 10px 0;
  padding: 6px 14px;
  border-left: 3px solid #2563eb;
  background: #f8fafc;
  color: #475569;
}
.md-content strong { font-weight: 600; }
.word-body {
  flex: 1;
  min-height: 0;
  overflow: auto;
  background: #fff;
  padding: 16px 24px;
}
.word-content {
  font-size: 14px;
  line-height: 1.8;
  color: #1e293b;
  word-break: break-word;
}
.word-content h1,
.word-content h2,
.word-content h3 {
  margin: 16px 0 8px;
  color: #1e293b;
  border-bottom: 1px solid #e5e7eb;
  padding-bottom: 6px;
}
.word-content h1 { font-size: 22px; }
.word-content h2 { font-size: 18px; }
.word-content h3 { font-size: 16px; }
.word-content p { margin: 8px 0; }
.word-content ul,
.word-content ol {
  margin: 8px 0;
  padding-left: 22px;
}
.word-content li { margin: 4px 0; }
.word-content strong { font-weight: 600; }
.word-content table {
  border-collapse: collapse;
  width: 100%;
  margin: 8px 0;
}
.word-content table td,
.word-content table th {
  border: 1px solid #e2e8f0;
  padding: 6px 10px;
}
.preview-hint {
  color: #94a3b8;
  font-size: 14px;
  text-align: center;
  padding: 40px 20px;
}
.preview-hint.error {
  color: #dc2626;
}
.preview-empty {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #94a3b8;
}
</style>
