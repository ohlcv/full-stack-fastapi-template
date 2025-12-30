#!/usr/bin/env python3
"""重置数据库脚本 - 匹配当前模型"""
from app.core.config import settings
from sqlalchemy import create_engine, text

def reset_database():
    """重置数据库"""
    engine = create_engine(str(settings.SQLALCHEMY_DATABASE_URI))
    
    with engine.connect() as conn:
        # 删除所有表
        conn.execute(text("DROP SCHEMA public CASCADE"))
        conn.execute(text("CREATE SCHEMA public"))
        conn.commit()
    print("Database reset successfully")

if __name__ == "__main__":
    reset_database()
