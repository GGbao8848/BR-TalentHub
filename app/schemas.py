"""Pydantic 请求/响应模型（API 契约）。"""
from typing import Optional

from pydantic import BaseModel, Field


class ConfigPayload(BaseModel):
    """设置招聘会名称 / 保存目录 / 开始时间。"""
    event_name: Optional[str] = Field(default=None, max_length=100)
    save_dir: Optional[str] = None
    started_at: Optional[str] = None


class PositionPayload(BaseModel):
    """创建 / 编辑岗位。"""
    name: str = Field(min_length=1, max_length=100)
    requirement: Optional[str] = Field(default="", max_length=500)


class SchoolPayload(BaseModel):
    """创建学校。"""
    name: str = Field(min_length=1, max_length=100)
    positions: Optional[list[int]] = Field(default_factory=list)


class SchoolPositionsPayload(BaseModel):
    """更新学校绑定的岗位。"""
    positions: list[int] = Field(default_factory=list)


class EventResetResponse(BaseModel):
    event_id: str
    event_name: str
    save_dir: str
    host_ip: str
    port: int
    count: int
    active_school: str = ""
    updated_at: str = ""


class UploadOk(BaseModel):
    id: int
    message: str = "上传成功"
    filename: str = ""
