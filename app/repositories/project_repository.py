from app.models import Project
from app import db

class ProjectRepository:
    @staticmethod
    def get_all():
        """获取所有项目"""
        return Project.query.all()
    
    @staticmethod
    def get_by_id(project_id):
        """根据ID获取项目"""
        return Project.query.get(project_id)
    
    @staticmethod
    def get_by_name(name):
        """根据名称获取项目"""
        return Project.query.filter_by(name=name).first()
    
    @staticmethod
    def create(name):
        """创建新项目"""
        project = Project(name=name)
        db.session.add(project)
        db.session.commit()
        return project
    
    @staticmethod
    def update(project_id, name):
        """更新项目名称"""
        project = Project.query.get(project_id)
        if project:
            project.name = name
            db.session.commit()
            return project
        return None
    
    @staticmethod
    def delete(project_id):
        """删除项目"""
        project = Project.query.get(project_id)
        if project:
            db.session.delete(project)
            db.session.commit()
            return True
        return False
