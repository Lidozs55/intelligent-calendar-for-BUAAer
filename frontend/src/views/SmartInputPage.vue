<template>
  <div class="smart-input-page">
    <!-- 顶部导航栏 -->
    <header class="page-header">
      <button @click="goBack" class="back-btn">← 返回主页</button>
      <h1>智能输入中心</h1>
    </header>
    
    <main class="page-content">
      <!-- 智能输入面板 -->
      <section class="input-section">
        <SmartInput />
      </section>
      
      <!-- 剪切板队列面板 -->
      <section class="clipboard-section">
        <h2>剪切板内容队列 ({{ clipboardQueue.length }})</h2>
        <ClipboardQueue @use-clipboard-item="handleUseClipboardItem" />
      </section>
    </main>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import SmartInput from '../components/SmartInput.vue'
import ClipboardQueue from '../components/ClipboardQueue.vue'
import { useClipboardStore } from '../store'

const emit = defineEmits(['go-back'])
const clipboardStore = useClipboardStore()

// 计算属性：获取剪切板队列
const clipboardQueue = computed(() => clipboardStore.clipboardQueue)

// 返回主页
const goBack = () => {
  emit('go-back')
}

// 处理使用剪切板内容
const handleUseClipboardItem = (text) => {
  console.log('使用剪切板内容:', text)
  // 这里可以添加将内容传递给智能输入组件的逻辑
  // 由于智能输入组件是子组件，需要通过事件或状态管理来传递数据
  // 暂时只打印日志，后续可以扩展
}
</script>

<style scoped>
.smart-input-page {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background-color: #f5f5f5;
}

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem 2rem;
  background-color: #4a90e2;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.page-header h1 {
  margin: 0;
  font-size: 1.5rem;
  font-weight: 500;
  color: inherit; /* 使用默认文本颜色 */
}

.back-btn {
  background-color: rgba(255, 255, 255, 0.2);
  border: none;
  color: white;
  padding: 0.5rem 1rem;
  border-radius: 4px;
  cursor: pointer;
  font-size: 1rem;
  transition: background-color 0.3s ease;
}

.back-btn:hover {
    background-color: rgba(255, 255, 255, 0.3);
  }

  .page-header h1 {
    margin: 0;
    font-size: 1.5rem;
    font-weight: 500;
    color: white; /* 设置为白色，与蓝色背景形成对比 */
  }

.page-content {
  flex: 1;
  padding: 2rem;
  overflow: hidden;
  display: flex;
  gap: 1.5rem;
  align-items: stretch;
  height: calc(100vh - 80px); /* 减去header高度 */
}

/* 智能输入面板样式 */
.input-section {
  flex: 0.65; /* 调整比例，为剪贴板队列栏留出更多空间 */
  background-color: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  padding: 2rem;
  font-size: 1.1rem;
  height: 85vh; /* 与剪切板队列高度一致 */
  display: flex;
  flex-direction: column;
}

/* 剪切板队列面板样式 */
.clipboard-section {
  flex: 0.35; /* 使用flex比例，与智能输入栏一起填满屏幕 */
  background-color: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  padding: 1.5rem;
  height: 85vh;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  min-width: 400px;
}

.clipboard-section h2 {
  display: none; /* 移除剪切板内容队列标题 */
}

/* 响应式设计 */
@media (max-width: 1024px) {
  .page-content {
    flex-direction: column;
    align-items: center;
  }
  
  .clipboard-section {
    width: 100%;
    max-width: 100%;
  }
}

@media (max-width: 768px) {
  .page-header {
    padding: 1rem;
  }
  
  .page-content {
    padding: 1rem;
  }
  
  .input-section, .clipboard-section {
    padding: 1.5rem;
  }
}
</style>