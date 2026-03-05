from app.models import Page
from app import db

class PageRepository:
    @staticmethod
    def get_all(page=1, per_page=10, project_id=None):
        """获取所有页面，支持分页和按项目过滤"""
        query = Page.query
        if project_id:
            query = query.filter_by(project_id=project_id)
        
        pagination = query.order_by(Page.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return pagination
    
    @staticmethod
    def get_by_id(page_id):
        """根据ID获取页面"""
        return Page.query.get(page_id)
    
    @staticmethod
    def get_by_name_and_project(name, project_id):
        """根据名称和项目ID获取页面"""
        return Page.query.filter_by(name=name, project_id=project_id).first()
    
    @staticmethod
    def create(project_id, name, parent_page_id=None, elements=None):
        """创建新页面"""
        page = Page(
            project_id=project_id,
            name=name,
            parent_page_id=parent_page_id,
            elements=elements or {}
        )
        db.session.add(page)
        db.session.commit()
        return page
    
    @staticmethod
    def update(page_id, name=None, parent_page_id=None, elements=None):
        """更新页面信息"""
        page = Page.query.get(page_id)
        if not page:
            return None
        
        if name is not None:
            page.name = name
        if parent_page_id is not None:
            page.parent_page_id = parent_page_id
        if elements is not None:
            page.elements = elements
        
        db.session.commit()
        return page
    
    @staticmethod
    def delete(page_id):
        """删除页面"""
        page = Page.query.get(page_id)
        if page:
            db.session.delete(page)
            db.session.commit()
            return True
        return False
    
    @staticmethod
    def get_by_project(project_id):
        """根据项目ID获取所有页面"""
        return Page.query.filter_by(project_id=project_id).all()
    
    @staticmethod
    def get_children(page_id):
        """获取页面的所有子页面"""
        return Page.query.filter_by(parent_page_id=page_id).all()
