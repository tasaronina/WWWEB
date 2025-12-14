import axios from 'axios'

const api = axios.create({ baseURL: '', withCredentials: true })
api.defaults.xsrfCookieName = 'csrftoken'
api.defaults.xsrfHeaderName = 'X-CSRFToken'

function getCookie(name){
  const m = document.cookie.match(new RegExp('(^|;)\\s*' + name + '\\s*=\\s*([^;]+)'))
  return m ? decodeURIComponent(m.pop()) : ''
}
function withCsrf(headers={}){
  const token = getCookie('csrftoken')
  return token ? { ...headers, 'X-CSRFToken': token } : headers
}
export async function ensureCsrf(){ try{ await api.get('/api/csrf/') }catch{} }

export async function login(username, password){
  await ensureCsrf()
  const { data } = await api.post('/api/auth/login/', { username, password }, { headers: withCsrf() })
  return data
}
export async function logout(){
  await ensureCsrf()
  const { data } = await api.post('/api/auth/logout/', {}, { headers: withCsrf() })
  return data
}
export async function me(){ const { data } = await api.get('/api/auth/me/'); return data }
export async function otpStatus(){ const { data } = await api.get('/api/2fa/otp-status/'); return data }
export async function otpSecret(){ const { data } = await api.get('/api/2fa/otp-secret/'); return data }
export async function otpLogin(code){
  await ensureCsrf()
  const { data } = await api.post('/api/2fa/otp-login/', { key: String(code||'').trim() }, { headers: withCsrf() })
  return data
}
export async function otpReset(){
  await ensureCsrf()
  const { data } = await api.post('/api/2fa/otp-reset/', {}, { headers: withCsrf() })
  return data
}
export async function downloadExport(resource, params, type, filenameNoExt){
  const usp = new URLSearchParams({ ...(params||{}), type: type || 'excel' })
  const url = `/api/${resource}/export/?${usp.toString()}`
  const res = await api.get(url, { responseType: 'blob' })
  const blob = new Blob([res.data])
  const a = document.createElement('a')
  a.href = URL.createObjectURL(blob)
  a.download = `${filenameNoExt || resource}.${type === 'word' ? 'doc' : 'csv'}`
  a.click()
  URL.revokeObjectURL(a.href)
}
export default api
