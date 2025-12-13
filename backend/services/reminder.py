from datetime import datetime, timedelta
from models.entry import Entry
from models.task import Task

class ReminderService:
    """提醒服务，用于获取即将到来的事件和任务"""
    
    def get_upcoming_events(self, settings=None):
        """
        获取即将到来的所有事件，根据不同事件类型使用不同的阈值时间
        
        Args:
            settings: 用户设置的提醒参数，包含不同事件类型的阈值时间
            
        Returns:
            list: 包含即将到来事件的列表
        """
        now = datetime.now()
        
        # 默认提醒设置
        default_settings = {
            'course': 30,        # 课程提前30分钟
            'homework': 60,      # 作业提前1小时
            'exam': [30, 60],    # 考试提前30天和1小时提醒
            'lecture': 60,       # 讲座提前1小时
            'meeting': 30,       # 会议提前30分钟
            'default': 60        # 默认提前1小时
        }
        
        # 合并用户设置
        reminder_settings = {**default_settings, **(settings or {})}
        
        # 计算非考试entries的最大查询时间范围
        non_exam_max_minutes = 0
        for key, value in reminder_settings.items():
            if key != 'exam':
                if isinstance(value, list):
                    non_exam_max_minutes = max(non_exam_max_minutes, max(value))
                else:
                    non_exam_max_minutes = max(non_exam_max_minutes, value)
        
        # 查询非考试的Entry事件（课程、会议等）
        non_exam_future_time = now + timedelta(minutes=non_exam_max_minutes)
        non_exam_entries = Entry.query.filter(
            Entry.start_time >= now,
            Entry.start_time <= non_exam_future_time,
            Entry.entry_type != 'exam'
        ).all()
        
        # 计算考试entries的最大查询时间范围
        exam_max_minutes = 0
        if 'exam' in reminder_settings:
            exam_settings = reminder_settings['exam']
            if isinstance(exam_settings, list):
                # 考试复习提醒是天数，需要转换为分钟
                for i, value in enumerate(exam_settings):
                    if i == 0:  # 复习提醒是天数
                        exam_max_minutes = max(exam_max_minutes, value * 24 * 60)
                    else:  # 其他是分钟
                        exam_max_minutes = max(exam_max_minutes, value)
        
        # 查询考试的Entry事件
        exam_future_time = now + timedelta(minutes=exam_max_minutes)
        exam_entries = Entry.query.filter(
            Entry.start_time >= now,
            Entry.start_time <= exam_future_time,
            Entry.entry_type == 'exam'
        ).all()
        
        # 合并所有entries
        upcoming_entries = non_exam_entries + exam_entries
        
        # 查询即将到来的Task任务（作业等，不包括考试）
        task_max_minutes = 0
        for key, value in reminder_settings.items():
            if key != 'exam':
                if isinstance(value, list):
                    task_max_minutes = max(task_max_minutes, max(value))
                else:
                    task_max_minutes = max(task_max_minutes, value)
        
        task_future_time = now + timedelta(minutes=task_max_minutes)
        upcoming_tasks = Task.query.filter(
            Task.deadline >= now,
            Task.deadline <= task_future_time,
            Task.completed == False
        ).all()
        
        # 合并并转换为字典格式
        reminders = []
        
        # 添加Entry事件
        for entry in upcoming_entries:
            time_diff = (entry.start_time - now).total_seconds() / 60
            
            # 根据事件类型获取对应的阈值时间
            event_type = entry.entry_type.lower()
            threshold = reminder_settings.get(event_type, reminder_settings['default'])
            
            # 检查是否在提醒时间范围内
            if event_type == 'exam':
                # 对于考试，特殊处理：如果同时满足两个提醒，只保留前往考场提醒
                # threshold[0] 是复习提醒（天数），threshold[1] 是前往考场提醒（分钟）
                # 确保threshold是列表类型
                if not isinstance(threshold, list):
                    threshold = [threshold] if isinstance(threshold, int) else [30, 60]  # 默认值
                
                # 检查是否满足前往考场提醒
                exam_reminders = []
                if len(threshold) > 1:
                    exam_reminder = threshold[1]  # 前往考场提醒（分钟）
                    if time_diff <= exam_reminder and time_diff > 0:
                        urgency = self._calculate_urgency(time_diff)
                        exam_reminders.append({
                            'id': f'entry_{entry.id}_{exam_reminder}',
                            'title': f'前往考场：{entry.title}',
                            'event_type': entry.entry_type,
                            'start_time': entry.start_time,
                            'end_time': entry.end_time,
                            'time_diff': time_diff,
                            'urgency': urgency,
                            'description': entry.description,
                            'color': entry.color
                        })
                
                # 如果不满足前往考场提醒，检查是否满足复习提醒
                if len(exam_reminders) == 0 and len(threshold) > 0:
                    review_days = threshold[0]  # 复习提醒（天数）
                    review_reminder = review_days * 24 * 60  # 转换为分钟
                    if time_diff <= review_reminder and time_diff > 0:
                        urgency = self._calculate_urgency(time_diff)
                        exam_reminders.append({
                            'id': f'entry_{entry.id}_{review_reminder}',
                            'title': f'考试复习：{entry.title}',
                            'event_type': entry.entry_type,
                            'start_time': entry.start_time,
                            'end_time': entry.end_time,
                            'time_diff': time_diff,
                            'urgency': urgency,
                            'description': entry.description,
                            'color': entry.color
                        })
                
                # 添加考试提醒
                reminders.extend(exam_reminders)
            elif isinstance(threshold, list):
                # 对于其他多级提醒类型
                for t in threshold:
                    if time_diff <= t and time_diff > 0:
                        urgency = self._calculate_urgency(time_diff)
                        reminders.append({
                            'id': f'entry_{entry.id}_{t}',
                            'title': entry.title,
                            'event_type': entry.entry_type,
                            'start_time': entry.start_time,
                            'end_time': entry.end_time,
                            'time_diff': time_diff,
                            'urgency': urgency,
                            'description': entry.description,
                            'color': entry.color
                        })
            else:
                # 对于普通提醒类型
                if time_diff <= threshold and time_diff > 0:
                    urgency = self._calculate_urgency(time_diff)
                    reminders.append({
                        'id': f'entry_{entry.id}',
                        'title': entry.title,
                        'event_type': entry.entry_type,
                        'start_time': entry.start_time,
                        'end_time': entry.end_time,
                        'time_diff': time_diff,
                        'urgency': urgency,
                        'description': entry.description,
                        'color': entry.color
                    })
        
        # 添加Task任务
        for task in upcoming_tasks:
            time_diff = (task.deadline - now).total_seconds() / 60
            
            # 根据任务类型获取对应的阈值时间
            task_type = task.task_type.lower()
            threshold = reminder_settings.get(task_type, reminder_settings['default'])
            
            # 检查是否在提醒时间范围内
            if isinstance(threshold, list):
                # 对于支持多级提醒的类型
                for t in threshold:
                    if time_diff <= t and time_diff > 0:
                        urgency = self._calculate_urgency(time_diff)
                        reminders.append({
                            'id': f'task_{task.id}_{t}',
                            'title': task.title,
                            'event_type': task.task_type,
                            'start_time': task.deadline,
                            'end_time': task.deadline,
                            'time_diff': time_diff,
                            'urgency': urgency,
                            'description': task.description,
                            'color': self._get_task_color(task.priority)
                        })
            else:
                # 对于普通提醒类型
                if time_diff <= threshold and time_diff > 0:
                    urgency = self._calculate_urgency(time_diff)
                    reminders.append({
                        'id': f'task_{task.id}',
                        'title': task.title,
                        'event_type': task.task_type,
                        'start_time': task.deadline,
                        'end_time': task.deadline,
                        'time_diff': time_diff,
                        'urgency': urgency,
                        'description': task.description,
                        'color': self._get_task_color(task.priority)
                    })
        
        # 按时间差排序，最近的事件排在前面
        reminders.sort(key=lambda x: x['time_diff'])
        
        return reminders
    
    def _calculate_urgency(self, time_diff):
        """
        根据时间差计算紧急程度
        
        Args:
            time_diff: 距离事件开始的分钟数
            
        Returns:
            str: 紧急程度，包括 'urgent'（紧急）、'high'（高）、'medium'（中）、'low'（低）
        """
        if time_diff <= 5:
            return 'urgent'  # 5分钟内，紧急
        elif time_diff <= 15:
            return 'high'  # 15分钟内，高优先级
        elif time_diff <= 30:
            return 'medium'  # 30分钟内，中优先级
        else:
            return 'low'  # 30分钟以上，低优先级
    
    def _get_task_color(self, priority):
        """
        根据任务优先级获取颜色
        
        Args:
            priority: 任务优先级（整数）
            
        Returns:
            str: 颜色代码
        """
        # 将整数优先级映射到颜色
        if isinstance(priority, int):
            # 根据优先级相对值判断：
            # 0-80: high优先级（重要）
            # 81-240: medium优先级
            # 241+: low优先级（不重要）
            if priority <= 80:
                priority_str = 'high'  # 高优先级
            elif priority <= 240:
                priority_str = 'medium'  # 中优先级
            else:
                priority_str = 'low'  # 低优先级
        else:
            # 兼容旧的字符串优先级
            priority_str = priority
        
        priority_color_map = {
            'urgent': '#ff4444',
            'high': '#ff6666',
            'medium': '#ffaa00',
            'low': '#4a90e2'
        }
        return priority_color_map.get(priority_str, '#4a90e2')

# 创建单例实例
reminder_service = ReminderService()