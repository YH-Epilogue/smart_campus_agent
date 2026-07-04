import json
import csv
import io
from fastapi import APIRouter, Depends, Query
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
    """查询对话日志"""
    query = db.query(ChatLog)
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
    """列出所有会话"""
    query = db.query(ChatLog.session_id).distinct()
    if current_user.role != "admin":
        query = query.filter(ChatLog.user_id == current_user.id)

    sessions = query.all()
    result = []
    for (session_id,) in sessions:
        first_msg = (
            db.query(ChatLog)
            .filter(ChatLog.session_id == session_id, ChatLog.role == "user")
            .order_by(ChatLog.created_at)
            .first()
        )
        msg_count = db.query(ChatLog).filter(ChatLog.session_id == session_id).count()
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
    """获取综合统计"""
    user_filter = ChatLog.user_id == current_user.id if current_user.role != "admin" else True

    total_messages = db.query(ChatLog).filter(user_filter).count()
    user_messages = db.query(ChatLog).filter(user_filter, ChatLog.role == "user").count()
    total_sessions = db.query(ChatLog.session_id).filter(user_filter).distinct().count()
    total_kb = db.query(KnowledgeBase).count()
    total_docs = db.query(Document).count()
    ready_docs = db.query(Document).filter(Document.status == "ready").count()

    return {
        "total_messages": total_messages,
        "user_messages": user_messages,
        "total_sessions": total_sessions,
        "total_kb": total_kb,
        "total_docs": total_docs,
        "ready_docs": ready_docs,
    }


@router.get("/export")
def export_logs(
    session_id: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """导出对话日志为 CSV"""
    query = db.query(ChatLog)
    if current_user.role != "admin":
        query = query.filter(ChatLog.user_id == current_user.id)
    if session_id:
        query = query.filter(ChatLog.session_id == session_id)

    logs = query.order_by(ChatLog.created_at).all()

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
    """获取对话数据分析"""
    user_filter = ChatLog.user_id == current_user.id if current_user.role != "admin" else True

    # 总体统计
    total_messages = db.query(ChatLog).filter(user_filter).count()
    user_messages = db.query(ChatLog).filter(user_filter, ChatLog.role == "user").count()
    total_sessions = db.query(ChatLog.session_id).filter(user_filter).distinct().count()

    # 热门问题（用户消息中出现频率最高的关键词）
    user_logs = db.query(ChatLog.content).filter(user_filter, ChatLog.role == "user").all()
    word_freq = {}
    for (content,) in user_logs:
        words = content.split()
        for word in words:
            if len(word) > 1:
                word_freq[word] = word_freq.get(word, 0) + 1
    top_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:10]

    # 按天统计消息量
    daily_stats = {}
    all_logs = db.query(ChatLog.created_at).filter(user_filter).all()
    for (created_at,) in all_logs:
        if created_at:
            day = created_at.strftime("%Y-%m-%d")
            daily_stats[day] = daily_stats.get(day, 0) + 1

    return {
        "total_messages": total_messages,
        "user_messages": user_messages,
        "total_sessions": total_sessions,
        "top_words": [{"word": w, "count": c} for w, c in top_words],
        "daily_stats": [{"date": d, "count": c} for d, c in sorted(daily_stats.items())],
    }


@router.delete("/cleanup")
def cleanup_logs(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """清理过期日志"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="无权限")

    from datetime import datetime, timedelta
    cutoff = datetime.now() - timedelta(days=days)
    deleted = db.query(ChatLog).filter(ChatLog.created_at < cutoff).delete()
    db.commit()
    return {"detail": f"已清理 {deleted} 条过期日志"}
