"""
日志与数据分析模块：对话日志查询、统计、导出和清理

提供以下接口：
- GET  /logs/           — 查询对话日志（分页、筛选）
- GET  /logs/sessions   — 列出所有会话（含首条消息、消息数）
- GET  /logs/stats      — 获取综合统计数据
- GET  /logs/export     — 导出对话日志为 CSV
- GET  /logs/analytics  — 获取对话数据分析（热门问题、每日趋势、检索成功率）
- DELETE /logs/cleanup  — 清理过期日志

权限规则：
- admin/teacher：可查看所有用户的日志
- 普通用户：仅查看自己的日志
- cleanup 仅 admin 可执行
"""
import json
import csv
import io
from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from ...models.tables import ChatLog, User, KnowledgeBase, Document
from ..deps import get_db, get_current_user

router = APIRouter(prefix="/logs", tags=["日志"])


@router.get("/")
def list_logs(
    session_id: str = None,
    user_id: int = None,
    keyword: str = None,
    start_time: str = None,
    end_time: str = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """查询对话日志

    - admin 可查看所有用户的日志
    - 普通用户仅查看自己的日志（user_id 过滤）
    - 支持按会话 ID、用户 ID、关键词、时间范围筛选
    - 分页返回，按创建时间倒序
    """
    query = db.query(ChatLog)
    # 权限控制：非管理员只能看自己的日志
    if current_user.role != "admin":
        query = query.filter(ChatLog.user_id == current_user.id)
    if session_id:
        query = query.filter(ChatLog.session_id == session_id)
    if user_id:
        query = query.filter(ChatLog.user_id == user_id)
    if keyword:
        query = query.filter(ChatLog.content.contains(keyword))
    if start_time:
        query = query.filter(ChatLog.created_at >= start_time)
    if end_time:
        query = query.filter(ChatLog.created_at <= end_time)

    # 分页查询
    total = query.count()
    logs = (
        query.order_by(desc(ChatLog.created_at))
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": [
            {
                "id": log.id,
                "user_id": log.user_id,
                "session_id": log.session_id,
                "role": log.role,
                "content": log.content,
                "sources": json.loads(log.sources) if log.sources else [],
                "created_at": log.created_at.isoformat(),
            }
            for log in logs
        ],
    }


@router.get("/sessions")
def list_sessions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """列出所有会话

    - admin 看所有会话，普通用户仅看自己的
    - 每个会话包含：session_id、标题（首条消息前50字）、消息数、最新时间
    """
    query = db.query(ChatLog.session_id).distinct()
    if current_user.role != "admin":
        query = query.filter(ChatLog.user_id == current_user.id)

    sessions = query.all()
    result = []
    for (session_id,) in sessions:
        # 获取会话首条用户消息作为标题
        first_msg = (
            db.query(ChatLog)
            .filter(ChatLog.session_id == session_id, ChatLog.role == "user")
            .order_by(ChatLog.created_at)
            .first()
        )
        # 统计会话消息总数
        msg_count = db.query(ChatLog).filter(ChatLog.session_id == session_id).count()
        # 获取最新一条消息的时间
        latest = (
            db.query(ChatLog)
            .filter(ChatLog.session_id == session_id)
            .order_by(desc(ChatLog.created_at))
            .first()
        )
        result.append({
            "session_id": session_id,
            "title": first_msg.content[:50] if first_msg else "空会话",
            "message_count": msg_count,
            "latest_time": latest.created_at.isoformat() if latest else None,
        })
    return result


@router.get("/stats")
def get_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取综合统计数据

    返回：总消息数、用户消息数、总会话数、知识库数、
    文档总数、就绪文档数、用户总数
    用于仪表盘顶部的统计卡片展示。
    """
    total_messages = db.query(ChatLog).count()
    user_messages = db.query(ChatLog).filter(ChatLog.role == "user").count()
    total_sessions = db.query(ChatLog.session_id).distinct().count()
    total_kb = db.query(KnowledgeBase).count()
    total_docs = db.query(Document).count()
    ready_docs = db.query(Document).filter(Document.status == "ready").count()
    total_users = db.query(User).count()

    return {
        "total_messages": total_messages,
        "user_messages": user_messages,
        "total_sessions": total_sessions,
        "total_kb": total_kb,
        "total_docs": total_docs,
        "ready_docs": ready_docs,
        "total_users": total_users,
    }


@router.get("/export")
def export_logs(
    session_id: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """导出对话日志为 CSV

    - admin 导出全部日志，普通用户仅导出自己的
    - 可选按会话 ID 筛选
    - 返回 CSV 格式的流式响应，自动触发浏览器下载
    - CSV 列：ID、会话ID、角色、内容、来源、时间
    """
    query = db.query(ChatLog)
    if current_user.role != "admin":
        query = query.filter(ChatLog.user_id == current_user.id)
    if session_id:
        query = query.filter(ChatLog.session_id == session_id)

    logs = query.order_by(ChatLog.created_at).all()

    # 生成 CSV 内容
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "会话ID", "角色", "内容", "来源", "时间"])

    for log in logs:
        writer.writerow([
            log.id,
            log.session_id,
            log.role,
            log.content,
            log.sources or "",
            log.created_at.isoformat() if log.created_at else "",
        ])

    output.seek(0)
    # 返回流式 CSV 响应，触发浏览器下载
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=chat_logs.csv"},
    )


@router.get("/analytics")
def get_analytics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取对话数据分析

    admin/teacher 查看全部数据分析，普通用户仅看自己的。

    返回以下分析维度：
    - 总体统计：总消息数、用户消息数、总会话数
    - 热门问题：用户提问中频率最高的 Top10 词语
    - 每日消息量趋势：按天统计消息数
    - 检索成功率：助手回复中包含检索来源的比例
    - 每日检索成功率趋势
    - 用户活跃度：Top10 活跃用户的消息数
    """
    # 根据角色确定数据范围
    if current_user.role in ("admin", "teacher"):
        # 管理员和教师看全部数据
        base_query = db.query(ChatLog)
    else:
        # 普通用户只看自己的数据
        base_query = db.query(ChatLog).filter(ChatLog.user_id == current_user.id)

    # 总体统计
    total_messages = base_query.count()
    user_messages = base_query.filter(ChatLog.role == "user").count()
    total_sessions = base_query.with_entities(ChatLog.session_id).distinct().count()

    # 热门问题：统计用户消息中每个词的出现频率，取 Top10
    user_logs = base_query.filter(ChatLog.role == "user").with_entities(ChatLog.content).all()
    word_freq = {}
    for (content,) in user_logs:
        words = content.split()
        for word in words:
            if len(word) > 1:  # 过滤单字词
                word_freq[word] = word_freq.get(word, 0) + 1
    top_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:10]

    # 每日消息量趋势：按天聚合统计
    daily_stats = {}
    all_logs = base_query.with_entities(ChatLog.created_at).all()
    for (created_at,) in all_logs:
        if created_at:
            day = created_at.strftime("%Y-%m-%d")
            daily_stats[day] = daily_stats.get(day, 0) + 1

    # 检索成功率：助手回复中有检索来源（sources 非空）的比例
    total_assistant = base_query.filter(ChatLog.role == "assistant").count()
    retrieved_count = 0
    if total_assistant > 0:
        assistant_logs = base_query.filter(
            ChatLog.role == "assistant"
        ).with_entities(ChatLog.sources).all()
        for (sources,) in assistant_logs:
            if sources and str(sources).strip():
                retrieved_count += 1
    retrieval_rate = round(retrieved_count / total_assistant * 100, 1) if total_assistant > 0 else 0

    # 每日检索成功率趋势
    daily_retrieval = {}
    daily_total_assistant = {}
    assistant_logs = base_query.filter(
        ChatLog.role == "assistant"
    ).with_entities(ChatLog.created_at, ChatLog.sources).all()
    for created_at, sources in assistant_logs:
        if created_at:
            day = created_at.strftime("%Y-%m-%d")
            daily_total_assistant[day] = daily_total_assistant.get(day, 0) + 1
            if sources and str(sources).strip():
                daily_retrieval[day] = daily_retrieval.get(day, 0) + 1
    daily_retrieval_rate = []
    for day in sorted(daily_total_assistant.keys()):
        total = daily_total_assistant[day]
        success = daily_retrieval.get(day, 0)
        daily_retrieval_rate.append({
            "date": day,
            "rate": round(success / total * 100, 1) if total > 0 else 0,
        })

    # 用户活跃度：按消息数降序，取 Top10
    user_activity_rows = db.query(
        User.username, func.count(ChatLog.id)
    ).join(ChatLog, User.id == ChatLog.user_id).filter(
        ChatLog.role == "user"
    ).group_by(User.username).order_by(func.count(ChatLog.id).desc()).limit(10).all()

    return {
        "total_messages": total_messages,
        "user_messages": user_messages,
        "total_sessions": total_sessions,
        "top_words": [{"word": w, "count": c} for w, c in top_words],
        "daily_stats": [{"date": d, "count": c} for d, c in sorted(daily_stats.items())],
        "retrieval_rate": retrieval_rate,
        "daily_retrieval_rate": daily_retrieval_rate,
        "user_activity": [{"username": u, "count": c} for u, c in user_activity_rows],
    }


@router.delete("/cleanup")
def cleanup_logs(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """清理过期日志

    - 仅 admin 可执行
    - 删除指定天数之前的日志记录
    - 默认清理 30 天前的日志
    - 返回被删除的记录数
    """
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="无权限")

    from datetime import datetime, timedelta
    cutoff = datetime.now() - timedelta(days=days)
    deleted = db.query(ChatLog).filter(ChatLog.created_at < cutoff).delete()
    db.commit()
    return {"detail": f"已清理 {deleted} 条过期日志"}
