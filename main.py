import os
from fastapi import FastAPI, HTTPException
from supabase import create_client, Client
from pydantic import BaseModel
from typing import List

App = FastAPI(title="Supabase Records API")

SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")

if not SUPABASE_KEY or not SUPABASE_URL:
    raise RuntimeError("Error! Environment Variables Missing!")

Supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

class Record(BaseModel):
    id: int
    name: str
    value: str
    status: str

@App.get("/records", response_model=List[Record])
async def get_records():
    try:
        response = Supabase.table("records").select("*").execute()
        return response.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))