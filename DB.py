# MySQL 설정
import aiomysql

DATABASE_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'user': 'root',
    'password': '1234',
    'db': 'ramen',
    'autocommit': True
}

async def get_db_connection():
    return await aiomysql.connect(**DATABASE_CONFIG)