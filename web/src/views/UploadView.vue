<template>
  <div class="upload-page">
    <div class="hero">
      <h1>{{ eventTitle }}</h1>
      <p>请填写信息并上传简历</p>
    </div>

    <div v-if="!submitted" class="form">
      <n-form ref="formRef" :model="form" :rules="rules" label-placement="top">
        <n-form-item label="姓名" path="name">
          <n-input v-model:value="form.name" placeholder="请填写姓名" maxlength="30" />
        </n-form-item>
        <n-form-item label="手机号" path="phone">
          <n-input v-model:value="form.phone" placeholder="请填写手机号" maxlength="20" />
        </n-form-item>
        <n-form-item label="应聘岗位" path="position">
          <n-select
            v-model:value="form.positionId"
            :options="positionOptions"
            placeholder="请选择或搜索岗位"
            filterable
            clearable
          />
        </n-form-item>
        <n-form-item label="简历附件" path="file">
          <div class="upload-zone" @click="openFilePicker">
            <div style="font-size:36px">📎</div>
            <div style="font-size:16px;color:#1e293b;margin-top:8px">{{ fileLabel }}</div>
            <div style="font-size:13px;color:#94a3b8;margin-top:6px">支持 PDF / DOC / DOCX，≤20MB</div>
          </div>
          <input ref="fileInput" type="file" accept=".pdf,.doc,.docx" style="display:none" @change="onFileChange">
        </n-form-item>
        <n-button type="primary" block :loading="uploading" @click="submit">
          提交简历
        </n-button>
        <div style="text-align:center;font-size:12px;color:#94a3b8;margin-top:14px">提交即表示同意将简历用于招聘用途</div>
      </n-form>
    </div>

    <div v-else class="success-box">
      <div style="font-size:64px;color:#22c55e;animation:tickPop .5s ease">✅</div>
      <h2>上传成功！</h2>
      <p>岗位「{{ selectedPositionName }}」的简历已提交，感谢参加本次招聘会。</p>
      <n-button type="primary" @click="resetForm">再传一份</n-button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { api, toast } from '../api'

const formRef = ref()
const fileInput = ref()
const form = ref({ name: '', phone: '', positionId: null })
const file = ref(null)
const uploading = ref(false)
const submitted = ref(false)
const selectedPositionName = ref('')
const eventTitle = ref('招聘会')
const positions = ref([])

const params = new URLSearchParams(location.search)
const schoolName = params.get('school') || ''

const rules = {
  name: { required: true, message: '请填写姓名', trigger: 'blur' },
  phone: { required: true, message: '请填写手机号', trigger: 'blur' },
  positionId: { required: true, message: '请选择应聘岗位', trigger: 'change' },
  file: { required: true, validator: () => !!file.value, message: '请选择简历附件', trigger: 'change' }
}

const positionOptions = computed(() =>
  positions.value.map(p => ({ label: p.name, value: p.id }))
)

const fileLabel = computed(() => {
  if (!file.value) return '点击选择简历文件'
  const mb = (file.value.size / 1024 / 1024).toFixed(1)
  return `📄 ${file.value.name}（${mb}MB）`
})

async function loadEvent() {
  try {
    const cfg = await api.getConfig()
    const company = cfg.event_name || '江苏北人智能制造科技股份有限公司'
    eventTitle.value = schoolName ? `${schoolName} · ${company}` : company
    const opt = await api.getOptions(schoolName)
    positions.value = opt.positions || []
    if (!positions.value.length && schoolName) {
      toast('该学校暂未配置招聘岗位，请联系现场工作人员')
    }
  } catch (e) {
    eventTitle.value = '招聘会'
  }
}

function openFilePicker() { fileInput.value.click() }
function onFileChange(e) {
  const f = e.target.files[0]
  if (!f) return
  const ok = ['.pdf', '.doc', '.docx'].some(x => f.name.toLowerCase().endsWith(x))
  if (!ok) { toast('仅支持 PDF / DOC / DOCX 格式'); file.value = null; return }
  if (f.size > 20 * 1024 * 1024) { toast('文件不能超过 20MB'); file.value = null; return }
  file.value = f
}

async function submit() {
  try {
    await formRef.value.validate()
  } catch (e) { return }
  const pos = positions.value.find(p => p.id === form.value.positionId)
  if (!pos) { toast('请选择应聘岗位'); return }
  if (!file.value) { toast('请选择简历附件'); return }
  selectedPositionName.value = pos.name

  const fd = new FormData()
  fd.append('name', form.value.name.trim())
  fd.append('phone', form.value.phone.trim())
  fd.append('position', pos.name)
  fd.append('position_id', pos.id)
  fd.append('school', schoolName)
  fd.append('file', file.value)

  uploading.value = true
  try {
    await api.uploadResume(fd)
    submitted.value = true
  } catch (e) {
    toast(e.message)
  } finally {
    uploading.value = false
  }
}

function resetForm() {
  submitted.value = false
  form.value = { name: '', phone: '', positionId: null }
  file.value = null
  if (fileInput.value) fileInput.value.value = ''
}

onMounted(loadEvent)
</script>

<style scoped>
.upload-page { min-height: 100vh; background: #f4f6f9; font-family: "PingFang SC", "Microsoft YaHei", sans-serif; }
.hero {
  background: linear-gradient(135deg, #0f2027, #2c5364); color: #fff;
  padding: 28px 20px; text-align: center;
}
.hero h1 { font-size: 20px; margin-bottom: 6px; }
.hero p { font-size: 14px; color: #b3cde0; }
.form { padding: 24px 20px; max-width: 480px; margin: 0 auto; }
.upload-zone {
  border: 2px dashed #b0bfcc; border-radius: 12px; padding: 26px 16px;
  text-align: center; cursor: pointer; background: #fff; width: 100%;
  transition: border .15s, background .15s;
}
.upload-zone:hover { border-color: #2563eb; background: #f8fafc; }
.success-box { text-align: center; padding: 40px 24px; }
.success-box h2 { margin: 12px 0 8px; font-size: 20px; }
.success-box p { color: #5a6b7a; font-size: 14px; margin-bottom: 24px; }
@keyframes tickPop { 0% { transform: scale(0); } 70% { transform: scale(1.3); } 100% { transform: scale(1); } }
</style>
