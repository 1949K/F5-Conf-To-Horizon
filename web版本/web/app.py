import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from typing import Union, Any
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_file, flash, redirect, url_for, session
from werkzeug.utils import secure_filename
from core.config import Config
from core.processors.f5_ucs_processor import F5UCSProcessor
from core.processors.unified_processor import UnifiedProcessor
from core.processors.horizon_processor import HorizonProcessor
from core.user_manager import user_manager
from core.auth import login_required, get_current_user, get_user_upload_dir, get_user_processed_dir

# 初始化Flask应用
app = Flask(__name__)
app.config['SECRET_KEY'] = Config.SECRET_KEY
app.config['MAX_CONTENT_LENGTH'] = Config.MAX_CONTENT_LENGTH

# 设置会话配置
app.config['PERMANENT_SESSION_LIFETIME'] = 3600  # 会话有效期1小时
app.config['SESSION_COOKIE_SECURE'] = False  # 开发环境设为False
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# 确保必要的目录存在
Config.init()

# 初始化统一处理器
unified_processor = None

# 添加请求前处理中间件，定期清理过期会话
@app.before_request
def before_request():
    """请求前处理，清理过期会话"""
    user_manager.cleanup_expired_sessions()

@app.route('/health')
def health_check():
    """健康检查端点"""
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()}), 200

@app.route('/')
def index() -> str:
    """Main index route for the web application"""
    current_user = get_current_user()
    return render_template('index.html', title='F5 Config Translator', user=current_user)

@app.route('/login', methods=['GET', 'POST'])
def login():
    """用户登录"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if not username or not password:
            flash('用户名和密码不能为空', 'error')
            return render_template('login.html')
        
        session_id = user_manager.authenticate_user(username, password)
        if session_id:
            session['session_id'] = session_id
            session.permanent = True  # 设置会话为永久性
            flash('登录成功！', 'success')
            return redirect(url_for('index'))
        else:
            flash('用户名或密码错误', 'error')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """用户注册"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        email = request.form.get('email', '')
        
        if not username or not password:
            flash('用户名和密码不能为空', 'error')
            return render_template('register.html')
        
        if password != confirm_password:
            flash('两次输入的密码不一致', 'error')
            return render_template('register.html')
        
        if len(password) < 6:
            flash('密码长度至少6位', 'error')
            return render_template('register.html')
        
        if user_manager.register_user(username, password, email):
            flash('注册成功！请登录', 'success')
            return redirect(url_for('login'))
        else:
            flash('用户名已存在', 'error')
    
    return render_template('register.html')

@app.route('/logout')
def logout():
    """用户登出"""
    user_manager.logout_user()
    flash('已成功登出', 'success')
    return redirect(url_for('index'))

@app.route('/ucs')
@login_required
def ucs_page() -> Union[str, Any]:
    """UCS configuration page"""
    current_user = get_current_user()
    if not current_user:
        return redirect(url_for('login'))
    
    user_files = user_manager.get_user_files(current_user, 'ucs')
    user_processed_files = user_manager.get_user_processed_files(current_user, 'ucs')
    
    return render_template('f5_ucs.html', 
                         title='UCS Configuration', 
                         user=current_user,
                         files=user_files,
                         processed_files=user_processed_files)

@app.route('/show')
@login_required
def show_page() -> Union[str, Any]:
    """Show configuration page"""
    current_user = get_current_user()
    if not current_user:
        return redirect(url_for('login'))
    
    user_files = user_manager.get_user_files(current_user, 'show')
    user_processed_files = user_manager.get_user_processed_files(current_user, 'show')
    
    return render_template('f5_show.html', 
                         title='Show Configuration', 
                         user=current_user,
                         files=user_files,
                         processed_files=user_processed_files)

@app.route('/horizon')
@login_required
def horizon_page() -> Union[str, Any]:
    """弘积主备配置对比页面"""
    current_user = get_current_user()
    if not current_user:
        return redirect(url_for('login'))
    
    user_files = user_manager.get_user_files(current_user, 'horizon')
    user_processed_files = user_manager.get_user_processed_files(current_user, 'horizon')
    
    return render_template('horizon_compare.html', 
                         title='弘积主备配置对比', 
                         user=current_user,
                         files=user_files,
                         processed_files=user_processed_files)

@app.route('/upload/<file_type>', methods=['POST'])
@login_required
def upload_file(file_type) -> Union[Any, tuple[Any, int]]:
    """Handle file upload with user isolation"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    if file.filename is None or file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    # 检查文件数量限制
    files = request.files.getlist('file')
    if len(files) > Config.MAX_FILES_COUNT:
        return jsonify({'error': f'文件数量超过限制，最多只能上传 {Config.MAX_FILES_COUNT} 个文件'}), 400
    
    # 验证文件类型
    filename = secure_filename(file.filename)
    file_ext = filename.lower().split('.')[-1] if '.' in filename else ''
    
    if file_type == 'ucs' and file_ext not in ['ucs', 'tar']:
        return jsonify({'error': '只支持UCS和TAR文件'}), 400
    elif file_type == 'show' and file_ext not in ['txt', 'conf']:
        return jsonify({'error': '只支持TXT和CONF文件'}), 400
    elif file_type == 'conf' and file_ext not in ['conf']:
        return jsonify({'error': '只支持CONF文件'}), 400
    elif file_type == 'horizon':
        # 对于弘积文件，允许无扩展名或支持的压缩格式
        # 检查是否为弘积配置文件格式（IP地址-日期格式）
        if file_ext and file_ext not in ['tar', 'zip', 'gz', 'bz2']:
            # 检查是否为弘积配置文件格式（如：10.20.252.43-20250801）
            if '-' in filename and '.' in filename.split('-')[0]:
                # 可能是弘积配置文件，允许上传
                pass
            else:
                return jsonify({'error': '只支持TAR、ZIP、GZ、BZ2等压缩文件或无扩展名文件'}), 400
    elif file_type == 'processed':
        # processed类型接受所有文件
        pass
    
    # 获取用户上传目录
    current_user = get_current_user()
    if not current_user:
        return jsonify({'error': '用户未登录'}), 401
    
    # 确保用户的所有目录都存在
    if not user_manager.ensure_user_directories_exist(current_user):
        app.logger.error(f"用户 {current_user} 不存在或无法创建目录")
        return jsonify({'error': '用户不存在或无法创建目录'}), 500
    
    user_upload_dir = user_manager.get_user_upload_dir(current_user, file_type)
    
    # 自动创建用户目录（如果不存在）
    if not user_upload_dir:
        app.logger.error(f"用户 {current_user} 的 {file_type} 上传目录不存在")
        return jsonify({'error': '用户目录不存在'}), 500
    
    # 确保目录存在
    try:
        os.makedirs(user_upload_dir, exist_ok=True)
        app.logger.info(f"确保用户 {current_user} 的 {file_type} 上传目录存在: {user_upload_dir}")
    except Exception as e:
        app.logger.error(f"创建用户 {current_user} 的 {file_type} 上传目录时发生错误: {e}")
        return jsonify({'error': f'创建用户目录失败: {str(e)}'}), 500
    
    # 特殊处理conf文件：根据文件名分别放到conf和base目录
    if file_type == 'conf':
        # 对于conf文件，user_upload_dir已经是ucs目录
        ucs_dir = user_upload_dir
        conf_dir = os.path.join(ucs_dir, 'conf')
        base_dir = os.path.join(ucs_dir, 'base')
        
        # 确保目录存在
        try:
            os.makedirs(conf_dir, exist_ok=True)
            os.makedirs(base_dir, exist_ok=True)
            app.logger.info(f"确保conf和base目录存在: conf={conf_dir}, base={base_dir}")
        except Exception as e:
            app.logger.error(f"创建conf和base目录时发生错误: {e}")
            return jsonify({'error': f'创建conf和base目录失败: {str(e)}'}), 500
        
        # 严格判断文件名后缀，避免混淆
        if filename.lower().endswith('bigip_base.conf'):
            # 放到base目录
            upload_path = Path(base_dir)
            target_filename = filename
            app.logger.info(f"将 {filename} 分类为base文件，目标目录: {base_dir}")
        elif filename.lower().endswith('bigip.conf'):
            # 放到conf目录
            upload_path = Path(conf_dir)
            target_filename = filename
            app.logger.info(f"将 {filename} 分类为conf文件，目标目录: {conf_dir}")
        else:
            # 其他conf文件放到conf目录
            upload_path = Path(conf_dir)
            target_filename = filename
            app.logger.info(f"将 {filename} 分类为其他conf文件，目标目录: {conf_dir}")
    elif file_type == 'horizon':
        # 弘积文件特殊处理：标准化文件名
        upload_path = Path(user_upload_dir)
        
        # 检查是否为弘积配置文件格式（IP地址-日期格式）
        if '-' in filename and '.' in filename.split('-')[0]:
            # 弘积配置文件，添加.tar后缀
            target_filename = f"{filename}.tar"
        else:
            # 其他文件，检查扩展名
            name, ext = os.path.splitext(filename)
            if not ext:
                # 没有后缀，添加.tar
                target_filename = f"{name}.tar"
            elif ext.lower() not in ['.tar', '.zip', '.gz', '.bz2']:
                # 有其他后缀，改为.tar
                target_filename = f"{name}.tar"
            else:
                # 已经是支持的压缩格式，保持原样
                target_filename = filename
        
        app.logger.info(f"弘积文件标准化: {filename} -> {target_filename}")
    else:
        # 其他文件类型正常处理
        upload_path = Path(user_upload_dir)
        target_filename = filename
    
    try:
        upload_path.mkdir(parents=True, exist_ok=True)
        file_path = upload_path / target_filename
        file.save(file_path)
        app.logger.info(f"成功保存文件 {filename} 到 {file_path}")
    except Exception as e:
        app.logger.error(f"保存文件 {filename} 时发生错误: {e}")
        return jsonify({'error': f'保存文件失败: {str(e)}'}), 500

    # 自动翻译：如果是bigip.conf或bigip_base.conf，自动调用conf_and_base_to_excel_txt
    auto_translate = False
    if file_type == 'conf' and (filename.lower().endswith('bigip.conf') or filename.lower().endswith('bigip_base.conf')):
        auto_translate = True
        try:
            # 导入两个不同的处理模块
            from core.function.ucs.lxl_package_4_BaseConfProcess.F5_base_to_excel_txt import process_folder as process_base_folder
            from core.function.ucs.lxl_package_3_ConfProcess.Conf_Add_File import process_folder as process_conf_folder
            
            # conf和base目录
            conf_dir = os.path.join(user_upload_dir, 'conf')
            base_dir = os.path.join(user_upload_dir, 'base')
            
            # 只处理对应目录
            if filename.lower().endswith('bigip.conf'):
                if os.path.exists(conf_dir):
                    app.logger.info(f"自动翻译conf目录: {conf_dir}")
                    process_conf_folder(conf_dir)  # 使用conf处理模块
                    app.logger.info(f"自动翻译conf目录完成: {conf_dir}")
                else:
                    app.logger.warning(f"conf目录不存在: {conf_dir}")
            elif filename.lower().endswith('bigip_base.conf'):
                if os.path.exists(base_dir):
                    app.logger.info(f"自动翻译base目录: {base_dir}")
                    process_base_folder(base_dir)  # 使用base处理模块
                    app.logger.info(f"自动翻译base目录完成: {base_dir}")
                else:
                    app.logger.warning(f"base目录不存在: {base_dir}")
        except ImportError as e:
            app.logger.error(f"自动翻译时导入配置翻译模块失败: {e}")
            return jsonify({'error': f'自动翻译模块导入失败: {str(e)}'}), 500
        except Exception as e:
            app.logger.error(f"自动翻译conf/base目录时发生错误: {e}")
            return jsonify({'error': f'自动翻译失败: {str(e)}'}), 500

    # 弘积文件自动解压处理
    if file_type == 'horizon':
        try:
            from core.processors.horizon_processor import HorizonProcessor
            
            # 创建弘积处理器
            user_horizon_dir = user_manager.get_user_processed_dir(current_user, 'horizon')
            processor = HorizonProcessor()
            processor.set_user_directories(user_horizon_dir, user_upload_dir)
            
            # 立即处理文件
            file_path = str(upload_path / target_filename)
            result = processor.process(file_path, current_user)
            
            if result.get('success'):
                app.logger.info(f"弘积文件自动处理成功: {target_filename}")
                return jsonify({
                    'success': True,
                    'message': f'文件上传并自动处理成功',
                    'filename': target_filename,
                    'processed': True
                }), 200
            else:
                app.logger.warning(f"弘积文件自动处理失败: {target_filename} - {result.get('error', '未知错误')}")
                return jsonify({
                    'success': True,
                    'message': f'文件上传成功，但处理失败: {result.get("error", "未知错误")}',
                    'filename': target_filename,
                    'processed': False
                }), 200
                
        except Exception as e:
            app.logger.error(f"弘积文件自动处理时发生错误: {e}")
            return jsonify({
                'success': True,
                'message': f'文件上传成功，但自动处理失败: {str(e)}',
                'filename': target_filename,
                'processed': False
            }), 200

    return jsonify({
        'success': True,
        'message': 'File uploaded successfully' + ('，已自动翻译' if auto_translate else ''),
        'filename': filename
    }), 200

@app.route('/process/<action>', methods=['POST'])
@login_required
def process_files(action):
    """处理文件操作 with user isolation - 统一自动化处理"""
    try:
        current_user = get_current_user()
        if not current_user:
            return jsonify({'error': '用户未登录'}), 401
        
        file_type = request.form.get('file_type', 'ucs')
        
        # 获取用户专属处理器
        user_processed_dir = user_manager.get_user_processed_dir(current_user, file_type)
        processor = UnifiedProcessor(user_processed_dir)
        
        # 获取用户文件列表
        user_files = user_manager.get_user_files(current_user, file_type)
        upload_dir = user_manager.get_user_upload_dir(current_user, file_type)
        
        if action == 'auto_process':
            # 统一的自动化处理流程
            if file_type == 'ucs':
                result = processor.process_ucs_files(user_files, upload_dir)
            elif file_type == 'show':
                result = processor.process_show_files(user_files, upload_dir)
            elif file_type == 'horizon':
                # 弘积文件特殊处理
                try:
                    from core.processors.horizon_processor import HorizonProcessor
                    
                    # 获取用户目录
                    user_horizon_dir = user_manager.get_user_processed_dir(current_user, 'horizon')
                    user_upload_dir = user_manager.get_user_upload_dir(current_user, 'horizon')
                    
                    # 使用缓存的处理器实例
                    processor_key = f"horizon_processor_{current_user}"
                    if not hasattr(app, '_processors'):
                        app._processors = {}
                    
                    if processor_key not in app._processors:
                        app._processors[processor_key] = HorizonProcessor()
                        app._processors[processor_key].set_user_directories(user_horizon_dir, user_upload_dir)
                    
                    processor = app._processors[processor_key]
                    
                    # 处理所有弘积文件
                    results = []
                    processed_files = []
                    
                    for file in user_files:
                        file_path = os.path.join(user_upload_dir, file)
                        if os.path.exists(file_path):
                            try:
                                result = processor.process(file_path, current_user)
                                if result.get('success'):
                                    results.append(f'弘积文件处理成功: {file}')
                                    processed_files.append(file)
                                else:
                                    results.append(f'弘积文件处理失败: {file} - {result.get("error", "未知错误")}')
                            except Exception as e:
                                results.append(f'弘积文件处理失败: {file} - {str(e)}')
                    
                    # 进行配置对比
                    try:
                        config_dir = os.path.join(user_horizon_dir, 'config')
                        config_files = []
                        if os.path.exists(config_dir):
                            for config_file in os.listdir(config_dir):
                                if config_file.endswith('.config'):
                                    config_files.append(os.path.join(config_dir, config_file))
                        
                        if len(config_files) >= 2:
                            comparison_result = processor.compare_configs(config_files)
                            if "error" not in comparison_result:
                                results.append(f'配置对比完成，共 {comparison_result["summary"]["total_pairs"]} 对文件，总计 {comparison_result["summary"]["total_differences"]} 处差异')
                            else:
                                results.append(f'配置对比失败: {comparison_result["error"]}')
                        else:
                            results.append('配置文件数量不足，无法进行对比')
                    
                    except Exception as e:
                        results.append(f'配置对比失败: {str(e)}')
                    
                    result = {
                        'success': True,
                        'message': '弘积文件自动化处理完成',
                        'results': results,
                        'processed_files': processed_files
                    }
                    
                except Exception as e:
                    result = {'success': False, 'error': f'弘积文件处理失败: {str(e)}'}
            else:
                result = {'success': False, 'error': f'不支持的文件类型: {file_type}'}
            return jsonify(result)
            
        elif action == 'reprocess':
            # 重新处理所有文件
            if file_type == 'ucs':
                result = processor.process_ucs_files(user_files, upload_dir)
            elif file_type == 'show':
                result = processor.process_show_files(user_files, upload_dir)
            else:
                result = {'success': False, 'error': f'不支持的文件类型: {file_type}'}
            return jsonify(result)
            
        else:
            return jsonify({'success': False, 'error': f'不支持的操作: {action}'})
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/process/horizon', methods=['POST'])
@login_required
def process_horizon_files():
    """处理弘积配置文件"""
    try:
        current_user = get_current_user()
        if not current_user:
            return jsonify({'error': '用户未登录'}), 401
        
        # 获取请求数据
        data = request.get_json()
        filename = data.get('filename') if data else None
        
        # 获取用户目录
        user_horizon_dir = user_manager.get_user_processed_dir(current_user, 'horizon')
        user_upload_dir = user_manager.get_user_upload_dir(current_user, 'horizon')
        
        # 使用缓存的处理器实例
        processor_key = f"horizon_processor_{current_user}"
        if not hasattr(app, '_processors'):
            app._processors = {}
        
        if processor_key not in app._processors:
            app._processors[processor_key] = HorizonProcessor()
            app._processors[processor_key].set_user_directories(user_horizon_dir, user_upload_dir)
        
        processor = app._processors[processor_key]
        
        if filename:
            # 处理单个文件
            file_path = os.path.join(user_upload_dir, filename)
            if not os.path.exists(file_path):
                return jsonify({'success': False, 'error': f'文件不存在: {filename}'})
            
            result = processor.process(file_path, current_user)
            return jsonify(result)
        else:
            # 处理所有文件
            user_files = user_manager.get_user_files(current_user, 'horizon')
            results = []
            
            for file in user_files:
                file_path = os.path.join(user_upload_dir, file)
                if os.path.exists(file_path):
                    result = processor.process(file_path, current_user)
                    results.append(result)
            
            return jsonify({
                'success': True,
                'results': results,
                'message': f'处理了 {len(results)} 个文件'
            })
            
    except Exception as e:
        app.logger.error(f"处理弘积文件时发生错误: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/delete/horizon/<path:filename>', methods=['DELETE'])
@login_required
def delete_horizon_file(filename):
    """删除弘积文件"""
    try:
        current_user = get_current_user()
        if not current_user:
            return jsonify({'error': '用户未登录'}), 401
        
        # 获取用户目录
        user_upload_dir = user_manager.get_user_upload_dir(current_user, 'horizon')
        user_horizon_dir = user_manager.get_user_processed_dir(current_user, 'horizon')
        
        # 删除上传文件
        upload_file_path = os.path.join(user_upload_dir, filename)
        if os.path.exists(upload_file_path):
            os.remove(upload_file_path)
            app.logger.info(f"已删除上传文件: {upload_file_path}")
        
        # 删除相关的解压目录和配置文件
        base_name = os.path.splitext(filename)[0]
        unzip_dir = os.path.join(user_horizon_dir, 'unzip', base_name)
        config_file = os.path.join(user_horizon_dir, 'config', f"{base_name}.config")
        
        if os.path.exists(unzip_dir):
            import shutil
            shutil.rmtree(unzip_dir)
            app.logger.info(f"已删除解压目录: {unzip_dir}")
        
        if os.path.exists(config_file):
            os.remove(config_file)
            app.logger.info(f"已删除配置文件: {config_file}")
        
        return jsonify({'success': True, 'message': f'文件 {filename} 删除成功'})
        
    except Exception as e:
        app.logger.error(f"删除弘积文件时发生错误: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/download/<file_type>/<path:filename>')
@login_required
def download_file(file_type, filename):
    """文件下载 with user isolation"""
    try:
        current_user = get_current_user()
        if not current_user:
            return jsonify({'error': '用户未登录'}), 401
        
        processed_dir = user_manager.get_user_processed_dir(current_user, file_type)
        file_path = os.path.join(processed_dir, filename)
        
        if not os.path.exists(file_path):
            return jsonify({'error': '文件不存在'}), 404
        
        return send_file(file_path, as_attachment=True)
    except Exception as e:
        return jsonify({'error': str(e)}), 404

@app.route('/download_directory/<file_type>/<base_name>')
@login_required
def download_directory(file_type, base_name):
    """下载指定主文件名的所有相关文件"""
    import zipfile
    import tempfile
    from io import BytesIO
    
    try:
        current_user = get_current_user()
        if not current_user:
            return jsonify({'error': '用户未登录'}), 401
        
        # 获取用户目录
        user_upload_dir = user_manager.get_user_upload_dir(current_user, file_type)
        user_processed_dir = user_manager.get_user_processed_dir(current_user, file_type)
        ucs_dir = os.path.dirname(user_processed_dir)
        
        # 创建临时TAR文件
        temp_zip = BytesIO()
        with zipfile.ZipFile(temp_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
            files_added = []
            
            # 1. 添加上传的UCS和TAR文件
            if os.path.exists(user_upload_dir):
                for filename in os.listdir(user_upload_dir):
                    if filename.startswith(base_name):
                        file_path = os.path.join(user_upload_dir, filename)
                        zipf.write(file_path, f"uploads/{filename}")
                        files_added.append(f"uploads/{filename}")
            
            # 2. 添加解压目录
            if os.path.exists(user_processed_dir):
                for dir_name in os.listdir(user_processed_dir):
                    if dir_name.startswith(base_name):
                        dir_path = os.path.join(user_processed_dir, dir_name)
                        if os.path.isdir(dir_path):
                            for root, dirs, files in os.walk(dir_path):
                                for file in files:
                                    file_path = os.path.join(root, file)
                                    arc_name = os.path.relpath(file_path, user_processed_dir)
                                    zipf.write(file_path, f"processed/{arc_name}")
                                    files_added.append(f"processed/{arc_name}")
            
            # 3. 添加conf和base文件
            conf_dir = os.path.join(ucs_dir, 'conf')
            base_dir = os.path.join(ucs_dir, 'base')
            
            if os.path.exists(conf_dir):
                for filename in os.listdir(conf_dir):
                    if filename.startswith(base_name):
                        file_path = os.path.join(conf_dir, filename)
                        zipf.write(file_path, f"conf/{filename}")
                        files_added.append(f"conf/{filename}")
            
            if os.path.exists(base_dir):
                for filename in os.listdir(base_dir):
                    if filename.startswith(base_name):
                        file_path = os.path.join(base_dir, filename)
                        zipf.write(file_path, f"base/{filename}")
                        files_added.append(f"base/{filename}")
            
            # 4. 添加output目录下的文件
            conf_output_dir = os.path.join(conf_dir, 'output')
            base_output_dir = os.path.join(base_dir, 'output')
            
            if os.path.exists(conf_output_dir):
                for filename in os.listdir(conf_output_dir):
                    if filename.startswith(base_name):
                        file_path = os.path.join(conf_output_dir, filename)
                        zipf.write(file_path, f"conf/output/{filename}")
                        files_added.append(f"conf/output/{filename}")
            
            if os.path.exists(base_output_dir):
                for filename in os.listdir(base_output_dir):
                    if filename.startswith(base_name):
                        file_path = os.path.join(base_output_dir, filename)
                        zipf.write(file_path, f"base/output/{filename}")
                        files_added.append(f"base/output/{filename}")
        
        if not files_added:
            return jsonify({'error': '未找到相关文件'}), 404
        
        temp_zip.seek(0)
        return send_file(
            BytesIO(temp_zip.getvalue()),
            mimetype='application/zip',
            as_attachment=True,
            download_name=f"{base_name}_all_files.tar"
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/download_all_files/<file_type>')
@login_required
def download_all_files(file_type):
    """下载所有文件的所有状态内容"""
    import zipfile
    import tempfile
    from io import BytesIO
    
    try:
        current_user = get_current_user()
        if not current_user:
            return jsonify({'error': '用户未登录'}), 401
        
        # 获取用户目录
        user_upload_dir = user_manager.get_user_upload_dir(current_user, file_type)
        user_processed_dir = user_manager.get_user_processed_dir(current_user, file_type)
        ucs_dir = os.path.dirname(user_processed_dir)
        
        # 创建临时TAR文件
        temp_zip = BytesIO()
        with zipfile.ZipFile(temp_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
            files_added = []
            
            # 1. 添加所有上传的UCS和TAR文件
            if os.path.exists(user_upload_dir):
                for filename in os.listdir(user_upload_dir):
                    file_path = os.path.join(user_upload_dir, filename)
                    zipf.write(file_path, f"uploads/{filename}")
                    files_added.append(f"uploads/{filename}")
            
            # 2. 添加所有解压目录
            if os.path.exists(user_processed_dir):
                for dir_name in os.listdir(user_processed_dir):
                    dir_path = os.path.join(user_processed_dir, dir_name)
                    if os.path.isdir(dir_path):
                        for root, dirs, files in os.walk(dir_path):
                            for file in files:
                                file_path = os.path.join(root, file)
                                arc_name = os.path.relpath(file_path, user_processed_dir)
                                zipf.write(file_path, f"processed/{arc_name}")
                                files_added.append(f"processed/{arc_name}")
            
            # 3. 添加所有conf和base文件
            conf_dir = os.path.join(ucs_dir, 'conf')
            base_dir = os.path.join(ucs_dir, 'base')
            
            if os.path.exists(conf_dir):
                for filename in os.listdir(conf_dir):
                    file_path = os.path.join(conf_dir, filename)
                    zipf.write(file_path, f"conf/{filename}")
                    files_added.append(f"conf/{filename}")
            
            if os.path.exists(base_dir):
                for filename in os.listdir(base_dir):
                    file_path = os.path.join(base_dir, filename)
                    zipf.write(file_path, f"base/{filename}")
                    files_added.append(f"base/{filename}")
            
            # 4. 添加所有output目录下的文件
            conf_output_dir = os.path.join(conf_dir, 'output')
            base_output_dir = os.path.join(base_dir, 'output')
            
            if os.path.exists(conf_output_dir):
                for filename in os.listdir(conf_output_dir):
                    file_path = os.path.join(conf_output_dir, filename)
                    zipf.write(file_path, f"conf/output/{filename}")
                    files_added.append(f"conf/output/{filename}")
            
            if os.path.exists(base_output_dir):
                for filename in os.listdir(base_output_dir):
                    file_path = os.path.join(base_output_dir, filename)
                    zipf.write(file_path, f"base/output/{filename}")
                    files_added.append(f"base/output/{filename}")
        
        if not files_added:
            return jsonify({'error': '未找到任何文件'}), 404
        
        temp_zip.seek(0)
        return send_file(
            BytesIO(temp_zip.getvalue()),
            mimetype='application/zip',
            as_attachment=True,
            download_name=f"all_files_{file_type}.tar"
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/download_by_type/<file_type>/<content_type>')
@login_required
def download_by_type(file_type, content_type):
    """按类型下载文件内容"""
    import zipfile
    import tempfile
    from io import BytesIO
    
    try:
        current_user = get_current_user()
        if not current_user:
            return jsonify({'error': '用户未登录'}), 401
        
        # 获取用户目录
        user_upload_dir = user_manager.get_user_upload_dir(current_user, file_type)
        user_processed_dir = user_manager.get_user_processed_dir(current_user, file_type)
        ucs_dir = os.path.dirname(user_processed_dir)
        
        # 创建临时TAR文件
        temp_zip = BytesIO()
        with zipfile.ZipFile(temp_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
            files_added = []
            
            if content_type == 'ucs':
                # 下载所有UCS文件
                if os.path.exists(user_upload_dir):
                    for filename in os.listdir(user_upload_dir):
                        if filename.lower().endswith('.ucs'):
                            file_path = os.path.join(user_upload_dir, filename)
                            zipf.write(file_path, filename)
                            files_added.append(filename)
            
            elif content_type == 'tar':
                # 下载所有TAR文件
                if os.path.exists(user_upload_dir):
                    for filename in os.listdir(user_upload_dir):
                        if filename.lower().endswith('.tar'):
                            file_path = os.path.join(user_upload_dir, filename)
                            zipf.write(file_path, filename)
                            files_added.append(filename)
            
            elif content_type == 'extracted':
                # 下载所有已解压文件
                if os.path.exists(user_processed_dir):
                    for dir_name in os.listdir(user_processed_dir):
                        dir_path = os.path.join(user_processed_dir, dir_name)
                        if os.path.isdir(dir_path):
                            try:
                                for root, dirs, files in os.walk(dir_path):
                                    for file in files:
                                        file_path = os.path.join(root, file)
                                        # 使用相对于processed_dir的路径
                                        arc_name = os.path.relpath(file_path, user_processed_dir)
                                        zipf.write(file_path, arc_name)
                                        files_added.append(arc_name)
                            except Exception as e:
                                # 如果遍历失败，尝试直接添加目录内容
                                for root, dirs, files in os.walk(dir_path):
                                    for file in files:
                                        file_path = os.path.join(root, file)
                                        # 使用简单的文件名作为归档名
                                        arc_name = f"{dir_name}/{os.path.relpath(file_path, dir_path)}"
                                        zipf.write(file_path, arc_name)
                                        files_added.append(arc_name)
                                    break  # 只处理第一层
            
            elif content_type == 'conf':
                # 下载所有conf文件
                conf_dir = os.path.join(ucs_dir, 'conf')
                if os.path.exists(conf_dir):
                    for filename in os.listdir(conf_dir):
                        if filename.endswith('.conf'):
                            file_path = os.path.join(conf_dir, filename)
                            zipf.write(file_path, filename)
                            files_added.append(filename)
            
            elif content_type == 'base':
                # 下载所有base文件
                base_dir = os.path.join(ucs_dir, 'base')
                if os.path.exists(base_dir):
                    for filename in os.listdir(base_dir):
                        if filename.endswith('.conf'):
                            file_path = os.path.join(base_dir, filename)
                            zipf.write(file_path, filename)
                            files_added.append(filename)
            
            elif content_type == 'excel':
                # 下载所有Excel文件
                conf_output_dir = os.path.join(ucs_dir, 'conf', 'output')
                base_output_dir = os.path.join(ucs_dir, 'base', 'output')
                
                if os.path.exists(conf_output_dir):
                    for filename in os.listdir(conf_output_dir):
                        if filename.endswith('.xlsx'):
                            file_path = os.path.join(conf_output_dir, filename)
                            zipf.write(file_path, f"conf_output/{filename}")
                            files_added.append(f"conf_output/{filename}")
                
                if os.path.exists(base_output_dir):
                    for filename in os.listdir(base_output_dir):
                        if filename.endswith('.xlsx'):
                            file_path = os.path.join(base_output_dir, filename)
                            zipf.write(file_path, f"base_output/{filename}")
                            files_added.append(f"base_output/{filename}")
            
            elif content_type == 'txt':
                # 下载所有TXT文件（包括HJ和ATTN）
                conf_output_dir = os.path.join(ucs_dir, 'conf', 'output')
                base_output_dir = os.path.join(ucs_dir, 'base', 'output')
                
                if os.path.exists(conf_output_dir):
                    for filename in os.listdir(conf_output_dir):
                        if filename.endswith('.txt'):
                            file_path = os.path.join(conf_output_dir, filename)
                            zipf.write(file_path, f"conf_output/{filename}")
                            files_added.append(f"conf_output/{filename}")
                
                if os.path.exists(base_output_dir):
                    for filename in os.listdir(base_output_dir):
                        if filename.endswith('.txt'):
                            file_path = os.path.join(base_output_dir, filename)
                            zipf.write(file_path, f"base_output/{filename}")
                            files_added.append(f"base_output/{filename}")
        
        if not files_added:
            return jsonify({'error': f'未找到{content_type}类型的文件'}), 404
        
        temp_zip.seek(0)
        return send_file(
            BytesIO(temp_zip.getvalue()),
            mimetype='application/zip',
            as_attachment=True,
            download_name=f"{content_type}_files.tar"
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/download_by_group/<file_type>/<group_type>')
@login_required
def download_by_group(file_type, group_type):
    """按组下载文件内容"""
    import zipfile
    import tempfile
    from io import BytesIO
    import logging
    
    # 设置日志
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    try:
        current_user = get_current_user()
        if not current_user:
            return jsonify({'error': '用户未登录'}), 401
        
        # 获取用户目录
        user_upload_dir = user_manager.get_user_upload_dir(current_user, file_type)
        user_processed_dir = user_manager.get_user_processed_dir(current_user, file_type)
        ucs_dir = os.path.dirname(user_processed_dir)
        
        logger.info(f"下载组: {group_type}")
        logger.info(f"用户上传目录: {user_upload_dir}")
        logger.info(f"用户处理目录: {user_processed_dir}")
        logger.info(f"UCS目录: {ucs_dir}")
        
        # 创建临时TAR文件
        temp_zip = BytesIO()
        with zipfile.ZipFile(temp_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
            files_added = []
            
            if group_type == 'import':
                # 下载所有导入文件（UCS和TAR）
                if os.path.exists(user_upload_dir):
                    for filename in os.listdir(user_upload_dir):
                        if filename.lower().endswith(('.ucs', '.tar')):
                            file_path = os.path.join(user_upload_dir, filename)
                            zipf.write(file_path, filename)
                            files_added.append(filename)
            
            elif group_type == 'extracted':
                # 下载所有已解压文件
                logger.info(f"开始下载已解压文件，处理目录: {user_processed_dir}")
                if os.path.exists(user_processed_dir):
                    logger.info(f"处理目录存在，内容: {os.listdir(user_processed_dir)}")
                    for dir_name in os.listdir(user_processed_dir):
                        dir_path = os.path.join(user_processed_dir, dir_name)
                        logger.info(f"检查目录: {dir_path}")
                        if os.path.isdir(dir_path):
                            logger.info(f"目录存在，开始遍历: {dir_path}")
                            try:
                                for root, dirs, files in os.walk(dir_path):
                                    logger.info(f"遍历目录: {root}, 文件数: {len(files)}")
                                    for file in files:
                                        file_path = os.path.join(root, file)
                                        # 使用相对于processed_dir的路径
                                        arc_name = os.path.relpath(file_path, user_processed_dir)
                                        logger.info(f"添加文件: {file_path} -> {arc_name}")
                                        zipf.write(file_path, arc_name)
                                        files_added.append(arc_name)
                            except Exception as e:
                                logger.error(f"遍历目录失败: {e}")
                                # 如果遍历失败，尝试直接添加目录内容
                                for root, dirs, files in os.walk(dir_path):
                                    for file in files:
                                        file_path = os.path.join(root, file)
                                        # 使用简单的文件名作为归档名
                                        arc_name = f"{dir_name}/{os.path.relpath(file_path, dir_path)}"
                                        logger.info(f"备用方法添加文件: {file_path} -> {arc_name}")
                                        zipf.write(file_path, arc_name)
                                        files_added.append(arc_name)
                                    break  # 只处理第一层
                        else:
                            logger.warning(f"目录不存在: {dir_path}")
                else:
                    logger.warning(f"处理目录不存在: {user_processed_dir}")
            
            elif group_type == 'config':
                # 下载所有配置文件（conf和base）
                conf_dir = os.path.join(ucs_dir, 'conf')
                base_dir = os.path.join(ucs_dir, 'base')
                
                if os.path.exists(conf_dir):
                    for filename in os.listdir(conf_dir):
                        if filename.endswith('.conf'):
                            file_path = os.path.join(conf_dir, filename)
                            zipf.write(file_path, f"conf/{filename}")
                            files_added.append(f"conf/{filename}")
                
                if os.path.exists(base_dir):
                    for filename in os.listdir(base_dir):
                        if filename.endswith('.conf'):
                            file_path = os.path.join(base_dir, filename)
                            zipf.write(file_path, f"base/{filename}")
                            files_added.append(f"base/{filename}")
            
            elif group_type == 'output_base':
                # 下载所有base输出文件（Excel和TXT）
                base_output_dir = os.path.join(ucs_dir, 'base', 'output')
                
                if os.path.exists(base_output_dir):
                    for filename in os.listdir(base_output_dir):
                        if filename.endswith(('.xlsx', '.txt')):
                            file_path = os.path.join(base_output_dir, filename)
                            zipf.write(file_path, f"base_output/{filename}")
                            files_added.append(f"base_output/{filename}")
            
            elif group_type == 'output_conf':
                # 下载所有conf输出文件（Excel、HJ和ATTN）
                conf_output_dir = os.path.join(ucs_dir, 'conf', 'output')
                
                if os.path.exists(conf_output_dir):
                    for filename in os.listdir(conf_output_dir):
                        if filename.endswith(('.xlsx', '.txt')):
                            file_path = os.path.join(conf_output_dir, filename)
                            zipf.write(file_path, f"conf_output/{filename}")
                            files_added.append(f"conf_output/{filename}")
        
        if not files_added:
            return jsonify({'error': f'未找到{group_type}组的文件'}), 404
        
        temp_zip.seek(0)
        return send_file(
            BytesIO(temp_zip.getvalue()),
            mimetype='application/zip',
            as_attachment=True,
            download_name=f"{group_type}_files.tar"
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/download_translation_results/<file_type>/<result_type>')
@login_required
def download_translation_results(file_type, result_type):
    """下载翻译结果"""
    import zipfile
    import tempfile
    from io import BytesIO
    
    try:
        current_user = get_current_user()
        if not current_user:
            return jsonify({'error': '用户未登录'}), 401
        
        # 获取用户目录
        user_processed_dir = user_manager.get_user_processed_dir(current_user, file_type)
        ucs_dir = os.path.dirname(user_processed_dir)
        
        # 创建临时TAR文件
        temp_zip = BytesIO()
        with zipfile.ZipFile(temp_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
            files_added = []
            
            conf_output_dir = os.path.join(ucs_dir, 'conf', 'output')
            base_output_dir = os.path.join(ucs_dir, 'base', 'output')
            
            if result_type == 'excel':
                # 下载所有Excel文件
                if os.path.exists(conf_output_dir):
                    for filename in os.listdir(conf_output_dir):
                        if filename.endswith('.xlsx'):
                            file_path = os.path.join(conf_output_dir, filename)
                            zipf.write(file_path, f"conf_output/{filename}")
                            files_added.append(f"conf_output/{filename}")
                
                if os.path.exists(base_output_dir):
                    for filename in os.listdir(base_output_dir):
                        if filename.endswith('.xlsx'):
                            file_path = os.path.join(base_output_dir, filename)
                            zipf.write(file_path, f"base_output/{filename}")
                            files_added.append(f"base_output/{filename}")
            
            elif result_type == 'txt':
                # 下载所有TXT文件（包括HJ和ATTN）
                if os.path.exists(conf_output_dir):
                    for filename in os.listdir(conf_output_dir):
                        if filename.endswith('.txt'):
                            file_path = os.path.join(conf_output_dir, filename)
                            zipf.write(file_path, f"conf_output/{filename}")
                            files_added.append(f"conf_output/{filename}")
                
                if os.path.exists(base_output_dir):
                    for filename in os.listdir(base_output_dir):
                        if filename.endswith('.txt'):
                            file_path = os.path.join(base_output_dir, filename)
                            zipf.write(file_path, f"base_output/{filename}")
                            files_added.append(f"base_output/{filename}")
            
            elif result_type == 'all':
                # 下载所有翻译结果（Excel、HJ和ATTN）
                if os.path.exists(conf_output_dir):
                    for filename in os.listdir(conf_output_dir):
                        if filename.endswith(('.xlsx', '.txt')):
                            file_path = os.path.join(conf_output_dir, filename)
                            zipf.write(file_path, f"conf_output/{filename}")
                            files_added.append(f"conf_output/{filename}")
                
                if os.path.exists(base_output_dir):
                    for filename in os.listdir(base_output_dir):
                        if filename.endswith(('.xlsx', '.txt')):
                            file_path = os.path.join(base_output_dir, filename)
                            zipf.write(file_path, f"base_output/{filename}")
                            files_added.append(f"base_output/{filename}")
        
        if not files_added:
            return jsonify({'error': f'未找到{result_type}类型的翻译结果'}), 404
        
        temp_zip.seek(0)
        return send_file(
            BytesIO(temp_zip.getvalue()),
            mimetype='application/zip',
            as_attachment=True,
            download_name=f"translation_results_{result_type}.tar"
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/delete_all_files/<file_type>', methods=['POST'])
@login_required
def delete_all_files(file_type):
    """删除用户的所有相关文件"""
    import shutil
    from datetime import datetime
    
    try:
        current_user = get_current_user()
        if not current_user:
            return jsonify({'error': '用户未登录'}), 401
        
        # 获取用户目录
        user_upload_dir = user_manager.get_user_upload_dir(current_user, file_type)
        user_processed_dir = user_manager.get_user_processed_dir(current_user, file_type)
        ucs_dir = os.path.dirname(user_processed_dir)
        
        # 创建删除目录
        data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
        delete_dir = os.path.join(data_dir, 'delete')
        user_delete_dir = os.path.join(delete_dir, current_user)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        final_delete_dir = os.path.join(user_delete_dir, timestamp)
        
        os.makedirs(final_delete_dir, exist_ok=True)
        
        deleted_items = []
        
        # 1. 移动上传文件
        if os.path.exists(user_upload_dir):
            upload_delete_dir = os.path.join(final_delete_dir, 'uploads')
            os.makedirs(upload_delete_dir, exist_ok=True)
            for filename in os.listdir(user_upload_dir):
                src_path = os.path.join(user_upload_dir, filename)
                dst_path = os.path.join(upload_delete_dir, filename)
                shutil.move(src_path, dst_path)
                deleted_items.append(f"uploads/{filename}")
        
        # 2. 移动处理文件
        if os.path.exists(user_processed_dir):
            processed_delete_dir = os.path.join(final_delete_dir, 'processed')
            os.makedirs(processed_delete_dir, exist_ok=True)
            for dir_name in os.listdir(user_processed_dir):
                src_path = os.path.join(user_processed_dir, dir_name)
                dst_path = os.path.join(processed_delete_dir, dir_name)
                shutil.move(src_path, dst_path)
                deleted_items.append(f"processed/{dir_name}")
        
        # 3. 移动conf和base文件
        conf_dir = os.path.join(ucs_dir, 'conf')
        base_dir = os.path.join(ucs_dir, 'base')
        
        if os.path.exists(conf_dir):
            conf_delete_dir = os.path.join(final_delete_dir, 'conf')
            os.makedirs(conf_delete_dir, exist_ok=True)
            for filename in os.listdir(conf_dir):
                src_path = os.path.join(conf_dir, filename)
                dst_path = os.path.join(conf_delete_dir, filename)
                shutil.move(src_path, dst_path)
                deleted_items.append(f"conf/{filename}")
        
        if os.path.exists(base_dir):
            base_delete_dir = os.path.join(final_delete_dir, 'base')
            os.makedirs(base_delete_dir, exist_ok=True)
            for filename in os.listdir(base_dir):
                src_path = os.path.join(base_dir, filename)
                dst_path = os.path.join(base_delete_dir, filename)
                shutil.move(src_path, dst_path)
                deleted_items.append(f"base/{filename}")
        
        # 4. 移动output文件
        conf_output_dir = os.path.join(conf_dir, 'output')
        base_output_dir = os.path.join(base_dir, 'output')
        
        if os.path.exists(conf_output_dir):
            conf_output_delete_dir = os.path.join(final_delete_dir, 'conf_output')
            os.makedirs(conf_output_delete_dir, exist_ok=True)
            for filename in os.listdir(conf_output_dir):
                src_path = os.path.join(conf_output_dir, filename)
                dst_path = os.path.join(conf_output_delete_dir, filename)
                shutil.move(src_path, dst_path)
                deleted_items.append(f"conf_output/{filename}")
        
        if os.path.exists(base_output_dir):
            base_output_delete_dir = os.path.join(final_delete_dir, 'base_output')
            os.makedirs(base_output_delete_dir, exist_ok=True)
            for filename in os.listdir(base_output_dir):
                src_path = os.path.join(base_output_dir, filename)
                dst_path = os.path.join(base_output_delete_dir, filename)
                shutil.move(src_path, dst_path)
                deleted_items.append(f"base_output/{filename}")
        
        return jsonify({
            'success': True,
            'message': f'已删除 {len(deleted_items)} 个文件/目录',
            'deleted_items': deleted_items,
            'delete_location': final_delete_dir
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/files/<file_type>')
@login_required
def get_user_files(file_type):
    """获取用户文件列表"""
    current_user = get_current_user()
    if not current_user:
        return jsonify({'error': '用户未登录'}), 401
    
    files = user_manager.get_user_files(current_user, file_type)
    processed_files = user_manager.get_user_processed_files(current_user, file_type)

    if file_type == 'horizon':
        # 为弘积文件返回详细文件信息
        from core.processors.horizon_processor import HorizonProcessor
        
        file_details = []
        for filename in files:
            file_path = os.path.join(user_manager.get_user_upload_dir(current_user, file_type), filename)
            if os.path.exists(file_path):
                stat = os.stat(file_path)
                
                # 获取处理状态
                processor = HorizonProcessor()
                user_horizon_dir = user_manager.get_user_processed_dir(current_user, file_type)
                processor.set_user_directories(user_horizon_dir, user_manager.get_user_upload_dir(current_user, file_type))
                status_info = processor.get_processing_status(filename)
                
                # 根据处理状态确定显示状态
                if status_info.get('upload') and status_info.get('unzip') and status_info.get('config'):
                    if status_info.get('compare'):
                        status = 'completed'
                    else:
                        status = 'processing'
                elif status_info.get('upload'):
                    status = 'pending'
                else:
                    status = 'error'
                
                # 提取配置文件信息
                config_info = {
                    'hostname': '',
                    'vrrp_unit_id': '',
                    'first_ip_address': ''
                }
                
                if status_info.get('config'):
                    # 如果配置文件已提取，获取配置信息
                    config_file = os.path.join(user_horizon_dir, 'config', f"{os.path.splitext(filename)[0].replace('.tar', '')}.config")
                    if os.path.exists(config_file):
                        config_info = processor.extract_config_info(config_file)
                
                file_details.append({
                    'name': filename,
                    'size': stat.st_size,
                    'status': status,
                    'status_details': status_info,
                    'config_info': config_info
                })
        
        # 按VRRP Unit-ID分组
        vrrp_groups = {}
        for file_info in file_details:
            vrrp_id = file_info['config_info'].get('vrrp_unit_id', '')
            if vrrp_id:
                if vrrp_id not in vrrp_groups:
                    vrrp_groups[vrrp_id] = []
                vrrp_groups[vrrp_id].append(file_info)
        
        # 生成跨VRRP组的对比结果
        comparison_pairs = []
        vrrp_ids = sorted(vrrp_groups.keys())
        
        for i in range(len(vrrp_ids)):
            for j in range(i + 1, len(vrrp_ids)):
                vrrp_id_1 = vrrp_ids[i]
                vrrp_id_2 = vrrp_ids[j]
                group_1 = vrrp_groups[vrrp_id_1]
                group_2 = vrrp_groups[vrrp_id_2]
                
                # 对两个VRRP组进行跨组对比
                best_pair = processor.find_best_match_between_groups(group_1, group_2, vrrp_id_1, vrrp_id_2)
                if best_pair:
                    comparison_pairs.append({
                        'group1_id': vrrp_id_1,
                        'group2_id': vrrp_id_2,
                        'file1': best_pair['file1'],
                        'file2': best_pair['file2'],
                        'differences': best_pair['differences'],
                        'stats': best_pair['stats']
                    })
        
        return jsonify({
            'success': True,
            'files': file_details,
            'vrrp_groups': vrrp_groups,
            'comparison_pairs': comparison_pairs,
            'processed_files': processed_files
        })
    else:
        # 其他文件类型保持原有逻辑
        # 分组：去除 .ucs/.tar/_bigip/_conf/_base 等后缀
        file_groups = {}
        for filename in files:
            base = filename
            for suffix in ['.ucs', '.tar', '_bigip.conf', '_conf.conf', '_base.conf', '.conf']:
                if base.endswith(suffix):
                    base = base[: -len(suffix)]
            if base not in file_groups:
                file_groups[base] = {'ucs': False, 'tar': False}
            if filename.lower().endswith('.ucs'):
                file_groups[base]['ucs'] = True
            elif filename.lower().endswith('.tar'):
                file_groups[base]['tar'] = True
        
        return jsonify({
            'success': True,
            'file_groups': file_groups,
            'files': files,
            'processed_files': processed_files
        })

@app.route('/extracted-dirs/<file_type>')
@login_required
def get_extracted_dirs(file_type):
    """获取用户解压目录列表"""
    current_user = get_current_user()
    if not current_user:
        return jsonify({'error': '用户未登录'}), 401
    
    processed_dir = user_manager.get_user_processed_dir(current_user, file_type)
    extracted_dirs = []
    
    if os.path.exists(processed_dir):
        for dir_name in os.listdir(processed_dir):
            dir_path = os.path.join(processed_dir, dir_name)
            if os.path.isdir(dir_path):
                extracted_dirs.append(dir_path)
    
    return jsonify({
        'success': True,
        'dirs': extracted_dirs
    })

@app.route('/extracted-configs/<file_type>')
@login_required
def get_extracted_configs(file_type):
    """按主文件名分组显示 conf 和 base 文件，主文件名去除 _bigip/_conf/_base 等后缀"""
    current_user = get_current_user()
    if not current_user:
        return jsonify({'error': '用户未登录'}), 401

    processed_dir = user_manager.get_user_processed_dir(current_user, file_type)
    ucs_dir = os.path.dirname(processed_dir)  # processed的上一级就是ucs

    conf_dir = os.path.join(ucs_dir, 'conf')
    base_dir = os.path.join(ucs_dir, 'base')

    conf_files = []
    base_files = []

    if os.path.exists(conf_dir):
        conf_files = [f for f in os.listdir(conf_dir) if f.endswith('.conf')]
    if os.path.exists(base_dir):
        base_files = [f for f in os.listdir(base_dir) if f.endswith('.conf')]

    # 分组：去除 _bigip/_conf/_base 等后缀
    file_groups = {}
    for conf_file in conf_files:
        base = conf_file
        for suffix in ['_bigip.conf', '_conf.conf', '_base.conf', '.conf']:
            if base.endswith(suffix):
                base = base[: -len(suffix)]
        if base not in file_groups:
            file_groups[base] = {'conf': False, 'base': False}
        file_groups[base]['conf'] = True
    for base_file in base_files:
        base = base_file
        for suffix in ['_bigip_base.conf', '_base.conf', '_conf.conf', '.conf']:
            if base.endswith(suffix):
                base = base[: -len(suffix)]
        if base not in file_groups:
            file_groups[base] = {'conf': False, 'base': False}
        file_groups[base]['base'] = True

    return jsonify({
        'success': True,
        'file_groups': file_groups,
        'conf_files': conf_files,
        'base_files': base_files,
        'conf_dir': conf_dir,
        'base_dir': base_dir
    })

@app.route('/ucs_status_matrix')
@login_required
def ucs_status_matrix():
    """返回所有主文件名的5个状态（ucs, tar, extracted, conf, base）"""
    import os
    current_user = get_current_user()
    if not current_user:
        return jsonify({'error': '用户未登录'}), 401

    # 0. 统一主文件名分组
    def normalize_base(name):
        for suffix in ['_bigip_base', '_bigip', '_base', '_conf']:
            if name.endswith(suffix):
                return name[: -len(suffix)]
        return name

    # 1. 获取上传文件（ucs/tar）
    files = user_manager.get_user_files(current_user, 'ucs')
    upload_groups = {}
    for filename in files:
        base = filename
        for suffix in ['.ucs', '.tar', '_bigip.conf', '_conf.conf', '_base.conf', '.conf']:
            if base.endswith(suffix):
                base = base[: -len(suffix)]
        if base not in upload_groups:
            upload_groups[base] = {'ucs': False, 'tar': False}
        if filename.lower().endswith('.ucs'):
            upload_groups[base]['ucs'] = True
        elif filename.lower().endswith('.tar'):
            upload_groups[base]['tar'] = True

    # 2. 获取已解压目录
    processed_dir = user_manager.get_user_processed_dir(current_user, 'ucs')
    extracted_groups = set()
    if os.path.exists(processed_dir):
        for dir_name in os.listdir(processed_dir):
            dir_path = os.path.join(processed_dir, dir_name)
            if os.path.isdir(dir_path):
                base = dir_name
                for suffix in ['_bigip', '_conf', '_base']:
                    if base.endswith(suffix):
                        base = base[: -len(suffix)]
                extracted_groups.add(base)

    # 3. 获取conf/base文件
    ucs_dir = os.path.dirname(processed_dir)
    conf_dir = os.path.join(ucs_dir, 'conf')
    base_dir = os.path.join(ucs_dir, 'base')
    conf_files = []
    base_files = []
    if os.path.exists(conf_dir):
        conf_files = [f for f in os.listdir(conf_dir) if f.endswith('.conf')]
    if os.path.exists(base_dir):
        base_files = [f for f in os.listdir(base_dir) if f.endswith('.conf')]
    conf_groups = set()
    base_groups = set()
    for conf_file in conf_files:
        base = conf_file
        for suffix in ['_bigip.conf', '_conf.conf', '_base.conf', '.conf']:
            if base.endswith(suffix):
                base = base[: -len(suffix)]
        conf_groups.add(base)
    for base_file in base_files:
        base = base_file
        for suffix in ['_bigip_base.conf', '_base.conf', '_conf.conf', '.conf']:
            if base.endswith(suffix):
                base = base[: -len(suffix)]
        base_groups.add(base)

    # 4. 检查Excel和TXT文件状态（分别检查conf和base的output目录）
    excel_conf_groups = set()
    txt_conf_groups = set()
    attention_conf_groups = set()
    excel_base_groups = set()
    txt_base_groups = set()
    conf_output_dir = os.path.join(conf_dir, 'output')
    base_output_dir = os.path.join(base_dir, 'output')
    
    # 检查conf/output目录下的Excel、TXT和Attention文件
    if os.path.exists(conf_output_dir):
        for file in os.listdir(conf_output_dir):
            if file.endswith('.xlsx'):
                base = file.replace('.xlsx', '')
                excel_conf_groups.add(base)
            elif file.endswith('.txt') and not file.endswith('_attention.txt'):
                base = file.replace('.txt', '')
                txt_conf_groups.add(base)
            elif file.endswith('_attention.txt'):
                base = file.replace('_attention.txt', '')
                attention_conf_groups.add(base)
    # 检查base/output目录下的Excel和TXT文件
    if os.path.exists(base_output_dir):
        for file in os.listdir(base_output_dir):
            if file.endswith('.xlsx'):
                base = file.replace('.xlsx', '')
                excel_base_groups.add(base)
            elif file.endswith('.txt'):
                base = file.replace('.txt', '')
                txt_base_groups.add(base)
    
    # 5. 汇总所有主文件名
    all_bases = set(upload_groups.keys()) | extracted_groups | conf_groups | base_groups | excel_conf_groups | txt_conf_groups | attention_conf_groups | excel_base_groups | txt_base_groups
    status_matrix = {}
    for base in all_bases:
        status_matrix[base] = {
            'ucs': upload_groups.get(base, {}).get('ucs', False),
            'tar': upload_groups.get(base, {}).get('tar', False),
            'extracted': base in extracted_groups,
            'conf': base in conf_groups,
            'base': base in base_groups,
            'excel_conf': base in excel_conf_groups,
            'txt_conf': base in txt_conf_groups,
            'attention_conf': base in attention_conf_groups,
            'excel_base': base in excel_base_groups,
            'txt_base': base in txt_base_groups
        }

    # 6. 合并所有子文件状态到主key
    merged_matrix = {}
    for base in all_bases:
        main_key = normalize_base(base)
        if main_key not in merged_matrix:
            merged_matrix[main_key] = {
                'ucs': False, 'tar': False, 'extracted': False, 'conf': False, 'base': False, 
                'excel_conf': False, 'txt_conf': False, 'attention_conf': False, 'excel_base': False, 'txt_base': False
            }
        for k in ['ucs', 'tar', 'extracted', 'conf', 'base', 'excel_conf', 'txt_conf', 'attention_conf', 'excel_base', 'txt_base']:
            merged_matrix[main_key][k] = merged_matrix[main_key][k] or status_matrix[base][k]
    return jsonify({'success': True, 'matrix': merged_matrix})

@app.route('/show_status_matrix')
@login_required
def show_status_matrix():
    """返回所有show主文件名的状态（txt, conf, excel, log等）"""
    import os
    current_user = get_current_user()
    if not current_user:
        return jsonify({'error': '用户未登录'}), 401

    # 0. 统一主文件名分组
    def normalize_base(name):
        for suffix in ['.txt', '.conf', '.log', '_conf', '_base']:
            if name.endswith(suffix):
                return name[: -len(suffix)]
        return name

    # 1. 获取上传文件（txt/conf）
    files = user_manager.get_user_files(current_user, 'show')
    upload_groups = {}
    for filename in files:
        base = filename
        for suffix in ['.txt', '.conf', '.log']:
            if base.endswith(suffix):
                base = base[: -len(suffix)]
        if base not in upload_groups:
            upload_groups[base] = {'txt': False, 'conf': False, 'log': False}
        if filename.lower().endswith('.txt'):
            upload_groups[base]['txt'] = True
        elif filename.lower().endswith('.conf'):
            upload_groups[base]['conf'] = True
        elif filename.lower().endswith('.log'):
            upload_groups[base]['log'] = True

    # 2. 获取已处理目录
    processed_dir = user_manager.get_user_processed_dir(current_user, 'show')
    processed_groups = set()
    if os.path.exists(processed_dir):
        for dir_name in os.listdir(processed_dir):
            dir_path = os.path.join(processed_dir, dir_name)
            if os.path.isdir(dir_path):
                base = dir_name
                for suffix in ['_conf', '_base']:
                    if base.endswith(suffix):
                        base = base[: -len(suffix)]
                processed_groups.add(base)

    # 3. 检查Excel和LOG文件状态（output目录）
    excel_groups = set()
    log_groups = set()
    output_dir = os.path.join(processed_dir, 'output')
    if os.path.exists(output_dir):
        for file in os.listdir(output_dir):
            if file.endswith('.xlsx'):
                base = file.replace('.xlsx', '')
                excel_groups.add(base)
            elif file.endswith('.log'):
                base = file.replace('.log', '')
                log_groups.add(base)

    # 4. 汇总所有主文件名
    all_bases = set(upload_groups.keys()) | processed_groups | excel_groups | log_groups
    status_matrix = {}
    for base in all_bases:
        status_matrix[base] = {
            'txt': upload_groups.get(base, {}).get('txt', False),
            'conf': upload_groups.get(base, {}).get('conf', False),
            'log': upload_groups.get(base, {}).get('log', False),
            'processed': base in processed_groups,
            'excel': base in excel_groups,
            'log_output': base in log_groups
        }
    # 合并所有子文件状态到主key
    merged_matrix = {}
    for base in all_bases:
        main_key = normalize_base(base)
        if main_key not in merged_matrix:
            merged_matrix[main_key] = {
                'txt': False, 'conf': False, 'log': False, 'processed': False, 'excel': False, 'log_output': False
            }
        for k in ['txt', 'conf', 'log', 'processed', 'excel', 'log_output']:
            merged_matrix[main_key][k] = merged_matrix[main_key][k] or status_matrix[base][k]
    return jsonify({'success': True, 'matrix': merged_matrix})

@app.route('/logs')
@login_required
def get_logs():
    """获取处理日志"""
    current_user = get_current_user()
    if not current_user:
        return jsonify({'error': '用户未登录'}), 401
    
    try:
        lines = request.args.get('lines', 5, type=int)
        if lines > 50:
            lines = 50
        
        log_file = os.path.join(Config.DATA_DIR, 'logs', 'app.log')
        if not os.path.exists(log_file):
            return jsonify({'logs': [], 'message': '日志文件不存在'})
        
        # 读取最近N行日志
        with open(log_file, 'r', encoding='utf-8') as f:
            all_lines = f.readlines()
            recent_lines = all_lines[-lines:] if len(all_lines) >= lines else all_lines
        
        # 格式化日志内容
        formatted_logs = []
        for line in recent_lines:
            line = line.strip()
            if line:
                formatted_logs.append(line)
        
        return jsonify({
            'logs': formatted_logs,
            'total_lines': len(all_lines),
            'showing_lines': len(formatted_logs)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/clear_logs', methods=['POST'])
@login_required
def clear_logs():
    log_path = os.path.join('data', 'logs', 'app.log')
    try:
        with open(log_path, 'w', encoding='utf-8') as f:
            f.write('')
        return jsonify({'success': True, 'message': '日志已清空'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.errorhandler(413)
def request_entity_too_large(error):
    """文件过大错误处理"""
    return jsonify({
        'error': f'文件大小超过限制 ({Config.MAX_CONTENT_LENGTH // (1024*1024)}MB)'
    }), 413

@app.errorhandler(500)
def internal_error(error):
    """内部错误处理"""
    return jsonify({'error': '服务器内部错误'}), 500

@app.errorhandler(404)
def not_found_error(error):
    """404错误处理"""
    return jsonify({'error': '请求的资源不存在'}), 404

@app.route('/preview_config/<path:filename>')
@login_required
def preview_config_file(filename):
    """预览配置文件内容"""
    try:
        current_user = get_current_user()
        if not current_user:
            return jsonify({'error': '用户未登录'}), 401
        
        # 获取用户目录
        user_horizon_dir = user_manager.get_user_processed_dir(current_user, 'horizon')
        config_dir = os.path.join(user_horizon_dir, 'config')
        config_file_path = os.path.join(config_dir, filename)
        
        if not os.path.exists(config_file_path):
            return jsonify({'error': '配置文件不存在'}), 404
        
        # 读取配置文件内容
        try:
            with open(config_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return jsonify({
                'success': True,
                'content': content
            })
        except UnicodeDecodeError:
            # 如果UTF-8解码失败，尝试其他编码
            with open(config_file_path, 'r', encoding='gbk') as f:
                content = f.read()
            return jsonify({
                'success': True,
                'content': content
            })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/download_config/<path:filename>')
@login_required
def download_config_file(filename):
    """下载配置文件"""
    try:
        current_user = get_current_user()
        if not current_user:
            return jsonify({'error': '用户未登录'}), 401
        
        # 获取用户目录
        user_horizon_dir = user_manager.get_user_processed_dir(current_user, 'horizon')
        config_dir = os.path.join(user_horizon_dir, 'config')
        config_file_path = os.path.join(config_dir, filename)
        
        if not os.path.exists(config_file_path):
            return jsonify({'error': '配置文件不存在'}), 404
        
        return send_file(config_file_path, as_attachment=True)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/horizon_compare_results')
@login_required
def get_horizon_compare_results():
    """获取弘积配置对比结果"""
    current_user = get_current_user()
    if not current_user:
        return jsonify({'error': '用户未登录'}), 401
    
    try:
        from core.processors.horizon_processor import HorizonProcessor
        
        # 获取用户目录
        user_horizon_dir = user_manager.get_user_processed_dir(current_user, 'horizon')
        user_upload_dir = user_manager.get_user_upload_dir(current_user, 'horizon')
        
        # 初始化处理器（使用用户特定的实例）
        processor_key = f"horizon_processor_{current_user}"
        if not hasattr(app, '_processors'):
            app._processors = {}
        
        if processor_key not in app._processors:
            app._processors[processor_key] = HorizonProcessor()
            app._processors[processor_key].set_user_directories(user_horizon_dir, user_upload_dir)
        
        processor = app._processors[processor_key]
        
        # 获取配置文件列表
        config_files = []
        config_dir = os.path.join(user_horizon_dir, 'config')
        if os.path.exists(config_dir):
            for file in os.listdir(config_dir):
                if file.endswith('.config'):
                    config_file = os.path.join(config_dir, file)
                    config_files.append(config_file)
        
        if len(config_files) < 2:
            return jsonify({
                'success': True,
                'message': '需要至少两个配置文件才能进行对比',
                'results': None
            })
        
        # 使用新的对比逻辑
        comparison_result = processor.compare_configs(config_files)
        
        if "error" in comparison_result:
            return jsonify({
                'success': False,
                'error': comparison_result['error']
            })
        
        return jsonify({
            'success': True,
            'results': comparison_result
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'获取对比结果失败: {str(e)}'
        })

def main() -> None:
    """Run the web application"""
    Config.init()
    app.run(host=Config.WEB_HOST, port=Config.WEB_PORT, debug=Config.DEBUG_MODE, use_reloader=False)

if __name__ == '__main__':
    main()

print("Registered routes:")
for rule in app.url_map.iter_rules():
    print(f"Endpoint: {rule.endpoint}, Path: {rule.rule}") 