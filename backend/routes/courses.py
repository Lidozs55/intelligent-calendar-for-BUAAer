import requests
import time
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify
from extensions import db
from models.course import Course
from services.buaa_api import buaa_api_client, sso_login_handler, parse_course_data, NetworkError, AuthenticationError, DataError
from services.session_manager import global_session_manager

# 创建蓝图
courses_bp = Blueprint('courses', __name__)


@courses_bp.route('/', methods=['GET'])
def get_courses():
    """获取课程列表"""
    # 获取所有课程
    courses = Course.query.all()
    
    # 转换为JSON格式
    result = []
    for course in courses:
        course_data = {
            'id': course.id,
            'course_name': course.course_name,
            'teacher': course.teacher,
            'classroom': course.classroom,
            'start_time': course.start_time.strftime('%H:%M'),
            'end_time': course.end_time.strftime('%H:%M'),
            'day_of_week': course.day_of_week,
            'week_range': course.week_range
        }
        
        # 添加日期字段（如果存在）
        if course.date:
            course_data['date'] = course.date.strftime('%Y-%m-%d')
        
        result.append(course_data)
    
    return jsonify({'courses': result}), 200


@courses_bp.route('/', methods=['POST'])
def add_course():
    """添加课程"""
    data = request.get_json()
    
    new_course = Course(
        course_name=data['course_name'],
        teacher=data['teacher'],
        classroom=data['classroom'],
        start_time=data['start_time'],
        end_time=data['end_time'],
        day_of_week=data['day_of_week'],
        week_range=data['week_range']
    )
    
    db.session.add(new_course)
    db.session.commit()
    
    return jsonify({'message': '课程添加成功'}), 201


@courses_bp.route('/<int:course_id>', methods=['PUT'])
def update_course(course_id):
    """更新课程"""
    data = request.get_json()
    course = Course.query.get(course_id)
    
    if not course:
        return jsonify({'message': '课程不存在'}), 404
    
    # 更新课程信息
    course.course_name = data.get('course_name', course.course_name)
    course.teacher = data.get('teacher', course.teacher)
    course.classroom = data.get('classroom', course.classroom)
    course.start_time = data.get('start_time', course.start_time)
    course.end_time = data.get('end_time', course.end_time)
    course.day_of_week = data.get('day_of_week', course.day_of_week)
    course.week_range = data.get('week_range', course.week_range)
    
    db.session.commit()
    
    return jsonify({'message': '课程更新成功'}), 200


@courses_bp.route('/<int:course_id>', methods=['DELETE'])
def delete_course(course_id):
    """删除课程"""
    course = Course.query.get(course_id)
    
    if not course:
        return jsonify({'message': '课程不存在'}), 404
    
    db.session.delete(course)
    db.session.commit()
    
    return jsonify({'message': '课程删除成功'}), 200


@courses_bp.route('/init_session', methods=['POST'])
def init_session():
    """初始化会话"""
    data = request.get_json()
    user_id = data.get('user_id')
    buaa_id = data.get('buaa_id')
    
    if not user_id or not buaa_id:
        return jsonify({'message': '缺少必要参数'}), 400
    
    try:
        # 创建新会话
        user_key = global_session_manager.create_session(user_id, buaa_id)
        return jsonify({
            'message': '会话初始化成功',
            'user_key': user_key
        }), 200
    except Exception as e:
        return jsonify({'message': f'会话初始化失败: {str(e)}'}), 500


@courses_bp.route('/check_login', methods=['POST'])
def check_login():
    """检查登录状态"""
    data = request.get_json()
    user_key = data.get('user_key')
    
    if not user_key:
        return jsonify({'message': '缺少必要参数'}), 400
    
    try:
        # 使用新的API客户端检查登录状态
        logged_in, login_url = buaa_api_client.check_login_status(user_key)
        
        return jsonify({
            'logged_in': logged_in,
            'login_url': login_url
        }), 200
    except Exception as e:
        return jsonify({'message': f'检查登录状态失败: {str(e)}'}), 500


@courses_bp.route('/process_login_callback', methods=['POST'])
def process_login_callback():
    """处理登录回调"""
    data = request.get_json()
    user_key = data.get('user_key')
    callback_url = data.get('callback_url')
    
    if not user_key or not callback_url:
        return jsonify({'message': '缺少必要参数'}), 400
    
    try:
        session = global_session_manager.get_session(user_key)
        if not session:
            return jsonify({'message': '会话已过期或不存在'}), 401
        
        # 处理登录回调，获取byxt Cookie
        cookies = buaa_api_client.process_login_callback(session, callback_url)
        
        return jsonify({
            'message': '登录回调处理成功',
            'cookies': cookies
        }), 200
    except NetworkError as e:
        return jsonify({'message': f'网络错误: {str(e)}'}), 500
    except Exception as e:
        return jsonify({'message': f'处理登录回调失败: {str(e)}'}), 500


@courses_bp.route('/fetch_course_schedule', methods=['GET'])
def fetch_course_schedule():
    """作为代理，直接将前端请求转发到北航API，保留浏览器的Cookie和请求头"""
    from flask import Response
    import requests
    
    # 获取前端的请求参数
    date = request.args.get('date', '2025-11-28')
    lxdm = request.args.get('lxdm', 'student')
    
    # 构建北航API URL，添加正确的路径前缀
    api_url = f"https://byxt.buaa.edu.cn/jwapp/sys/homeapp/api/home/teachingSchedule/detail.do?rq={date}&lxdm={lxdm}"
    
    # 获取前端的请求头和Cookie
    frontend_headers = dict(request.headers)
    frontend_cookies = request.cookies.to_dict()
    
    # 过滤掉不必要的请求头
    headers_to_forward = {
        'User-Agent': frontend_headers.get('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36'),
        'Accept': frontend_headers.get('Accept', '*/*'),
        'Accept-Language': frontend_headers.get('Accept-Language', 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6'),
        'Referer': frontend_headers.get('Referer', 'https://byxt.buaa.edu.cn/jwapp/sys/homeapp/home/index.html'),
        'Sec-Ch-Ua': frontend_headers.get('Sec-Ch-Ua', '"Chromium";v="142", "Microsoft Edge";v="142", "Not_A Brand";v="99"'),
        'Sec-Ch-Ua-Mobile': frontend_headers.get('Sec-Ch-Ua-Mobile', '?0'),
        'Sec-Ch-Ua-Platform': frontend_headers.get('Sec-Ch-Ua-Platform', '"Windows"'),
        'Sec-Fetch-Dest': frontend_headers.get('Sec-Fetch-Dest', 'empty'),
        'Sec-Fetch-Mode': frontend_headers.get('Sec-Fetch-Mode', 'cors'),
        'Sec-Fetch-Site': frontend_headers.get('Sec-Fetch-Site', 'same-origin')
    }
    
    try:
        # 发送请求，使用前端的请求头和Cookie
        response = requests.get(
            api_url,
            headers=headers_to_forward,
            cookies=frontend_cookies,
            allow_redirects=False,
            timeout=10
        )
        
        # 创建响应对象，将北航API的响应直接返回给前端
        proxy_response = Response(
            response.content,
            status=response.status_code,
            headers=dict(response.headers)
        )
        
        return proxy_response
    except Exception as e:
        return jsonify({'message': f'代理请求失败: {str(e)}'}), 500


@courses_bp.route('/sync_buaa', methods=['POST'])
def sync_buaa_courses():
    """同步北航课程表（登录并获取考试数据）"""
    # 调用带日期参数的同步函数，默认使用当前日期
    return sync_buaa_courses_by_date()

@courses_bp.route('/sync_buaa/<string:date>', methods=['POST'])
def sync_buaa_courses_by_date(date=None):
    """同步北航课程表（按指定日期开始同步）"""
    try:
        from models.entry import Entry
        from datetime import datetime, timedelta
        
        # 解析请求数据
        data = request.get_json() if request.is_json else {}
        buaa_id = data.get('buaa_id')
        password = data.get('password')
        
        if not buaa_id:
            return jsonify({"status": "error", "message": "缺少必要参数"}), 400
        
        # 初始化会话，使用固定的user_id
        user_key = global_session_manager.create_session('default_user', buaa_id)
        session = global_session_manager.get_session(user_key)
        
        # 设置会话的Cookie为前端传递的Cookie
        frontend_cookies = request.cookies.to_dict()
        if frontend_cookies:
            session.cookies.update(frontend_cookies)
        
        # 检查是否提供了密码，如果提供则执行登录
        if password:
            print("使用提供的密码执行登录")
            try:
                # 执行SSO登录
                cookies = sso_login_handler.perform_sso_login(session, buaa_id, password)
                # 更新会话Cookie
                session.cookies.update(cookies)
                print("登录成功，更新会话Cookie")
            except AuthenticationError as e:
                return jsonify({"status": "error", "message": f"北航登录失败: {str(e)}"}), 401
            except NetworkError as e:
                return jsonify({"status": "error", "message": f"网络错误: {str(e)}"}), 503
            except Exception as e:
                print(f"登录过程中发生未知错误: {str(e)}")
                import traceback
                traceback.print_exc()
                return jsonify({"status": "error", "message": "登录过程中发生未知错误"}), 500
        
        # 确定起始日期
        if date:
            # 使用传入的日期作为起始日期
            try:
                today = datetime.strptime(date, '%Y-%m-%d')+timedelta(days=8)
            except ValueError:
                return jsonify({"status": "error", "message": "日期格式错误，应为YYYY-MM-DD"}), 400
        else:
            # 默认使用当前日期
            today = datetime.now()
        
        # 一次性同步14天内的所有课程内容
        all_courses = []
        
        # 先检查登录状态
        login_status, login_url = buaa_api_client.check_login_status(user_key)
        if not login_status:
            return jsonify({"status": "error", "message": "需要登录"}), 401
        
        # 循环获取接下来14天的课程数据
        for i in range(7):
            # 计算当前日期
            current_date = today + timedelta(days=i)
            date_str = current_date.strftime('%Y-%m-%d')
            
            print(f"获取课程数据，日期: {date_str}")
            result = buaa_api_client.fetch_course_schedule(user_key, date_str)
            
            if result.get('need_login'):
                print(f"需要重新登录")
                return jsonify({"status": "error", "message": "需要登录"}), 401
            
            if result.get('error'):
                print(f"获取日期 {date_str} 的课程数据失败: {result['error']}")
                # 继续尝试获取其他日期的课程数据，而不是直接返回错误
                continue
            
            # 获取课程数据，注意：result['data']['data']才是课程列表
            course_data = result.get('data', {}).get('data', [])
            
            # 构建API返回的数据格式，兼容parse_course_data函数
            api_response = {
                "datas": course_data,
                "code": "0",
                "msg": None
            }
            
            # 解析课程数据，确保数据准确性
            parsed_courses = parse_course_data(api_response, date_str)
            print(f"日期 {date_str} 解析后的课程数据: {parsed_courses}")
            all_courses.extend(parsed_courses)
            
            # 等待一段时间，避免请求过于频繁
            time.sleep(0.2)
        
        # 日志：总共获取到的课程数量
        print(f"[DB SYNC] 总共获取到的课程数量: {len(all_courses)}")
        
        # 对课程数据进行去重
        # 使用课程名称、教师、教室、开始时间、结束时间和星期几作为去重依据
        unique_courses = []
        seen_courses = set()
        
        for course in all_courses:
            # 构建唯一标识，包含原始日期以区分不同日期的相同课程
            course_key = f"{course['kcmc']}_{course['jsxm']}_{course['jxlh']}{course['jash']}_{course['kssj']}_{course['jssj']}_{course['xqj']}_{course.get('original_date', '')}"
            
            if course_key not in seen_courses:
                seen_courses.add(course_key)
                unique_courses.append(course)
        
        # 日志：去重后的课程数据
        print(f"[DB SYNC] 去重后的课程数量: {len(unique_courses)}")
        
        # 调用一次考试信息API，只获取一次
        exam_data = []
        try:
            # 使用今天的日期计算学期代码
            today_str = datetime.now().strftime('%Y-%m-%d')
            
            # 调用fetch_exam_schedule函数获取考试信息
            exam_result = buaa_api_client.fetch_exam_schedule(user_key, today_str)
            
            # 检查考试信息获取结果
            if not exam_result.get('need_login', False) and 'data' in exam_result:
                exam_data = exam_result['data']['exams']
                # 日志：获取到的考试数据
                print(f"[DB SYNC] 获取到的考试数量: {len(exam_data)}")
        except Exception as e:
            print(f"[DB SYNC] 获取考试信息失败: {str(e)}")
        
        # 保存课程数据
        if unique_courses:
            # 遍历解析后的课程数据并保存
            course_add_count = 0
            course_update_count = 0
            entry_add_count = 0
            entry_update_count = 0
            
            for course_item in unique_courses:
                # 解析教室信息
                classroom = f"{course_item['jxlh']}{course_item['jash']}"
                
                # 解析时间字符串为time对象
                from datetime import time as time_obj
                start_time_parts = course_item['kssj'].split(':')
                end_time_parts = course_item['jssj'].split(':')
                
                start_time = time_obj(int(start_time_parts[0]), int(start_time_parts[1]))
                end_time = time_obj(int(end_time_parts[0]), int(end_time_parts[1]))
                
                try:
                    # 1. 处理Course表：增量更新
                    # 查找是否已存在相同的课程
                    existing_course = Course.query.filter(
                        Course.course_name == course_item['kcmc'],
                        Course.teacher == course_item['jsxm'],
                        Course.classroom == classroom,
                        Course.start_time == start_time,
                        Course.end_time == end_time,
                        Course.day_of_week == course_item['xqj']
                    ).first()
                    
                    if existing_course:
                        # 如果存在，更新现有课程
                        existing_course.week_range = course_item['zcd']
                        course_update_count += 1
                    else:
                        # 如果不存在，添加新课程
                        new_course = Course(
                            course_name=course_item['kcmc'],
                            teacher=course_item['jsxm'],
                            classroom=classroom,
                            start_time=start_time,
                            end_time=end_time,
                            day_of_week=course_item['xqj'],
                            week_range=course_item['zcd']
                        )
                        db.session.add(new_course)
                        course_add_count += 1
                    
                    # 2. 处理Entry表：增量更新（如果有原始日期）
                    if course_item.get('original_date'):
                        try:
                            # 构建完整的开始和结束时间
                            start_time_str = f"{course_item['original_date']}T{course_item['kssj']}:00"
                            end_time_str = f"{course_item['original_date']}T{course_item['jssj']}:00"
                            start_datetime = datetime.fromisoformat(start_time_str)
                            end_datetime = datetime.fromisoformat(end_time_str)
                            # 查找是否已存在相同的条目
                            existing_entry = Entry.query.filter(
                                Entry.title == course_item['kcmc'],
                                Entry.entry_type == 'course',
                                Entry.start_time == start_datetime,
                                Entry.end_time == end_datetime
                            ).first()
                            
                            if existing_entry:
                                # 如果存在，更新现有条目
                                existing_entry.description = f"教师: {course_item['jsxm']}\n教室: {classroom}"
                                existing_entry.color = '#4a90e2'
                                entry_update_count += 1
                            else:
                                # 如果不存在，添加新条目
                                new_entry = Entry(
                                    title=course_item['kcmc'],
                                    description=f"教师: {course_item['jsxm']}\n教室: {classroom}",
                                    entry_type='course',
                                    start_time=start_datetime,
                                    end_time=end_datetime,
                                    color='#4a90e2'
                                )
                                db.session.add(new_entry)
                                entry_add_count += 1
                        except ValueError as e:
                            continue
                except Exception as e:
                    print(f"[DB SYNC] 保存课程数据失败: {str(e)}")
                    continue
            
            # 日志：课程数据保存结果
            print(f"[DB SYNC] 条目数据保存完成：新增 {entry_add_count} 条，更新 {entry_update_count} 条课程条目")
        
        # 保存考试数据
        if exam_data:
            exam_add_count = 0
            exam_update_count = 0
            
            # 遍历考试数据并保存为Entry
            for exam_item in exam_data:
                try:
                    # 解析考试日期和时间
                    exam_date_str = exam_item['examDate'].split(' ')[0]  # 提取日期部分
                    
                    # 构建完整的开始和结束时间
                    start_time_str = f"{exam_date_str}T{exam_item['startTime']}:00"
                    end_time_str = f"{exam_date_str}T{exam_item['endTime']}:00"
                    start_datetime = datetime.fromisoformat(start_time_str)
                    end_datetime = datetime.fromisoformat(end_time_str)
                    
                    # 查找是否已存在相同的考试条目
                    existing_exam = Entry.query.filter(
                        Entry.title == exam_item['courseName'],
                        Entry.entry_type == 'exam',
                        Entry.start_time == start_datetime,
                        Entry.end_time == end_datetime
                    ).first()
                    
                    if existing_exam:
                        # 如果存在，更新现有考试条目
                        existing_exam.description = f"考试地点: {exam_item['examPlace']}\n考试时间: {exam_item['examTimeDescription']}"
                        existing_exam.color = '#ff4444'
                        exam_update_count += 1
                    else:
                        # 如果不存在，添加新考试条目
                        new_entry = Entry(
                            title=exam_item['courseName'],
                            description=f"考试地点: {exam_item['examPlace']}\n考试时间: {exam_item['examTimeDescription']}",
                            entry_type='exam',
                            start_time=start_datetime,
                            end_time=end_datetime,
                            color='#ff4444'
                        )
                        db.session.add(new_entry)
                        exam_add_count += 1
                except ValueError as e:
                    print(f"[DB SYNC] 解析考试日期时间失败: {str(e)}")
                    continue
                except Exception as e:
                    print(f"[DB SYNC] 保存考试数据失败: {str(e)}")
                    continue
            
            # 日志：考试数据保存结果
            print(f"[DB SYNC] 考试数据保存完成：新增 {exam_add_count} 条，更新 {exam_update_count} 条考试条目")
        
        # 提交事务
        db.session.commit()
        
        # 返回结果
        return jsonify({
            "status": "success",
            "message": "课程表和考试信息同步成功", 
            "courses": unique_courses, 
            "exams": exam_data,
            "course_count": len(unique_courses),
            "exam_count": len(exam_data)
        }), 200
    
    except ValueError as e:
        # 发生错误时回滚事务
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 400
    except requests.RequestException as e:
        # 发生错误时回滚事务
        db.session.rollback()
        print(f"网络错误: {str(e)}")
        return jsonify({"status": "error", "message": f"网络错误: {str(e)}"}), 503
    except Exception as e:
        # 发生错误时回滚事务
        db.session.rollback()
        print(f"同步课程表失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"status": "error", "message": "服务器内部错误"}), 500


@courses_bp.route('/save_courses', methods=['POST'])
def save_courses():
    """保存课程表数据"""
    data = request.get_json()
    buaa_id = data.get('buaa_id')
    course_data = data.get('course_data')
    
    if not buaa_id or not course_data:
        return jsonify({'message': '缺少必要参数'}), 400
    
    try:
        # 处理北航API返回的格式：{"datas":[],"code":"0","msg":null}
        if isinstance(course_data, dict) and 'datas' in course_data and 'code' in course_data:
            if course_data.get('code') == '0':
                # 获取课程数据
                actual_course_data = {
                    'data': course_data.get('datas', [])
                }
                
                # 解析课程数据，确保数据准确性
                from services.buaa_api import parse_course_data
                parsed_courses = parse_course_data(actual_course_data)
                
                if parsed_courses:
                    # 先删除所有课程数据
                    Course.query.delete()
                    
                    # 遍历解析后的课程数据并保存
                    for course_item in parsed_courses:
                        # 解析教室信息
                        classroom = f"{course_item['jxlh']}{course_item['jash']}"
                        
                        # 创建课程对象，不使用user_id
                        new_course = Course(
                            course_name=course_item['kcmc'],
                            teacher=course_item['jsxm'],
                            classroom=classroom,
                            start_time=course_item['kssj'],
                            end_time=course_item['jssj'],
                            day_of_week=course_item['xqj'],
                            week_range=course_item['zcd']
                        )
                        
                        # 保存到数据库
                        db.session.add(new_course)
                    
                    # 提交事务
                    db.session.commit()
                    return jsonify({
                        'message': '课程表保存成功', 
                        'courses': parsed_courses, 
                        'count': len(parsed_courses)
                    }), 200
                else:
                    return jsonify({'message': '没有获取到有效的课程数据'}), 400
            else:
                return jsonify({
                    'message': f'API返回错误: {course_data.get("msg", "未知错误")}'
                }), 500
        else:
            return jsonify({
                'message': f'无效的API返回格式'
            }), 500
    except Exception as e:
        # 发生错误时回滚事务
        db.session.rollback()
        return jsonify({'message': f'课程表保存失败: {str(e)}'}), 500


@courses_bp.route('/destroy_session', methods=['POST'])
def destroy_session():
    """销毁会话"""
    data = request.get_json()
    user_key = data.get('user_key')
    
    if not user_key:
        return jsonify({'message': '缺少必要参数'}), 400
    
    try:
        # 销毁会话
        success = global_session_manager.destroy_session(user_key)
        if success:
            return jsonify({'message': '会话销毁成功'}), 200
        else:
            return jsonify({'message': '会话不存在'}), 404
    except Exception as e:
        return jsonify({'message': f'会话销毁失败: {str(e)}'}), 500
