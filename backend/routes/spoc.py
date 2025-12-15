from flask import Blueprint, request, jsonify
from services.buaa_api import spoc_api_client, BUAAAPIError
from models import User, Task, Entry
from extensions import db
from datetime import datetime

spoc_bp = Blueprint('spoc', __name__)

@spoc_bp.route('/login', methods=['POST'])
def login_spoc():
    """
    SPOC系统登录
    """
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'error': '用户名和密码不能为空'}), 400
    
    try:
        # 调用SPOC API客户端进行登录
        login_result = spoc_api_client.login_spoc(username, password)
        
        return jsonify({
            'status': 'success',
            'message': 'SPOC登录成功'
        })
        
    except BUAAAPIError as e:
        return jsonify({'error': str(e)}), 401
    except Exception as e:
        return jsonify({'error': f'登录失败: {str(e)}'}), 500


@spoc_bp.route('/homeworks', methods=['POST'])
def get_homeworks():
    """
    获取SPOC作业列表
    """
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'error': '用户名和密码不能为空'}), 400
    
    try:
        # 调用SPOC API客户端获取作业列表
        homework_data = spoc_api_client.fetch_all_homeworks(username, password)
        
        return jsonify({
            'status': 'success',
            'data': homework_data
        })
        
    except BUAAAPIError as e:
        return jsonify({'error': str(e)}), 500
    except Exception as e:
        return jsonify({'error': f'获取作业列表失败: {str(e)}'}), 500


@spoc_bp.route('/sync-homeworks', methods=['POST'])
def sync_homeworks():
    """
    同步SPOC作业到任务列表
    """
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    user_id = data.get('user_id')
    
    if not username or not password or not user_id:
        return jsonify({'error': '用户名、密码和用户ID不能为空'}), 400
    
    try:
        # 1. 获取作业列表
        homework_data = spoc_api_client.fetch_all_homeworks(username, password)
        homework_list = homework_data.get('list', [])
        
        # 2. 处理作业数据，创建任务
        synced_count = 0
        for homework in homework_list:
            # 检查作业是否已存在
            existing_task = Task.query.filter_by(
                title=f"{homework.get('kcmc', '')}+{homework.get('zymc', '')}",
                user_id=user_id
            ).first()
            
            if not existing_task:
                # 解析截止日期
                deadline_str = homework.get('zyjzsj', '')
                deadline = None
                if deadline_str:
                    try:
                        deadline = datetime.strptime(deadline_str, '%Y-%m-%d %H:%M:%S')
                    except ValueError:
                        try:
                            deadline = datetime.strptime(deadline_str, '%Y-%m-%d')
                        except ValueError:
                            deadline = None
                
                # 创建新任务
                new_task = Task(
                    title=f"{homework.get('kcmc', '')}+{homework.get('zymc', '')}",
                    description=homework.get('zyxq', ''),
                    deadline=deadline,
                    status='pending',
                    priority='medium',
                    user_id=user_id,
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )
                
                db.session.add(new_task)
                synced_count += 1
        
        # 3. 提交数据库事务
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': f'成功同步{synced_count}条作业',
            'total': len(homework_list),
            'synced': synced_count
        })
        
    except BUAAAPIError as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'同步作业失败: {str(e)}'}), 500


@spoc_bp.route('/sync-homeworks-with-schedule', methods=['POST'])
def sync_homeworks_with_schedule():
    """
    同步SPOC作业并调用LLM自动安排时间
    """
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    user_id = data.get('user_id')
    
    if not username or not password or not user_id:
        return jsonify({'error': '用户名、密码和用户ID不能为空'}), 400
    
    try:
        # 1. 先调用fetch_all_homeworks获取作业数据
        from services.buaa_api import spoc_api_client
        homework_data = spoc_api_client.fetch_all_homeworks(username, password)
        homework_list = homework_data.get('list', [])
        
        # 2. 处理作业数据，创建任务
        synced_count = 0
        created_tasks = []
        
        for homework in homework_list:
            # 检查作业是否已存在
            existing_task = Task.query.filter_by(
                title=f"{homework.get('kcmc', '')}+{homework.get('zymc', '')}",
                user_id=user_id
            ).first()
            
            if not existing_task:
                # 创建新任务
                import datetime
                deadline_str = homework.get('zyjzsj', '')
                deadline = None
                
                if deadline_str:
                    try:
                        deadline = datetime.datetime.strptime(deadline_str, '%Y-%m-%d %H:%M:%S')
                    except ValueError:
                        try:
                            deadline = datetime.datetime.strptime(deadline_str, '%Y-%m-%d')
                        except ValueError:
                            deadline = None
                
                new_task = Task(
                    title=f"{homework.get('kcmc', '')}+{homework.get('zymc', '')}",
                    description=homework.get('zyxq', ''),
                    deadline=deadline,
                    status='pending',
                    priority='medium',
                    user_id=user_id,
                    created_at=datetime.datetime.now(),
                    updated_at=datetime.datetime.now()
                )
                
                db.session.add(new_task)
                db.session.commit()
                
                synced_count += 1
                created_tasks.append(new_task)
        
        # 3. 调用LLM自动安排时间
        from services.llm_parser import LLMParser
        llm_parser = LLMParser()
        
        created_entries = []
        
        # 为每个新创建的任务调用LLM生成日程安排
        for task in created_tasks:
            try:
                # 准备任务数据
                task_data = {
                    'title': task.title,
                    'description': task.description,
                    'task_type': 'homework',
                    'deadline': task.deadline.isoformat() if task.deadline else '',
                    'priority': task.priority
                }
                
                # 调用LLM生成日程安排
                llm_result = llm_parser.generate_entries_from_task(task_data)
                
                if llm_result:
                    import json
                    from datetime import datetime
                    
                    # 解析LLM返回的JSON
                    llm_data = json.loads(llm_result)
                    
                    # 创建条目
                    if llm_data.get('entries'):
                        for entry in llm_data['entries']:
                            # 创建条目
                            new_entry = Entry(
                                title=entry['title'],
                                description=entry.get('description', ''),
                                entry_type=entry.get('entry_type', 'study'),
                                start_time=datetime.fromisoformat(entry['start_time'].replace(' ', 'T')),
                                end_time=datetime.fromisoformat(entry['end_time'].replace(' ', 'T')),
                                color=entry.get('color', '#4a90e2'),
                                user_id=user_id
                            )
                            
                            db.session.add(new_entry)
                            db.session.commit()
                            
                            created_entries.append(new_entry)
            except Exception as e:
                print(f"[ERROR] 为任务 {task.title} 生成日程安排失败: {str(e)}")
                continue
        
        return jsonify({
            'status': 'success',
            'message': f'成功同步{synced_count}条作业并为{len(created_entries)}条作业安排时间',
            'sync_result': {
                'total': len(homework_list),
                'synced': synced_count
            },
            'scheduled_count': len(created_entries)
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'同步作业并安排时间失败: {str(e)}'}), 500