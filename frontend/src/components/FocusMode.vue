<template>
  <div class="focus-mode-container" v-if="isFocusModeActive">
    <div class="focus-overlay" @click="exitFocusMode"></div>
    <div class="focus-content" @click.stop>
      <div class="focus-header">
        <h2>{{ isBreakMode ? '休息模式' : currentTaskTitle }}</h2>
        <button class="exit-btn" @click="exitFocusMode">×</button>
      </div>
      
      <div class="timer-container">
        <!-- 计时模式切换 - 只在非休息模式显示 -->
        <div class="timer-mode-toggle" v-if="!isBreakMode">
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
          <button class="control-btn" @click="isBreakMode ? endBreakMode() : toggleTimer()" id="main-control-btn">
            {{ isBreakMode ? '结束休息' : (isRunning ? '暂停' : '开始') }}
          </button>
          <button class="control-btn" @click="resetTimer()" v-if="!isBreakMode">重置</button>
        </div>
        
        <!-- 只有倒计时模式且非休息模式显示预设时长 -->
        <div class="timer-presets" v-if="timerMode === 'countdown' && !isBreakMode">
          <button 
            v-for="preset in timerPresets" 
            :key="preset"
            :class="['preset-btn', { active: selectedPreset === preset }]"
            @click="selectPreset(preset)"
          >
            {{ preset }}分钟
          </button>
        </div>
        
        <!-- 只有倒计时模式且非休息模式显示自定义时长 -->
        <div class="custom-duration" v-if="timerMode === 'countdown' && !isBreakMode">
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
          <button class="action-btn" @click="scheduleBreak(5)" :disabled="isBreakMode || isRunning">5分钟休息</button>
          <button class="action-btn" @click="scheduleBreak(10)" :disabled="isBreakMode || isRunning">10分钟休息</button>
          <button class="action-btn" @click="scheduleBreak(15)" :disabled="isBreakMode || isRunning">15分钟休息</button>
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
              <span class="sound-icon">{{ preset.icon }}</span>
              <span class="sound-name">{{ preset.name }}</span>
              <span v-if="preset.playing" class="sound-indicator">▶️</span>
            </button>
          </div>
          
          <!-- 音量控制 -->
          <div class="volume-control">
            <label for="globalVolume">音量：</label>
            <input 
              type="range" 
              id="globalVolume" 
              v-model.number="globalVolume"
              min="0"
              max="100"
              step="1"
              @input="updateGlobalVolume"
            />
            <span>{{ globalVolume }}%</span>
          </div>
          
          <!-- 音效单独音量控制 -->
          <div class="individual-volume-controls" v-if="selectedSound !== 'none'">
            <h4>当前音效音量</h4>
            <div class="individual-volume" v-for="preset in soundPresets" :key="preset.id" v-if="preset.id === selectedSound">
              <label :for="`volume-${preset.id}`">{{ preset.icon }} {{ preset.name }}：</label>
              <input 
                :id="`volume-${preset.id}`"
                type="range" 
                v-model.number="preset.volume"
                min="0"
                max="100"
                step="1"
                @input="updateSoundVolume(preset.id, preset.volume)"
              />
              <span>{{ preset.volume }}%</span>
            </div>
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
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
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
const isBreakMode = ref(false)
const breakDuration = ref(0)
const remainingBreakTime = ref(0)

// 计时器状态 - 关键修复：所有时间变量必须是ref
const isRunning = ref(false)
const timerMode = ref('countdown')
const duration = ref(25 * 60) // 1500秒
const remainingTime = ref(duration.value)
const elapsedTime = ref(0)
const timerPresets = ref([25, 45, 60, 90])
const selectedPreset = ref(25)
const customMinutes = ref(25)

// 关键修复1：使用ref管理计时器ID
const timerInterval = ref(null)
const breakTimerInterval = ref(null)

// 专注历史记录
const focusHistory = ref([])

// 白噪音系统状态
const isSoundPlaying = ref(false)
const globalVolume = ref(50)
const selectedSound = ref('none')
const audioContext = ref(null)
const audioSources = ref({})
const gainNodes = ref({})

// 预设音效列表 - 使用用户提供的外部URL和图标
const soundPresets = ref([ 
  { id: 'none', name: '暂无音效', icon: '🔇', playing: false, volume: 0, url: '' }, 
  { id: 'rain', name: '雨声', icon: '🌧️', playing: false, volume: 40, url: 'https://assets.mixkit.co/active_storage/sfx/2390/2390-preview.mp3' }, 
  { id: 'cafe', name: '咖啡馆', icon: '☕', playing: false, volume: 35, url: 'https://assets.mixkit.co/active_storage/sfx/2313/2313-preview.mp3' }, 
  { id: 'forest', name: '森林', icon: '🌲', playing: false, volume: 40, url: 'https://assets.mixkit.co/active_storage/sfx/1237/1237-preview.mp3' }, 
  { id: 'ocean', name: '海浪', icon: '🌊', playing: false, volume: 35, url: 'https://assets.mixkit.co/active_storage/sfx/1451/1451-preview.mp3' }, 
  { id: 'fire', name: '壁炉', icon: '🔥', playing: false, volume: 38, url: 'https://assets.mixkit.co/active_storage/sfx/1423/1423-preview.mp3' }, 
  { id: 'wind', name: '风声', icon: '💨', playing: false, volume: 35, url: 'https://assets.mixkit.co/active_storage/sfx/1438/1438-preview.mp3' } 
])

// 本地导入的音频文件
const localAudioFile = ref(null)

// 计算属性：格式化时间显示
const formattedTime = computed(() => {
  let minutes, seconds 
  
  if (isBreakMode.value) {
    minutes = Math.floor(remainingBreakTime.value / 60)
    seconds = Math.floor(remainingBreakTime.value % 60)
  } else if (timerMode.value === 'countdown') {
    minutes = Math.floor(remainingTime.value / 60)
    seconds = Math.floor(remainingTime.value % 60)
  } else {
    minutes = Math.floor(elapsedTime.value / 60)
    seconds = Math.floor(elapsedTime.value % 60)
  }
  
  return `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`
})

// 方法：格式化时长显示
const formatDuration = (seconds) => {
  const minutes = Math.floor(seconds / 60)
  const remainingSeconds = seconds % 60
  if (remainingSeconds === 0) {
    return `${minutes}分钟`
  }
  return `${minutes}分钟${remainingSeconds}秒`
}

// 关键修复2：专注计时器逻辑
const startTimer = () => {
  console.log('====================================');
  console.log('🔢 startTimer 函数调用');
  console.log('调用时状态:');
  console.log('   isBreakMode:', isBreakMode.value);
  console.log('   isRunning:', isRunning.value);
  console.log('   timerMode:', timerMode.value);
  
  // 设置运行状态
  isRunning.value = true;
  console.log('   设置 isRunning 为 true');
  
  // 清除已有计时器
  if (timerInterval.value) {
    console.log('   清除已有计时器:', timerInterval.value);
    clearInterval(timerInterval.value);
    timerInterval.value = null;
    console.log('   计时器已清除');
  }
  
  // 检查当前是否处于休息模式
  if (isBreakMode.value) {
    console.warn('⚠️  尝试在休息模式下启动专注计时器，已阻止');
    isRunning.value = false;
    console.log('   设置 isRunning 为 false');
    return;
  }
  
  console.log('✅ 准备启动新计时器');
  console.log('   启动参数:');
  console.log('   - 模式:', timerMode.value);
  console.log('   - 剩余时间:', remainingTime.value);
  console.log('   - 已用时间:', elapsedTime.value);
  
  // 启动新计时器
  console.log('⏱️  调用 setInterval 启动计时器...');
  timerInterval.value = setInterval(() => {
    // 每次执行都打印状态，便于调试
    console.log('⏱️  计时器回调执行:');
    console.log('   - isRunning:', isRunning.value);
    console.log('   - isBreakMode:', isBreakMode.value);
    console.log('   - timerMode:', timerMode.value);
    console.log('   - remainingTime:', remainingTime.value);
    console.log('   - elapsedTime:', elapsedTime.value);
    
    // 检查是否应该继续运行
    if (!isRunning.value) {
      console.log('⏹️  计时器停止：isRunning 为 false');
      if (timerInterval.value) {
        clearInterval(timerInterval.value);
        timerInterval.value = null;
        console.log('   计时器已清除');
      }
      return;
    }
    
    if (isBreakMode.value) {
      console.log('⏹️  计时器停止：isBreakMode 为 true');
      if (timerInterval.value) {
        clearInterval(timerInterval.value);
        timerInterval.value = null;
        console.log('   计时器已清除');
      }
      return;
    }
    
    // 执行计时逻辑
    if (timerMode.value === 'countdown') {
      console.log('⏰ 执行倒计时逻辑');
      if (remainingTime.value > 0) {
        remainingTime.value--;
        console.log('   ⏳ 倒计时更新:', remainingTime.value);
      } else {
        console.log('🎉 倒计时结束');
        handleTimerComplete();
      }
    } else {
      console.log('⏰ 执行正计时逻辑');
      elapsedTime.value++;
      console.log('   ⏳ 正计时更新:', elapsedTime.value);
    }
    
  }, 1000);
  
  console.log('✅ 计时器已启动，interval ID:', timerInterval.value);
  console.log('====================================');
};

// 关键修复3：休息计时器逻辑
const startBreakTimer = () => {
  console.log('====================================');
  console.log('☕ startBreakTimer 函数调用');
  console.log('调用时状态:');
  console.log('   isRunning:', isRunning.value);
  console.log('   breakTimerInterval:', breakTimerInterval.value);
  console.log('   remainingBreakTime:', remainingBreakTime.value);
  
  // 清除已有休息计时器
  if (breakTimerInterval.value) {
    console.log('⏹️  清除已有休息计时器:', breakTimerInterval.value);
    clearInterval(breakTimerInterval.value);
    breakTimerInterval.value = null;
    console.log('   休息计时器已清除');
  }
  
  console.log('⏱️  调用 setInterval 启动休息计时器...');
  breakTimerInterval.value = setInterval(() => {
    console.log('☕ 休息计时器回调执行:');
    console.log('   - remainingBreakTime:', remainingBreakTime.value);
    
    // 更新剩余休息时间
    remainingBreakTime.value--;
    
    if (remainingBreakTime.value > 0) {
      console.log('⏳ 休息计时器更新:', remainingBreakTime.value);
    } else {
      console.log('🎉 休息计时器结束');
      endBreakMode();
    }
  }, 1000);
  
  console.log('✅ 休息计时器已启动，interval ID:', breakTimerInterval.value);
  console.log('====================================');
};

// 计时结束处理
const handleTimerComplete = () => {
  console.log('====================================');
  console.log('🎉 handleTimerComplete 函数调用');
  console.log('调用时状态:');
  console.log('   isRunning:', isRunning.value);
  console.log('   timerInterval:', timerInterval.value);
  
  // 停止计时器
  console.log('🔄 设置状态：isRunning = false');
  isRunning.value = false;
  
  // 清除计时器
  if (timerInterval.value) {
    console.log('⏹️  清除计时器:', timerInterval.value);
    clearInterval(timerInterval.value);
    timerInterval.value = null;
    console.log('   计时器已清除');
  }
  
  // 播放结束音效
  if (isSoundPlaying.value && selectedSound.value !== 'none') {
    console.log('🔊 播放结束音效');
    playNotificationSound();
  }
  
  // 自动进入休息模式
  const autoBreak = settingsStore.getSetting('autoBreakOnComplete', true);
  const breakDuration = settingsStore.getSetting('defaultBreakDuration', 5);
  
  console.log('🔧 自动休息设置:');
  console.log('   - autoBreak:', autoBreak);
  console.log('   - breakDuration:', breakDuration, '分钟');
  
  if (autoBreak) {
    console.log('⏳ 500ms后自动进入休息模式');
    setTimeout(() => {
      startBreakMode(breakDuration);
    }, 500);
  } else {
    console.log('💬 显示提示：专注时间结束！');
    alert('专注时间结束！');
  }
  
  console.log('✅ 计时结束处理完成');
  console.log('====================================');
};

// 通知音效
const playNotificationSound = () => {
  try {
    const audio = new Audio('/sounds/timer-complete.mp3');
    audio.volume = volume.value / 100;
    audio.play().catch(e => console.log('音效播放失败:', e));
  } catch (error) {
    console.error('播放通知音失败:', error);
  }
};

// 方法：切换计时器
const toggleTimer = () => {
  console.log('====================================');
  console.log('🔘 toggleTimer 按钮点击事件触发');
  console.log('当前状态:');
  console.log('   isBreakMode:', isBreakMode.value);
  console.log('   isRunning:', isRunning.value);
  console.log('   timerMode:', timerMode.value);
  console.log('   remainingTime:', remainingTime.value);
  console.log('   elapsedTime:', elapsedTime.value);
  console.log('   timerInterval:', timerInterval.value);
  console.log('   breakTimerInterval:', breakTimerInterval.value);
  
  if (isBreakMode.value) {
    console.log('⏸️  休息模式下调用 toggleTimer，调用 endBreakMode');
    endBreakMode();
    return;
  }
  
  if (isRunning.value) {
    console.log('⏸️  当前正在运行，调用 pauseTimer');
    pauseTimer();
  } else {
    console.log('▶️  当前未运行，准备启动计时器');
    
    // 确保在开始前重置状态
    if (timerMode.value === 'countdown' && remainingTime.value <= 0) {
      console.log('🔄 剩余时间为0，自动重置计时器');
      resetTimer();
      console.log('   重置后 remainingTime:', remainingTime.value);
    }
    
    console.log('▶️  调用 startTimer() 启动计时器');
    startTimer();
  }
  
  console.log('====================================');
};

// 方法：暂停计时
const pauseTimer = () => {
  console.log('====================================');
  console.log('⏸️  pauseTimer 函数调用');
  console.log('调用时状态:');
  console.log('   isRunning:', isRunning.value);
  console.log('   timerInterval:', timerInterval.value);
  
  // 设置状态为暂停
  console.log('🔄 设置状态：isRunning = false');
  isRunning.value = false;
  
  // 清除计时器
  if (timerInterval.value) {
    console.log('⏹️  清除计时器:', timerInterval.value);
    clearInterval(timerInterval.value);
    timerInterval.value = null;
    console.log('   计时器已清除');
  } else {
    console.log('⏹️  没有需要清除的计时器');
  }
  
  console.log('✅ 暂停操作完成');
  console.log('====================================');
};

// 方法：重置计时
const resetTimer = () => {
  console.log('====================================');
  console.log('🔄 resetTimer 函数调用');
  console.log('调用时状态:');
  console.log('   timerMode:', timerMode.value);
  console.log('   remainingTime:', remainingTime.value);
  console.log('   elapsedTime:', elapsedTime.value);
  console.log('   duration:', duration.value);
  
  // 先暂停计时器
  pauseTimer();
  
  // 根据模式重置时间
  if (timerMode.value === 'countdown') {
    console.log('🔄 重置倒计时：remainingTime =', duration.value);
    remainingTime.value = duration.value;
  } else {
    console.log('🔄 重置正计时：elapsedTime = 0');
    elapsedTime.value = 0;
  }
  
  console.log('✅ 重置完成后状态:');
  console.log('   - remainingTime:', remainingTime.value);
  console.log('   - elapsedTime:', elapsedTime.value);
  console.log('====================================');
};

// 方法：选择预设时长
const selectPreset = (preset) => {
  console.log('====================================');
  console.log('🎯 selectPreset 函数调用');
  console.log('选择的预设:', preset, '分钟');
  
  selectedPreset.value = preset;
  const newDuration = preset * 60;
  duration.value = newDuration;
  customMinutes.value = preset;
  
  console.log('🔄 更新时长:', newDuration, '秒');
  resetTimer();
  console.log('✅ 预设选择完成');
  console.log('====================================');
};

// 方法：更新自定义时长
const updateCustomDuration = () => {
  console.log('====================================');
  console.log('⏱️  updateCustomDuration 函数调用');
  console.log('输入的自定义时长:', customMinutes.value, '分钟');
  
  // 限制自定义时长范围
  if (customMinutes.value < 5) {
    console.log('⚠️  自定义时长小于最小值5，自动调整为5分钟');
    customMinutes.value = 5;
  }
  if (customMinutes.value > 180) {
    console.log('⚠️  自定义时长大于最大值180，自动调整为180分钟');
    customMinutes.value = 180;
  }
  
  const newDuration = customMinutes.value * 60;
  duration.value = newDuration;
  selectedPreset.value = 0;
  
  console.log('🔄 更新时长:', newDuration, '秒');
  resetTimer();
  console.log('✅ 自定义时长更新完成');
  console.log('====================================');
};

// 方法：开始休息模式
const startBreakMode = (minutes) => {
  console.log('====================================');
  console.log('☕ startBreakMode 函数调用');
  console.log('调用参数:');
  console.log('   休息时长:', minutes, '分钟');
  console.log('调用时状态:');
  console.log('   isBreakMode:', isBreakMode.value);
  console.log('   isRunning:', isRunning.value);
  
  // 确保专注计时器已停止
  console.log('⏸️  确保专注计时器已停止');
  pauseTimer();
  
  // 设置休息模式状态
  console.log('🔄 设置状态：isBreakMode = true');
  isBreakMode.value = true;
  console.log('🔄 设置状态：isRunning = true');
  isRunning.value = true;
  
  // 设置休息时长
  const breakSeconds = minutes * 60;
  console.log('🔄 设置休息时长:', breakSeconds, '秒');
  breakDuration.value = breakSeconds;
  console.log('🔄 设置剩余休息时间:', breakSeconds, '秒');
  remainingBreakTime.value = breakSeconds;
  
  // 启动休息计时器
  console.log('⏱️  调用 startBreakTimer() 启动休息计时器');
  startBreakTimer();
  
  // 显示状态提示
  showStatusMessage(`开始${minutes}分钟休息`);
  console.log('✅ 休息模式已启动');
  console.log('====================================');
};

// 方法：结束休息模式
const endBreakMode = () => {
  console.log('====================================');
  console.log('🛑 endBreakMode 函数调用');
  console.log('调用时状态:');
  console.log('   isBreakMode:', isBreakMode.value);
  console.log('   isRunning:', isRunning.value);
  console.log('   breakTimerInterval:', breakTimerInterval.value);
  
  // 停止休息计时器
  console.log('🔄 设置状态：isBreakMode = false');
  isBreakMode.value = false;
  console.log('🔄 设置状态：isRunning = false');
  isRunning.value = false;
  
  // 清除休息计时器
  if (breakTimerInterval.value) {
    console.log('⏹️  清除休息计时器:', breakTimerInterval.value);
    clearInterval(breakTimerInterval.value);
    breakTimerInterval.value = null;
    console.log('   休息计时器已清除');
  }
  
  // 保存休息记录
  console.log('💾 保存休息记录');
  saveBreakRecord();
  
  // 重置专注计时器状态
  console.log('🔄 重置专注计时器状态');
  resetTimer();
  
  // 确保状态正确，便于调试
  console.log('✅ 结束休息模式后状态:');
  console.log('   - isBreakMode:', isBreakMode.value);
  console.log('   - isRunning:', isRunning.value);
  console.log('   - timerMode:', timerMode.value);
  console.log('   - remainingTime:', remainingTime.value);
  console.log('   - elapsedTime:', elapsedTime.value);
  console.log('   - timerInterval:', timerInterval.value);
  console.log('   - breakTimerInterval:', breakTimerInterval.value);
  
  // 不弹出确认框，直接返回选择界面
  console.log('🏠 已返回专注模式选择界面');
  
  // 可选：添加一个短暂的状态提示
  showStatusMessage('休息结束，已返回专注模式');
  console.log('====================================');
};

// 方法：安排休息
const scheduleBreak = (minutes = 5) => {
  startBreakMode(minutes);
};

// 方法：保存专注记录
const saveFocusRecord = () => {
  let actualFocusTime;
  
  if (timerMode.value === 'countdown') {
    actualFocusTime = duration.value - remainingTime.value;
  } else {
    actualFocusTime = elapsedTime.value;
  }
  
  if (actualFocusTime > 60) { // 只保存超过1分钟的记录
    scheduleAPI.saveFocusRecord({
      task_title: currentTaskTitle.value, 
      duration: actualFocusTime, 
      start_time: new Date(Date.now() - actualFocusTime * 1000).toISOString(), 
      end_time: new Date().toISOString() 
    }).catch(console.error);
  }
};

// 方法：保存休息记录
const saveBreakRecord = () => {
  const breakTime = breakDuration.value - remainingBreakTime.value;
  if (breakTime > 30) { // 只保存超过30秒的休息
    scheduleAPI.saveBreakRecord({
      duration: breakTime, 
      start_time: new Date(Date.now() - breakTime * 1000).toISOString(), 
      end_time: new Date().toISOString() 
    }).catch(console.error);
  }
};

// 音频相关方法
const initAudioContext = () => {
  if (!audioContext.value) {
    audioContext.value = new (window.AudioContext || window.webkitAudioContext)();
  }
};

const playSound = async (soundId) => {
  // 停止当前播放的所有音效
  await stopAllSounds();
  
  initAudioContext();
  
  try {
    // 检查是否有本地音频文件
    if (localAudioFile.value) {
      console.log('🔊 加载本地音频:', localAudioFile.value.name);
      
      // 更新状态
      selectedSound.value = 'local';
      isSoundPlaying.value = true;
      
      // 加载本地音频文件
      const arrayBuffer = await localAudioFile.value.arrayBuffer();
      const audioBuffer = await audioContext.value.decodeAudioData(arrayBuffer);
      
      // 创建音频源
      const source = audioContext.value.createBufferSource();
      source.buffer = audioBuffer;
      source.loop = true;
      
      // 创建增益节点
      const gainNode = audioContext.value.createGain();
      gainNode.gain.value = globalVolume.value / 100; // 使用全局音量
      
      // 连接音频节点
      source.connect(gainNode);
      gainNode.connect(audioContext.value.destination);
      
      // 存储音频源和增益节点
      audioSources.value['local'] = source;
      gainNodes.value['local'] = gainNode;
      
      // 开始播放
      source.start();
      console.log('🔊 开始播放本地音频:', localAudioFile.value.name);
      return;
    }
    
    // 如果选择的是"暂无音效"且没有本地音频，直接返回
    if (soundId === 'none') {
      selectedSound.value = 'none';
      isSoundPlaying.value = false;
      return;
    }
    
    // 获取音效预设
    const preset = soundPresets.value.find(p => p.id === soundId);
    if (!preset || !preset.url) return;
    
    // 更新选中的音效
    selectedSound.value = soundId;
    preset.playing = true;
    isSoundPlaying.value = true;
    
    // 加载音频
    console.log('🔊 加载音效:', preset.name, 'URL:', preset.url);
    const response = await fetch(preset.url);
    const arrayBuffer = await response.arrayBuffer();
    const audioBuffer = await audioContext.value.decodeAudioData(arrayBuffer);
    
    // 创建音频源
    const source = audioContext.value.createBufferSource();
    source.buffer = audioBuffer;
    source.loop = true;
    
    // 创建增益节点
    const gainNode = audioContext.value.createGain();
    gainNode.gain.value = (preset.volume / 100) * (globalVolume.value / 100);
    
    // 连接音频节点
    source.connect(gainNode);
    gainNode.connect(audioContext.value.destination);
    
    // 存储音频源和增益节点
    audioSources.value[soundId] = source;
    gainNodes.value[soundId] = gainNode;
    
    // 开始播放
    source.start();
    console.log('🔊 开始播放音效:', preset.name);
  } catch (error) {
    console.error('播放音效失败:', error);
    alert('播放音效失败，请检查网络连接、音频URL或本地音频文件');
  }
};

const toggleSound = async () => {
  if (isSoundPlaying.value) {
    await stopAllSounds();
  } else {
    await playSound(selectedSound.value);
  }
};

const stopAllSounds = async () => {
  // 停止所有音频源
  Object.values(audioSources.value).forEach(source => {
    try {
      source.stop();
    } catch (error) {
      console.error('停止音效失败:', error);
    }
  });
  
  // 清空音频源和增益节点
  audioSources.value = {};
  gainNodes.value = {};
  
  // 更新状态
  isSoundPlaying.value = false;
  soundPresets.value.forEach(preset => {
    preset.playing = false;
  });
  
  console.log('🔇 停止所有音效');
};

const updateSoundVolume = (soundId, newVolume) => {
  // 更新预设的音量
  const preset = soundPresets.value.find(p => p.id === soundId);
  if (preset) {
    preset.volume = newVolume;
  }
  
  // 更新增益节点的音量
  const gainNode = gainNodes.value[soundId];
  if (gainNode) {
    gainNode.gain.value = (newVolume / 100) * (globalVolume.value / 100);
    console.log('🔊 更新音效音量:', soundId, '音量:', newVolume);
  }
};

const updateGlobalVolume = () => {
  // 更新所有增益节点的音量
  Object.entries(gainNodes.value).forEach(([soundId, gainNode]) => {
    if (soundId === 'local') {
      // 本地音频使用全局音量
      gainNode.gain.value = globalVolume.value / 100;
    } else {
      // 预设音效使用预设音量 + 全局音量
      const preset = soundPresets.value.find(p => p.id === soundId);
      if (preset) {
        gainNode.gain.value = (preset.volume / 100) * (globalVolume.value / 100);
      }
    }
  });
  
  console.log('🔊 更新全局音量:', globalVolume.value);
};

const toggleSoundPreset = async (soundId) => {
  console.log('🔘 切换音效预设:', soundId);
  
  // 如果当前已经在播放这个音效，停止播放
  if (selectedSound.value === soundId && isSoundPlaying.value) {
    await stopAllSounds();
    selectedSound.value = 'none';
  } else {
    // 否则播放选中的音效
    await playSound(soundId);
  }
};

const importLocalAudio = (event) => {
  const file = event.target.files[0];
  if (file) {
    if (file.size > 10 * 1024 * 1024) {
      alert('音频文件大小不能超过10MB');
      return;
    }
    
    if (!file.type.startsWith('audio/')) {
      alert('请选择音频文件');
      return;
    }
    
    // 停止当前播放的音效
    stopAllSounds();
    
    localAudioFile.value = file;
    selectedSound.value = 'local'; // 使用'local'标识本地音频
    isSoundPlaying.value = false;
    
    console.log('💾 本地音频导入成功:', file.name);
    alert(`音频导入成功: ${file.name}`);
    
    // 重置文件输入，允许重复选择同一文件
    event.target.value = '';
  }
};

const selectSoundPreset = async (soundId) => {
  await toggleSoundPreset(soundId);
};

// 添加状态提示方法
const showStatusMessage = (message) => {
  // 可以在这里实现一个非阻塞的状态提示
  const statusEl = document.createElement('div');
  statusEl.className = 'status-message';
  statusEl.textContent = message;
  statusEl.style.cssText = ` 
    position: fixed;
    top: 20px;
    right: 20px;
    background: #4CAF50;
    color: white;
    padding: 10px 20px;
    border-radius: 5px;
    z-index: 10000;
    animation: fadeInOut 3s ease-in-out;
  `;
  
  document.body.appendChild(statusEl);
  
  setTimeout(() => {
    if (statusEl.parentNode) {
      statusEl.parentNode.removeChild(statusEl);
    }
  }, 3000);
};

// 添加组件初始化方法
const initTimerState = () => {
  console.log('====================================');
  console.log('🔄 initTimerState 函数调用');
  console.log('初始化前状态:');
  console.log('   isRunning:', isRunning.value);
  console.log('   isBreakMode:', isBreakMode.value);
  console.log('   remainingTime:', remainingTime.value);
  console.log('   elapsedTime:', elapsedTime.value);
  console.log('   remainingBreakTime:', remainingBreakTime.value);
  
  // 重置所有状态
  console.log('🔄 重置所有状态:');
  console.log('   - isRunning = false');
  isRunning.value = false;
  console.log('   - isBreakMode = false');
  isBreakMode.value = false;
  console.log('   - remainingTime =', duration.value);
  remainingTime.value = duration.value;
  console.log('   - elapsedTime = 0');
  elapsedTime.value = 0;
  console.log('   - remainingBreakTime = 0');
  remainingBreakTime.value = 0;
  
  // 清除所有计时器
  if (timerInterval.value) {
    console.log('⏹️  清除计时器:', timerInterval.value);
    clearInterval(timerInterval.value);
    timerInterval.value = null;
    console.log('   计时器已清除');
  }
  
  if (breakTimerInterval.value) {
    console.log('⏹️  清除休息计时器:', breakTimerInterval.value);
    clearInterval(breakTimerInterval.value);
    breakTimerInterval.value = null;
    console.log('   休息计时器已清除');
  }
  
  console.log('✅ 初始化完成后状态:');
  console.log('   - isRunning:', isRunning.value);
  console.log('   - isBreakMode:', isBreakMode.value);
  console.log('   - remainingTime:', remainingTime.value);
  console.log('   - elapsedTime:', elapsedTime.value);
  console.log('====================================');
};

// 专注模式控制
const startFocusMode = () => {
  console.log('====================================');
  console.log('🚀 startFocusMode 函数调用');
  console.log('调用时状态:');
  console.log('   isFocusModeActive:', isFocusModeActive.value);
  console.log('   showStartConfirm:', showStartConfirm.value);
  
  // 设置状态
  console.log('🔄 设置状态：isFocusModeActive = true');
  isFocusModeActive.value = true;
  console.log('🔄 设置状态：showStartConfirm = false');
  showStartConfirm.value = false;
  console.log('🔄 设置状态：isBreakMode = false');
  isBreakMode.value = false;
  
  // 重置计时器
  console.log('🔄 重置计时器');
  resetTimer();
  
  // 获取专注历史
  console.log('📊 获取专注历史记录');
  fetchFocusHistory();
  
  console.log('✅ 专注模式已启动');
  console.log('====================================');
};

const exitFocusMode = () => {
  console.log('====================================');
  console.log('🚪 exitFocusMode 函数调用');
  console.log('调用时状态:');
  console.log('   isFocusModeActive:', isFocusModeActive.value);
  console.log('   isBreakMode:', isBreakMode.value);
  console.log('   isRunning:', isRunning.value);
  
  // 停止所有计时器
  console.log('⏹️  停止所有计时器');
  pauseTimer();
  
  if (breakTimerInterval.value) {
    console.log('⏹️  清除休息计时器:', breakTimerInterval.value);
    clearInterval(breakTimerInterval.value);
    breakTimerInterval.value = null;
    console.log('   休息计时器已清除');
  }
  
  // 保存当前记录
  console.log('💾 保存当前记录');
  if (!isBreakMode.value) {
    console.log('   保存专注记录');
    saveFocusRecord();
  } else {
    console.log('   保存休息记录');
    saveBreakRecord();
  }
  
  // 重置状态
  console.log('🔄 重置所有状态');
  initTimerState();
  
  // 退出专注模式
  console.log('🔄 设置状态：isFocusModeActive = false');
  isFocusModeActive.value = false;
  
  console.log('✅ 专注模式已退出');
  console.log('====================================');
};

const fetchFocusHistory = async () => {
  try {
    const response = await scheduleAPI.getFocusHistory();
    focusHistory.value = response.focus_history || [];
  } catch (error) {
    console.error('获取专注历史失败:', error);
    focusHistory.value = [];
  }
};

// 组件暴露方法
defineExpose({
  openFocusMode: (taskInfo = null) => {
    if (taskInfo?.title) {
      currentTaskTitle.value = taskInfo.title;
    } else {
      currentTaskTitle.value = '专注学习';
    }
    showStartConfirm.value = true;
  }
});

// 组件生命周期
onMounted(() => {
  // 预加载通知音
  const notificationAudio = new Audio('/sounds/timer-complete.mp3');
  notificationAudio.preload = 'auto';
});

onUnmounted(() => {
  // 彻底清理所有资源
  pauseTimer();
  if (breakTimerInterval.value) {
    clearInterval(breakTimerInterval.value);
  }
  stopAllSounds();
});

// 监听音量变化
watch(globalVolume, (newVal) => {
  console.log('🔊 全局音量变化:', newVal);
  updateGlobalVolume();
});

// 添加对timerMode变化的监听，便于调试
watch(timerMode, (newMode, oldMode) => {
  console.log('🔄 计时模式变化:', oldMode, '→', newMode);
  console.log('   重置计时器以应用新模式');
  resetTimer();
});

// 添加对isBreakMode变化的监听，便于调试
watch(isBreakMode, (newVal, oldVal) => {
  console.log('🔄 休息模式状态变化:', oldVal, '→', newVal);
});

// 添加对isRunning变化的监听，便于调试
watch(isRunning, (newVal, oldVal) => {
  console.log('🔄 运行状态变化:', oldVal, '→', newVal);
});
</script>

<style scoped>
/* 添加状态提示的动画 */
@keyframes fadeInOut {
  0% { opacity: 0; transform: translateY(-20px); }
  10% { opacity: 1; transform: translateY(0); }
  90% { opacity: 1; transform: translateY(0); }
  100% { opacity: 0; transform: translateY(-20px); }
}

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
  max-height: 80vh;
  overflow-y: auto;
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

.action-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  background-color: rgba(255, 255, 255, 0.1);
  border-color: rgba(255, 255, 255, 0.2);
  color: rgba(255, 255, 255, 0.5);
}

.action-btn:disabled:hover {
  background-color: rgba(255, 255, 255, 0.1);
  color: rgba(255, 255, 255, 0.5);
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
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
}

.sound-presets .preset-btn.active {
  background-color: var(--primary-color);
  border-color: var(--primary-color);
}

.sound-icon {
  font-size: 1.2rem;
}

.sound-name {
  flex: 1;
}

.sound-indicator {
  font-size: 0.8rem;
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

/* 单独音量控制样式 */
.individual-volume-controls {
  margin-top: 1rem;
  padding-top: 1rem;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
}

.individual-volume-controls h4 {
  margin: 0 0 0.5rem 0;
  font-size: 1rem;
  color: #ffffff;
}

.individual-volume {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  color: rgba(255, 255, 255, 0.8);
  font-size: 0.9rem;
}

.individual-volume input[type="range"] {
  flex: 1;
  max-width: 150px;
  -webkit-appearance: none;
  appearance: none;
  height: 5px;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 5px;
  outline: none;
}

.individual-volume input[type="range"]::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 12px;
  height: 12px;
  background: var(--primary-color);
  border-radius: 50%;
  cursor: pointer;
  transition: background-color 0.3s ease;
}

.individual-volume input[type="range"]::-webkit-slider-thumb:hover {
  background: var(--primary-dark);
}

.individual-volume span:last-child {
  width: 35px;
  text-align: right;
  font-size: 0.8rem;
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