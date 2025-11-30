from flask import Blueprint, request, jsonify
from services.llm_parser import LLMParser
import pytesseract
from PIL import Image
import io
import os

# 设置TESSDATA_PREFIX环境变量，指向tessdata目录
os.environ['TESSDATA_PREFIX'] = r'D:\Tesseract-OCR\tessdata'

# 设置pytesseract的tesseract命令路径
pytesseract.pytesseract.tesseract_cmd = r'D:\Tesseract-OCR\tesseract.exe'

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
        return jsonify({'result': result}), 200
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
            
            # 使用pytesseract进行OCR识别
            print("开始OCR识别...")
            try:
                # 尝试使用中文语言包
                ocr_text = pytesseract.image_to_string(img, lang='chi_sim')
                print(f"中文OCR识别结果: {ocr_text}")
            except pytesseract.pytesseract.TesseractError as e:
                print(f"中文OCR识别失败: {str(e)}")
                print("尝试使用英文语言包...")
                try:
                    # 回退到使用英文语言包
                    ocr_text = pytesseract.image_to_string(img, lang='eng')
                    print(f"英文OCR识别结果: {ocr_text}")
                except Exception as e2:
                    print(f"英文OCR识别也失败: {str(e2)}")
                    ocr_text = "OCR识别失败，可能缺少语言包"
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
