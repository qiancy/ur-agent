# db/postgres_client.py

"""
PostgreSQL客户端模块
用于与PostgreSQL数据库进行交互
"""

import psycopg2
from psycopg2.extras import RealDictCursor
from typing import Optional
import os

def get_db_connection():
    """
    获取数据库连接
    
    Returns:
        psycopg2.extensions.connection: 数据库连接对象
        
    Raises:
        Exception: 数据库连接失败时抛出异常
    """
    try:
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST", "localhost"),
            database=os.getenv("DB_NAME", "uni_resource_agent"),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD", "postgres"),
            port=os.getenv("DB_PORT", "5432")
        )
        return conn
    except Exception as e:
        raise Exception(f"无法连接到数据库: {str(e)}")

def init_database():
    """
    初始化数据库表结构
    """
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # 创建contexts表
        cur.execute("""
            CREATE TABLE IF NOT EXISTS contexts (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                type VARCHAR(100) NOT NULL,
                owner_user_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 创建physical_assets表
        cur.execute("""
            CREATE TABLE IF NOT EXISTS physical_assets (
                id SERIAL PRIMARY KEY,
                context_id INTEGER NOT NULL,
                name VARCHAR(255) NOT NULL,
                type VARCHAR(100),
                quantity INTEGER NOT NULL DEFAULT 0,
                status VARCHAR(50) DEFAULT 'active',
                lifecycle_log TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (context_id) REFERENCES contexts(id)
            )
        """)
        
        # 创建virtual_assets表
        cur.execute("""
            CREATE TABLE IF NOT EXISTS virtual_assets (
                id SERIAL PRIMARY KEY,
                context_id INTEGER NOT NULL,
                name VARCHAR(255) NOT NULL,
                content TEXT,
                embedding VECTOR(1024),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (context_id) REFERENCES contexts(id)
            )
        """)
        
        # 创建personnel表
        cur.execute("""
            CREATE TABLE IF NOT EXISTS personnel (
                id SERIAL PRIMARY KEY,
                context_id INTEGER NOT NULL,
                name VARCHAR(255) NOT NULL,
                role VARCHAR(100),
                birth_date DATE,
                health_reminders JSONB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (context_id) REFERENCES contexts(id)
            )
        """)
        
        # 创建transactions表
        cur.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id SERIAL PRIMARY KEY,
                context_id INTEGER NOT NULL,
                amount DECIMAL(15,2) NOT NULL,
                category VARCHAR(100) NOT NULL,
                description TEXT,
                transaction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (context_id) REFERENCES contexts(id)
            )
        """)
        
        conn.commit()
        print("数据库初始化成功")
        
    except Exception as e:
        print(f"数据库初始化失败: {str(e)}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()