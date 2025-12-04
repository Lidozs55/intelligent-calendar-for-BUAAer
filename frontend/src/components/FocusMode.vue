<template>
  <div class="focus-mode-container" v-if="isFocusModeActive">
    <div class="focus-overlay" @click="exitFocusMode"></div>
    <div class="focus-content" @click.stop>
      <div class="focus-header">
        <h2>{{ currentTaskTitle }}</h2>
        <button class="exit-btn" @click="exitFocusMode">×</button>
      </div>
      
      <div class="timer-container">
        <!-- 计时模式切换 -->
        <div class="timer-mode-toggle">
          <button 
            :class="['mode-btn', { active: timerMode === 'countdown' }]"
            @click="timerMode = 'countdown'"
          >
            倒计时
          </button>
          <button 
            :class="['mode-btn', { active: timerMode === 'countup' }]"
            @click="timerMode = 'countup'"
          >
            正计时
          </button>
        </div>
        
        <div class="timer-display">{{ formattedTime }}</div>
        <div class="timer-controls">
          <button class="control-btn" @click="toggleTimer">
            {{ isRunning ? '暂停' : '开始' }}
          </button>
          <button class="control-btn" @click="resetTimer">重置</button>
        </div>
        
        <!-- 只有倒计时模式显示预设时长 -->
        <div class="timer-presets" v-if="timerMode === 'countdown'">
          <button 
            v-for="preset in timerPresets" 
            :key="preset"
            :class="['preset-btn', { active: selectedPreset === preset }]"
            @click="selectPreset(preset)"
          >
            {{ preset }}分钟
          </button>
        </div>
        
        <!-- 只有倒计时模式显示自定义时长 -->
        <div class="custom-duration" v-if="timerMode === 'countdown'">
          <label for="custom-minutes">自定义时长：</label>
          <input 
            type="number" 
            id="custom-minutes" 
            v-model.number="customMinutes"
            min="5"
            max="180"
            @change="updateCustomDuration"
          />
          <span>分钟</span>
        </div>
      </div>
      
      <div class="focus-actions">
        <h3>快速休息安排</h3>
        <div class="break-presets">
          <button class="action-btn" @click="scheduleBreak(5)">5分钟休息</button>
          <button class="action-btn" @click="scheduleBreak(10)">10分钟休息</button>
          <button class="action-btn" @click="scheduleBreak(15)">15分钟休息</button>
        </div>
      </div>
      
      <!-- 白噪音系统 -->
      <div class="ambient-sound-section">
        <h3>白噪音</h3>
        <div class="ambient-controls">
          <!-- 预设音效选择 -->
          <div class="sound-presets">
            <button 
              v-for="preset in soundPresets" 
              :key="preset.id"
              :class="['preset-btn', { active: selectedSound === preset.id }]"
              @click="selectSoundPreset(preset.id)"
            >
              {{ preset.name }}
            </button>
          </div>
          
          <!-- 音量控制 -->
          <div class="volume-control">
            <label for="volume">音量：</label>
            <input 
              type="range" 
              id="volume" 
              v-model.number="volume"
              min="0"
              max="100"
              step="1"
              @input="updateVolume"
            />
            <span>{{ volume }}%</span>
          </div>
          
          <!-- 播放控制 -->
          <div class="sound-playback">
            <button class="control-btn" @click="toggleSound">
              {{ isSoundPlaying ? '暂停' : '播放' }}
            </button>
            
            <!-- 本地音频导入 -->
            <div class="audio-import">
              <input 
                type="file" 
                id="audio-file" 
                accept="audio/*" 
                @change="importLocalAudio"
                style="display: none;"
              />
              <button class="control-btn" @click="document.getElementById('audio-file').click()">
                导入本地音频
              </button>
            </div>
          </div>
        </div>
      </div>
      
      <!-- 专注历史记录 -->
      <div class="focus-history" v-if="focusHistory.length > 0">
        <h3>最近专注记录</h3>
        <div class="history-list">
          <div class="history-item" v-for="record in focusHistory" :key="record.id">
            <div class="history-title">{{ record.task_title }}</div>
            <div class="history-time">{{ formatDuration(record.duration) }} - {{ new Date(record.start_time).toLocaleString() }}</div>
          </div>
        </div>
      </div>
    </div>
  </div>
  
  <!-- 专注模式启动确认弹窗 -->
  <div class="modal-overlay" v-if="showStartConfirm">
    <div class="modal-content">
      <h3>开始专注模式？</h3>
      <p>你确定要开始专注模式吗？</p>
      <div class="modal-actions">
        <button class="modal-btn cancel" @click="showStartConfirm = false">取消</button>
        <button class="modal-btn confirm" @click="startFocusMode">确认</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useTaskStore, useSettingsStore, useUserStore } from '../store'
import { scheduleAPI } from '../services/api'

// 状态管理
const taskStore = useTaskStore()
const settingsStore = useSettingsStore()
const userStore = useUserStore()

// 专注模式状态
const isFocusModeActive = ref(false)
const showStartConfirm = ref(false)
const currentTaskTitle = ref('专注学习')

// 计时器状态
const isRunning = ref(false)
const timerMode = ref('countdown') // 'countdown' 或 'countup'
const duration = ref(25 * 60) // 默认25分钟，单位：秒
const remainingTime = ref(duration.value)
const elapsedTime = ref(0) // 正计时已过时间，单位：秒
const timerPresets = ref([25, 45, 60, 90])
const selectedPreset = ref(25)
const customMinutes = ref(25)
let timerInterval = null

// 专注历史记录
const focusHistory = ref([])

// 白噪音系统状态
const isSoundPlaying = ref(false)
const volume = ref(50) // 音量 0-100
const selectedSound = ref(null)
const audioContext = ref(null)
const audioSource = ref(null)
const gainNode = ref(null)

// 预设音效列表
const soundPresets = ref([
  { id: 'rain', name: '雨声', url: '' },
  { id: 'cafe', name: '咖啡馆', url: '' },
  { id: 'forest', name: '森林', url: '' },
  { id: 'ocean', name: '海洋', url: '' },
  { id: 'fire', name: '篝火', url: '' }
])

// 本地导入的音频文件
const localAudioFile = ref(null)

// 计算属性：格式化时间显示
const formattedTime = computed(() => {
  let minutes, seconds
  
  if (timerMode.value === 'countdown') {
    // 倒计时模式
    minutes = Math.floor(remainingTime.value / 60)
    seconds = remainingTime.value % 60
  } else {
    // 正计时模式
    minutes = Math.floor(elapsedTime.value / 60)
    seconds = elapsedTime.value % 60
  }
  
  return `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`
})

// 方法：格式化时长显示（用于历史记录）
const formatDuration = (seconds) => {
  const minutes = Math.floor(seconds / 60)
  const remainingSeconds = seconds % 60
  if (remainingSeconds === 0) {
    return `${minutes}分钟`
  }
  return `${minutes}分钟${remainingSeconds}秒`
}

// 初始化音频上下文
const initAudioContext = () => {
  if (!audioContext.value) {
    audioContext.value = new (window.AudioContext || window.webkitAudioContext)()
    gainNode.value = audioContext.value.createGain()
    gainNode.value.connect(audioContext.value.destination)
    gainNode.value.gain.value = volume.value / 100
  }
}

// 选择预设音效
const selectSoundPreset = (soundId) => {
  selectedSound.value = soundId
  // 停止当前播放的音频
  stopSound()
}

// 切换音效播放状态
const toggleSound = async () => {
  if (!selectedSound.value && !localAudioFile.value) {
    alert('请先选择或导入音频')
    return
  }
  
  if (isSoundPlaying.value) {
    pauseSound()
  } else {
    await playSound()
  }
}

// 播放音效
const playSound = async () => {
  initAudioContext()
  
  try {
    if (localAudioFile.value) {
      // 播放本地导入的音频
      const fileReader = new FileReader()
      fileReader.onload = async (e) => {
        const arrayBuffer = e.target.result
        const audioBuffer = await audioContext.value.decodeAudioData(arrayBuffer)
        playAudioBuffer(audioBuffer)
      }
      fileReader.readAsArrayBuffer(localAudioFile.value)
    } else {
      // 播放预设音效（这里需要实际的音频URL，暂时使用模拟）
      // 实际项目中应该替换为真实的音频文件URL
      const audioBuffer = await simulateAudioBuffer()
      playAudioBuffer(audioBuffer)
    }
  } catch (error) {
    console.error('播放音效失败:', error)
    alert('播放音效失败，请检查音频文件')
  }
}

// 模拟音频缓冲（实际项目中应替换为真实音频加载）
const simulateAudioBuffer = async () => {
  // 创建一个简单的白噪音缓冲
  const sampleRate = audioContext.value.sampleRate
  const duration = 60 // 60秒
  const buffer = audioContext.value.createBuffer(1, sampleRate * duration, sampleRate)
  const data = buffer.getChannelData(0)
  
  // 生成白噪音
  for (let i = 0; i < data.length; i++) {
    data[i] = Math.random() * 2 - 1
  }
  
  return buffer
}

// 播放音频缓冲
const playAudioBuffer = (audioBuffer) => {
  if (audioSource.value) {
    audioSource.value.stop()
  }
  
  audioSource.value = audioContext.value.createBufferSource()
  audioSource.value.buffer = audioBuffer
  audioSource.value.loop = true // 循环播放
  audioSource.value.connect(gainNode.value)
  audioSource.value.start()
  
  isSoundPlaying.value = true
}

// 暂停音效
const pauseSound = () => {
  if (audioSource.value) {
    audioSource.value.stop()
    audioSource.value = null
  }
  isSoundPlaying.value = false
}

// 停止音效
const stopSound = () => {
  pauseSound()
}

// 更新音量
const updateVolume = () => {
  if (gainNode.value) {
    gainNode.value.gain.value = volume.value / 100
  }
}

// 导入本地音频
const importLocalAudio = (event) => {
  const file = event.target.files[0]
  if (file) {
    // 检查文件大小，限制在10MB以内
    if (file.size > 10 * 1024 * 1024) {
      alert('音频文件大小不能超过10MB')
      return
    }
    
    // 检查文件类型
    if (!file.type.startsWith('audio/')) {
      alert('请选择音频文件')
      return
    }
    
    localAudioFile.value = file
    selectedSound.value = null // 清除选中的预设音效
    alert('音频导入成功')
  }
}

// 方法：获取最近专注历史
const fetchFocusHistory = async () => {
  try {
    // 调用真实API获取专注历史
    const response = await scheduleAPI.getFocusHistory()
    focusHistory.value = response.focus_history || []
  } catch (error) {
    console.error('获取专注历史失败:', error)
    focusHistory.value = []
  }
}

// 方法：开始专注模式
const startFocusMode = () => {
  isFocusModeActive.value = true
  showStartConfirm.value = false
  resetTimer()
  fetchFocusHistory()
}

// 方法：退出专注模式
const exitFocusMode = () => {
  isFocusModeActive.value = false
  isRunning.value = false
  if (timerInterval) {
    clearInterval(timerInterval)
    timerInterval = null
  }
  // 保存专注记录
  saveFocusRecord()
}

// 方法：切换计时器
const toggleTimer = () => {
  isRunning.value = !isRunning.value
  if (isRunning.value) {
    startTimer()
  } else {
    pauseTimer()
  }
}

// 方法：开始计时
const startTimer = () => {
  timerInterval = setInterval(() => {
    if (timerMode.value === 'countdown') {
      // 倒计时模式
      remainingTime.value--
      if (remainingTime.value <= 0) {
        // 计时结束
        isRunning.value = false
        clearInterval(timerInterval)
        timerInterval = null
        // 可以添加提示音或其他通知
      }
    } else {
      // 正计时模式
      elapsedTime.value++
    }
  }, 1000)
}

// 方法：暂停计时
const pauseTimer = () => {
  if (timerInterval) {
    clearInterval(timerInterval)
    timerInterval = null
  }
}

// 方法：重置计时
const resetTimer = () => {
  isRunning.value = false
  if (timerInterval) {
    clearInterval(timerInterval)
    timerInterval = null
  }
  
  if (timerMode.value === 'countdown') {
    // 倒计时模式重置
    remainingTime.value = duration.value
  } else {
    // 正计时模式重置
    elapsedTime.value = 0
  }
}

// 方法：选择预设时长
const selectPreset = (preset) => {
  selectedPreset.value = preset
  duration.value = preset * 60
  customMinutes.value = preset
  resetTimer()
}

// 方法：更新自定义时长
const updateCustomDuration = () => {
  // 确保自定义时长在5-180分钟之间
  if (customMinutes.value < 5) customMinutes.value = 5
  if (customMinutes.value > 180) customMinutes.value = 180
  
  duration.value = customMinutes.value * 60
  selectedPreset.value = 0 // 清除选中的预设
  resetTimer()
}

// 方法：切换计时模式
const toggleTimerMode = () => {
  timerMode.value = timerMode.value === 'countdown' ? 'countup' : 'countdown'
  resetTimer()
}

// 方法：安排休息
const scheduleBreak = (duration = 5) => {
  // 调用后端API安排休息
  const currentTime = new Date()
  const breakStartTime = new Date(currentTime)
  const breakEndTime = new Date(currentTime)
  breakEndTime.setMinutes(breakStartTime.getMinutes() + duration)
  
  scheduleAPI.scheduleBreak({
    start_time: breakStartTime.toISOString().slice(0, 16),
    end_time: breakEndTime.toISOString().slice(0, 16),
    title: `[建议]${duration}分钟休息`,
    entry_type: 'sports'
  })
  
  // 可以添加提示
  alert(`已安排${duration}分钟休息`)
}

// 方法：保存专注记录
const saveFocusRecord = () => {
  // 计算实际专注时长（已运行时间）
  let actualFocusTime
  if (timerMode.value === 'countdown') {
    // 倒计时模式：计算已运行时间
    actualFocusTime = duration.value - remainingTime.value
  } else {
    // 正计时模式：直接使用已过时间
    actualFocusTime = elapsedTime.value
  }
  
  if (actualFocusTime > 0) {
    // 调用后端API保存专注记录
    scheduleAPI.saveFocusRecord({
      task_title: currentTaskTitle.value,
      duration: actualFocusTime,
      start_time: new Date(Date.now() - actualFocusTime * 1000).toISOString(),
      end_time: new Date().toISOString()
    })
  }
}

// 暴露给父组件的方法
defineExpose({
  openFocusMode: (taskInfo = null) => {
    if (taskInfo && taskInfo.title) {
      currentTaskTitle.value = taskInfo.title
    } else {
      currentTaskTitle.value = '专注学习'
    }
    showStartConfirm.value = true
  }
})

// 组件卸载时清理
onUnmounted(() => {
  if (timerInterval) {
    clearInterval(timerInterval)
  }
})
</script>

<style scoped>
.focus-mode-container {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 10000;
  display: flex;
  justify-content: center;
  align-items: center;
}

.focus-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.85);
  backdrop-filter: blur(5px);
}

.focus-content {
  position: relative;
  background-color: #1e1e1e;
  color: white;
  padding: 2rem;
  border-radius: 16px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
  text-align: center;
  width: 90%;
  max-width: 500px;
}

.focus-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
}

.focus-header h2 {
  margin: 0;
  font-size: 1.5rem;
  color: #ffffff;
}

.exit-btn {
  background: none;
  border: none;
  color: white;
  font-size: 1.5rem;
  cursor: pointer;
  padding: 0;
  width: 30px;
  height: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  transition: background-color 0.3s ease;
}

.exit-btn:hover {
  background-color: rgba(255, 255, 255, 0.1);
}

.timer-container {
  margin-bottom: 2rem;
}

/* 计时模式切换样式 */
.timer-mode-toggle {
  display: flex;
  justify-content: center;
  gap: 0.5rem;
  margin-bottom: 1rem;
}

.mode-btn {
  padding: 0.5rem 1rem;
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: 6px;
  background-color: rgba(255, 255, 255, 0.1);
  color: white;
  font-size: 0.9rem;
  cursor: pointer;
  transition: all 0.3s ease;
}

.mode-btn:hover {
  background-color: rgba(255, 255, 255, 0.2);
}

.mode-btn.active {
  background-color: var(--primary-color);
  border-color: var(--primary-color);
}

.timer-display {
  font-size: 4rem;
  font-weight: bold;
  margin-bottom: 1.5rem;
  color: #ffffff;
  font-family: monospace;
}

.timer-controls {
  display: flex;
  gap: 1rem;
  justify-content: center;
  margin-bottom: 1.5rem;
}

.control-btn {
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 8px;
  background-color: var(--primary-color);
  color: white;
  font-size: 1rem;
  cursor: pointer;
  transition: background-color 0.3s ease;
}

.control-btn:hover {
  background-color: var(--primary-dark);
}

.timer-presets {
  display: flex;
  gap: 0.5rem;
  justify-content: center;
  margin-bottom: 1.5rem;
  flex-wrap: wrap;
}

.preset-btn {
  padding: 0.5rem 1rem;
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: 6px;
  background-color: rgba(255, 255, 255, 0.1);
  color: white;
  font-size: 0.9rem;
  cursor: pointer;
  transition: all 0.3s ease;
}

.preset-btn:hover {
  background-color: rgba(255, 255, 255, 0.2);
}

.preset-btn.active {
  background-color: var(--primary-color);
  border-color: var(--primary-color);
}

.custom-duration {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  font-size: 0.9rem;
  color: rgba(255, 255, 255, 0.8);
}

.custom-duration input {
  width: 60px;
  padding: 0.5rem;
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: 4px;
  background-color: rgba(255, 255, 255, 0.1);
  color: white;
  font-size: 0.9rem;
  text-align: center;
}

.custom-duration input:focus {
  outline: none;
  border-color: var(--primary-color);
  box-shadow: 0 0 0 2px rgba(74, 144, 226, 0.2);
}

.focus-actions {
  margin-bottom: 2rem;
  text-align: left;
}

.focus-actions h3 {
  margin: 0 0 1rem 0;
  font-size: 1.1rem;
  color: #ffffff;
}

.break-presets {
  display: flex;
  gap: 0.75rem;
  flex-wrap: wrap;
}

.action-btn {
  padding: 0.75rem 1.5rem;
  border: 1px solid var(--primary-color);
  border-radius: 8px;
  background-color: transparent;
  color: var(--primary-color);
  font-size: 1rem;
  cursor: pointer;
  transition: all 0.3s ease;
}

.action-btn:hover {
  background-color: var(--primary-color);
  color: white;
}

/* 白噪音系统样式 */
.ambient-sound-section {
  margin-top: 2rem;
  padding-top: 1.5rem;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
  text-align: left;
}

.ambient-sound-section h3 {
  margin: 0 0 1rem 0;
  font-size: 1.1rem;
  color: #ffffff;
}

.ambient-controls {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.sound-presets {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.sound-presets .preset-btn {
  background-color: rgba(255, 255, 255, 0.05);
  border-color: rgba(255, 255, 255, 0.2);
}

.sound-presets .preset-btn.active {
  background-color: var(--primary-color);
  border-color: var(--primary-color);
}

.volume-control {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  color: rgba(255, 255, 255, 0.8);
  font-size: 0.9rem;
}

.volume-control input[type="range"] {
  flex: 1;
  max-width: 200px;
  -webkit-appearance: none;
  appearance: none;
  height: 5px;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 5px;
  outline: none;
}

.volume-control input[type="range"]::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 15px;
  height: 15px;
  background: var(--primary-color);
  border-radius: 50%;
  cursor: pointer;
  transition: background-color 0.3s ease;
}

.volume-control input[type="range"]::-webkit-slider-thumb:hover {
  background: var(--primary-dark);
}

.volume-control input[type="range"]::-moz-range-thumb {
  width: 15px;
  height: 15px;
  background: var(--primary-color);
  border-radius: 50%;
  cursor: pointer;
  border: none;
  transition: background-color 0.3s ease;
}

.volume-control input[type="range"]::-moz-range-thumb:hover {
  background: var(--primary-dark);
}

.volume-control span {
  width: 40px;
  text-align: right;
}

.sound-playback {
  display: flex;
  gap: 0.75rem;
  align-items: center;
  flex-wrap: wrap;
}

.audio-import {
  margin-top: 0.5rem;
}

/* 专注历史记录样式 */
.focus-history {
  margin-top: 2rem;
  padding-top: 1.5rem;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
  text-align: left;
}

.focus-history h3 {
  margin: 0 0 1rem 0;
  font-size: 1.1rem;
  color: #ffffff;
}

.history-list {
  max-height: 200px;
  overflow-y: auto;
}

.history-item {
  background-color: rgba(255, 255, 255, 0.05);
  padding: 0.75rem;
  border-radius: 6px;
  margin-bottom: 0.75rem;
  transition: background-color 0.3s ease;
}

.history-item:hover {
  background-color: rgba(255, 255, 255, 0.1);
}

.history-title {
  font-weight: 500;
  margin-bottom: 0.25rem;
  color: #ffffff;
}

.history-time {
  font-size: 0.85rem;
  color: rgba(255, 255, 255, 0.6);
}

/* 弹窗样式 */
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
  z-index: 10001;
}

.modal-content {
  background-color: white;
  color: #333;
  padding: 1.5rem;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  width: 90%;
  max-width: 400px;
  text-align: center;
}

.modal-content h3 {
  margin: 0 0 1rem 0;
  font-size: 1.25rem;
}

.modal-content p {
  margin: 0 0 1.5rem 0;
  color: #666;
}

.modal-actions {
  display: flex;
  gap: 1rem;
  justify-content: center;
}

.modal-btn {
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 6px;
  font-size: 1rem;
  cursor: pointer;
  transition: background-color 0.3s ease;
}

.modal-btn.cancel {
  background-color: #f5f5f5;
  color: #333;
}

.modal-btn.confirm {
  background-color: var(--primary-color);
  color: white;
}

.modal-btn:hover {
  opacity: 0.9;
}
</style>