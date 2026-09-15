from datetime import datetime

from pydantic import BaseModel, Field, ConfigDict

from schemas.base import NewsItemBase


# 添加浏览记录
class HistoryAddRequest(BaseModel):
    news_id: int = Field(..., alias="newsId")


# 浏览历史中的单条新闻：新闻基础字段 + 该新闻的浏览时间
class HistoryNewsItemResponse(NewsItemBase):
    view_time: datetime = Field(alias="viewTime")

    model_config = ConfigDict(
        populate_by_name=True,
        from_attributes=True
    )


# 浏览历史列表接口响应模型类
class HistoryListResponse(BaseModel):
    list: list[HistoryNewsItemResponse]
    total: int
    has_more: bool = Field(alias="hasMore")

    model_config = ConfigDict(
        populate_by_name=True,
        from_attributes=True
    )
