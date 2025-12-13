<template>
  <div>
    <div class="input-header">
      <h2 class="input-title">智能输入</h2>
      <div class="input-toolbar">
        <button @click="toggleVoiceInput" :class="['tool-btn', { active: isVoiceInputActive }]">
          <span v-if="!isVoiceInputActive">🎤 语音</span>
          <span v-else>⏹️ 停止</span>
        </button>
        <button @click="triggerFileInput" class="tool-btn">
          📷 图片
        </button>
        <input 
          ref="fileInput" 
          type="file" 
          accept="image/*" 
          style="display: none" 
          @change="handleImageUpload"
        />
        <button @click="checkClipboard" class="tool-btn">
          📋 粘贴
        </button>
      </div>
    </div>
    
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
        placeholder="输入任务描述，例如：'明天下午3点交数学作业'.支持拖拽图片上传或从剪切板粘贴图片"
        rows="4"
        @input="handleInput"
        @paste="handlePaste"
      ></textarea>
    </div>
    
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
      <h3>解析结果预览</h3>
      
      <!-- 任务列表预览 -->
      <div v-if="parsedResult.tasks && parsedResult.tasks.length > 0" class="preview-section">
        <h4>识别到的任务 ({{ parsedResult.tasks.length }})</h4>
        <div class="preview-list">
          <div v-for="(task, index) in parsedResult.tasks" :key="index" class="preview-item">
            <div class="preview-item-header">
              <span class="preview-item-title">{{ task.name }}</span>
            </div>
            <div class="preview-item-details">
              <span class="preview-item-detail">截止时间: {{ task.deadline || '无' }}</span>
              <span class="preview-item-detail">预估耗时: {{ task.estimated_time || 0 }} 分钟</span>
            </div>
          </div>
        </div>
      </div>
      
      <!-- 条目列表预览 -->
      <div v-if="parsedResult.entries && parsedResult.entries.length > 0" class="preview-section">
        <h4>识别到的日程 ({{ parsedResult.entries.length }})</h4>
        <div class="preview-list">
          <div v-for="(entry, index) in parsedResult.entries" :key="index" class="preview-item">
            <div class="preview-item-header">
              <span class="preview-item-title">{{ entry.title }}</span>
              <span class="preview-item-type">{{ entry.entry_type }}</span>
            </div>
            <div class="preview-item-details">
              <span class="preview-item-detail">开始时间: {{ entry.start_time || '无' }}</span>
              <span class="preview-item-detail">结束时间: {{ entry.end_time || '无' }}</span>
            </div>
          </div>
        </div>
      </div>
      
      <div class="parse-actions">
        <button @click="confirmParse" class="confirm-btn">确认并创建</button>
        <button @click="clearParse" class="clear-btn">重新解析</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { llmAPI, tasksAPI, entriesAPI } from '../services/api'
import { useUserStore, useClipboardStore } from '../store'

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
  } else {
    alert('您的浏览器不支持语音识别功能')
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
    // 清空文件输入，允许用户重新选择同一文件
    event.target.value = ''
  }
}

// 处理粘贴事件（支持图片）
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

// 处理拖拽进入事件
const handleDragEnter = (event) => {
  event.preventDefault()
  isDragging.value = true
}

// 处理拖拽离开事件
const handleDragLeave = (event) => {
  event.preventDefault()
  isDragging.value = false
}

// 处理拖拽释放事件
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
  
  console.log('处理图片:', file.name)
  isParsing.value = true
  try {
    // 创建FormData对象，用于上传图片
    const formData = new FormData()
    formData.append('image', file)
    
    // 调用OCR API识别图片内容
    const response = await llmAPI.parseImage(formData)
    console.log('OCR识别结果:', response)
    
    if (response && response.text) {
      // 将识别结果填充到输入框
      inputText.value = response.text
      // 不自动调用LLM，等待用户点击提交按钮
      console.log('OCR识别结果已填充到输入框，等待用户提交')
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

// 使用大语言模型解析文本
const parseWithLLM = async () => {
  isParsing.value = true
  try {
    const response = await llmAPI.parseText({ text: inputText.value })
    console.log('LLM解析结果:', response)
    if (response && response.result) {
      // 解析LLM返回的JSON字符串
      parsedResult.value = JSON.parse(response.result)
    }
  } catch (error) {
    console.error('LLM解析错误:', error)
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
      // 使用LLM解析剪切板内容
      await parseWithLLM()
      // 更新最后一次剪切板内容
      lastClipboardText = text
    } else {
      alert('剪切板为空')
    }
  } catch (err) {
    console.error('读取剪切板失败:', err)
    alert('读取剪切板失败，请手动粘贴')
  }
}

// 组件挂载时，初始化语音识别
onMounted(() => {
  // 初始化语音识别
  initVoiceRecognition()
})

// 提交输入
const submitInput = async () => {
  if (inputText.value.trim()) {
    console.log('提交输入:', inputText.value)
    // 调用LLM进行解析
    await parseWithLLM()
  }
}

// 确认解析结果
const confirmParse = async () => {
  console.log('确认解析结果:', parsedResult.value)
  try {
    // 处理空间分隔的日期格式 (YYYY-MM-DD HH:MM) 转换为本地时间格式 (YYYY-MM-DDTHH:MM:SS)
    const parseDateString = (dateStr) => {
      if (!dateStr) return null;
      // 替换空格为 'T' 以符合 ISO 格式
      const isoDateStr = dateStr.replace(' ', 'T');
      // 如果没有秒，添加秒
      if (isoDateStr.length === 16) { // 格式为 YYYY-MM-DDTHH:MM
        return isoDateStr + ':00';
      }
      return isoDateStr;
    };
    
    let taskCount = 0;
    let entryCount = 0;
    
    console.log('检查parsedResult结构:', {
      hasTasks: !!parsedResult.value.tasks,
      hasEntries: !!parsedResult.value.entries,
      tasksType: typeof parsedResult.value.tasks,
      entriesType: typeof parsedResult.value.entries,
      tasksLength: parsedResult.value.tasks ? parsedResult.value.tasks.length : 0,
      entriesLength: parsedResult.value.entries ? parsedResult.value.entries.length : 0
    });
    
    // 处理任务数组
    if (parsedResult.value.tasks && Array.isArray(parsedResult.value.tasks) && parsedResult.value.tasks.length > 0) {
      console.log('开始处理任务数组，共', parsedResult.value.tasks.length, '个任务')
      for (const task of parsedResult.value.tasks) {
        console.log('处理任务:', task)
        // 检查任务是否有截止日期，因为Task模型的deadline字段是必填的
        if (!task.deadline) {
          console.warn('任务缺少截止日期，跳过创建:', task)
          continue;
        }
        
        // 准备任务数据
        const taskData = {
          title: task.name,
          description: '',
          task_type: 'homework',
          deadline: parseDateString(task.deadline),
          estimated_time: task.estimated_time || 0,
          priority: 'medium',
          completed: false
        }
        
        console.log('发送任务创建请求:', taskData)
        // 调用API创建任务
        try {
          const response = await tasksAPI.addTask(taskData)
          console.log('任务创建成功:', response)
          taskCount++;
        } catch (error) {
          console.error('任务创建失败:', error)
          console.error('错误详情:', error.response ? error.response.data : error.message)
        }
      }
    } else {
      console.log('没有任务需要处理或任务不是有效数组')
    }
    
    // 处理条目数组
    if (parsedResult.value.entries && Array.isArray(parsedResult.value.entries) && parsedResult.value.entries.length > 0) {
      console.log('开始处理条目数组，共', parsedResult.value.entries.length, '个条目')
      for (const entry of parsedResult.value.entries) {
        console.log('处理条目:', entry)
        // 准备条目数据
        const entryData = {
          title: entry.title,
          description: '',
          entry_type: entry.entry_type || 'meeting',
          start_time: parseDateString(entry.start_time),
          end_time: parseDateString(entry.end_time)
        }
        
        console.log('发送条目创建请求:', entryData)
        // 调用API创建条目
        try {
          const response = await entriesAPI.addEntry(entryData)
          console.log('条目创建成功:', response)
          entryCount++;
        } catch (error) {
          console.error('条目创建失败:', error)
          console.error('错误详情:', error.response ? error.response.data : error.message)
        }
      }
    } else {
      console.log('没有条目需要处理或条目不是有效数组')
    }
    
    // 显示成功提示
    alert(`解析成功！\n已创建 ${taskCount} 个任务和 ${entryCount} 个条目。`)
    
    // 清空输入和解析结果
    inputText.value = ''
    parsedResult.value = null
  } catch (error) {
    console.error('创建失败:', error)
    console.error('错误详情:', error.response ? error.response.data : error.message)
    console.error('错误堆栈:', error.stack)
    alert(`创建失败，请重试\n错误信息: ${error.message}`)
  }
}

// 清除解析结果
const clearParse = () => {
  parsedResult.value = null
}
</script>

<style scoped>
.input-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.input-title {
  margin: 0;
  font-size: 1.25rem;
  color: #333;
  font-weight: 500;
}

.input-toolbar {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.tool-btn {
  padding: 0.5rem 0.75rem;
  border: 1px solid #e0e0e0;
  border-radius: 4px;
  background-color: white;
  cursor: pointer;
  transition: all 0.3s ease;
  font-size: 0.875rem;
}

.tool-btn:hover {
  background-color: #f5f5f5;
}

.tool-btn.active {
  background-color: var(--primary-color);
  color: white;
  border-color: var(--primary-color);
}

.input-area {
  margin-bottom: 1rem;
  flex: 1;
  display: flex;
  flex-direction: column;
  position: relative;
}

.input-area textarea {
  width: 100%;
  padding: 1rem;
  border: 1px solid #e0e0e0;
  border-radius: 4px;
  font-size: 1.1rem;
  resize: vertical;
  font-family: inherit;
  min-height: 400px;
  max-height: none;
  height: 100%;
  line-height: 1.5;
  flex: 1;
}

.input-area textarea:focus {
  outline: none;
  border-color: var(--primary-color);
  box-shadow: 0 0 0 2px rgba(var(--primary-color-rgb), 0.2);
}

/* 拖拽样式 */
.input-area {
  position: relative;
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
  border-radius: 4px;
  font-size: 1.5rem;
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
  margin-top: auto;
  padding-top: 1rem;
  border-top: 1px solid #e0e0e0;
}

.input-stats {
  font-size: 0.95rem;
  color: #666;
}

.submit-btn {
  padding: 0.625rem 1.75rem;
  border: none;
  border-radius: 4px;
  background-color: var(--primary-color);
  color: white;
  cursor: pointer;
  transition: all 0.3s ease;
  font-size: 1.1rem;
}

.submit-btn:hover:not(:disabled) {
  background-color: var(--primary-dark);
}

.submit-btn:disabled {
  background-color: #cccccc;
  cursor: not-allowed;
}

.voice-status {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-top: 1rem;
  padding: 0.875rem;
  background-color: var(--primary-light);
  border-radius: 4px;
  color: var(--primary-dark);
  font-size: 1rem;
}

.voice-indicator {
  display: flex;
  gap: 0.5rem;
  align-items: center;
}

.pulse {
  width: 10px;
  height: 10px;
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

@keyframes pulse {
  0%, 100% {
    transform: scale(1);
    opacity: 1;
  }
  50% {
    transform: scale(1.5);
    opacity: 0.5;
  }
}

.parse-preview {
  margin-top: 1.5rem;
  padding: 1.25rem;
  background-color: #f5f5f5;
  border-radius: 8px;
}

.parse-preview h3 {
  margin-bottom: 1rem;
  font-size: 1.25rem;
  color: #333;
}

.parse-preview h4 {
  margin: 1rem 0 0.75rem 0;
  font-size: 1.1rem;
  color: #444;
}

.preview-section {
  margin-bottom: 1.5rem;
  padding: 1rem;
  background-color: white;
  border-radius: 6px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.preview-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.preview-item {
  padding: 0.75rem;
  background-color: #f9f9f9;
  border-radius: 4px;
  border-left: 3px solid var(--primary-color);
}

.preview-item-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
}

.preview-item-title {
  font-weight: 500;
  color: #333;
  font-size: 1rem;
}

.preview-item-type {
  font-size: 0.8rem;
  color: white;
  background-color: var(--primary-color);
  padding: 0.25rem 0.5rem;
  border-radius: 12px;
}

.preview-item-details {
  display: flex;
  flex-wrap: wrap;
  gap: 1rem;
  font-size: 0.9rem;
  color: #666;
}

.preview-item-detail {
  display: flex;
  align-items: center;
}

.preview-item-detail::before {
  content: "•";
  margin-right: 0.25rem;
  color: var(--primary-color);
}

.parse-status {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-top: 1rem;
  padding: 0.875rem;
  background-color: var(--primary-light);
  border-radius: 4px;
  color: var(--primary-dark);
  font-size: 1rem;
}

.loading-indicator {
  display: flex;
  gap: 0.5rem;
  align-items: center;
}

.parse-actions {
  display: flex;
  gap: 1rem;
  margin-top: 1.25rem;
}

.confirm-btn {
  padding: 0.625rem 1.75rem;
  border: none;
  border-radius: 4px;
  background-color: var(--primary-color);
  color: white;
  cursor: pointer;
  transition: all 0.3s ease;
  font-size: 1.1rem;
}

.confirm-btn:hover {
  background-color: var(--primary-dark);
}

.clear-btn {
  padding: 0.625rem 1.75rem;
  border: 1px solid #e0e0e0;
  border-radius: 4px;
  background-color: white;
  cursor: pointer;
  transition: all 0.3s ease;
  font-size: 1.1rem;
}

.clear-btn:hover {
  background-color: #f5f5f5;
}
</style>
