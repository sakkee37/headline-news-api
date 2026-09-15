# headline-news-api

基于 **FastAPI + SQLAlchemy 2.0 异步 ORM** 的新闻资讯后端 API。

覆盖用户认证、新闻浏览、收藏、浏览历史四大模块，共 **15 个接口**，采用
`router → crud → model` 分层 + Pydantic 请求/响应模型校验 + 全局异常处理。

> 项目定位：个人后端工程练习项目，重点实践异步 I/O、分层架构与统一接口规范。

---

## 技术栈

| 层 | 选型 | 说明 |
|---|---|---|
| Web 框架 | FastAPI 0.141 | 原生异步、自动生成 OpenAPI 文档 |
| ORM | SQLAlchemy 2.0（`Mapped` / `mapped_column`） | 全异步会话，`async_sessionmaker` |
| 数据库 | MySQL 8+ | 驱动 `aiomysql`（异步） |
| 数据校验 | Pydantic v2 | 请求体校验 + 响应模型 + `from_attributes` |
| 密码存储 | passlib + bcrypt | 密文入库，不存明文 |
| 认证 | 数据库 Token | `Authorization: Bearer <token>`，7 天有效 |
| ASGI | uvicorn | 本地开发用 |

---

## 架构分层

```
main.py                  应用入口：注册路由、全局异常处理、CORS
│
├── routers/             路由层：只负责参数接收、调用 crud、组装响应
│   ├── new.py            新闻：分类 / 列表（分页）/ 详情（含相关推荐）
│   ├── users.py          用户：注册 / 登录 / 资料 / 改密
│   ├── favorite.py       收藏：检查 / 添加 / 删除 / 列表 / 清空
│   └── history.py        历史：添加（重复浏览只刷新时间）/ 列表
│
├── crud/                数据访问层：只写 SQLAlchemy 查询，不碰 HTTP
├── models/              ORM 模型：表结构、索引、外键、唯一约束
├── schemas/             Pydantic 模型：请求体与响应体结构
├── utils/              横切关注点
│   ├── auth.py           依赖注入：由 Token 解析当前用户
│   ├── security.py       密码哈希与校验
│   ├── response.py       统一成功响应包装
│   ├── exception.py      各类异常处理器实现
│   └── exception_handler.py  异常处理器注册
└── config/db_config.py  异步引擎、会话工厂、get_db 依赖
```

**分层约定**：`routers` 不直接写 SQL，`crud` 不感知 HTTP，`schemas` 只描述数据结构。
新增一个功能模块时按 `models → schemas → crud → routers → main.py 注册` 的顺序自下而上补齐。

---

## 接口一览

所有需要登录的接口都要求请求头 `Authorization: Bearer <token>`。

### 新闻 `/api/news`

| 方法 | 路径 | 说明 | 需登录 |
|---|---|---|---|
| GET | `/api/news/categories` | 新闻分类列表 | 否 |
| GET | `/api/news/list?categoryId=1&page=1&pageSize=10` | 分类下新闻分页列表 | 否 |
| GET | `/api/news/detail?id=1` | 新闻详情（浏览量 +1，附相关推荐） | 否 |

### 用户 `/api/user`

| 方法 | 路径 | 说明 | 需登录 |
|---|---|---|---|
| POST | `/api/user/register` | 注册，返回 token | 否 |
| POST | `/api/user/login` | 登录，返回 token | 否 |
| GET | `/api/user/info` | 当前用户信息 | 是 |
| PUT | `/api/user/update` | 修改昵称/头像/性别/简介 | 是 |
| PUT | `/api/user/password` | 修改密码（校验旧密码） | 是 |

### 收藏 `/api/favorite`

| 方法 | 路径 | 说明 | 需登录 |
|---|---|---|---|
| GET | `/api/favorite/check?newsId=1` | 检查是否已收藏 | 是 |
| POST | `/api/favorite/add` | 添加收藏 | 是 |
| DELETE | `/api/favorite/remove?newsId=1` | 取消收藏 | 是 |
| GET | `/api/favorite/list?page=1&pageSize=10` | 收藏列表（分页） | 是 |
| DELETE | `/api/favorite/clear` | 清空当前用户收藏 | 是 |

### 浏览历史 `/api/history`

| 方法 | 路径 | 说明 | 需登录 |
|---|---|---|---|
| POST | `/api/history/add` | 添加浏览记录（重复浏览只刷新时间） | 是 |
| GET | `/api/history/list?page=1&pageSize=10` | 浏览历史（按时间倒序分页） | 是 |

---

## 快速开始

### 1. 准备数据库

```bash
mysql -uroot -e "CREATE DATABASE IF NOT EXISTS news_app DEFAULT CHARSET utf8mb4;"
```

### 2. 配置连接串

编辑 `config/db_config.py` 中的 `ASYNC_DATABASE_URL`：

```python
ASYNC_DATABASE_URL = "mysql+aiomysql://root:你的密码@localhost:3306/news_app?charset=utf8mb4"
```

### 3. 建表

项目未使用 Alembic 迁移，首次运行前用模型元数据建表：

```bash
python -c "
import asyncio
from config.db_config import async_engine
from models.news import Base as NewsBase
from models.users import Base as UserBase, User, UserToken
from models.favorite import Favorite
from models.history import History

async def main():
    async with async_engine.begin() as conn:
        await conn.run_sync(NewsBase.metadata.create_all)
    await async_engine.dispose()
    print('建表完成')

asyncio.run(main())
"
```

> 注意：`models/` 下每个文件各自定义了 `Base`，建表时需确保全部模型类已被导入，
> 否则对应表不会出现在元数据中。

### 4. 安装依赖并启动

```bash
# 使用 uv（推荐）
uv sync
uv run uvicorn main:app --reload

# 或使用 pip
python -m venv .venv && source .venv/bin/activate
pip install -e .
uvicorn main:app --reload
```

启动后访问 **http://127.0.0.1:8000/docs** 查看交互式接口文档。

---

## 测试

项目提供了一份端到端冒烟测试脚本，直接对真实数据库发起请求，覆盖全部 15 个接口：

```bash
# 先确保 uvicorn 已在 8000 端口启动
python tests/smoke_test.py

# 或指定地址
python tests/smoke_test.py --base-url http://127.0.0.1:8848
```

脚本会注册一个随机用户名走完整流程：注册 → 登录 → 用户资料 → 改密 →
收藏增删查清 → 浏览历史写入与列表，逐条打印 HTTP 状态码与响应摘要。

---

## 实现要点

**异步链路**：从 uvicorn 到 `aiomysql` 全程异步。`get_db` 以依赖注入方式下发
`AsyncSession`，请求正常结束时统一 `commit`，抛异常则 `rollback`，避免在各层手写事务。

**分层依赖注入**：需要登录的接口通过 `Depends(get_current_user)` 从请求头取 Token，
查库校验有效期后返回 `User` 对象；业务函数只需声明 `user: User = Depends(...)`，
无需重复解析 Token。

**统一响应格式**：成功响应统一为 `{"code": 200, "message": "...", "data": ...}`。
异常分四类注册处理器（`HTTPException` → 业务，`IntegrityError` → 约束冲突，
`SQLAlchemyError` → 数据库，`Exception` → 兜底），按"子类在前、父类在后"的顺序注册，
保证更具体的处理器优先生效。

**场景化的数据建模**：
- 收藏表对 `(user_id, news_id)` 建唯一约束，从数据库层面防止重复收藏；
- 浏览历史对同一用户同一新闻只保留一条记录，重复浏览刷新 `view_time` 而非新增行；
- 高频查询字段（`category_id`、`publish_time`、`user_id` 等）均建索引。

---

## 已知待改进

诚实记录当前不足，也是后续迭代方向：

- [ ] **响应格式尚未完全统一**：多数接口走 `success_response` 包装，但
      `/api/news/detail` 直接返回裸对象；`/api/news/categories` 与
      `/api/favorite/add` 直接返回 ORM 对象，会带出 `created_at`、`updated_at`
      等内部字段且命名风格为 snake_case。应统一补上响应模型。
- [ ] **收藏列表字段命名不一致**：`/api/favorite/list` 返回的 `favorite_time` /
      `favorite_id` 未按其他接口的 camelCase 别名输出。
- [ ] **无自动化测试**：目前只有冒烟脚本，缺少基于 `pytest` + `TestClient` 的
      单元测试与数据库隔离（测试库或事务回滚）。
- [ ] **无数据库迁移**：建表依赖手动执行元数据，生产环境应引入 Alembic。
- [ ] **数据库连接串硬编码**在 `config/db_config.py`，应改为环境变量读取。
- [ ] **Token 未设滑动过期**，且同一用户仅保留一个 Token（重新登录会使旧 Token 失效）。

---

## License

[MIT](LICENSE)
