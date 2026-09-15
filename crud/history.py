from datetime import datetime

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from models.history import History
from models.news import News


async def add_history(
        db: AsyncSession,
        user_id: int,
        news_id: int,
):
    """
    添加浏览记录：同一用户对同一新闻只保留一条记录。
    已存在则把浏览时间刷新为当前时间，不存在则新建。
    """
    query = select(History).where(History.news_id == news_id, History.user_id == user_id)
    result = await db.execute(query)
    existing_history = result.scalar_one_or_none()

    if existing_history:
        existing_history.view_time = datetime.now()
        await db.commit()
        await db.refresh(existing_history)
        return existing_history

    history = History(news_id=news_id, user_id=user_id)
    db.add(history)
    await db.commit()
    await db.refresh(history)
    return history


async def get_history_list(
        db: AsyncSession,
        user_id: int,
        page: int = 1,
        page_size: int = 10
):
    """
    查看浏览历史记录：按浏览时间倒序，联表带回新闻信息并分页。

    返回 (rows, total)，rows 中每一项为 (News, view_time) 二元组。
    """
    count_query = select(func.count(History.id)).where(History.user_id == user_id)
    count_result = await db.execute(count_query)
    total = count_result.scalar_one()

    offset = (page - 1) * page_size
    query = (
        select(News, History.view_time.label("view_time"))
        .join(History, History.news_id == News.id)
        .where(History.user_id == user_id)
        .order_by(History.view_time.desc())
        .offset(offset).limit(page_size)
    )
    result = await db.execute(query)
    rows = result.all()
    return rows, total
