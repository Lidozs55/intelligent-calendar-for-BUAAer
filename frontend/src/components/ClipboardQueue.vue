<template>
  <div class="clipboard-queue-container">
    <div class="queue-list">
      <div v-if="clipboardQueue.length === 0" class="empty-state">
        <p>剪切板队列为空</p>
      </div>
      
      <div 
        v-for="item in clipboardQueue" 
        :key="item.id"
        class="queue-item"
        :class="{ processed: item.processed }"
      >
        <div class="item-content">
          <div class="item-header">
            <span class="item-time">{{ formatTime(item.timestamp) }}</span>
            <span v-if="item.processed" class="processed-badge">已处理</span>
          </div>
          <div class="item-text">{{ item.text }}</div>
        </div>
        
        <div class="item-actions">
          <button 
            @click="useClipboardItem(item)"
            class="action-btn use-btn"
            :disabled="item.processed"
          >
            使用
          </button>
          <button 
            @click="markAsProcessed(item.id)"
            class="action-btn process-btn"
            :disabled="item.processed"
          >
            标记已处理
          </button>
          <button 
            @click="removeItem(item.id)"
            class="action-btn remove-btn"
          >
            删除
          </button>
        </div>
      </div>
    </div>
    
    <div class="queue-footer">
      <button @click="clearQueue" class="action-btn clear-btn">清空队列</button>
      <div class="queue-stats">
        <span>共 {{ clipboardQueue.length }} 条记录</span>
        <span v-if="unprocessedCount > 0" class="unprocessed-count">
          {{ unprocessedCount }} 条未处理
        </span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useClipboardStore } from '../store'
import { llmAPI } from '../services/api'

const clipboardStore = useClipboardStore()
const inputText = ref('')
const isParsing = ref(false)
const parsedResult = ref(null)

// 定义事件
const emit = defineEmits(['use-clipboard-item'])

// 计算属性：获取剪切板队列
const clipboardQueue = computed(() => clipboardStore.clipboardQueue)

// 计算属性：获取未处理的数量
const unprocessedCount = computed(() => {
  return clipboardStore.getUnprocessedItems().length
})

// 格式化时间
const formatTime = (timestamp) => {
  const date = new Date(timestamp)
  return date.toLocaleString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// 使用剪切板内容
const useClipboardItem = async (item) => {
  try {
    // 发送事件给父组件
    emit('use-clipboard-item', item.text)
    
    // 标记为已处理
    clipboardStore.markAsProcessed(item.id)
    
    // 使用LLM解析剪切板内容
    isParsing.value = true
    const response = await llmAPI.parseText({ text: item.text })
    if (response && response.result) {
      parsedResult.value = JSON.parse(response.result)
      console.log('LLM解析结果:', parsedResult.value)
    }
  } catch (error) {
    console.error('解析剪切板内容失败:', error)
  } finally {
    isParsing.value = false
  }
}

// 标记为已处理
const markAsProcessed = (id) => {
  clipboardStore.markAsProcessed(id)
}

// 移除项目
const removeItem = (id) => {
  clipboardStore.removeFromQueue(id)
}

// 清空队列
const clearQueue = () => {
  if (confirm('确定要清空剪切板队列吗？')) {
    clipboardStore.clearQueue()
  }
}
</script>

<style scoped>
.clipboard-queue-container {
  background-color: white;
  border-radius: 8px;
  padding: 0;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.action-btn {
  padding: 0.5rem 1rem;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.9rem;
  transition: all 0.3s ease;
}

.clear-btn {
  background-color: #f44336;
  color: white;
}

.clear-btn:hover {
  background-color: #d32f2f;
}

.use-btn {
  background-color: #4caf50;
  color: white;
}

.use-btn:hover:not(:disabled) {
  background-color: #388e3c;
}

.process-btn {
  background-color: #2196f3;
  color: white;
}

.process-btn:hover:not(:disabled) {
  background-color: #1976d2;
}

.remove-btn {
  background-color: #f44336;
  color: white;
}

.remove-btn:hover {
  background-color: #d32f2f;
}

.action-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.queue-stats {
  display: flex;
  gap: 1rem;
  align-items: center;
  font-size: 0.9rem;
  color: #666;
}

.unprocessed-count {
  background-color: #ff9800;
  color: white;
  padding: 0.25rem 0.5rem;
  border-radius: 12px;
  font-size: 0.8rem;
}

.queue-list {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  padding: 1rem;
}

.empty-state {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 200px;
  color: #666;
}

.queue-item {
  background-color: #f5f5f5;
  border-radius: 8px;
  padding: 1rem;
  display: flex;
  gap: 1rem;
  transition: all 0.3s ease;
}

.queue-item.processed {
  opacity: 0.7;
  background-color: #e8f5e8;
}

.item-content {
  flex: 1;
  min-width: 0;
}

.item-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
  font-size: 0.8rem;
  color: #666;
}

.item-time {
  font-weight: 500;
}

.processed-badge {
  background-color: #4caf50;
  color: white;
  padding: 0.125rem 0.5rem;
  border-radius: 12px;
  font-size: 0.75rem;
}

.item-text {
  font-size: 0.95rem;
  color: #333;
  white-space: pre-wrap;
  word-break: break-word;
  line-height: 1.5;
}

.item-actions {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  align-items: flex-end;
}

.queue-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem;
  background-color: #f5f5f5;
  border-top: 1px solid #e0e0e0;
  gap: 1rem;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .queue-item {
    flex-direction: column;
  }
  
  .item-actions {
    flex-direction: row;
    justify-content: flex-end;
    align-items: center;
  }
  
  .queue-footer {
    flex-direction: column;
    align-items: stretch;
  }
}
</style>