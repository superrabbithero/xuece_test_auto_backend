#在 routes.py中，提供基础的 RESTful API，例如获取已连接的设备列表、项目管理、页面管理等。

from flask import jsonify, Blueprint, request
import subprocess
import re
from app.repositories import ProjectRepository, PageRepository

bp = Blueprint('main', __name__)

@bp.route('/api/devices', methods=['GET'])
def get_devices():
    """获取通过 ADB 连接的设备列表"""
    try:
        result = subprocess.run(['adb', 'devices'], capture_output=True, text=True, check=True)
        lines = result.stdout.strip().split('\n')[1:]  # 跳过第一行 'List of devices attached'
        devices = []
        for line in lines:
            if line.strip():
                parts = line.split('\t')
                if len(parts) >= 2:
                    devices.append({'udid': parts[0], 'status': parts[1]})
        return jsonify(devices)
    except FileNotFoundError:
        # 服务器未安装 adb 或 adb 不在 PATH 中
        return jsonify([])
    except subprocess.CalledProcessError as e:
        return jsonify({'error': str(e)}), 500

# 项目管理 API

@bp.route('/api/projects', methods=['GET'])
def get_projects():
    """获取所有项目"""
    projects = ProjectRepository.get_all()
    return jsonify([project.to_dict() for project in projects])

@bp.route('/api/projects/<int:project_id>', methods=['GET'])
def get_project(project_id):
    """获取单个项目"""
    project = ProjectRepository.get_by_id(project_id)
    if not project:
        return jsonify({'error': '项目不存在'}), 404
    return jsonify(project.to_dict())

@bp.route('/api/projects', methods=['POST'])
def create_project():
    """创建新项目"""
    data = request.get_json()
    if not data or 'name' not in data:
        return jsonify({'error': '缺少项目名称'}), 400
    
    name = data['name']
    if ProjectRepository.get_by_name(name):
        return jsonify({'error': '项目名称已存在'}), 400
    
    project = ProjectRepository.create(name)
    return jsonify(project.to_dict()), 201

@bp.route('/api/projects/<int:project_id>', methods=['PUT'])
def update_project(project_id):
    """更新项目"""
    data = request.get_json()
    if not data or 'name' not in data:
        return jsonify({'error': '缺少项目名称'}), 400
    
    project = ProjectRepository.update(project_id, data['name'])
    if not project:
        return jsonify({'error': '项目不存在'}), 404
    
    return jsonify(project.to_dict())

@bp.route('/api/projects/<int:project_id>', methods=['DELETE'])
def delete_project(project_id):
    """删除项目"""
    if not ProjectRepository.delete(project_id):
        return jsonify({'error': '项目不存在'}), 404
    
    return jsonify({'message': '项目删除成功'})

# 页面管理 API

@bp.route('/api/pages', methods=['GET'])
def get_pages():
    """获取所有页面，支持分页和项目过滤"""
    page = request.args.get('page', default=1, type=int)
    per_page = request.args.get('per_page', default=10, type=int)
    project_id = request.args.get('project_id', type=int)
    
    pagination = PageRepository.get_all(page=page, per_page=per_page, project_id=project_id)
    
    return jsonify({
        'items': [page.to_dict() for page in pagination.items],
        'total': pagination.total,
        'page': pagination.page,
        'per_page': pagination.per_page,
        'pages': pagination.pages
    })

@bp.route('/api/pages/<int:page_id>', methods=['GET'])
def get_page(page_id):
    """获取单个页面"""
    page = PageRepository.get_by_id(page_id)
    if not page:
        return jsonify({'error': '页面不存在'}), 404
    return jsonify(page.to_dict())

@bp.route('/api/pages', methods=['POST'])
def create_page():
    """创建新页面"""
    data = request.get_json()
    
    # 验证必填字段
    if not data or 'project_id' not in data or 'name' not in data:
        return jsonify({'error': '缺少必填字段'}), 400
    
    project_id = data['project_id']
    name = data['name']
    parent_page_id = data.get('parent_page_id')
    elements = data.get('elements')
    
    # 检查项目是否存在
    if not ProjectRepository.get_by_id(project_id):
        return jsonify({'error': '项目不存在'}), 404
    
    # 检查同一项目下是否存在同名页面
    if PageRepository.get_by_name_and_project(name, project_id):
        return jsonify({'error': '页面名称已存在'}), 400
    
    page = PageRepository.create(project_id, name, parent_page_id, elements)
    return jsonify(page.to_dict()), 201

@bp.route('/api/pages/<int:page_id>', methods=['PUT'])
def update_page(page_id):
    """更新页面"""
    data = request.get_json()
    if not data:
        return jsonify({'error': '缺少更新数据'}), 400
    
    name = data.get('name')
    parent_page_id = data.get('parent_page_id')
    elements = data.get('elements')
    
    # 如果更新名称，检查是否与同一项目下其他页面重名
    if name:
        existing_page = PageRepository.get_by_id(page_id)
        if not existing_page:
            return jsonify({'error': '页面不存在'}), 404
        
        duplicate_page = PageRepository.get_by_name_and_project(name, existing_page.project_id)
        if duplicate_page and duplicate_page.id != page_id:
            return jsonify({'error': '页面名称已存在'}), 400
    
    page = PageRepository.update(page_id, name, parent_page_id, elements)
    if not page:
        return jsonify({'error': '页面不存在'}), 404
    
    return jsonify(page.to_dict())

@bp.route('/api/pages/<int:page_id>', methods=['DELETE'])
def delete_page(page_id):
    """删除页面"""
    if not PageRepository.delete(page_id):
        return jsonify({'error': '页面不存在'}), 404
    
    return jsonify({'message': '页面删除成功'})