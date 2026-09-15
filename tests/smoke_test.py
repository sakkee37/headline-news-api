#!/usr/bin/env python3
"""
headline-news-api 端到端冒烟测试

直接对运行中的服务发起真实 HTTP 请求，覆盖全部 15 个接口。
只依赖 Python 标准库，无需安装额外依赖。

用法：
    # 先启动服务：uvicorn main:app --port 8000
    python tests/smoke_test.py
    python tests/smoke_test.py --base-url http://127.0.0.1:8848
"""

import argparse
import json
import random
import sys
import urllib.error
import urllib.request

PASSED = 0
FAILED = 0
FAILURES = []


def request(method, url, body=None, token=None, timeout=10):
    """发起一次请求，返回 (status_code, parsed_json_or_text)。"""
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    if data is not None:
        req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", f"Bearer {token}")

    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8")
            status = resp.status
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8")
        status = e.code
    except urllib.error.URLError as e:
        print(f"\n❌ 无法连接服务：{e.reason}")
        print("   请先启动：uvicorn main:app --port 8000")
        sys.exit(2)

    try:
        return status, json.loads(raw)
    except json.JSONDecodeError:
        return status, raw


def check(name, status, payload, expect=200):
    """记录一条断言结果。"""
    global PASSED, FAILED
    ok = status == expect
    mark = "✅" if ok else "❌"
    if ok:
        PASSED += 1
    else:
        FAILED += 1
        FAILURES.append(name)

    summary = json.dumps(payload, ensure_ascii=False) if not isinstance(payload, str) else payload
    if len(summary) > 110:
        summary = summary[:110] + "…"
    print(f"  {mark} {name:<36} HTTP {status:<4} {summary}")
    return ok


def main():
    parser = argparse.ArgumentParser(description="headline-news-api 冒烟测试")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000", help="服务地址")
    args = parser.parse_args()
    base = args.base_url.rstrip("/")

    print(f"\n目标服务：{base}\n")

    # ---------- 新闻模块（无需登录） ----------
    print("【新闻模块】")
    st, body = request("GET", f"{base}/api/news/categories")
    check("GET /api/news/categories", st, body)

    st, body = request("GET", f"{base}/api/news/list?categoryId=1&page=1&pageSize=3")
    check("GET /api/news/list", st, body)

    news_id = 1
    st, body = request("GET", f"{base}/api/news/detail?id={news_id}")
    check("GET /api/news/detail", st, body)

    # ---------- 用户模块 ----------
    print("\n【用户模块】")
    username = f"smoke_{random.randint(10000, 99999)}"
    old_pwd, new_pwd = "pass1234", "newpass456"

    st, body = request("POST", f"{base}/api/user/register",
                       {"username": username, "password": old_pwd})
    check("POST /api/user/register", st, body)

    st, body = request("POST", f"{base}/api/user/login",
                       {"username": username, "password": old_pwd})
    check("POST /api/user/login", st, body)
    if st != 200 or not isinstance(body, dict) or not body.get("data"):
        print("\n登录失败，后续需要鉴权的用例无法继续。")
        return finish()
    token = body["data"]["token"]

    st, body = request("GET", f"{base}/api/user/info", token=token)
    check("GET /api/user/info", st, body)

    st, body = request("PUT", f"{base}/api/user/update",
                       {"nickname": "冒烟测试"}, token=token)
    check("PUT /api/user/update", st, body)

    st, body = request("PUT", f"{base}/api/user/password",
                       {"oldPassword": old_pwd, "newPassword": new_pwd}, token=token)
    check("PUT /api/user/password", st, body)

    # 改密后旧 token 会被重新登录顶掉，换新密码重新登录
    st, body = request("POST", f"{base}/api/user/login",
                       {"username": username, "password": new_pwd})
    if st == 200 and isinstance(body, dict) and body.get("data"):
        token = body["data"]["token"]

    # ---------- 收藏模块 ----------
    print("\n【收藏模块】")
    st, body = request("GET", f"{base}/api/favorite/check?newsId={news_id}", token=token)
    check("GET /api/favorite/check", st, body)

    st, body = request("POST", f"{base}/api/favorite/add",
                       {"newsId": news_id}, token=token)
    check("POST /api/favorite/add", st, body)

    st, body = request("GET", f"{base}/api/favorite/list?page=1&pageSize=10", token=token)
    check("GET /api/favorite/list", st, body)

    st, body = request("DELETE", f"{base}/api/favorite/remove?newsId={news_id}", token=token)
    check("DELETE /api/favorite/remove", st, body)

    st, body = request("DELETE", f"{base}/api/favorite/clear", token=token)
    check("DELETE /api/favorite/clear", st, body)

    # ---------- 浏览历史模块 ----------
    print("\n【浏览历史模块】")
    st, body = request("POST", f"{base}/api/history/add",
                       {"newsId": 2}, token=token)
    check("POST /api/history/add", st, body)

    st, body = request("POST", f"{base}/api/history/add",
                       {"newsId": 3}, token=token)
    check("POST /api/history/add (第二条)", st, body)

    st, body = request("GET", f"{base}/api/history/list?page=1&pageSize=10", token=token)
    check("GET /api/history/list", st, body)

    # ---------- 鉴权反向用例 ----------
    print("\n【鉴权校验】")
    st, body = request("GET", f"{base}/api/user/info", token="invalid-token-xxx")
    check("GET /api/user/info (无效 token)", st, body, expect=401)

    st, body = request("POST", f"{base}/api/user/login",
                       {"username": username, "password": "wrong-password"})
    check("POST /api/user/login (错误密码)", st, body, expect=401)

    return finish()


def finish():
    total = PASSED + FAILED
    print(f"\n{'=' * 56}")
    if FAILED == 0:
        print(f"全部通过：{PASSED}/{total} ✅")
    else:
        print(f"通过 {PASSED}/{total}，失败 {FAILED}  ❌")
        for name in FAILURES:
            print(f"  失败用例：{name}")
    print("=" * 56)
    return 0 if FAILED == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
