from fastapi import APIRouter, Depends
from fastapi.params import Query
from sqlalchemy.ext.asyncio import AsyncSession

from config.db_config import get_db
from crud import history as history_crud
from models.users import User
from schemas.history import HistoryAddRequest, HistoryListResponse, HistoryNewsItemResponse
from utils.auth import get_current_user
from utils.response import success_response

router = APIRouter(prefix="/api/history", tags=["history"])


@router.post("/add")
async def add_history(
        data: HistoryAddRequest,
        user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    """添加浏览记录：同一新闻重复浏览只刷新浏览时间。"""
    record = await history_crud.add_history(db, user.id, data.news_id)

    return success_response(
        message="添加历史成功",
        data={
            "id": record.id,
            "newsId": record.news_id,
            "viewTime": record.view_time
        }
    )


@router.get("/list")
async def get_history_list(
        page: int = Query(1, ge=1),
        page_size: int = Query(10, ge=1, le=100, alias="pageSize"),
        user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    """获取当前用户的浏览历史：按浏览时间倒序分页。"""
    rows, total = await history_crud.get_history_list(db, user.id, page, page_size)

    # rows 中每一项为 (News, view_time) 二元组，展开成响应模型
    history_list = [
        HistoryNewsItemResponse(**news_item.__dict__, viewTime=view_time)
        for news_item, view_time in rows
    ]

    has_more = total > page * page_size

    return success_response(
        message="获取浏览历史成功",
        data=HistoryListResponse(list=history_list, total=total, hasMore=has_more)
    )
