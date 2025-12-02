from flask import Blueprint, request, jsonify
from services.llm_parser import LLMParser
import easyocr
from PIL import Image
import io
import os

# 初始化easyocr阅读器（只需要初始化一次）
reader = easyocr.Reader(['ch_sim', 'en'], gpu=False)

# 创建蓝图
llm_bp = Blueprint('llm', __name__)

# 初始化LLM解析器
llm_parser = LLMParser()


@llm_bp.route('/parse/text', methods=['POST'])
def parse_text():
    """解析文本内容"""
    data = request.get_json()
    text = data.get('text')
    user_preferences = data.get('user_preferences')
    start_date = data.get('start_date')
    
    if not text:
        return jsonify({'message': '缺少文本内容'}), 400
    
    result = llm_parser.parse_text(text, user_preferences, start_date)
    
    if result:
        # 直接处理LLM返回的结果，创建条目和任务
        import json
        from datetime import datetime
        
        try:
            # 解析LLM返回的JSON
            llm_data = json.loads(result)
            # 仅保留LLM返回的JSON文本输出
            print(json.dumps(llm_data, ensure_ascii=False, indent=2))
            
            # 创建任务
            if llm_data.get('tasks'):
                for task in llm_data['tasks']:
                    # 调用tasksAPI创建任务
                    task_data = {
                        'title': task['name'],
                        'description': '',
                        'task_type': 'homework',
                        'deadline': task['deadline'].replace(' ', 'T') + ':00' if task.get('deadline') else None,
                        'estimated_time': task['estimated_time'] or 0,
                        'priority': 'medium',
                        'completed': False
                    }
                    
                    # 直接调用Task模型创建任务
                    from models.task import Task
                    
                    def parse_datetime(date_str):
                        if date_str:
                            if len(date_str) == 16:  # 格式为 YYYY-MM-DDTHH:MM
                                date_str += ':00'  # 添加秒
                            return datetime.fromisoformat(date_str)
                        return None
                    
                    new_task = Task(
                        title=task_data['title'],
                        description=task_data.get('description', ''),
                        task_type=task_data.get('task_type', 'homework'),
                        deadline=parse_datetime(task_data.get('deadline')),
                        priority=task_data.get('priority', 'medium')
                    )
                    
                    from extensions import db
                    db.session.add(new_task)
                    db.session.commit()
            
            # 创建条目
            if llm_data.get('entries'):
                for entry in llm_data['entries']:
                    # 调用entriesAPI创建条目
                    entry_data = {
                        'title': entry['title'],
                        'description': '',
                        'entry_type': entry['entry_type'] or 'meeting',
                        'start_time': entry['start_time'].replace(' ', 'T') + ':00',
                        'end_time': entry['end_time'].replace(' ', 'T') + ':00'
                    }
                    
                    # 直接调用Entry模型创建条目
                    from models.entry import Entry
                    
                    def parse_datetime_local(date_str):
                        if len(date_str) == 16:  # 格式为 YYYY-MM-DDTHH:MM
                            date_str += ':00'  # 添加秒
                        local_dt = datetime.fromisoformat(date_str)
                        return local_dt.replace(tzinfo=None)
                    
                    new_entry = Entry(
                        title=entry_data['title'],
                        description=entry_data.get('description'),
                        entry_type=entry_data['entry_type'],
                        start_time=parse_datetime_local(entry_data['start_time']),
                        end_time=parse_datetime_local(entry_data['end_time']),
                        color=entry_data.get('color')
                    )
                    
                    from extensions import db
                    db.session.add(new_entry)
                    db.session.commit()
            
            return jsonify({'result': result, 'message': '解析成功，已创建条目和任务'}), 200
        except Exception as e:
            import traceback
            traceback.print_exc()
            return jsonify({'result': result, 'message': '解析成功，但创建条目和任务失败'}), 500
    else:
        return jsonify({'message': '解析失败'}), 500


@llm_bp.route('/parse/voice', methods=['POST'])
def parse_voice():
    """解析语音转文字内容"""
    data = request.get_json()
    voice_text = data.get('voice_text')
    user_preferences = data.get('user_preferences')
    start_date = data.get('start_date')
    
    if not voice_text:
        return jsonify({'message': '缺少语音转文字内容'}), 400
    
    result = llm_parser.parse_voice(voice_text, user_preferences, start_date)
    if result:
        return jsonify({'result': result}), 200
    else:
        return jsonify({'message': '解析失败'}), 500


@llm_bp.route('/parse/image', methods=['POST'])
def parse_image():
    """解析图片OCR识别内容"""
    # 添加详细日志
    print(f"接收到图片识别请求，请求方法: {request.method}")
    print(f"请求文件: {request.files}")
    print(f"请求表单: {request.form}")
    print(f"请求头: {request.headers}")
    
    # 检查是否是文件上传
    if 'image' in request.files:
        # 处理文件上传情况
        image = request.files['image']
        print(f"获取到图片文件: {image.filename}")
        try:
            # 读取图片文件
            img = Image.open(image)
            print(f"成功打开图片，格式: {img.format}, 尺寸: {img.size}")
            
            # 使用easyocr进行OCR识别
            print("开始OCR识别...")
            try:
                # 保存图片到临时文件，因为easyocr需要文件路径
                import tempfile
                with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_file:
                    img.save(temp_file, format='PNG')
                    temp_file_path = temp_file.name
                
                # 使用easyocr进行识别
                results = reader.readtext(temp_file_path, detail=0)
                print(f"OCR识别结果: {results}")
                
                # 合并识别结果
                ocr_text = ' '.join(results)
                print(f"合并后的OCR识别结果: {ocr_text}")
                
                # 删除临时文件
                os.unlink(temp_file_path)
            except Exception as e:
                print(f"OCR识别失败: {str(e)}")
                import traceback
                traceback.print_exc()
                ocr_text = f"OCR识别失败: {str(e)}"
            print(f"最终OCR识别结果: {ocr_text}")
            
            if not ocr_text.strip():
                ocr_text = "OCR识别结果为空"
            
            # 返回OCR识别的原始文本
            response_data = {'text': ocr_text}
            print(f"返回响应: {response_data}")
            return jsonify(response_data), 200
        except Exception as e:
            print(f"OCR识别失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return jsonify({'message': f'图片识别失败: {str(e)}'}), 500
    else:
        print("请求中没有图片文件")
        # 处理JSON数据情况
        data = request.get_json()
        image_text = data.get('image_text')
        
        if not image_text:
            return jsonify({'message': '缺少图片OCR识别内容'}), 400
        
        result = llm_parser.parse_image(image_text)
        if result:
            return jsonify({'result': result}), 200
        else:
            return jsonify({'message': '解析失败'}), 500


@llm_bp.route('/parse/clipboard', methods=['POST'])
def parse_clipboard():
    """解析剪切板内容"""
    data = request.get_json()
    clipboard_text = data.get('clipboard_text')
    user_preferences = data.get('user_preferences')
    start_date = data.get('start_date')
    
    if not clipboard_text:
        return jsonify({'message': '缺少剪切板内容'}), 400
    
    result = llm_parser.parse_clipboard(clipboard_text, user_preferences, start_date)
    if result:
        return jsonify({'result': result}), 200
    else:
        return jsonify({'message': '解析失败'}), 500
