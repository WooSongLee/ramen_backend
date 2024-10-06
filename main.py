from fastapi import FastAPI
from pydantic import BaseModel
from DB import *;
from fastapi.middleware.cors import CORSMiddleware

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
            INSERT INTO ranking (name, phone, score)
            VALUES (%s, %s, %s)
        """, (user.name, user.phone, user.score))
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
