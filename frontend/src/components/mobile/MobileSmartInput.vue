<template>
  <div class="mobile-smart-input">
    <!-- 标题 -->
    <h2 class="input-title">智能输入</h2>
    
    <!-- 工具栏 -->
    <div class="input-toolbar">
      <button 
        class="tool-btn" 
        :class="{ active: isVoiceInputActive }"
        @click="toggleVoiceInput"
      >
        <div class="voice-icon-container">
          <img v-if="!isVoiceInputActive" src="/svg/microphone.svg" alt="语音" class="icon" />
          <svg v-else class="icon" width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
            <path d="M12 14c1.66 0 2.99-1.34 2.99-3L15 5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3zm5.3-3c0 3-2.54 5.1-5.3 5.1S6.7 14 6.7 11H5c0 3.41 2.72 6.23 6 6.72V21h2v-3.28c3.28-.48 6-3.3 6-6.72h-1.7z"></path>
          </svg>
        </div>
        <span class="tool-btn-text">{{ isVoiceInputActive ? '停止' : '语音' }}</span>
      </button>
      <button class="tool-btn" @click="triggerFileInput">
        <img src="/svg/image.svg" alt="图片" class="icon" />
        <span class="tool-btn-text">图片</span>
      </button>
      <input 
        ref="fileInput" 
        type="file" 
        accept="image/*" 
        style="display: none" 
        @change="handleImageUpload"
      />
      <button class="tool-btn" @click="checkClipboard">
        <img src="/svg/paste.svg" alt="粘贴" class="icon" />
        <span class="tool-btn-text">粘贴</span>
      </button>
    </div>
    
    <!-- 输入区域 -->
    <div 
      class="input-area"
      @dragover.prevent
      @drop="handleDrop"
      @dragenter.prevent
      @dragleave.prevent
    >
      <div v-if="isDragging" class="drag-overlay">
        <p>释放图片以上传</p>
      </div>
      <textarea
        v-model="inputText"
        placeholder="输入任务描述，例如：'明天下午3点交数学作业'"
        rows="6"
        @input="handleInput"
        @paste="handlePaste"
      ></textarea>
    </div>
    
    <!-- 输入统计和提交按钮 -->
    <div class="input-footer">
      <div class="input-stats">
        <span>{{ inputText.length }} 字符</span>
      </div>
      <button 
        class="submit-btn" 
        @click="submitInput" 
        :disabled="!inputText.trim()"
      >
        提交
      </button>
    </div>
    
    <!-- 语音识别状态提示 -->
    <div v-if="isVoiceInputActive" class="voice-status">
      <div class="voice-indicator">
        <div class="pulse"></div>
        <div class="pulse"></div>
        <div class="pulse"></div>
      </div>
      <p>正在识别语音...</p>
    </div>
    
    <!-- 解析状态 -->
    <div v-if="isParsing" class="parse-status">
      <div class="loading-indicator">
        <div class="pulse"></div>
        <div class="pulse"></div>
        <div class="pulse"></div>
      </div>
      <p>正在解析，请稍候...</p>
    </div>
    
    <!-- 解析结果预览 -->
    <div v-else-if="parsedResult" class="parse-preview">
      <h3>解析结果</h3>
      
      <!-- 任务列表预览 -->
      <div v-if="parsedResult.tasks && parsedResult.tasks.length > 0" class="preview-section">
        <h4>任务 ({{ parsedResult.tasks.length }})</h4>
        <div class="preview-list">
          <div v-for="(task, index) in parsedResult.tasks" :key="index" class="preview-item">
            <div class="preview-item-header">
              <span class="preview-item-title">{{ task.name }}</span>
            </div>
            <div class="preview-item-details">
              <span class="preview-item-detail">截止: {{ task.deadline || '无' }}</span>
              <span class="preview-item-detail">耗时: {{ task.estimated_time || 0 }} 分钟</span>
            </div>
          </div>
        </div>
      </div>
      
      <!-- 条目列表预览 -->
      <div v-if="parsedResult.entries && parsedResult.entries.length > 0" class="preview-section">
        <h4>日程 ({{ parsedResult.entries.length }})</h4>
        <div class="preview-list">
          <div v-for="(entry, index) in parsedResult.entries" :key="index" class="preview-item">
            <div class="preview-item-header">
              <span class="preview-item-title">{{ entry.title }}</span>
              <span class="preview-item-type">{{ entry.entry_type }}</span>
            </div>
            <div class="preview-item-details">
              <span class="preview-item-detail">开始: {{ entry.start_time || '无' }}</span>
              <span class="preview-item-detail">结束: {{ entry.end_time || '无' }}</span>
            </div>
          </div>
        </div>
      </div>
      
      <!-- 操作按钮 -->
      <div class="parse-actions">
        <button @click="confirmParse" class="confirm-btn">确认创建</button>
        <button @click="clearParse" class="clear-btn">重新解析</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { llmAPI, tasksAPI, entriesAPI } from '../../services/api'
import { useUserStore, useClipboardStore } from '../../store'

const inputText = ref('')
const isVoiceInputActive = ref(false)
const isDragging = ref(false)
const fileInput = ref(null)
const parsedResult = ref(null)
const isParsing = ref(false)
const userStore = useUserStore()
const clipboardStore = useClipboardStore()
let recognition = null
let lastClipboardText = ''

// 初始化语音识别
const initVoiceRecognition = () => {
  if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
    recognition = new SpeechRecognition()
    recognition.continuous = true
    recognition.interimResults = true
    recognition.lang = 'zh-CN'
    
    recognition.onresult = (event) => {
      let interimTranscript = ''
      let finalTranscript = ''
      
      for (let i = event.resultIndex; i < event.results.length; i++) {
        const transcript = event.results[i][0].transcript
        if (event.results[i].isFinal) {
          finalTranscript += transcript
        } else {
          interimTranscript += transcript
        }
      }
      
      inputText.value = finalTranscript + interimTranscript
    }
    
    recognition.onerror = (event) => {
      console.error('语音识别错误:', event.error)
      isVoiceInputActive.value = false
    }
    
    recognition.onend = () => {
      isVoiceInputActive.value = false
    }
  }
}

// 切换语音输入
const toggleVoiceInput = () => {
  if (!recognition) {
    initVoiceRecognition()
  }
  
  if (isVoiceInputActive.value) {
    recognition.stop()
    isVoiceInputActive.value = false
  } else {
    recognition.start()
    isVoiceInputActive.value = true
  }
}

// 触发文件选择
const triggerFileInput = () => {
  fileInput.value.click()
}

// 处理图片上传
const handleImageUpload = async (event) => {
  const file = event.target.files[0]
  if (file) {
    await processImageFile(file)
    event.target.value = ''
  }
}

// 处理粘贴事件
const handlePaste = async (event) => {
  const items = event.clipboardData.items
  for (let i = 0; i < items.length; i++) {
    if (items[i].type.indexOf('image') !== -1) {
      const file = items[i].getAsFile()
      await processImageFile(file)
      break
    }
  }
}

// 处理拖拽释放
const handleDrop = async (event) => {
  event.preventDefault()
  isDragging.value = false
  
  const files = event.dataTransfer.files
  for (let i = 0; i < files.length; i++) {
    if (files[i].type.indexOf('image') !== -1) {
      await processImageFile(files[i])
      break
    }
  }
}

// 处理图片文件
const processImageFile = async (file) => {
  if (!file) return
  
  isParsing.value = true
  try {
    const formData = new FormData()
    formData.append('image', file)
    
    const response = await llmAPI.parseImage(formData)
    
    if (response && response.text) {
      inputText.value = response.text
    }
  } catch (error) {
    console.error('图片识别失败:', error)
    alert('图片识别失败，请重试')
  } finally {
    isParsing.value = false
  }
}

// 处理输入变化
const handleInput = () => {
  // 仅记录输入变化，不自动调用LLM
  console.log('输入变化:', inputText.value)
}

// 使用LLM解析文本
const parseWithLLM = async () => {
  isParsing.value = true
  try {
    const response = await llmAPI.parseText({ text: inputText.value })
    if (response && response.result) {
      parsedResult.value = JSON.parse(response.result)
    }
  } catch (error) {
    console.error('LLM解析错误:', error)
    alert('解析失败，请重试')
  } finally {
    isParsing.value = false
  }
}

// 检查剪切板
const checkClipboard = async () => {
  try {
    const text = await navigator.clipboard.readText()
    if (text) {
      inputText.value = text
      await parseWithLLM()
      lastClipboardText = text
    } else {
      alert('剪切板为空')
    }
  } catch (err) {
    console.error('读取剪切板失败:', err)
    alert('读取剪切板失败，请手动粘贴')
  }
}

// 提交输入
const submitInput = async () => {
  if (inputText.value.trim()) {
    await parseWithLLM()
  }
}

// 确认解析结果
const confirmParse = async () => {
  try {
    // 处理日期格式
    const parseDateString = (dateStr) => {
      if (!dateStr) return null;
      const isoDateStr = dateStr.replace(' ', 'T');
      if (isoDateStr.length === 16) {
        return isoDateStr + ':00';
      }
      return isoDateStr;
    };
    
    let taskCount = 0;
    let entryCount = 0;
    
    // 处理任务
    if (parsedResult.value.tasks && Array.isArray(parsedResult.value.tasks)) {
      for (const task of parsedResult.value.tasks) {
        if (task.deadline) {
          const taskData = {
            title: task.name,
            description: '',
            task_type: 'homework',
            deadline: parseDateString(task.deadline),
            estimated_time: task.estimated_time || 0,
            priority: 'medium',
            completed: false
          }
          await tasksAPI.addTask(taskData)
          taskCount++
        }
      }
    }
    
    // 处理日程
    if (parsedResult.value.entries && Array.isArray(parsedResult.value.entries)) {
      for (const entry of parsedResult.value.entries) {
        const entryData = {
          title: entry.title,
          description: '',
          entry_type: entry.entry_type || 'meeting',
          start_time: parseDateString(entry.start_time),
          end_time: parseDateString(entry.end_time)
        }
        await entriesAPI.addEntry(entryData)
        entryCount++
      }
    }
    
    alert(`创建成功！\n任务: ${taskCount}个，日程: ${entryCount}个`)
    
    // 清空输入和结果
    inputText.value = ''
    parsedResult.value = null
  } catch (error) {
    console.error('创建失败:', error)
    alert('创建失败，请重试')
  }
}

// 清除解析结果
const clearParse = () => {
  parsedResult.value = null
}

// 初始化语音识别
onMounted(() => {
  initVoiceRecognition()
})
</script>

<style scoped>/* 基础样式 */
.mobile-smart-input {
  padding: 0;
  background-color: var(--bg-primary);
  color: var(--text-primary);
  min-height: calc(100vh - 60px);
}
.input-title {
  margin: 0 0 16px 0;
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
}

.input-toolbar {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
}

.tool-btn {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 12px 8px;
  background-color: #f5f5f5;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
  min-height: 60px;
}

.tool-btn:hover {
  background-color: #e8e8e8;
}

.tool-btn.active {
  background-color: var(--primary-color);
  color: white;
}

.icon {
  width: 24px;
  height: 24px;
  margin-bottom: 4px;
}

.tool-btn-text {
  font-size: 12px;
  font-weight: 500;
}

.input-area {
  margin-bottom: 16px;
  position: relative;
}

.input-area textarea {
  width: 100%;
  padding: 16px;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  font-size: 15px;
  font-family: inherit;
  resize: vertical;
  min-height: 150px;
  line-height: 1.5;
  box-sizing: border-box;
}

.input-area textarea:focus {
  outline: none;
  border-color: var(--primary-color);
  box-shadow: 0 0 0 2px rgba(var(--primary-color-rgb), 0.2);
}

.drag-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(var(--primary-color-rgb), 0.7);
  color: white;
  display: flex;
  justify-content: center;
  align-items: center;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 500;
  z-index: 10;
  pointer-events: none;
  animation: pulse 1.5s infinite;
}

@keyframes pulse {
  0%, 100% {
    opacity: 0.7;
  }
  50% {
    opacity: 0.9;
  }
}

.input-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-top: 12px;
  border-top: 1px solid #e0e0e0;
}

.input-stats {
  font-size: 13px;
  color: var(--text-secondary);
}

.submit-btn {
  padding: 10px 24px;
  border: none;
  border-radius: 8px;
  background-color: var(--primary-color);
  color: white;
  font-size: 15px;
  font-weight: 500;
  cursor: pointer;
  transition: background-color 0.3s ease;
}

.submit-btn:hover:not(:disabled) {
  background-color: var(--primary-dark);
}

.submit-btn:disabled {
  background-color: #cccccc;
  cursor: not-allowed;
}

.voice-status,
.parse-status {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  background-color: var(--primary-light);
  border-radius: 8px;
  margin-bottom: 16px;
}

.voice-indicator,
.loading-indicator {
  display: flex;
  gap: 6px;
  align-items: center;
}

.pulse {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background-color: var(--primary-color);
  animation: pulse 1.5s infinite;
}

.pulse:nth-child(2) {
  animation-delay: 0.2s;
}

.pulse:nth-child(3) {
  animation-delay: 0.4s;
}

.voice-status p,
.parse-status p {
  margin: 0;
  font-size: 14px;
  color: var(--primary-dark);
}

.parse-preview {
  background-color: #f9f9f9;
  border-radius: 8px;
  padding: 16px;
  margin-top: 16px;
}

.parse-preview h3 {
  margin: 0 0 16px 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
}

.parse-preview h4 {
  margin: 16px 0 12px 0;
  font-size: 15px;
  font-weight: 500;
  color: var(--text-primary);
}

.preview-section {
  background-color: white;
  border-radius: 6px;
  padding: 12px;
  margin-bottom: 16px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.preview-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.preview-item {
  background-color: #f5f5f5;
  border-radius: 6px;
  padding: 12px;
  border-left: 3px solid var(--primary-color);
}

.preview-item-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 8px;
}

.preview-item-title {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary);
  flex: 1;
}

.preview-item-type {
  font-size: 11px;
  color: white;
  background-color: var(--primary-color);
  padding: 4px 8px;
  border-radius: 12px;
  margin-left: 8px;
}

.preview-item-details {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.preview-item-detail {
  font-size: 13px;
  color: var(--text-secondary);
  display: flex;
  align-items: center;
}

.preview-item-detail::before {
  content: "•";
  margin-right: 6px;
  color: var(--primary-color);
}

.parse-actions {
  display: flex;
  gap: 12px;
  margin-top: 20px;
}

.confirm-btn,
.clear-btn {
  flex: 1;
  padding: 12px;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
}

.confirm-btn {
  background-color: var(--primary-color);
  color: white;
}

.confirm-btn:hover {
  background-color: var(--primary-dark);
}

.clear-btn {
  background-color: white;
  border: 1px solid #e0e0e0;
  color: var(--text-primary);
}

.clear-btn:hover {
  background-color: #f5f5f5;
}
</style>