<template>
  <div class="settings-panel-container">
    <div class="settings-header">
      <h2>设置</h2>
      <button class="close-btn" @click="$emit('close')">×</button>
    </div>
    
    <div class="settings-content">
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
            <button type="button" class="save-btn" @click="saveBuaaId">保存</button>
          </div>
        <div class="form-hint">
            提示：点击"同步课程表"按钮后，系统会自动处理登录流程。（密码不会存储，仅临时使用）
        </div>
        <div v-if="syncStatus" class="sync-status" :class="syncStatus.includes('成功') ? 'success' : 'error'">
            {{ syncStatus }}
        </div>
        </form>
      </section>
      
      <!-- 提醒偏好设置 -->
      <section class="settings-section">
        <h3>提醒偏好设置</h3>
        <div class="settings-form">
          <div class="form-group">
            <label for="course-reminder">课程提前提醒时间（分钟）</label>
            <input 
              type="number" 
              id="course-reminder" 
              v-model.number="reminderSettings.course" 
              min="0"
            />
          </div>
          
          <div class="form-group">
            <label for="homework-reminder">作业提前提醒时间（分钟）</label>
            <input 
              type="number" 
              id="homework-reminder" 
              v-model.number="reminderSettings.homework" 
              min="0"
            />
          </div>
          
          <div class="form-group">
            <label>考试多级提醒（分钟）</label>
            <div class="multi-reminder">
              <input 
                type="number" 
                v-model.number="reminderSettings.exam[0]" 
                placeholder="第一级" 
                min="0"
              />
              <input 
                type="number" 
                v-model.number="reminderSettings.exam[1]" 
                placeholder="第二级" 
                min="0"
              />
              <input 
                type="number" 
                v-model.number="reminderSettings.exam[2]" 
                placeholder="第三级" 
                min="0"
              />
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
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useUserStore, useSettingsStore, useCourseStore } from '../store'
import { authAPI, coursesAPI, settingsAPI } from '../services/api'
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
  } catch (error) {
    // console.error('加载北航学号失败:', error)
  }
})

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
    
    // 更新同步状态
    syncStatus.value = '课程表同步成功！'
    
    // 刷新课程列表
    const courseStore = useCourseStore()
    const coursesResponse = await coursesAPI.getCourses()
    courseStore.setCourses(coursesResponse.courses)
    
    // 清空密码
    buaaPassword.value = ''
  } catch (error) {
    // 处理不同类型的错误
    if (error.response) {
      // 服务器返回错误
      const errorData = error.response.data
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
      syncStatus.value = '请求失败: 无法连接到服务器'
    } else {
      // 请求配置错误
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

.multi-reminder input {
  flex: 1;
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
</style>
