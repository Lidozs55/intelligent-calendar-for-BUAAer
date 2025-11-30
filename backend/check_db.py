from app import create_app
from extensions import db
from models.course import Course

app = create_app()

with app.app_context():
    print('数据库中的课程数量:', Course.query.count())
    print('课程列表:')
    for course in Course.query.all():
        print(f'- {course.course_name} (星期{course.day_of_week}, {course.start_time}-{course.end_time}, {course.classroom})')
