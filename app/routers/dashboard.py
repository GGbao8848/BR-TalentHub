"""数据看板：/api/dashboard。"""
from fastapi import APIRouter

from app import database as db

router = APIRouter()


@router.get("/api/dashboard")
def get_dashboard():
    """看板统计：总数 / 按学校 / 按岗位 / 近14日。"""
    return db.dashboard_stats()
