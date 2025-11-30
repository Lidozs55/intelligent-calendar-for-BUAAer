<template>
  <div class="app-container" :class="theme">
    <!-- 根据当前页面显示不同内容 -->
    <template v-if="currentPage === 'home'">
      <header class="app-header">
        <h1>智能日程助手 - 北航版</h1>
        <div class="header-actions">
          <button @click="goToSmartInput" class="header-btn">智能输入中心</button>
          <button @click="toggleSettings" class="header-btn">设置</button>
        </div>
      </header>
      
      <main class="app-main">
        <aside class="sidebar">
          <TaskSidebar @add-task="goToSmartInput" />
        </aside>
        
        <section class="main-content">
          <Home />
        </section>
      </main>
      
      <div v-if="showSettings" class="settings-overlay" @click="toggleSettings">
        <div class="settings-panel" @click.stop>
          <SettingsPanel @close="toggleSettings" />
        </div>
      </div>
    </template>
    
    <!-- 智能输入页面 -->
    <template v-else-if="currentPage === 'smartInput'">
      <SmartInputPage @go-back="goToHome" />
    </template>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue'
import Home from './views/Home.vue'
import SmartInputPage from './views/SmartInputPage.vue'
import TaskSidebar from './components/TaskSidebar.vue'
import SettingsPanel from './components/SettingsPanel.vue'
import { useUserStore, useTaskStore, useCourseStore, useSettingsStore, useClipboardStore } from './store'
import notificationService from './services/notification'

// 页面管理状态
const currentPage = ref('home')
const showSettings = ref(false)
const userStore = useUserStore()
const taskStore = useTaskStore()
const courseStore = useCourseStore()
const settingsStore = useSettingsStore()
const clipboardStore = useClipboardStore()
let notificationIntervalId = null
let clipboardCheckInterval = null

// 最后一次剪切板内容
let lastClipboardText = ''

// 自动检测剪切板内容
const autoCheckClipboard = async () => {
  try {
    const text = await navigator.clipboard.readText()
    if (text && text !== lastClipboardText) {
      console.log('检测到剪切板内容变化:', text)
      // 将剪切板内容添加到队列，不弹出确认框
      clipboardStore.addToQueue(text)
      // 更新最后一次剪切板内容
      lastClipboardText = text
    }
  } catch (err) {
    // 忽略读取剪切板的错误，因为用户可能没有授权
    console.error('自动读取剪切板失败:', err)
  }
}

// 切换设置面板
const toggleSettings = () => {
  showSettings.value = !showSettings.value
}

// 跳转到智能输入页面
const goToSmartInput = () => {
  currentPage.value = 'smartInput'
}

// 返回到主页
const goToHome = () => {
  currentPage.value = 'home'
}

// 计算属性：获取所有任务（包括已完成和未完成）
const allTasks = computed(() => {
  return [...taskStore.tasks, ...taskStore.completedTasks]
})

// 初始化通知服务
const initNotifications = async () => {
  // 请求通知权限
  const hasPermission = await notificationService.requestPermission()
  if (hasPermission) {
    // 启动定时检查通知
    notificationIntervalId = notificationService.startCheckInterval(
      allTasks.value,
      courseStore.courses,
      settingsStore.reminderSettings
    )
  }
}

// 初始化用户信息，设置默认的buaaId用于测试
onMounted(() => {
  // 初始化通知服务
  initNotifications()
  
  // 启动定期检查剪切板，每5秒检查一次
  clipboardCheckInterval = setInterval(autoCheckClipboard, 5000)
})

// 组件卸载时清除定时器
onUnmounted(() => {
  if (notificationIntervalId) {
    notificationService.stopCheckInterval(notificationIntervalId)
  }
  if (clipboardCheckInterval) {
    clearInterval(clipboardCheckInterval)
  }
})

// 监听任务和课程变化，更新通知检查
const updateNotificationCheck = () => {
  if (notificationIntervalId) {
    notificationService.stopCheckInterval(notificationIntervalId)
  }
  
  if (notificationService.permission === 'granted') {
    notificationIntervalId = notificationService.startCheckInterval(
      allTasks.value,
      courseStore.courses,
      settingsStore.reminderSettings
    )
  }
}

// 监听任务变化
taskStore.$subscribe(updateNotificationCheck)

// 监听课程变化
courseStore.$subscribe(updateNotificationCheck)

// 计算属性：获取当前主题
const theme = computed(() => {
  return settingsStore.theme
})

// 监听设置变化
settingsStore.$subscribe(updateNotificationCheck)
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

/* 浅色主题变量 */
:root {
  --bg-primary: #f5f5f5;
  --bg-secondary: white;
  --bg-header: #4a90e2;
  --text-primary: #333;
  --text-secondary: #666;
  --border-color: #e0e0e0;
  --shadow-color: rgba(0, 0, 0, 0.1);
}

/* 深色主题变量 */
.dark {
  --bg-primary: #121212;
  --bg-secondary: #1e1e1e;
  --bg-header: #1f3a5f;
  --text-primary: #e0e0e0;
  --text-secondary: #b0b0b0;
  --border-color: #333;
  --shadow-color: rgba(0, 0, 0, 0.3);
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
  background-color: var(--bg-primary);
  color: var(--text-primary);
  transition: background-color 0.3s ease, color 0.3s ease;
}

.app-container {
  display: flex;
  flex-direction: column;
  height: 100vh;
}

.app-header {
  background-color: var(--bg-header);
  color: white;
  padding: 0.75rem 2rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  box-shadow: 0 2px 4px var(--shadow-color);
  transition: background-color 0.3s ease, box-shadow 0.3s ease;
}

.app-header h1 {
  margin: 0;
  font-size: 1.5rem;
  font-weight: 500;
}

.header-actions button {
  background-color: rgba(255, 255, 255, 0.2);
  border: none;
  color: white;
  padding: 0.5rem 1rem;
  border-radius: 4px;
  cursor: pointer;
  font-size: 1rem;
  transition: background-color 0.3s ease;
}

.header-actions button:hover {
  background-color: rgba(255, 255, 255, 0.3);
}

.app-main {
  display: flex;
  flex: 1;
  overflow: hidden;
}

.sidebar {
  width: 300px;
  background-color: var(--bg-secondary);
  border-right: 1px solid var(--border-color);
  overflow-y: auto;
  transition: background-color 0.3s ease, border-color 0.3s ease;
}

.main-content {
  flex: 1;
  padding: 1rem;
  overflow-y: auto;
  transition: background-color 0.3s ease;
}

.settings-overlay {
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

.settings-panel {
  background-color: var(--bg-secondary);
  border-radius: 8px;
  box-shadow: 0 4px 20px var(--shadow-color);
  width: 90%;
  max-width: 600px;
  max-height: 80vh;
  overflow-y: auto;
  padding: 1.5rem;
  transition: background-color 0.3s ease, box-shadow 0.3s ease;
}
</style>
