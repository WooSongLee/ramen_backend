import datetime
from fastapi import FastAPI
from pydantic import BaseModel
from DB import *;
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime

app = FastAPI()
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


@app.post("/start")
async def start(user: UserInput):
    conn = await get_db_connection()
    async with conn.cursor() as cursor:
        await cursor.execute("""
            SELECT name, score FROM ranking WHERE phone = %s
        """, (user.phone,))
        result = await cursor.fetchone()

        if result:
            existing_name, existing_score = result
            if existing_name != user.name:
                await cursor.execute("""
                    UPDATE ranking
                    SET name = %s
                    WHERE phone = %s
                """, (user.name, user.phone))
            if user.score > existing_score:
                await cursor.execute("""
                    UPDATE ranking
                    SET score = %s, created_at = %s
                    WHERE phone = %s
                """, (user.score, datetime.now(), user.phone))
        else:
            await cursor.execute("""
                INSERT INTO ranking (name, phone, score, created_at)
                VALUES (%s, %s, %s, %s)
            """, (user.name, user.phone, user.score, datetime.now()))

    conn.close()


@app.get("/ranking")
async def get_ranking():
    conn = await get_db_connection()
    async with conn.cursor(aiomysql.DictCursor) as cursor:
        await cursor.execute("""
            SELECT name, phone, score FROM ranking
            ORDER BY score DESC
        """)
        ranking_data = await cursor.fetchall()
    conn.close()
    return {"ranking": ranking_data}
