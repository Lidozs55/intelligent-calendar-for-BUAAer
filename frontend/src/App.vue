<template>
  <div class="app-container" :class="theme" :style="appStyle">
    <!-- 根据当前页面显示不同内容 -->
    <template v-if="currentPage === 'home'">
      <header class="app-header">
        <h1>智能日程助手 - 北航版</h1>
        <div class="header-actions">
          <button @click="goToSmartInput" class="header-btn compact-btn">
            <span class="btn-icon">✏️</span>
            <span class="btn-text">智能输入</span>
          </button>
          <button @click="enterFocusMode" class="header-btn compact-btn">
            <span class="btn-icon">🎯</span>
            <span class="btn-text">专注模式</span>
          </button>
          <button @click="toggleHelp" class="header-btn compact-btn">
            <span class="btn-icon">❓</span>
            <span class="btn-text">帮助</span>
          </button>
          <button @click="toggleSettings" class="header-btn compact-btn">
            <span class="btn-icon">⚙️</span>
            <span class="btn-text">设置</span>
          </button>
        </div>
      </header>
      
      <main class="app-main">
        <aside class="sidebar">
          <TaskSidebar @add-task="goToSmartInput" @start-focus="startFocusFromTask" />
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
      
      <!-- Help弹窗 -->
      <div v-if="showHelp" class="settings-overlay" @click="toggleHelp">
        <div class="settings-panel" @click.stop>
          <div class="help-content">
            <h2>使用帮助</h2>
            <div class="help-section">
              <h3>快速添加事件</h3>
              <ul>
                <li><strong>左键点击</strong>：在日历上左键点击任意时间点，快速创建一个1小时的临时事件</li>
                <li><strong>拖拽选择</strong>：拖拽选择时间段，创建自定义时长的临时事件</li>
                <li><strong>默认类型</strong>：快速添加的事件默认类型为"其他"，可在编辑时修改</li>
              </ul>
            </div>
            <div class="help-section">
              <h3>事件编辑</h3>
              <ul>
                <li><strong>左键点击事件</strong>：打开事件编辑弹窗</li>
                <li><strong>拖拽调整</strong>：拖拽事件可调整时间，拖拽事件边缘可调整时长</li>
                <li><strong>颜色自动分配</strong>：选择事件类型后，系统会自动分配对应类型的默认颜色</li>
              </ul>
            </div>
            <div class="help-section">
              <h3>快速跳转功能</h3>
              <ul>
                <li><strong>打开快速跳转</strong>：点击右上角的"快速跳转"按钮</li>
                <li><strong>选择日期</strong>：在弹出的小日历中选择任意日期</li>
                <li><strong>跳转效果</strong>：日历会自动跳转到所选日期，并显示该日期对应的七日日程</li>
                <li><strong>月份切换</strong>：使用小日历顶部的左右箭头切换月份</li>
              </ul>
            </div>
            <div class="help-section">
              <h3>智能输入中心</h3>
              <ul>
                <li><strong>文本输入</strong>：直接输入任务或日程描述，转发给大语言模型自动解析</li>
                <li><strong>语音输入</strong>：点击麦克风图标，使用语音输入</li>
                <li><strong>图片上传</strong>：支持粘贴/拖拽/点击上传图片，自动识别图片中的文字</li>
                <li><strong>剪贴板集成</strong>：复制文本后，系统会自动检测并添加到剪贴板队列</li>
              </ul>
            </div>
            <div class="help-section">
              <h3>设置偏好</h3>
              <ul>
                <li><strong>北航账号绑定</strong>：绑定北航学号和密码，自动同步课程表</li>
                <li><strong>提醒设置</strong>：设置课程、作业、考试的提前提醒时间</li>
                <li><strong>主题切换</strong>：支持浅色/深色主题切换</li>
                <li><strong>精力周期</strong>：设置不同时间段的精力水平，用于智能日程安排</li>
                <li><strong>API_KEY配置</strong>：在设置界面中配置OpenAI API Key，系统会优先使用此配置，否则使用系统环境变量。</li>
              </ul>
            </div>
            <div class="help-section">
              <h3>API_KEY配置指南</h3>
              <ul>
                <li><strong>获取API_KEY</strong>：登录OpenAI官网，在个人中心获取您的API Key。</li>
                <li><strong>配置方式</strong>：
                  <ul>
                    <li>方式一：在设置界面中直接输入API Key并保存，系统会自动保存到后端.env文件。</li>
                    <li>方式二：在服务器环境变量中设置OPENAI_API_KEY，系统会在没有配置API Key时自动使用。</li>
                  </ul>
                </li>
                <li><strong>注意事项</strong>：API Key是敏感信息，请妥善保管，不要泄露给他人。</li>
              </ul>
            </div>
            <div class="help-section">
              <h3>专注模式</h3>
              <ul>
                <li><strong>进入专注模式</strong>：点击顶部导航栏的"专注模式"按钮</li>
                <li><strong>预设时长</strong>：支持25/45/60/90分钟的预设时长，也可自定义5-180分钟</li>
                <li><strong>全屏专注</strong>：进入后会显示全屏专注界面，减少视觉干扰</li>
                <li><strong>专注记录</strong>：系统会自动记录您的专注时长，并保存到后台</li>
              </ul>
            </div>
            <div class="help-actions">
              <button @click="toggleHelp" class="save-btn">关闭</button>
            </div>
          </div>
        </div>
      </div>
      
      <!-- 专注模式组件 -->
      <FocusMode ref="focusModeRef" />
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
import FocusMode from './components/FocusMode.vue'
import { useUserStore, useTaskStore, useCourseStore, useSettingsStore, useClipboardStore } from './store'
import notificationService from './services/notification'

// 页面管理状态
const currentPage = ref('home')
const showSettings = ref(false)
const showHelp = ref(false)
const focusModeRef = ref(null)
const userStore = useUserStore()
const taskStore = useTaskStore()
const courseStore = useCourseStore()
const settingsStore = useSettingsStore()
const clipboardStore = useClipboardStore()
let notificationIntervalId = null
let clipboardCheckInterval = null

// 最后一次剪切板内容
let lastClipboardText = ''

// 计算应用样式，动态设置CSS变量
const appStyle = computed(() => {
  const defaultColor = settingsStore.defaultColor
  // 生成浅色版本：降低饱和度和亮度
  const lightVersion = getLightVersion(defaultColor)
  // 生成深色调版本：用于深色主题
  const darkVersion = getDarkVersion(defaultColor)
  
  return {
    '--primary-color': defaultColor,
    '--primary-light': lightVersion,
    '--primary-dark': darkVersion,
    '--bg-header': defaultColor,
    '--accent-color': defaultColor
  }
})

// 生成颜色的浅色版本
function getLightVersion(color) {
  // 解析颜色为RGB
  const rgb = hexToRgb(color)
  if (!rgb) return '#e3f2fd'
  
  // 转换为HSL
  const hsl = rgbToHsl(rgb.r, rgb.g, rgb.b)
  
  // 降低饱和度，提高亮度
  hsl.s = Math.max(0, hsl.s - 0.3)
  hsl.l = Math.min(0.95, hsl.l + 0.3)
  
  // 转换回RGB
  const lightRgb = hslToRgb(hsl.h, hsl.s, hsl.l)
  
  // 转换回十六进制
  return rgbToHex(lightRgb.r, lightRgb.g, lightRgb.b)
}

// 生成颜色的深色版本
function getDarkVersion(color) {
  // 解析颜色为RGB
  const rgb = hexToRgb(color)
  if (!rgb) return '#1976d2'
  
  // 转换为HSL
  const hsl = rgbToHsl(rgb.r, rgb.g, rgb.b)
  
  // 提高饱和度，降低亮度
  hsl.s = Math.min(1, hsl.s + 0.2)
  hsl.l = Math.max(0.2, hsl.l - 0.2)
  
  // 转换回RGB
  const darkRgb = hslToRgb(hsl.h, hsl.s, hsl.l)
  
  // 转换回十六进制
  return rgbToHex(darkRgb.r, darkRgb.g, darkRgb.b)
}

// 十六进制转RGB
function hexToRgb(hex) {
  const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex)
  return result ? {
    r: parseInt(result[1], 16),
    g: parseInt(result[2], 16),
    b: parseInt(result[3], 16)
  } : null
}

// RGB转HSL
function rgbToHsl(r, g, b) {
  r /= 255
  g /= 255
  b /= 255
  
  const max = Math.max(r, g, b)
  const min = Math.min(r, g, b)
  let h, s, l = (max + min) / 2
  
  if (max === min) {
    h = s = 0 // achromatic
  } else {
    const d = max - min
    s = l > 0.5 ? d / (2 - max - min) : d / (max + min)
    switch (max) {
      case r: h = (g - b) / d + (g < b ? 6 : 0); break
      case g: h = (b - r) / d + 2; break
      case b: h = (r - g) / d + 4; break
    }
    h /= 6
  }
  
  return { h, s, l }
}

// HSL转RGB
function hslToRgb(h, s, l) {
  let r, g, b
  
  if (s === 0) {
    r = g = b = l // achromatic
  } else {
    const hue2rgb = (p, q, t) => {
      if (t < 0) t += 1
      if (t > 1) t -= 1
      if (t < 1/6) return p + (q - p) * 6 * t
      if (t < 1/2) return q
      if (t < 2/3) return p + (q - p) * (2/3 - t) * 6
      return p
    }
    
    const q = l < 0.5 ? l * (1 + s) : l + s - l * s
    const p = 2 * l - q
    r = hue2rgb(p, q, h + 1/3)
    g = hue2rgb(p, q, h)
    b = hue2rgb(p, q, h - 1/3)
  }
  
  return {
    r: Math.round(r * 255),
    g: Math.round(g * 255),
    b: Math.round(b * 255)
  }
}

// RGB转十六进制
function rgbToHex(r, g, b) {
  return "#" + ((1 << 24) + (r << 16) + (g << 8) + b).toString(16).slice(1)
}

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

// 切换帮助弹窗
const toggleHelp = () => {
  showHelp.value = !showHelp.value
}

// 进入专注模式
const enterFocusMode = () => {
  focusModeRef.value.openFocusMode()
}

// 从任务列表进入专注模式
const startFocusFromTask = (taskInfo) => {
  focusModeRef.value.openFocusMode(taskInfo)
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
  --bg-header: var(--primary-color, #4a90e2);
  --text-primary: #333;
  --text-secondary: #666;
  --border-color: #e0e0e0;
  --shadow-color: rgba(0, 0, 0, 0.1);
  --primary-color: #4a90e2;
  --primary-light: #e3f2fd;
  --primary-dark: #1976d2;
  --accent-color: var(--primary-color, #4a90e2);
}

/* 深色主题变量 */
.dark {
  --bg-primary: #121212;
  --bg-secondary: #1e1e1e;
  --bg-header: var(--primary-dark, #1976d2);
  --text-primary: #ffffff;
  --text-secondary: #b0b0b0;
  --border-color: #333;
  --shadow-color: rgba(0, 0, 0, 0.5);
  --input-bg: #2d2d2d;
  --input-text: #ffffff;
  --button-hover: rgba(255, 255, 255, 0.1);
}

body {
  font-family: 'Microsoft YaHei', 'Source Han Sans CN', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
  background-color: var(--bg-primary);
  color: var(--text-primary);
  transition: background-color 0.3s ease, color 0.3s ease;
}

h1, h2, h3, h4, h5, h6 {
  font-family: 'Microsoft YaHei', 'Source Han Sans CN', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
  font-weight: 600;
}

/* 内容字体轻量化 */
p, span, div, button {
  font-weight: 400;
}

/* 深色模式下的表单元素样式 */
.dark input,
.dark select,
.dark textarea {
  background-color: var(--input-bg);
  color: var(--input-text);
  border-color: var(--border-color);
}

.dark input:focus,
.dark select:focus,
.dark textarea:focus {
  outline: none;
  border-color: var(--primary-color);
  box-shadow: 0 0 0 2px rgba(74, 144, 226, 0.2);
}

/* 深色模式下的按钮样式 */
.dark button {
  color: var(--text-primary);
}

.dark .header-btn {
  background-color: rgba(255, 255, 255, 0.1);
}

.dark .header-btn:hover {
  background-color: rgba(255, 255, 255, 0.2);
}

.app-container {
  display: flex;
  flex-direction: column;
  height: 100vh;
}

.app-header {
  background-color: var(--bg-header);
  color: white;
  padding: 0.4rem 1.5rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  box-shadow: 0 2px 4px var(--shadow-color);
  transition: background-color 0.3s ease, box-shadow 0.3s ease;
}

.app-header h1 {
  margin: 0;
  font-size: 1.2rem;
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
  transition: background-color 0.3s ease, transform 0.2s ease;
  margin-left: 0.5rem;
}

/* 紧凑按钮样式 - 统一固定宽度和对齐 */
.compact-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.2rem;
  padding: 0.3rem 0.5rem;
  width: 90px;
  height: 32px;
  box-sizing: border-box;
  border-radius: 4px;
  background-color: rgba(255, 255, 255, 0.2);
  margin-left: 0.4rem;
}

/* 统一所有按钮样式，包括第一个按钮 */
.header-actions button {
  /* 重置默认按钮样式 */
  all: unset;
  /* 应用统一样式 */
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.2rem;
  padding: 0.3rem 0.5rem;
  width: 90px;
  height: 32px;
  box-sizing: border-box;
  border-radius: 4px;
  background-color: rgba(255, 255, 255, 0.2);
  color: white;
  font-size: 0.9rem;
  cursor: pointer;
  transition: background-color 0.3s ease, transform 0.2s ease;
  margin-left: 0.4rem;
}

/* 第一个按钮特殊处理 - 取消左侧margin */
.header-actions button:first-child {
  margin-left: 0 !important;
}

.btn-icon {
  font-size: 1rem;
  width: 16px;
  text-align: center;
}

.btn-text {
  font-size: 0.9rem;
  white-space: nowrap;
}

/* 统一按钮悬停效果 */
.header-actions button:hover {
  background-color: rgba(255, 255, 255, 0.3);
  transform: translateY(-1px);
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

/* Help内容样式 */
.help-content {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.help-content h2 {
  margin-bottom: 1rem;
  color: var(--text-primary);
  font-size: 1.5rem;
  font-weight: 600;
}

.help-section {
  margin-bottom: 1.5rem;
}

.help-section h3 {
  margin-bottom: 0.75rem;
  color: var(--text-primary);
  font-size: 1.1rem;
  font-weight: 500;
}

.help-section ul {
  list-style-type: disc;
  padding-left: 1.5rem;
  color: var(--text-secondary);
  line-height: 1.6;
}

.help-section li {
  margin-bottom: 0.5rem;
}

.help-section strong {
  color: var(--text-primary);
  font-weight: 500;
}

.help-actions {
  display: flex;
  justify-content: flex-end;
  margin-top: 1.5rem;
  padding-top: 1rem;
  border-top: 1px solid var(--border-color);
}

.save-btn {
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 4px;
  background-color: var(--primary-color);
  color: white;
  cursor: pointer;
  transition: background-color 0.3s ease;
}

.save-btn:hover {
  background-color: var(--primary-dark);
}
</style>