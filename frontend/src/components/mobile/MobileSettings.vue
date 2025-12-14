<template>
  <div class="mobile-settings">
    <h2 class="settings-title">设置</h2>
    
    <!-- 服务器连接状态 -->
    <div class="settings-section">
      <h3 class="section-title">连接状态</h3>
      <div class="connection-status">
        <div class="status-icon">
          <span v-if="isConnected" class="connected">🟢</span>
          <span v-else class="disconnected">🔴</span>
        </div>
        <div class="status-info">
          <h4 class="status-title">{{ isConnected ? '已连接' : '未连接' }}</h4>
          <p class="status-detail">通过内网穿透服务连接</p>
        </div>
      </div>
    </div>
    
    <!-- 同步设置 -->
    <div class="settings-section">
      <h3 class="section-title">同步设置</h3>
      <div class="setting-item">
        <div class="setting-info">
          <h4 class="setting-label">自动同步</h4>
          <p class="setting-description">定期同步数据到服务器</p>
        </div>
        <label class="toggle-switch">
          <input type="checkbox" v-model="autoSync">
          <span class="toggle-slider"></span>
        </label>
      </div>
      <div class="setting-item" v-if="autoSync">
        <div class="setting-info">
          <h4 class="setting-label">同步间隔</h4>
          <p class="setting-description">设置数据同步的时间间隔</p>
        </div>
        <select class="select-input" v-model="syncInterval">
          <option value="5">5分钟</option>
          <option value="15">15分钟</option>
          <option value="30">30分钟</option>
          <option value="60">1小时</option>
        </select>
      </div>
      <div class="sync-actions">
        <button class="sync-btn" @click="manualSync">立即同步</button>
        <span v-if="syncing" class="syncing-text">同步中...</span>
        <span v-else-if="lastSyncTime" class="last-sync">上次同步: {{ formatSyncTime(lastSyncTime) }}</span>
      </div>
    </div>
    
    <!-- 主题设置 -->
    <div class="settings-section">
      <h3 class="section-title">主题</h3>
      <div class="theme-options">
        <button 
          class="theme-option" 
          :class="{ active: theme === 'light' }"
          @click="changeTheme('light')"
        >
          <div class="theme-preview light"></div>
          <span>浅色</span>
        </button>
        <button 
          class="theme-option" 
          :class="{ active: theme === 'dark' }"
          @click="changeTheme('dark')"
        >
          <div class="theme-preview dark"></div>
          <span>深色</span>
        </button>
        <button 
          class="theme-option" 
          :class="{ active: theme === 'system' }"
          @click="changeTheme('system')"
        >
          <div class="theme-preview system"></div>
          <span>跟随系统</span>
        </button>
      </div>
    </div>
    
    <!-- 关于信息 -->
    <div class="settings-section">
      <h3 class="section-title">关于</h3>
      <div class="about-info">
        <p class="app-name">北航智能日历</p>
        <p class="app-version">版本 1.0.0</p>
        <p class="app-description">为北航学生定制的智能日历系统</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useSettingsStore } from '../../store'
import api from '../../services/api'

const settingsStore = useSettingsStore()

// 连接状态
const isConnected = ref(true)
const localIp = ref('192.168.1.100')
const port = ref('5000')
const connectionInfo = ref('通过校园网连接')

// 同步设置
const autoSync = ref(true)
const syncInterval = ref('15')
const syncing = ref(false)
const lastSyncTime = ref(null)

// 主题设置
const theme = computed({
  get: () => settingsStore.theme,
  set: (newTheme) => settingsStore.theme = newTheme
})

// 格式化同步时间
const formatSyncTime = (time) => {
  if (!time) return ''
  const date = new Date(time)
  return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
}

// 手动同步
const manualSync = async () => {
  syncing.value = true
  try {
    // 模拟同步操作
    // 实际项目中应该调用具体的同步API
    await new Promise(resolve => setTimeout(resolve, 1000))
    lastSyncTime.value = new Date()
  } catch (error) {
    console.error('同步失败:', error)
  } finally {
    syncing.value = false
  }
}

// 切换主题
const changeTheme = (newTheme) => {
  // 更新Pinia状态
  settingsStore.updateTheme(newTheme)
  // 应用主题到根元素
  document.documentElement.setAttribute('data-theme', newTheme)
  // 根据主题设置添加或移除dark类
  if (newTheme === 'dark') {
    document.documentElement.classList.add('dark')
  } else if (newTheme === 'light') {
    document.documentElement.classList.remove('dark')
  } else {
    // 跟随系统
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches
    document.documentElement.classList.toggle('dark', prefersDark)
  }
  // 保存主题设置到本地存储
  localStorage.setItem('theme', newTheme)
}

// 初始化
onMounted(() => {
  // 使用settingsStore中的主题值
  const savedTheme = settingsStore.theme
  changeTheme(savedTheme)
  
  // 监听系统主题变化
  window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
    if (theme.value === 'system') {
      document.documentElement.classList.toggle('dark', e.matches)
    }
  })
  
  // 模拟获取连接信息
  setTimeout(() => {
    // 这里可以调用API获取实际的连接状态
    localIp.value = '192.168.1.105'
    port.value = '5000'
  }, 500)
})
</script>

<style scoped>
.mobile-settings {
  padding: 16px;
  background-color: var(--bg-primary);
  color: var(--text-primary);
}

.settings-title {
  margin: 0 0 20px 0;
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
}

.settings-section {
  background-color: var(--bg-secondary);
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 16px;
  border: 1px solid var(--border-color);
  box-shadow: 0 1px 3px var(--shadow-color);
}

.section-title {
  margin: 0 0 16px 0;
  font-size: 16px;
  font-weight: 500;
  color: var(--text-primary);
}

/* 连接状态 */
.connection-status {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}

.status-icon {
  font-size: 24px;
}

.status-info {
  flex: 1;
}

.status-title {
  margin: 0 0 4px 0;
  font-size: 15px;
  font-weight: 500;
  color: var(--text-primary);
}

.status-detail {
  margin: 0;
  font-size: 13px;
  color: var(--text-secondary);
}

.connection-details {
  background-color: var(--bg-secondary);
  border-radius: 6px;
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.connection-details p {
  margin: 0;
  font-size: 14px;
  color: var(--text-secondary);
}

.connection-details strong {
  color: var(--text-primary);
}

/* 设置项 */
.setting-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  background-color: var(--bg-primary);
  border-radius: 6px;
  padding: 12px;
  border: 1px solid var(--border-color);
}

.setting-info {
  flex: 1;
}

.setting-label {
  margin: 0 0 4px 0;
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary);
}

.setting-description {
  margin: 0;
  font-size: 12px;
  color: var(--text-secondary);
}

/* 开关 */
.toggle-switch {
  position: relative;
  display: inline-block;
  width: 48px;
  height: 24px;
}

.toggle-switch input {
  opacity: 0;
  width: 0;
  height: 0;
}

.toggle-slider {
  position: absolute;
  cursor: pointer;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: var(--border-color);
  transition: .4s;
  border-radius: 24px;
}

.toggle-slider:before {
  position: absolute;
  content: "";
  height: 18px;
  width: 18px;
  left: 3px;
  bottom: 3px;
  background-color: var(--bg-secondary);
  transition: .4s;
  border-radius: 50%;
}

input:checked + .toggle-slider {
  background-color: var(--primary-color);
}

input:focus + .toggle-slider {
  box-shadow: 0 0 1px var(--primary-color);
}

input:checked + .toggle-slider:before {
  transform: translateX(24px);
}

/* 选择框 */
.select-input {
  padding: 8px 12px;
  border: 1px solid var(--border-color);
  border-radius: 6px;
  background-color: var(--bg-secondary);
  font-size: 14px;
  color: var(--text-primary);
  cursor: pointer;
  min-width: 120px;
}

.select-input:focus {
  outline: none;
  border-color: var(--primary-color);
  box-shadow: 0 0 0 2px rgba(var(--primary-color-rgb), 0.2);
}

/* 同步操作 */
.sync-actions {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: 12px;
  flex-wrap: wrap;
}

.sync-btn {
  padding: 8px 16px;
  border: none;
  border-radius: 6px;
  background-color: var(--primary-color);
  color: white;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: background-color 0.3s ease;
}

.sync-btn:hover {
  background-color: var(--primary-dark);
}

.syncing-text {
  font-size: 13px;
  color: var(--primary-color);
  font-weight: 500;
}

.last-sync {
  font-size: 13px;
  color: var(--text-secondary);
}

/* 主题选项 */
.theme-options {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
}

.theme-option {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 12px;
  background-color: var(--bg-primary);
  border: 2px solid var(--border-color);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.theme-option.active {
  border-color: var(--primary-color);
  background-color: rgba(var(--primary-color-rgb), 0.05);
}

.theme-preview {
  width: 40px;
  height: 40px;
  border-radius: 8px;
  margin-bottom: 8px;
  border: 1px solid var(--border-color);
}

.theme-preview.light {
  background-color: white;
}

.theme-preview.dark {
  background-color: #1a1a1a;
}

.theme-preview.system {
  background: linear-gradient(135deg, white 50%, #1a1a1a 50%);
}

.theme-option span {
  font-size: 13px;
  color: var(--text-primary);
  font-weight: 500;
}

/* 关于信息 */
.about-info {
  background-color: var(--bg-primary);
  border-radius: 6px;
  padding: 16px;
  border: 1px solid var(--border-color);
  text-align: center;
}

.app-name {
  margin: 0 0 4px 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
}

.app-version {
  margin: 0 0 8px 0;
  font-size: 13px;
  color: var(--text-secondary);
}

.app-description {
  margin: 0;
  font-size: 13px;
  color: var(--text-secondary);
  line-height: 1.4;
}
</style>