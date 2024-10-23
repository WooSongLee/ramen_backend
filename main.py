"""
DB 구조

ranking:
    name: str
    score: int
    phone: str
    created_at: datetime
"""

import re
import uvicorn
import asyncio
from datetime import datetime
from pydantic import BaseModel, validator
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from DB import *;

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cursor:
                await cursor.execute("""
                    CREATE TABLE IF NOT EXISTS ranking (
                        name TEXT NOT NULL,
                        score INT NOT NULL,
                        phone VARCHAR(15) NOT NULL,
                        created_at DATETIME NOT NULL,
                        PRIMARY KEY (phone)
                    );
                """)
                await conn.commit()
        finally:
            conn.close()
    except Exception as e:
        print("Database initialization failed:", e)
        raise e
    
    yield

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class UserInput(BaseModel):
    name: str
    phone: str
    score: int

    @validator('phone')
    def validate_phone(cls, v):
        v = re.sub(r'[^0-9]', '', v)  # 숫자만 추출
        if not re.match(r'^01[016789][0-9]{7,8}$', v):
            raise ValueError('Invalid phone number format. Must be a valid Korean mobile number.')
        return v

    @validator('score')
    def validate_score(cls, v):
        if not (0 <= v <= 1500):
            raise ValueError('Score must be between 0 and 1500')
        return v

@app.post("/start")
async def start(user: UserInput):
    try:
        conn = await get_db_connection()
        try:
            async with conn.cursor() as cursor:
                # 기존에 등록된 번호인지 확인
                await cursor.execute(
                    "SELECT name, score FROM ranking WHERE phone = %s",
                    (user.phone,)
                )
                result = await cursor.fetchone()

                # 기존에 등록된 번호일때
                if result:
                    existing_name, existing_score = result
                    # 이름이 바뀌었을 경우
                    if existing_name != user.name:
                        await cursor.execute(
                            "UPDATE ranking SET name = %s WHERE phone = %s",
                            (user.name, user.phone)
                        )
                    
                    # 점수가 더 높을 경우
                    if user.score > existing_score:
                        await cursor.execute(
                            "UPDATE ranking SET score = %s, created_at = %s WHERE phone = %s",
                            (user.score, datetime.now(), user.phone)
                        )
                else:
                    await cursor.execute(
                        "INSERT INTO ranking (name, phone, score, created_at) VALUES (%s, %s, %s, %s)",
                        (user.name, user.phone, user.score, datetime.now())
                    )
                await conn.commit()  # commit 추가

        except Exception as e:
            await conn.rollback()  # rollback 추가
            raise HTTPException(status_code=500, detail="Database error occurred")
        finally:
            conn.close()
    except Exception as e:
        raise HTTPException(status_code=500, detail="Server error occurred")

    return {"status": "success", "message": "Score recorded successfully"}



@app.get("/ranking")
async def get_ranking():
    try:
        conn = await get_db_connection()
        try:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute("""
                    SELECT name, score 
                    FROM ranking 
                    ORDER BY score DESC, created_at ASC 
                    LIMIT 10
                """)
                ranking_data = await cursor.fetchall()
                
        except Exception as e:
            raise HTTPException(status_code=500, detail="Database query error")
        finally:
            conn.close()
    except Exception as e:
        raise HTTPException(status_code=500, detail="Database connection error: " + str(e))

    return {"ranking": ranking_data}

    
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=7700, workers=4, reload=False, proxy_headers=True)