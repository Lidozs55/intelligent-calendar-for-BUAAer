from datetime import datetime, timedelta
from models.task import Task
from models.course import Course

class ScheduleManager:
    def __init__(self):
        pass
    
    def check_conflict(self, user_id, new_event):
        """
        检查新事件是否与现有日程冲突
        :param user_id: 用户ID
        :param new_event: 新事件，包含start_time和end_time
        :return: 冲突的事件列表
        """
        conflicts = []
        
        # 解析新事件的时间
        new_start = datetime.fromisoformat(new_event['start_time'])
        new_end = datetime.fromisoformat(new_event['end_time'])
        
        # 检查与课程的冲突
        courses = Course.query.filter_by(user_id=user_id).all()
        for course in courses:
            # 计算课程在当前周的时间
            course_start = self._calculate_course_time(course, new_start)
            if course_start:
                course_end = datetime.combine(course_start.date(), course.end_time)
                
                # 检查时间重叠
                if self._is_overlap(new_start, new_end, course_start, course_end):
                    conflicts.append({
                        'type': 'course',
                        'id': course.id,
                        'title': course.course_name,
                        'start_time': course_start.isoformat(),
                        'end_time': course_end.isoformat()
                    })
        
        # 检查与现有任务的冲突
        tasks = Task.query.filter_by(user_id=user_id, completed=False).all()
        for task in tasks:
            if task.deadline:
                # 假设任务占用的时间是从deadline减去estimated_time到deadline
                # 这里可以根据实际需求调整
                if task.estimated_time:
                    task_start = task.deadline - timedelta(minutes=task.estimated_time)
                    task_end = task.deadline
                    
                    if self._is_overlap(new_start, new_end, task_start, task_end):
                        conflicts.append({
                            'type': 'task',
                            'id': task.id,
                            'title': task.title,
                            'start_time': task_start.isoformat(),
                            'end_time': task_end.isoformat()
                        })
        
        return conflicts
    
    def auto_schedule(self, user_id, task_id):
        """
        自动安排任务时间
        :param user_id: 用户ID
        :param task_id: 任务ID
        :return: 推荐的开始时间和结束时间
        """
        # 获取任务信息
        task = Task.query.get(task_id)
        if not task or task.completed:
            return None
        
        # 获取用户的课程和现有任务
        courses = Course.query.filter_by(user_id=user_id).all()
        existing_tasks = Task.query.filter_by(user_id=user_id, completed=False).all()
        
        # 计算可用时间段
        available_slots = self._find_available_slots(courses, existing_tasks, task.deadline, task.estimated_time)
        
        # 根据优先级和精力周期选择最佳时间段
        if available_slots:
            # 简单选择第一个可用时间段，实际可以根据更复杂的算法选择
            return available_slots[0]
        
        return None
    
    def _calculate_course_time(self, course, reference_date):
        """
        计算课程在参考日期所在周的具体时间
        :param course: 课程对象
        :param reference_date: 参考日期
        :return: 课程开始时间
        """
        # 获取参考日期的星期几（1-7）
        ref_day = reference_date.isoweekday()
        
        # 计算与课程星期几的差值
        days_diff = course.day_of_week - ref_day
        course_date = reference_date + timedelta(days=days_diff)
        
        # 组合日期和时间
        return datetime.combine(course_date.date(), course.start_time)
    
    def _is_overlap(self, start1, end1, start2, end2):
        """
        检查两个时间段是否重叠
        :param start1: 第一个时间段的开始时间
        :param end1: 第一个时间段的结束时间
        :param start2: 第二个时间段的开始时间
        :param end2: 第二个时间段的结束时间
        :return: 是否重叠
        """
        return (start1 < end2) and (end1 > start2)
    
    def _find_available_slots(self, courses, existing_tasks, deadline, estimated_time):
        """
        查找可用的时间段
        :param courses: 课程列表
        :param existing_tasks: 现有任务列表
        :param deadline: 任务截止时间
        :param estimated_time: 任务预估耗时（分钟）
        :return: 可用时间段列表
        """
        available_slots = []
        
        # 从当前时间到截止时间，每天查找可用时间段
        current_time = datetime.now()
        time_delta = timedelta(days=1)
        
        while current_time < deadline:
            # 每天的可用时间段（假设为8:00-22:00）
            day_start = current_time.replace(hour=8, minute=0, second=0, microsecond=0)
            day_end = current_time.replace(hour=22, minute=0, second=0, microsecond=0)
            
            # 获取当天的课程和任务
            day_courses = self._get_day_courses(courses, current_time)
            day_tasks = self._get_day_tasks(existing_tasks, current_time)
            
            # 合并所有占用时间段
            occupied_slots = []
            for course in day_courses:
                course_start = datetime.combine(current_time.date(), course.start_time)
                course_end = datetime.combine(current_time.date(), course.end_time)
                occupied_slots.append((course_start, course_end))
            
            for task in day_tasks:
                if task.estimated_time:
                    task_start = task.deadline - timedelta(minutes=task.estimated_time)
                    task_end = task.deadline
                    if task_start.date() == current_time.date():
                        occupied_slots.append((task_start, task_end))
            
            # 排序占用时间段
            occupied_slots.sort(key=lambda x: x[0])
            
            # 查找可用时间段
            last_end = day_start
            for start, end in occupied_slots:
                if start > last_end:
                    # 检查这个时间段是否足够长
                    slot_duration = (start - last_end).total_seconds() / 60
                    if slot_duration >= estimated_time:
                        available_slots.append({
                            'start_time': last_end.isoformat(),
                            'end_time': (last_end + timedelta(minutes=estimated_time)).isoformat()
                        })
                last_end = max(last_end, end)
            
            # 检查最后一个时间段
            if day_end > last_end:
                slot_duration = (day_end - last_end).total_seconds() / 60
                if slot_duration >= estimated_time:
                    available_slots.append({
                        'start_time': last_end.isoformat(),
                        'end_time': (last_end + timedelta(minutes=estimated_time)).isoformat()
                    })
            
            # 检查是否找到足够的时间段
            if len(available_slots) >= 3:  # 最多返回3个推荐时间段
                break
            
            # 下一天
            current_time += time_delta
        
        return available_slots
    
    def _get_day_courses(self, courses, date):
        """
        获取指定日期的课程
        :param courses: 课程列表
        :param date: 日期
        :return: 当天的课程列表
        """
        day_of_week = date.isoweekday()
        return [course for course in courses if course.day_of_week == day_of_week]
    
    def _get_day_tasks(self, tasks, date):
        """
        获取指定日期的任务
        :param tasks: 任务列表
        :param date: 日期
        :return: 当天的任务列表
        """
        return [task for task in tasks if task.deadline and task.deadline.date() == date.date()]
