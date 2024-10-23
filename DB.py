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



async def setup_database():
    try:
        conn = await get_db_connection()
        try:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute("""
                    USE ramen;
                    CREATE TABLE IF NOT EXISTS ranking (
                        name TEXT NOT NULL,
                        score INT NOT NULL,
                        phone VARCHAR(15) NOT NULL,
                        created_at DATETIME NOT NULL,
                        PRIMARY KEY (phone)
                    );
                """)
        except aiomysql.Warning as warn:
            # 테이블이 이미 존재할 경우 경고 무시
            pass
        except Exception as e:
            print("DB 쿼리 에러:", e)
            exit()
        finally:
            await conn.close()
    except Exception as e:
        print("DB 연결 실패:", e)
        exit()