"""
请假管理模块：请假记录查询、统计与审批

提供以下接口：
- GET  /leave/           — 查询请假列表
- GET  /leave/stats      — 请假统计数据
- PUT  /leave/{id}/approve — 批准请假
- PUT  /leave/{id}/reject  — 驳回请假

权限规则：
- admin/kb_admin/teacher：可查看所有请假记录，可批准/驳回
- 普通用户：仅查看自己学号相关的请假记录
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ...models.tables import LeaveRequest, Student
from ..deps import get_db, get_current_user

router = APIRouter(prefix="/leave", tags=["请假管理"])


@router.get("/")
def list_leave_requests(
    status: str = None,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """查询请假列表

    - admin/kb_admin/teacher：查看所有请假记录
    - 普通用户：仅查看自己学号关联的请假记录
    - 支持按状态筛选（pending/approved/rejected）
    - 返回请假详情（含学生姓名、班级等关联信息）
    """
    # 通过 Student 表关联查询
    query = db.query(LeaveRequest).join(Student)

    if user.role not in ("admin", "kb_admin", "teacher"):
        # 普通用户只能看自己学号相关的请假记录
        query = query.filter(Student.student_id == getattr(user, "student_id", None))

    if status:
        query = query.filter(LeaveRequest.status == status)

    # 按创建时间倒序排列
    leaves = query.order_by(LeaveRequest.created_at.desc()).all()

    # 组装返回数据：关联 Student 表获取学生信息
    result = []
    for l in leaves:
        student = db.query(Student).filter(Student.id == l.student_id).first()
        result.append({
            "id": l.id,
            "student_id": student.student_id if student else "",
            "student_name": student.name if student else "",
            "class_name": student.class_name if student else "",
            "start_date": l.start_date,
            "end_date": l.end_date,
            "reason": l.reason,
            "status": l.status,
            "created_at": l.created_at.isoformat() if l.created_at else "",
        })

    return result


@router.get("/stats")
def leave_stats(
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """请假统计

    - 所有已登录用户均可访问
    - 返回：总数、待审批数、已批准数、已驳回数
    - 用于仪表盘或请假管理页面的统计卡片
    """
    total = db.query(LeaveRequest).count()
    pending = db.query(LeaveRequest).filter(LeaveRequest.status == "pending").count()
    approved = db.query(LeaveRequest).filter(LeaveRequest.status == "approved").count()
    rejected = db.query(LeaveRequest).filter(LeaveRequest.status == "rejected").count()
    return {"total": total, "pending": pending, "approved": approved, "rejected": rejected}


@router.put("/{leave_id}/approve")
def approve_leave(
    leave_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """批准请假

    - 仅 admin/kb_admin/teacher 可操作
    - 仅待审批（pending）状态的请假可批准
    - 已批准或已驳回的请假不可重复操作
    """
    if user.role not in ("admin", "kb_admin", "teacher"):
        raise HTTPException(status_code=403, detail="无权限")

    leave = db.query(LeaveRequest).filter(LeaveRequest.id == leave_id).first()
    if not leave:
        raise HTTPException(status_code=404, detail="请假记录不存在")
    # 防止重复操作
    if leave.status != "pending":
        raise HTTPException(status_code=400, detail=f"该请假已{leave.status}，无法重复操作")

    leave.status = "approved"
    db.commit()
    return {"detail": "已批准", "id": leave_id, "status": "approved"}


@router.put("/{leave_id}/reject")
def reject_leave(
    leave_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """驳回请假

    - 仅 admin/kb_admin/teacher 可操作
    - 仅待审批（pending）状态的请假可驳回
    - 已批准或已驳回的请假不可重复操作
    """
    if user.role not in ("admin", "kb_admin", "teacher"):
        raise HTTPException(status_code=403, detail="无权限")

    leave = db.query(LeaveRequest).filter(LeaveRequest.id == leave_id).first()
    if not leave:
        raise HTTPException(status_code=404, detail="请假记录不存在")
    # 防止重复操作
    if leave.status != "pending":
        raise HTTPException(status_code=400, detail=f"该请假已{leave.status}，无法重复操作")

    leave.status = "rejected"
    db.commit()
    return {"detail": "已驳回", "id": leave_id, "status": "rejected"}
