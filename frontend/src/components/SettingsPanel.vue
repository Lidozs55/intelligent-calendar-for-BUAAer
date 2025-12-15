<template>
  <div class="settings-panel-container">
    <div class="settings-header">
      <h2>设置</h2>
      <button class="close-btn" @click="$emit('close')">×</button>
    </div>
    
    <div class="settings-content">
      <!-- 用户信息和头像设置 -->
      <section class="settings-section">
        <h3>用户信息</h3>
        <div class="settings-form">
          <div class="form-group">
            <label>头像设置</label>
            <div class="avatar-upload-container">
              <div class="avatar-preview">
                <img v-if="avatarUrl" :src="avatarUrl" alt="用户头像" class="avatar-img">
                <div v-else class="avatar-placeholder">{{ getInitials() }}</div>
              </div>
              <div class="avatar-upload-options">
                <input 
                  type="file" 
                  ref="avatarUpload" 
                  accept="image/*" 
                  @change="handleAvatarUpload" 
                  style="display: none;"
                />
                <button type="button" class="save-btn" @click="$refs.avatarUpload.click()">
                  上传头像
                </button>
                <button v-if="avatarUrl" type="button" class="cancel-btn" @click="removeAvatar">
                  移除头像
                </button>
              </div>
            </div>
          </div>
        </div>
      </section>
      
      <!-- 北航账号绑定 -->
      <section class="settings-section">
        <h3>北航账号绑定</h3>
        <form class="settings-form">
          <div class="form-group">
              <label for="buaa-id">北航学号</label>
              <input 
                  type="text" 
                  id="buaa-id" 
                  v-model="buaaId" 
                  placeholder="请输入北航学号"
              />
          </div>
          <div class="form-group">
              <label for="buaa-password">北航密码</label>
              <input 
                  type="password" 
                  id="buaa-password" 
                  v-model="buaaPassword" 
                  placeholder="请输入北航密码"
              />
          </div>
          <div class="button-group">
            <button type="button" class="sync-btn" @click="syncBuaaCourses" :disabled="syncLoading">
                <span v-if="syncLoading">正在同步...</span>
                <span v-else>同步课程表</span>
            </button>
            <button type="button" class="sync-btn" @click="syncSpocHomeworks" :disabled="spocSyncLoading">
                <span v-if="spocSyncLoading">正在同步...</span>
                <span v-else>同步SPOC作业</span>
            </button>
            <button type="button" class="save-btn" @click="saveBuaaId">保存</button>
          </div>
        <div class="form-hint">
            提示：点击"同步课程表"按钮后，系统会自动处理登录流程；spoc作业同步功能不稳定，可能存在提示成功但实际上没有获取到作业的情况。
        </div>
        <div v-if="syncStatus" class="sync-status" :class="syncStatus.includes('成功') ? 'success' : 'error'">
            {{ syncStatus }}
        </div>
        <div v-if="spocSyncStatus" class="sync-status" :class="spocSyncStatus.includes('成功') ? 'success' : 'error'">
            {{ spocSyncStatus }}
        </div>
        </form>
      </section>
      
      <!-- 提醒偏好设置 -->
      <section class="settings-section">
        <h3>提醒偏好设置</h3>
        <div class="settings-form">
          <div class="form-group">
            <label for="course-reminder">课程/讲座/会议提前提醒时间（分钟）</label>
            <input 
              type="number" 
              id="course-reminder" 
              v-model.number="reminderSettings.course" 
              min="0"
            />
          </div>
          
          <div class="form-group">
            <label>考试多级提醒</label>
            <div class="multi-reminder">
              <div class="exam-reminder-item">
                <label class="exam-reminder-label">复习提醒（天数）</label>
                <input 
                  type="number" 
                  v-model.number="reminderSettings.exam[0]" 
                  placeholder="复习提醒" 
                  min="0"
                />
              </div>
              <div class="exam-reminder-item">
                <label class="exam-reminder-label">前往考场提醒（分钟）</label>
                <input 
                  type="number" 
                  v-model.number="reminderSettings.exam[1]" 
                  placeholder="前往考场提醒" 
                  min="0"
                />
              </div>
            </div>
          </div>
          
          <button class="save-btn" @click="saveReminderSettings">保存</button>
        </div>
      </section>
      
      <!-- API_KEY配置 -->
      <section class="settings-section">
        <h3>API_KEY配置</h3>
        <div class="settings-form">
          <div class="form-group">
            <label for="api-key">OpenAI API Key</label>
            <input 
              type="password" 
              id="api-key" 
              v-model="apiKey" 
              placeholder="请输入您的OpenAI API Key"
            />
            <p class="form-hint">API Key将保存在后端服务器的.env文件中，优先使用此配置，否则使用系统环境变量。</p>
          </div>
          
          <button class="save-btn" @click="saveApiKey">保存API Key</button>
        </div>
      </section>
      
      <!-- 主题外观设置 -->
      <section class="settings-section">
        <h3>主题外观设置</h3>
        <div class="settings-form">
          <!-- 暂时禁用深色模式切换 -->
          <div class="form-group" style="display: none;">
            <label>主题选择</label>
            <div class="theme-options">
              <label class="theme-option">
                <input 
                  type="radio" 
                  v-model="theme" 
                  value="light" 
                  checked
                  disabled
                />
                <span>浅色主题</span>
              </label>
              <label class="theme-option">
                <input 
                  type="radio" 
                  v-model="theme" 
                  value="dark" 
                  disabled
                />
                <span>深色主题</span>
              </label>
            </div>
          </div>
          
          <div class="form-group">
            <label for="default-color">默认主题色</label>
            <div class="color-picker-group">
              <input 
                type="color" 
                id="default-color" 
                v-model="defaultColor" 
                class="color-picker"
              />
              <input 
                type="text" 
                v-model="defaultColor" 
                class="color-input"
                placeholder="#4a90e2"
              />
            </div>
          </div>
          
          <button class="save-btn" @click="saveThemeAndColor">保存</button>
        </div>
      </section>
      
      <!-- 精力周期设置 -->
      <section class="settings-section">
        <h3>精力周期设置</h3>
        <div class="settings-form">
          <div class="form-group">
            <label>上午精力</label>
            <select v-model="energyCycle.morning">
              <option value="high">高</option>
              <option value="medium">中</option>
              <option value="low">低</option>
            </select>
          </div>
          
          <div class="form-group">
            <label>下午精力</label>
            <select v-model="energyCycle.afternoon">
              <option value="high">高</option>
              <option value="medium">中</option>
              <option value="low">低</option>
            </select>
          </div>
          
          <div class="form-group">
            <label>晚上精力</label>
            <select v-model="energyCycle.evening">
              <option value="high">高</option>
              <option value="medium">中</option>
              <option value="low">低</option>
            </select>
          </div>
          
          <button class="save-btn" @click="saveEnergyCycle">保存</button>
        </div>
      </section>
      
      <!-- 安全与隐私 -->
      <section class="settings-section">
        <h3>安全与隐私</h3>
        <div class="settings-form">
          <div class="security-info">
            <h4>账号密码安全性保障</h4>
            <ul>
              <li><strong>密码不本地存储：</strong>您的北航账号密码仅用于北航统一身份认证（SSO），不会被本地数据库或文件存储。</li>
              <li><strong>SSO认证流程：</strong>密码直接提交给北航SSO系统验证，系统仅存储北航认证后的会话Cookie。</li>
              <li><strong>Cookie安全存储：</strong>北航系统的会话Cookie采用加密方式存储在本地数据库中。</li>
              <li><strong>单用户模式：</strong>应用采用单用户设计，所有数据仅对当前用户可见。</li>
              <li><strong>数据本地保存：</strong>所有日程、任务数据均保存在本地SQLite数据库中，确保数据隐私。</li>
            </ul>
            <div class="security-tips">
              <h4>安全建议</h4>
              <ul>
                <li>定期更新北航账号密码</li>
                <li>不要在公共设备上使用本应用</li>
                <li>使用完毕后及时退出应用</li>
              </ul>
            </div>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useUserStore, useSettingsStore, useCourseStore, useEntryStore } from '../store'
import { authAPI, coursesAPI, settingsAPI, entriesAPI, spocAPI } from '../services/api'
import axios from 'axios'

const userStore = useUserStore()
const settingsStore = useSettingsStore()

// 北航学号
const buaaId = ref(userStore.buaaId || '')
// 北航密码
const buaaPassword = ref('')

// 提醒设置
const reminderSettings = ref({
  ...settingsStore.reminderSettings
})

// 主题设置
const theme = ref(settingsStore.theme)

// 默认颜色设置
const defaultColor = ref(settingsStore.defaultColor)

// 精力周期设置
const energyCycle = ref({
  ...settingsStore.energyCycle
})

// API_KEY设置
const apiKey = ref('')

// 同步状态
const syncLoading = ref(false)
const syncStatus = ref('')

// SPOC作业同步状态
const spocSyncLoading = ref(false)
const spocSyncStatus = ref('')

// 头像相关
const avatarUrl = ref(userStore.avatarUrl || localStorage.getItem('avatarUrl') || null)

// 组件挂载时加载北航学号并自动同步课程表
onMounted(async () => {
  try {
    const response = await authAPI.getBuaaId()
    if (response.buaa_id) {
      buaaId.value = response.buaa_id
      userStore.updateBuaaId(response.buaa_id)
      
      // 自动同步课程表
      if (buaaId.value.trim()) {
        await syncBuaaCourses()
      }
    }
    
    // 加载头像
    const savedAvatar = localStorage.getItem('avatarUrl')
    if (savedAvatar) {
      avatarUrl.value = savedAvatar
      userStore.updateAvatarUrl(savedAvatar)
    }
  } catch (error) {
    // console.error('加载北航学号失败:', error)
  }
})

// 获取用户姓名首字母作为头像占位符
const getInitials = () => {
  if (userStore.userInfo?.name) {
    return userStore.userInfo.name.charAt(0).toUpperCase()
  }
  return 'U'
}

// 处理头像上传
const handleAvatarUpload = (event) => {
  const file = event.target.files[0]
  if (!file) return
  
  // 检查文件类型和大小
  if (!file.type.startsWith('image/')) {
    alert('请选择图片文件')
    return
  }
  
  if (file.size > 5 * 1024 * 1024) { // 5MB
    alert('图片大小不能超过5MB')
    return
  }
  
  const reader = new FileReader()
  reader.onload = (e) => {
    const dataUrl = e.target.result
    avatarUrl.value = dataUrl
    
    // 保存到localStorage
    localStorage.setItem('avatarUrl', dataUrl)
    
    // 更新store
    userStore.updateAvatarUrl(dataUrl)
    
    // 清空文件输入
    event.target.value = ''
  }
  reader.readAsDataURL(file)
}

// 移除头像
const removeAvatar = () => {
  avatarUrl.value = null
  localStorage.removeItem('avatarUrl')
  userStore.updateAvatarUrl(null)
}

// 保存北航学号
const saveBuaaId = async () => {
  try {
    // 调用API保存北航学号
    const response = await authAPI.setBuaaId({ 
      buaa_id: buaaId.value 
    })
    // console.log('保存北航学号:', response)
    // 更新store
    userStore.updateBuaaId(buaaId.value)
  } catch (error) {
    // console.error('保存失败:', error)
    alert('保存失败')
  }
}

// 同步北航课程表
const syncBuaaCourses = async () => {
  try {
    // 验证北航学号
    if (!buaaId.value.trim()) {
      alert('请先输入北航学号')
      return
    }
    
    // 设置加载状态
    syncLoading.value = true
    syncStatus.value = '正在登录北航系统...'
    
    // 通过后端代理调用北航API
    const date = new Date().toISOString().split('T')[0]
    
    console.log('发起同步请求，参数:', {
      buaa_id: buaaId.value,
      password: buaaPassword.value ? '******' : '',
      date: date
    })
    
    // 直接调用后端的sync_buaa接口，让后端处理北航API调用
    const syncResponse = await coursesAPI.syncBuaaCourses({
      buaa_id: buaaId.value,
      password: buaaPassword.value,
      date: date
    })
    
    console.log('同步请求返回结果:', syncResponse)
    
    // 检查同步结果
    if (syncResponse && syncResponse.status === 'success') {
      // 更新同步状态
      syncStatus.value = '课程表同步成功！'
      
      // 刷新课程列表和日历数据
      const courseStore = useCourseStore()
      const entryStore = useEntryStore()
      
      // 获取最新的课程列表
      const coursesResponse = await coursesAPI.getCourses()
      courseStore.setCourses(coursesResponse.courses)
      
      // 使用完整的GET-BUAA_API-GET逻辑：先获取指定日期范围内的entries，然后同步课程表，最后再次获取entries
    const formattedDate = date
      
      // 1. 先获取当前日期的entries，确保数据基础
      // 注：此步骤可考虑移除，因为后续会再次获取完整的7天数据
      // const initialEntriesResponse = await entriesAPI.getEntriesByDate(formattedDate)
      // const initialEntries = Array.isArray(initialEntriesResponse) ? initialEntriesResponse : (initialEntriesResponse.entries || [])
      
      // 2. 再次同步课程表（使用按日期同步API，确保获取最新数据）
      try {
        await coursesAPI.syncBuaaCoursesByDate(formattedDate, {
          buaa_id: buaaId.value,
          password: '' // 密码由后端存储，前端不需要传递
        })
      } catch (syncError) {
        console.error('再次同步课程表失败:', syncError)
        // 继续执行，不影响后续操作
      }
      
      // 3. 最后再次获取entries数据，确保获取到最新的课程表数据
      // 直接使用 /entries/<date> API，它已经默认返回7天范围的条目
      // 将formattedDate前移一天
      const targetDate = new Date(formattedDate)
      targetDate.setDate(targetDate.getDate() - 1)
      const previousDay = targetDate.toISOString().split('T')[0]
      const entriesResponse = await entriesAPI.getEntriesByDate(previousDay)
      const entries = Array.isArray(entriesResponse) ? entriesResponse : (entriesResponse.entries || [])
      entryStore.setEntries(entries)
      
      console.log('已执行完整的GET-BUAA_API-GET逻辑，刷新了日历数据')
    } else {
      // 同步失败
      const errorMessage = syncResponse && syncResponse.message ? syncResponse.message : '同步失败，请稍后重试'
      syncStatus.value = `同步失败: ${errorMessage}`
      console.error('同步课程表失败:', syncResponse)
    }
    
    // 清空密码
    buaaPassword.value = ''
  } catch (error) {
    // 处理不同类型的错误
    if (error.response) {
      // 服务器返回错误
      const errorData = error.response.data
      console.error('同步课程表失败，服务器返回错误:', errorData)
      if (error.response.status === 401) {
        // 认证错误
        syncStatus.value = `北航登录失败: ${errorData.message || '请检查学号和密码'}`
      } else if (error.response.status === 503) {
        // 网络错误
        syncStatus.value = `网络错误: ${errorData.message || '无法连接到北航服务器'}`
      } else {
        // 其他服务器错误
        syncStatus.value = `同步失败: ${errorData.message || '服务器内部错误'}`
      }
    } else if (error.request) {
      // 请求已发送但没有收到响应
      console.error('同步课程表失败，没有收到服务器响应:', error.request)
      syncStatus.value = '请求失败: 无法连接到服务器'
    } else {
      // 请求配置错误
      console.error('同步课程表失败，请求配置错误:', error.message)
      syncStatus.value = `请求失败: ${error.message}`
    }
  } finally {
    // 关闭加载状态
    syncLoading.value = false
  }
}

// 保存提醒设置
const saveReminderSettings = () => {
  settingsStore.updateReminderSettings(reminderSettings.value)
}

// 保存主题和颜色设置
const saveThemeAndColor = () => {
  settingsStore.updateTheme(theme.value)
  settingsStore.updateDefaultColor(defaultColor.value)
  // 主题和颜色切换会通过CSS变量自动生效
}

// 保存精力周期设置
const saveEnergyCycle = () => {
  settingsStore.updateEnergyCycle(energyCycle.value)
}

// 同步SPOC作业
const syncSpocHomeworks = async () => {
  try {
    // 验证北航学号和密码
    if (!buaaId.value.trim()) {
      alert('请先输入北航学号')
      return
    }
    
    if (!buaaPassword.value.trim()) {
      alert('请先输入北航密码')
      return
    }
    
    // 设置加载状态
    spocSyncLoading.value = true
    spocSyncStatus.value = '正在登录SPOC系统...'
    
    // 调用SPOC作业同步API
    const syncResponse = await spocAPI.syncHomeworksWithSchedule({
      username: buaaId.value,
      password: buaaPassword.value,
      user_id: userStore.userInfo?.id || 1 // 默认用户ID为1
    })
    
    console.log('SPOC作业同步返回结果:', syncResponse)
    
    // 检查同步结果
    if (syncResponse && syncResponse.status === 'success') {
      // 更新同步状态
      spocSyncStatus.value = 'SPOC作业同步成功！'
    } else {
      // 同步失败
      const errorMessage = syncResponse && syncResponse.message ? syncResponse.message : '同步失败，请稍后重试'
      spocSyncStatus.value = `同步失败: ${errorMessage}`
      console.error('同步SPOC作业失败:', syncResponse)
    }
    
    // 清空密码
    buaaPassword.value = ''
  } catch (error) {
    // 处理不同类型的错误
    if (error.response) {
      // 服务器返回错误
      const errorData = error.response.data
      console.error('同步SPOC作业失败，服务器返回错误:', errorData)
      if (error.response.status === 401) {
        // 认证错误
        spocSyncStatus.value = `SPOC登录失败: ${errorData.message || '请检查学号和密码'}`
      } else {
        // 其他服务器错误
        spocSyncStatus.value = `同步失败: ${errorData.message || '服务器内部错误'}`
      }
    } else if (error.request) {
      // 请求已发送但没有收到响应
      console.error('同步SPOC作业失败，没有收到服务器响应:', error.request)
      spocSyncStatus.value = '请求失败: 无法连接到服务器'
    } else {
      // 请求配置错误
      console.error('同步SPOC作业失败，请求配置错误:', error.message)
      spocSyncStatus.value = `请求失败: ${error.message}`
    }
  } finally {
    // 关闭加载状态
    spocSyncLoading.value = false
  }
}

// 保存API_KEY
const saveApiKey = async () => {
  if (!apiKey.value.trim()) {
    alert('请输入API_KEY')
    return
  }
  
  try {
    const response = await settingsAPI.saveApiKey({ api_key: apiKey.value })
    // 清空输入框
    apiKey.value = ''
  } catch (error) {
    console.error('保存API_KEY失败:', error)
    alert('保存API_KEY失败，请重试')
  }
}
</script>

<style scoped>
.settings-panel-container {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.settings-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
}

.settings-header h2 {
  font-size: 1.5rem;
  color: #333;
}

.close-btn {
  background: none;
  border: none;
  font-size: 1.5rem;
  cursor: pointer;
  color: #666;
  padding: 0;
  width: 30px;
  height: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
  transition: all 0.3s ease;
}

.close-btn:hover {
  background-color: #f5f5f5;
  color: #333;
}

.settings-content {
  overflow-y: auto;
}

.settings-section {
  margin-bottom: 2rem;
  padding-bottom: 1.5rem;
  border-bottom: 1px solid #e0e0e0;
}

.settings-section:last-child {
  border-bottom: none;
}

.settings-section h3 {
  font-size: 1.2rem;
  margin-bottom: 1rem;
  color: #333;
}

.settings-form {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.form-group label {
  font-weight: 500;
  color: #333;
  font-size: 0.9rem;
}

.form-group input,
.form-group select {
  padding: 0.75rem;
  border: 1px solid #e0e0e0;
  border-radius: 4px;
  font-size: 1rem;
}

.form-group input:focus,
.form-group select:focus {
  outline: none;
  border-color: var(--primary-color);
  box-shadow: 0 0 0 2px rgba(74, 144, 226, 0.2);
}

.button-group {
  display: flex;
  gap: 0.5rem;
}

.sync-btn {
  padding: 0.75rem 1.5rem;
  border: 1px solid var(--primary-color);
  border-radius: 4px;
  background-color: white;
  color: var(--primary-color);
  cursor: pointer;
  transition: all 0.3s ease;
  font-size: 1rem;
  align-self: flex-start;
}

.sync-btn:hover {
  background-color: var(--primary-light);
}

.form-hint {
        font-size: 0.85rem;
        color: #666;
        margin-top: 0.5rem;
        padding: 0.5rem;
        background-color: #f5f5f5;
        border-radius: 4px;
        border-left: 3px solid #4a90e2;
    }
    
    /* 登录选项对话框样式 */
    .modal-overlay {
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background-color: rgba(0, 0, 0, 0.5);
        display: flex;
        justify-content: center;
        align-items: center;
        z-index: 1000;
    }
    
    .modal-content {
        background-color: white;
        padding: 1.5rem;
        border-radius: 8px;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
        width: 90%;
        max-width: 600px;
    }
    
    .login-options {
        display: flex;
        flex-direction: column;
        gap: 1.5rem;
    }
    
    .login-option {
        display: flex;
        flex-direction: column;
        gap: 1rem;
    }
    
    .login-option h4 {
        margin: 0;
        font-size: 1.1rem;
        color: #333;
    }
    
    .login-option p {
        margin: 0;
        font-size: 0.9rem;
        color: #666;
    }
    
    .login-form {
        display: flex;
        flex-direction: column;
        gap: 1rem;
    }
    
    .remember-me {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        font-size: 0.9rem;
    }
    
    .login-divider {
        text-align: center;
        color: #999;
        position: relative;
    }
    
    .login-divider::before,
    .login-divider::after {
        content: '';
        position: absolute;
        top: 50%;
        width: 45%;
        height: 1px;
        background-color: #e0e0e0;
    }
    
    .login-divider::before {
        left: 0;
    }
    
    .login-divider::after {
        right: 0;
    }
    
    .cancel-btn {
        padding: 0.75rem 1.5rem;
        border: 1px solid #e0e0e0;
        border-radius: 4px;
        background-color: white;
        color: #333;
        cursor: pointer;
        transition: all 0.3s ease;
        font-size: 1rem;
        align-self: flex-start;
    }
    
    .cancel-btn:hover {
        background-color: #f5f5f5;
    }

.multi-reminder {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.exam-reminder-item {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.exam-reminder-label {
  font-size: 0.9rem;
  font-weight: 500;
  color: #333;
}

.multi-reminder input {
  width: 100%;
  max-width: 200px;
  padding: 0.75rem;
  border: 1px solid #e0e0e0;
  border-radius: 4px;
  font-size: 1rem;
}

.theme-options {
  display: flex;
  gap: 1.5rem;
}

.theme-option {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
}

/* 自定义单选按钮样式 */
.theme-option input[type="radio"] {
  accent-color: var(--primary-color);
}

.color-picker-group {
  display: flex;
  gap: 0.5rem;
  align-items: center;
}

.color-picker {
  width: 40px;
  height: 40px;
  border: 1px solid #e0e0e0;
  border-radius: 4px;
  cursor: pointer;
}

.color-input {
  flex: 1;
  padding: 0.75rem;
  border: 1px solid #e0e0e0;
  border-radius: 4px;
  font-size: 1rem;
}

.save-btn {
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 4px;
  background-color: var(--primary-color);
  color: white;
  cursor: pointer;
  transition: all 0.3s ease;
  font-size: 1rem;
  align-self: flex-start;
}

.save-btn:hover {
  background-color: var(--primary-dark);
}

/* 同步状态样式 */
.sync-status {
  margin-top: 1rem;
  padding: 0.75rem;
  border-radius: 4px;
  font-size: 0.9rem;
  font-weight: 500;
  text-align: center;
}

.sync-status.success {
  background-color: #d4edda;
  color: #155724;
  border: 1px solid #c3e6cb;
}

.sync-status.error {
  background-color: #f8d7da;
  color: #721c24;
  border: 1px solid #f5c6cb;
}

/* 头像上传样式 */
.avatar-upload-container {
  display: flex;
  align-items: center;
  gap: 1.5rem;
  margin-top: 0.5rem;
}

.avatar-preview {
  width: 100px;
  height: 100px;
  border-radius: 50%;
  overflow: hidden;
  border: 2px solid #e0e0e0;
  display: flex;
  align-items: center;
  justify-content: center;
}

.avatar-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.avatar-placeholder {
  width: 100%;
  height: 100%;
  background-color: var(--primary-color);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 2rem;
  font-weight: bold;
}

.avatar-upload-options {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}
</style>
