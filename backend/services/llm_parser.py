import os
import json
import requests
from dashscope import Generation
import dashscope

class LLMParser:
    def __init__(self):
        # 初始化阿里云百炼大模型配置
        self.api_key = os.getenv("DASHSCOPE_API_KEY")
        dashscope.base_http_api_url = 'https://dashscope.aliyuncs.com/api/v1'
    
    def _get_occupied_slots(self, start_date):
        """获取未来7天已占用时段"""
        try:
            # 调用本地API获取未来7天的日程
            api_url = f"http://127.0.0.1:5000/api/entries/{start_date}"
            response = requests.get(api_url)
            response.raise_for_status()
            data = response.json()
            
            # 仅保留每条entry的起止时间
            occupied_slots = []
            for entry in data.get('entries', []):
                occupied_slots.append({
                    'start_time': entry['start_time'],
                    'end_time': entry['end_time']
                })
            
            return occupied_slots
        except Exception as e:
            return []
    
    def parse_text(self, text, user_preferences=None, start_date=None):
        """解析文本内容，提取时限任务和固定日程信息"""
        # 如果没有提供开始日期，使用当前日期
        if not start_date:
            from datetime import datetime
            start_date = datetime.now().strftime('%Y-%m-%d')
        
        # 获取未来7天已占用时段
        occupied_slots = self._get_occupied_slots(start_date)
        
        # 构建提示词
        prompt = "请分析以下用户输入，提取时限任务和固定日程信息，并返回指定格式的JSON数据。\n\n"
        prompt += "输入数据：\n"
        prompt += f"- 文本内容：\"{text}\"\n"
        
        if user_preferences:
            prompt += f"- 用户偏好：{json.dumps(user_preferences)}\n"
        
        prompt += f"- 未来7天已占用时段：{json.dumps(occupied_slots)}\n\n"
        
        prompt += "处理要求：\n"
        prompt += "1. **时限任务(task)**：从文本中识别有截止时间的任务\n"
        prompt += "   - 提取：任务名称、截止时间\n"
        prompt += "   - 估算：预期完成时长\n"
        prompt += "   - 安排：在截止时间前，避开已占用时段，推荐合适的一个或多个完成时间段，同时生成一个或多个伴随的entry条目\n\n"
        prompt += "2. **固定日程(entry)**：从文本中识别时间固定的安排\n"
        prompt += "   - 提取：日程名称（如有地址信息则包含地址信息）、开始时间、结束时间、日程类型（详见json示例）\n"
        prompt += "   - 注意：保持原有时段不变\n"
        
        prompt += "输出要求：\n"
        prompt += "- 仅返回JSON格式数据，不包含其他内容\n"
        prompt += "- 确保时间安排不与已占用时段冲突\n"
        prompt += "- 合理安排任务完成时间，考虑用户偏好\n"
        
        prompt += "请返回以下JSON格式：\n"
        prompt += "{\n"
        prompt += "  \"tasks\": [\n"
        prompt += "    {\n"
        prompt += "      \"name\": \"任务名称\",\n"
        prompt += "      \"deadline\": \"YYYY-MM-DD HH:MM\",\n"
        prompt += "      \"estimated_time\": 120\n"
        prompt += "    }\n"
        prompt += "  ],\n"
        prompt += "  \"entries\": [\n"
        prompt += "    {\n"
        prompt += "      \"title\": \"日程名称\",\n"
        prompt += "      \"start_time\": \"YYYY-MM-DD HH:MM\",\n"
        prompt += "      \"end_time\": \"YYYY-MM-DD HH:MM\",\n"
        prompt += "      \"entry_type\": \"meeting/course/exam/study/lecture/sports\"\n"
        prompt += "    }\n"
        prompt += "  ]\n"
        prompt += "}\n"
        
        try:
            # 调用大语言模型API
            messages = [{"role": "user", "content": prompt}]
            response = Generation.call(
                api_key=self.api_key,
                model="qwen-plus",
                messages=messages,
                result_format="message",
                enable_thinking=False,
            )
            
            # 解析响应
            if response.status_code == 200:
                response_content = response.output.choices[0].message.content
                return response_content
            else:
                return None
        except Exception as e:
            return None
    
    def parse_voice(self, voice_text, user_preferences=None, start_date=None):
        """解析语音转文字内容，提取任务信息"""
        return self.parse_text(voice_text, user_preferences, start_date)
    
    def parse_image(self, image_text, user_preferences=None, start_date=None):
        """解析图片OCR识别内容，提取任务信息"""
        return self.parse_text(image_text, user_preferences, start_date)
    
    def parse_clipboard(self, clipboard_text, user_preferences=None, start_date=None):
        """解析剪切板内容，提取任务信息"""
        return self.parse_text(clipboard_text, user_preferences, start_date)
