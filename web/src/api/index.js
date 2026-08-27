// fetch 封装：统一错误处理 + JSON
let msgApi = null
export function setMessageApi(m) { msgApi = m }

function toast(msg, type = 'error') {
  if (msgApi) {
    if (type === 'error') msgApi.error(msg)
    else msgApi.success(msg)
  } else {
    console.error('[api]', msg)
  }
}

async function request(url, options = {}) {
  const res = await fetch(url, options)
  if (res.status === 204) return null
  const ct = res.headers.get('content-type') || ''
  if (ct.includes('application/json')) {
    const data = await res.json()
    if (!res.ok) {
      const detail = typeof data.detail === 'string' ? data.detail : (data.detail || res.statusText)
      throw new Error(detail)
    }
    return data
  }
  // 非 JSON（文件下载等）
  if (!res.ok) throw new Error(res.statusText)
  return res
}

export const api = {
  // 配置 / 统计
  getConfig: () => request('/api/config'),
  saveConfig: (payload) => request('/api/config', {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload)
  }),
  resetEvent: () => request('/api/event/reset', { method: 'POST' }),
  getStats: () => request('/api/stats'),
  getOptions: (school) => request('/api/options?school=' + encodeURIComponent(school || '')),

  // 岗位
  listPositions: () => request('/api/positions'),
  addPosition: (name, requirement) => request('/api/positions', {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ name, requirement })
  }),
  updatePosition: (id, name, requirement) => request('/api/positions/' + id, {
    method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ name, requirement })
  }),
  deletePosition: (id) => request('/api/positions/' + id, { method: 'DELETE' }),

  // 学校
  listSchools: () => request('/api/schools'),
  addSchool: (name, positions) => request('/api/schools', {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ name, positions })
  }),
  updateSchoolPositions: (id, positions) => request(`/api/schools/${id}/positions`, {
    method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ positions })
  }),
  deleteSchool: (id) => request('/api/schools/' + id, { method: 'DELETE' }),
  activateSchool: (id) => request(`/api/schools/${id}/activate`, { method: 'POST' }),
  schoolQrcode: (id) => `/api/schools/${id}/qrcode`,

  // 简历
  listResumes: (params) => request('/api/resumes?' + new URLSearchParams(params)),
  deleteResume: (id) => request('/api/resumes/' + id, { method: 'DELETE' }),
  resumeDownloadUrl: (id) => `/api/resumes/${id}/download`,
  resumePreviewUrl: (id) => `/api/resumes/${id}/download?inline=1`,
  exportZipUrl: (params) => '/api/resumes/export.zip?' + new URLSearchParams(params),
  uploadResume: (formData) => request('/api/resumes/upload', { method: 'POST', body: formData }),

  // 看板
  getDashboard: () => request('/api/dashboard')
}

export { toast }
