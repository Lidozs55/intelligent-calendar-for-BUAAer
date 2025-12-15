<template>
  <div class="app-container" :class="[isMobilePage ? 'mobile-page' : '', isMobilePage ? theme : 'light']" :style="appStyle">
    <!-- 移动端页面 -->
    <template v-if="isMobilePage">
      <MobileHome />
    </template>
    <!-- 桌面端页面 -->
    <template v-else-if="currentPage === 'home'">
      <header class="app-header">
        <div class="header-left">
          <h1>智能日程助手 - 北航版</h1>
          <div class="current-date-display">
            <span class="current-date">{{ new Date().toLocaleDateString('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit', weekday: 'long' }) }}</span>
          </div>
          <!-- 提醒信息展示 -->
          <div v-if="showReminders" class="reminder-display">
            <div class="reminder-item" :class="getReminderUrgencyClass(reminders[currentReminderIndex])">
              <span class="reminder-title">{{ reminders[currentReminderIndex]?.title }}</span>
              <span class="reminder-time">{{ formatReminderTime(reminders[currentReminderIndex]?.start_time) }}</span>
            </div>
          </div>
        </div>
        <div class="header-actions">
          
          <!-- 在手机打开按钮 -->
          <button @click="togglePhoneQRCode" class="header-btn compact-btn" :class="{ 'btn-compact': !showButtonText }">
            <span class="btn-icon">
              <img src="/svg/phone.svg" alt="在手机打开" class="btn-svg-icon">
            </span>
            <span class="btn-text" :class="{ 'hidden-text': !showButtonText }">在手机打开</span>
          </button>
          
          <button @click="goToSmartInput" class="header-btn compact-btn" :class="{ 'btn-compact': !showButtonText }">
            <span class="btn-icon">
              <img src="/svg/pen.svg" alt="智能输入" class="btn-svg-icon">
            </span>
            <span class="btn-text" :class="{ 'hidden-text': !showButtonText }">智能输入</span>
          </button>
          <button @click="enterFocusMode" class="header-btn compact-btn" :class="{ 'btn-compact': !showButtonText }">
            <span class="btn-icon">
              <img src="/svg/timer.svg" alt="专注模式" class="btn-svg-icon">
            </span>
            <span class="btn-text" :class="{ 'hidden-text': !showButtonText }">专注模式</span>
          </button>
          <button @click="toggleHelp" class="header-btn compact-btn small-btn" :class="{ 'btn-compact': !showButtonText }">
            <span class="btn-icon">
              <img src="/svg/help.svg" alt="帮助" class="btn-svg-icon">
            </span>
            <span class="btn-text" :class="{ 'hidden-text': !showButtonText }">帮助</span>
          </button>
          <button @click="toggleSettings" class="header-btn compact-btn small-btn" :class="{ 'btn-compact': !showButtonText }">
            <span class="btn-icon">
              <img src="/svg/setting.svg" alt="设置" class="btn-svg-icon">
            </span>
            <span class="btn-text" :class="{ 'hidden-text': !showButtonText }">设置</span>
          </button>
          
          <!-- 切换按钮显示/隐藏按钮文本 - 简化为左右箭头图标 -->
          <button @click="toggleButtonText" class="header-btn toggle-text-btn btn-compact" :class="{ 'btn-compact': !showButtonText }">
            <span class="btn-icon">
              <!-- 使用旋转的箭头表示展开/收起 -->
              <svg v-if="showButtonText" class="btn-svg-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <polyline points="9 18 15 12 9 6"></polyline>
              </svg>
              <svg v-else class="btn-svg-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <polyline points="15 18 9 12 15 6"></polyline>
              </svg>
            </span>
          </button>
        </div>
      </header>
      
      <main class="app-main">
        <aside class="sidebar">
          <TaskSidebar @add-task="goToSmartInput" @start-focus="startFocusFromTask" @open-quadrant-view="openQuadrantView" @close-quadrant-view="goToCalendarView" @llm-entries-created="handleLLMEntriesCreated" />
        </aside>
        
        <section class="main-content">
          <template v-if="currentView === 'calendar'">
            <Home ref="homeRef" />
          </template>
          <template v-else-if="currentView === 'quadrant'">
            <div class="quadrant-view-wrapper">
              <QuadrantView />
            </div>
          </template>
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
            <div class="help-section">
              <h3>手机端使用</h3>
              <ul>
                <li><strong>访问方式</strong>：点击右上角"在手机打开"按钮，扫描二维码或直接输入URL访问</li>
                <li><strong>功能支持</strong>：
                  <ul>
                    <li>完整的课程管理功能</li>
                    <li>任务创建和编辑</li>
                    <li>智能输入功能</li>
                    <li>日历视图查看</li>
                    <li>设置面板</li>
                  </ul>
                </li>
                <li><strong>深色模式</strong>：移动端支持浅色/深色主题自动切换，跟随系统设置</li>
                <li><strong>响应式设计</strong>：自动适配不同手机屏幕尺寸</li>
                <li><strong>连接说明</strong>：
                  <ul>
                    <li>确保手机和电脑在同一局域网</li>
                    <li>cpolar服务正常运行可获得公网访问地址</li>
                    <li>无cpolar时可使用本地IP访问</li>
                  </ul>
                </li>
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
      
      <!-- 手机端二维码弹窗 -->
      <div v-if="showPhoneQRCode" class="settings-overlay" @click="togglePhoneQRCode">
        <div class="settings-panel" @click.stop>
          <div class="phone-qr-content">
            <h2>在手机打开</h2>
            <div class="qr-code-section">
                <div class="qr-code-container">
                  <img v-if="phoneQRCodeData && mobileAccessInfo?.cpolar_status === 'available'" :src="phoneQRCodeData" alt="手机访问二维码" class="qr-code-image">
                  <div v-else-if="mobileAccessInfo?.cpolar_status === 'unavailable'" class="qr-error">
                    <div class="error-icon">⚠️</div>
                    <div class="error-message">
                      <h3>cpolar服务未正确启动</h3>
                      <p>请检查：</p>
                      <ul>
                        <li>cpolar软件是否已正确安装</li>
                        <li>是否有其他程序占用4040端口</li>
                        <li>尝试手动启动cpolar：cpolar http 5000</li>
                      </ul>
                    </div>
                  </div>
                  <div v-else class="qr-loading">加载二维码中...</div>
                </div>
                <div class="qr-info">
                  <p><strong>连接说明：</strong></p>
                  <ul>
                    <li v-if="mobileAccessInfo?.cpolar_status === 'available'">扫描上方二维码打开日历</li>
                    <li>或直接访问：<span class="access-url">{{ mobileAccessInfo?.mobile_url || '' }}</span></li>
                    <li v-if="mobileAccessInfo?.cpolar_status === 'unavailable'" class="cpolar-warning">
                      <strong>注意：</strong>cpolar服务未正确启动，当前使用本地地址
                    </li>
                  </ul>
                  <div class="refresh-section">
                    <button @click="handleRefreshQRCode" :disabled="isRefreshing" class="refresh-btn">
                      <svg v-if="!isRefreshing" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <polyline points="23 4 23 10 17 10"></polyline>
                        <polyline points="1 20 1 14 7 14"></polyline>
                        <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"></path>
                      </svg>
                      <svg v-else class="loading-spinner" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <circle cx="12" cy="12" r="10"></circle>
                        <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"></path>
                      </svg>
                      {{ isRefreshing ? '刷新中...' : '刷新二维码' }}
                    </button>
                  </div>
                </div>
              </div>
              <div class="connection-details">
              <h3>连接信息</h3>
              <p><strong>本地IP:</strong> {{ mobileAccessInfo?.local_ip || '获取中...' }}</p>
              <p><strong>端口:</strong> {{ mobileAccessInfo?.port || '5000' }}</p>
              <p><strong>cpolar状态:</strong> 
                <span :class="{ 
                  'cpolar-status-available': mobileAccessInfo?.cpolar_status === 'available',
                  'cpolar-status-unavailable': mobileAccessInfo?.cpolar_status === 'unavailable'
                }">
                  {{ mobileAccessInfo?.cpolar_status === 'available' ? '可用' : '未可用' }}
                </span>
              </p>
              <p><strong>访问地址:</strong> {{ mobileAccessInfo?.mobile_url || '' }}</p>
              <p v-if="mobileAccessInfo?.cpolar_url" class="cpolar-url-info">
                <strong>cpolar域名:</strong> {{ mobileAccessInfo?.cpolar_url }}
              </p>
            </div>
            
            <!-- CPolar Authtoken配置 -->
            <div class="cpolar-authtoken-section">
              <h3>CPolar配置</h3>
              <div class="cpolar-info">
                <p>获取CPolar Authtoken的方法：</p>
                <ol>
                  <li>访问 <a href="https://dashboard.cpolar.com/" target="_blank" class="external-link">https://dashboard.cpolar.com/</a></li>
                  <li>登录您的CPolar账号</li>
                  <li>在左侧菜单中选择"Authtokens"</li>
                  <li>复制您的Authtoken</li>
                  <li>粘贴到下方输入框并点击"保存"</li>
                </ol>
              </div>
              <div class="authtoken-input-section">
                <div class="input-group">
                  <label for="cpolar-authtoken">CPolar Authtoken：</label>
                  <input 
                    type="text" 
                    id="cpolar-authtoken" 
                    v-model="cpolarAuthtoken" 
                    placeholder="./cpolar authtoken"
                    class="authtoken-input"
                  >
                </div>
                <button @click="saveCPolarAuthtoken" class="save-btn authtoken-save-btn">保存</button>
              </div>
            </div>
            <div class="help-actions">
              <button @click="togglePhoneQRCode" class="save-btn">关闭</button>
            </div>
          </div>
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
import { ref, onMounted, onUnmounted, computed, nextTick } from 'vue'
import Home from './views/Home.vue'
import SmartInputPage from './views/SmartInputPage.vue'
import TaskSidebar from './components/TaskSidebar.vue'
import SettingsPanel from './components/SettingsPanel.vue'
import FocusMode from './components/FocusMode.vue'
import QuadrantView from './components/QuadrantView.vue'
import MobileHome from './pages/MobileHome.vue'
import { useUserStore, useTaskStore, useCourseStore, useSettingsStore, useClipboardStore } from './store'
import notificationService from './services/notification'
import { remindersAPI } from './services/api'

// 页面管理状态
const currentPage = ref('home')
const currentView = ref('calendar') // calendar 或 quadrant
const showSettings = ref(false)
const showHelp = ref(false)
const focusModeRef = ref(null)
const homeRef = ref(null)

// 手机端二维码状态
const showPhoneQRCode = ref(false)
const phoneQRCodeData = ref(null)
const mobileAccessInfo = ref(null)
const isRefreshing = ref(false)
const cpolarAuthtoken = ref('')
let refreshTimeout = null
const DEBOUNCE_TIME = 1000 // 防抖时间，1秒

// 判断是否为移动端页面
const isMobilePage = ref(false)

// 检查当前URL路径，判断是否为移动端页面
const checkIfMobilePage = () => {
  const path = window.location.pathname
  isMobilePage.value = path.startsWith('/mobile')
}

// 监听URL变化
window.addEventListener('popstate', checkIfMobilePage)
window.addEventListener('hashchange', checkIfMobilePage)
const userStore = useUserStore()
const taskStore = useTaskStore()
const courseStore = useCourseStore()
const settingsStore = useSettingsStore()
const clipboardStore = useClipboardStore()
let notificationIntervalId = null
let clipboardCheckInterval = null
let reminderIntervalId = null

// 控制按钮文本显示/隐藏的状态
const showButtonText = ref(true)

// 提醒相关状态
const reminders = ref([])
const currentReminderIndex = ref(0)
const showReminders = ref(false)
let reminderRotationInterval = null

// 最后一次剪切板内容
let lastClipboardText = ''

// 切换按钮文本显示/隐藏
const toggleButtonText = () => {
  showButtonText.value = !showButtonText.value
}

// 格式化提醒时间
const formatReminderTime = (startTime) => {
  if (!startTime) return ''
  
  const now = new Date()
  const eventTime = new Date(startTime)
  
  // 计算日期差，忽略时间部分
  const nowDate = new Date(now.getFullYear(), now.getMonth(), now.getDate())
  const eventDate = new Date(eventTime.getFullYear(), eventTime.getMonth(), eventTime.getDate())
  const diffTime = eventDate - nowDate
  const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24))
  
  // 格式化时间为hh:mm
  const timeString = eventTime.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
  
  if (diffDays === 0) {
    // 今天的事件，只显示时间
    return timeString
  } else {
    // 未来的事件，显示x天后hh:mm
    return `${diffDays}天后${timeString}`
  }
}

// 根据时间比值计算提醒的紧急程度类名
const getReminderUrgencyClass = (reminder) => {
  if (!reminder) return ''
  
  const now = new Date()
  const eventTime = new Date(reminder.start_time)
  const timeDiffMinutes = (eventTime - now) / (1000 * 60)
  
  // 获取用户设置的对应提醒时间
  let reminderTimeMinutes = 60 // 默认1小时
  const eventType = reminder.event_type?.toLowerCase()
  
  if (eventType === 'exam') {
    // 考试使用前往考场提醒时间
    reminderTimeMinutes = settingsStore.reminderSettings.exam[1] || 60
  } else {
    // 其他事件使用课程/讲座/会议提醒时间
    reminderTimeMinutes = settingsStore.reminderSettings.course || 30
  }
  
  // 计算时间比值
  const ratio = timeDiffMinutes / reminderTimeMinutes
  
  // 根据比值返回不同的紧急程度类名
  if (ratio <= 0.25) {
    return 'urgent'
  } else if (ratio <= 0.5) {
    return 'high'
  } else if (ratio <= 0.75) {
    return 'medium'
  } else {
    return 'low'
  }
}

// 获取即将到来的提醒
const fetchReminders = async () => {
  try {
    // 使用设置中的提醒参数
    const response = await remindersAPI.getUpcomingReminders(settingsStore.reminderSettings)
    if (response.success) {
      reminders.value = response.reminders
      showReminders.value = reminders.value.length > 0
      
      // 如果有提醒，开始轮换展示
      if (showReminders.value) {
        startReminderRotation()
      }
    }
  } catch (error) {
    console.error('获取提醒失败:', error)
  }
}

// 开始轮换提醒
const startReminderRotation = () => {
  // 清除现有的轮换定时器
  if (reminderRotationInterval) {
    clearInterval(reminderRotationInterval)
  }
  
  // 每5秒轮换一次提醒
  reminderRotationInterval = setInterval(() => {
    currentReminderIndex.value = (currentReminderIndex.value + 1) % reminders.value.length
  }, 5000)
}

// 停止轮换提醒
const stopReminderRotation = () => {
  if (reminderRotationInterval) {
    clearInterval(reminderRotationInterval)
    reminderRotationInterval = null
  }
}

// 计算应用样式，动态设置CSS变量
const appStyle = computed(() => {
  const defaultColor = settingsStore.defaultColor
  // 生成浅色版本：降低饱和度和亮度
  const lightVersion = getLightVersion(defaultColor)
  // 生成深色调版本：用于深色主题
  const darkVersion = getDarkVersion(defaultColor)
  
  // 解析颜色为RGB
  const rgb = hexToRgb(defaultColor)
  const rgbStr = rgb ? `${rgb.r}, ${rgb.g}, ${rgb.b}` : '74, 144, 226'
  
  return {
    '--primary-color': defaultColor,
    '--primary-color-rgb': rgbStr,
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

// 切换手机端二维码显示
const togglePhoneQRCode = async () => {
  showPhoneQRCode.value = !showPhoneQRCode.value
  if (showPhoneQRCode.value) {
    await fetchMobileAccessInfo()
  }
}

// 获取手机访问信息和二维码
const fetchMobileAccessInfo = async () => {
  try {
    const response = await fetch('/api/mobile/info')
    const data = await response.json()
    if (data.success) {
      mobileAccessInfo.value = data.data
      phoneQRCodeData.value = data.data.qr_code
    }
  } catch (error) {
    console.error('获取手机访问信息失败:', error)
  } finally {
    isRefreshing.value = false
  }
}

// 防抖刷新二维码
const handleRefreshQRCode = () => {
  // 清除之前的定时器
  if (refreshTimeout) {
    clearTimeout(refreshTimeout)
  }
  
  // 设置新的定时器
  refreshTimeout = setTimeout(async () => {
    isRefreshing.value = true
    await fetchMobileAccessInfo()
  }, DEBOUNCE_TIME)
}

// 保存CPolar authtoken
const saveCPolarAuthtoken = async () => {
  try {
    const response = await fetch('/api/mobile/set_cpolar_authtoken', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ authtoken: cpolarAuthtoken.value })
    })
    const data = await response.json()
    if (data.success) {
      alert('CPolar Authtoken保存成功')
      // 刷新二维码
      handleRefreshQRCode()
    } else {
      alert('CPolar Authtoken保存失败: ' + (data.message || '未知错误'))
    }
  } catch (error) {
    console.error('保存CPolar Authtoken失败:', error)
    alert('保存CPolar Authtoken失败，请检查网络连接')
  }
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

// 打开四象限视图
const openQuadrantView = () => {
  currentView.value = 'quadrant'
}

// 返回到日历视图
const goToCalendarView = () => {
  currentView.value = 'calendar'
}

// 处理LLM生成的新条目
const handleLLMEntriesCreated = (entries) => {
  // 将新条目传递给Home组件，以便Home组件可以通知CalendarView刷新
  if (homeRef.value) {
    homeRef.value.addLLMEntries(entries)
  }
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
  // 检查是否为移动端页面
  checkIfMobilePage()
  
  // 初始化通知服务
  initNotifications()
  
  // 启动定期检查剪切板，每5秒检查一次
  clipboardCheckInterval = setInterval(autoCheckClipboard, 5000)
  
  // 立即获取一次提醒，然后每分钟获取一次
  fetchReminders()
  reminderIntervalId = setInterval(fetchReminders, 60000)
})

// 组件卸载时清除定时器
onUnmounted(() => {
  if (notificationIntervalId) {
    notificationService.stopCheckInterval(notificationIntervalId)
  }
  if (clipboardCheckInterval) {
    clearInterval(clipboardCheckInterval)
  }
  if (reminderIntervalId) {
    clearInterval(reminderIntervalId)
  }
  if (reminderRotationInterval) {
    clearInterval(reminderRotationInterval)
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
  --input-bg: white;
  --input-text: #333;
  --button-hover: rgba(0, 0, 0, 0.1);
}

/* 仅移动端支持深色主题 */
.mobile-page.dark {
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

/* 移动端深色模式下的表单元素样式 */
.mobile-page.dark input,
.mobile-page.dark select,
.mobile-page.dark textarea {
  background-color: var(--input-bg);
  color: var(--input-text);
  border-color: var(--border-color);
}

.mobile-page.dark input:focus,
.mobile-page.dark select:focus,
.mobile-page.dark textarea:focus {
  outline: none;
  border-color: var(--primary-color);
  box-shadow: 0 0 0 2px rgba(74, 144, 226, 0.2);
}

/* 移动端深色模式下的按钮样式 */
.mobile-page.dark button {
  color: var(--text-primary);
}

.mobile-page.dark .header-btn {
  background-color: rgba(255, 255, 255, 0.1);
}

.mobile-page.dark .header-btn:hover {
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
  padding: 0.5rem 1.5rem 0.5rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  box-shadow: 0 2px 4px var(--shadow-color);
  transition: background-color 0.3s ease, box-shadow 0.3s ease;
  position: relative;
}

/* 提醒信息样式 - 基础样式 */
.reminder-display {
  width: 100%;
  max-width: 400px;
}

/* 提醒条居中定位 */
.reminder-display {
  position: absolute;
  left: 50%;
  transform: translateX(-50%);
  bottom: 0.5rem;
  margin: 0;
}

.reminder-item {
  display: flex;
  align-items: center;
  padding: 0.5rem 1rem;
  border-radius: 4px;
  font-weight: 500;
  animation: fadeIn 0.5s ease-in-out;
  transition: all 0.3s ease;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  width: 100%;
}

/* 根据紧急程度显示不同颜色 */
.reminder-item.urgent {
  background-color: rgba(255, 68, 68, 0.9);
  color: white;
}

.reminder-item.high {
  background-color: rgba(255, 102, 102, 0.9);
  color: white;
}

.reminder-item.medium {
  background-color: rgba(255, 170, 0, 0.9);
  color: white;
}

.reminder-item.low {
  background-color: rgba(74, 144, 226, 0.9);
  color: white;
}

.reminder-title {
  flex: 1;
  margin-right: 1rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.reminder-time {
  font-weight: 600;
  min-width: 80px;
  text-align: right;
}

/* 淡入动画 */
@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.header-left {
  display: flex;
  align-items: center;
  justify-content: flex-start;
  gap: 1rem;
  flex: 1;
}

.app-header h1 {
  margin: 0;
  font-size: 1.2rem;
  font-weight: 500;
  text-align: left;
}

.current-date-display {
  font-size: 0.9rem;
  font-weight: 400;
  color: rgba(255, 255, 255, 0.9);
  text-align: left;
}

/* 提醒信息容器 */
.app-header {
  position: relative;
}

/* 提醒信息样式 */
.reminder-display {
  position: absolute;
  left: 50%;
  transform: translateX(-50%);
  bottom: 0.5rem;
  width: 100%;
  max-width: 400px;
  margin: 0;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 0.2rem;
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
  width: 95px;
  height: 32px;
  box-sizing: border-box;
  border-radius: 4px;
  background-color: rgba(255, 255, 255, 0.2);
  color: white;
  font-size: 0.9rem;
  cursor: pointer;
  transition: background-color 0.3s ease, transform 0.2s ease, width 0.3s ease, padding 0.3s ease;
}

/* 小型按钮样式 - 用于设置、帮助和隐藏按钮 */
.header-actions button.small-btn {
  padding: 0.2rem 0.3rem;
  width: 75px;
  font-size: 0.85rem;
}

/* 隐藏文本后的紧凑按钮样式 */
.btn-compact {
  width: 40px !important;
  padding: 0.3rem !important;
}

/* 不再需要特殊处理第一个按钮，间距由header-actions的gap属性控制 */

.btn-icon {
  font-size: 1rem;
  width: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* 紧凑状态下确保图标略微偏右 */
.btn-compact .btn-icon {
  width: 100%;
  justify-content: center;
  padding-left: 2px;
  transform: translateX(1px);
}

/* SVG图标样式 */
.btn-svg-icon {
  width: 18px;
  height: 18px;
  filter: brightness(0) invert(1); /* 将图标转换为白色 */
  transition: filter 0.3s ease;
  vertical-align: middle;
}

/* 确保移动端深色模式下图标也是白色 */
.mobile-page.dark .btn-svg-icon {
  filter: brightness(0) invert(1);
}

/* 按钮悬停时的图标效果 */
.header-actions button:hover .btn-svg-icon {
  filter: brightness(0.8) invert(1); /* 悬停时稍微变暗 */
}

.btn-text {
  font-size: 0.9rem;
  white-space: nowrap;
  transition: opacity 0.3s ease, width 0.3s ease, margin-left 0.3s ease;
  opacity: 1;
  width: auto;
  margin-left: 0.2rem;
}

/* 隐藏文本的样式 */
.hidden-text {
  opacity: 0;
  width: 0;
  margin-left: 0;
  overflow: hidden;
}

/* 切换文本按钮的样式 */
.toggle-text-btn {
  display: flex;
  align-items: center;
  justify-content: center;
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

.quadrant-view-wrapper {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.view-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
  padding-bottom: 0.5rem;
  border-bottom: 1px solid var(--border-color);
}

.view-header h2 {
  margin: 0;
  font-size: 1.5rem;
  color: var(--text-primary);
}

.back-btn {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  background-color: var(--primary-color);
  color: white;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 4px;
  cursor: pointer;
  font-size: 1rem;
  transition: all 0.3s ease;
}

.back-btn:hover {
  background-color: var(--primary-dark);
  transform: translateY(-1px);
  box-shadow: 0 2px 4px var(--shadow-color);
}

.back-btn svg {
  filter: brightness(0) invert(1);
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

/* 手机端二维码弹窗样式 */
.phone-qr-content {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.qr-code-section {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  margin-bottom: 1rem;
  align-items: center;
}

@media (min-width: 768px) {
  .qr-code-section {
    flex-direction: row;
    justify-content: center;
    align-items: flex-start;
  }
}

.qr-code-container {
  display: flex;
  justify-content: center;
  align-items: center;
  width: 250px;
  height: 250px;
  background-color: white;
  padding: 1rem;
  border-radius: 8px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
}

.qr-code-image {
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
}

.qr-loading {
  font-size: 1rem;
  color: var(--text-secondary);
}

.qr-info {
  flex: 1;
  min-width: 200px;
  background-color: var(--bg-primary);
  padding: 1rem;
  border-radius: 8px;
}

.qr-info ul {
  list-style-type: disc;
  padding-left: 1.5rem;
  color: var(--text-secondary);
  line-height: 1.6;
}

.qr-info li {
  margin-bottom: 0.75rem;
}

.access-url {
  font-family: 'Courier New', Courier, monospace;
  word-break: break-all;
  background-color: rgba(74, 144, 226, 0.1);
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-size: 0.9rem;
  color: var(--primary-color);
}

.connection-details {
  background-color: var(--bg-primary);
  padding: 1rem;
  border-radius: 8px;
}

.connection-details h3 {
  margin-bottom: 0.75rem;
  color: var(--text-primary);
  font-size: 1.1rem;
  font-weight: 500;
}

.connection-details p {
  margin-bottom: 0.5rem;
  color: var(--text-secondary);
  line-height: 1.5;
}

.connection-details strong {
  color: var(--text-primary);
  font-weight: 500;
}

/* cpolar服务状态样式 */
.cpolar-status-available {
  color: #4caf50;
  font-weight: bold;
}

.cpolar-status-unavailable {
  color: #f44336;
  font-weight: bold;
}

.cpolar-url-info {
  font-family: 'Courier New', Courier, monospace;
  background-color: rgba(76, 175, 80, 0.1);
  padding: 0.5rem;
  border-radius: 4px;
  margin-top: 0.75rem !important;
  word-break: break-all;
}

.cpolar-warning {
  color: #ff9800;
  font-weight: bold;
}

/* 二维码错误状态样式 */
.qr-error {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
  padding: 1.5rem;
  background-color: rgba(244, 67, 54, 0.1);
  border-radius: 8px;
  text-align: center;
  color: #f44336;
}

.error-icon {
  font-size: 2.5rem;
}

.error-message {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  text-align: left;
  max-width: 300px;
}

.error-message h3 {
  margin: 0;
  font-size: 1.1rem;
  font-weight: 600;
}

.error-message p {
  margin: 0;
  color: var(--text-secondary);
}

.error-message ul {
  margin: 0;
  padding-left: 1.25rem;
  color: var(--text-secondary);
  line-height: 1.5;
}

.error-message li {
  margin-bottom: 0.5rem;
}

/* 适配移动端深色主题 */
.mobile-page.dark .cpolar-url-info {
  background-color: rgba(76, 175, 80, 0.2);
}

.mobile-page.dark .qr-error {
  background-color: rgba(244, 67, 54, 0.2);
  color: #ff5252;
}

/* 刷新按钮样式 */
.refresh-section {
  margin-top: 12px;
  display: flex;
  justify-content: flex-start;
}

.refresh-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  border: none;
  border-radius: 4px;
  background-color: var(--primary-color);
  color: white;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.refresh-btn:hover {
  background-color: var(--primary-dark);
}

.refresh-btn:disabled {
  background-color: #ccc;
  cursor: not-allowed;
}

.loading-spinner {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

/* CPolar配置区域样式 */
.cpolar-authtoken-section {
  background-color: var(--bg-primary);
  padding: 16px;
  border-radius: 8px;
  margin-top: 16px;
}

.cpolar-authtoken-section h3 {
  margin-top: 0;
  margin-bottom: 12px;
  color: var(--text-primary);
  font-size: 1.1rem;
}

.cpolar-info {
  margin-bottom: 16px;
  color: var(--text-secondary);
  line-height: 1.6;
}

.cpolar-info ol {
  padding-left: 20px;
  margin-top: 8px;
}

.cpolar-info li {
  margin-bottom: 8px;
}

.external-link {
  color: var(--primary-color);
  text-decoration: none;
}

.external-link:hover {
  text-decoration: underline;
}

/* CPolar Authtoken输入区域样式 */
.authtoken-input-section {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.input-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.input-group label {
  font-weight: 500;
  color: var(--text-primary);
  font-size: 0.9rem;
}

.authtoken-input {
  padding: 10px;
  border: 1px solid var(--border-color);
  border-radius: 4px;
  font-size: 1rem;
  color: var(--text-primary);
  background-color: var(--bg-secondary);
  transition: all 0.3s ease;
}

.authtoken-input:focus {
  outline: none;
  border-color: var(--primary-color);
  box-shadow: 0 0 0 2px rgba(var(--primary-color-rgb), 0.2);
}

.authtoken-save-btn {
  align-self: flex-start;
  padding: 10px 20px;
  font-size: 0.9rem;
}

/* 适配深色主题 */
.dark .authtoken-input {
  background-color: #2d2d2d;
  color: white;
  border-color: #444;
}

.dark .authtoken-input:focus {
  border-color: var(--primary-color);
  box-shadow: 0 0 0 2px rgba(74, 144, 226, 0.3);
}
</style>