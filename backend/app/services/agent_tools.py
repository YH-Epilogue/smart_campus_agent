"""
Agent Tools: 智能体动作执行器
处理结构化函数调用，如自动写入请假表等
"""
from sqlalchemy.orm import Session
from ..models.tables import Student, LeaveRequest


class ToolRegistry:
    """工具注册与执行"""

    def __init__(self):
        self._tools: dict[str, callable] = {}
        self._register_builtin()

    def _register_builtin(self):
        self.register("query_student", self._query_student)
        self.register("create_leave_request", self._create_leave_request)
        self.register("get_leave_status", self._get_leave_status)

    def register(self, name: str, func: callable):
        self._tools[name] = func

    def get_tool_descriptions(self) -> list[dict]:
        """返回所有工具的描述，供 LLM 做 function calling"""
        return [
            {"name": name, "description": func.__doc__ or ""}
            for name, func in self._tools.items()
        ]

    async def execute(self, tool_name: str, arguments: dict, db: Session) -> dict:
        if tool_name not in self._tools:
            return {"error": f"未知工具: {tool_name}"}
        try:
            result = self._tools[tool_name](db=db, **arguments)
            return {"success": True, "result": result}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _query_student(self, db: Session, student_id: str = None, name: str = None) -> dict:
        """查询学生信息"""
        if student_id:
            student = db.query(Student).filter(Student.student_id == student_id).first()
        elif name:
            student = db.query(Student).filter(Student.name.contains(name)).first()
        else:
            return {"error": "请提供学号或姓名"}

        if not student:
            return {"error": "未找到该学生"}
        return {
            "student_id": student.student_id,
            "name": student.name,
            "class_name": student.class_name,
            "phone": student.phone,
        }

    def _create_leave_request(
        self,
        db: Session,
        student_id: int = None,
        student_id_str: str = None,
        start_date: str = "",
        end_date: str = "",
        reason: str = "",
    ) -> dict:
        """创建请假申请"""
        if student_id_str:
            student = db.query(Student).filter(Student.student_id == student_id_str).first()
            if not student:
                return {"error": "未找到该学生"}
            student_id = student.id

        leave = LeaveRequest(
            student_id=student_id,
            start_date=start_date,
            end_date=end_date,
            reason=reason,
            status="pending",
        )
        db.add(leave)
        db.commit()
        db.refresh(leave)
        return {
            "leave_id": leave.id,
            "status": leave.status,
            "message": "请假申请已提交",
        }

    def _get_leave_status(self, db: Session, student_id: int = None, student_id_str: str = None) -> dict:
        """查询请假状态"""
        if student_id_str:
            student = db.query(Student).filter(Student.student_id == student_id_str).first()
            if not student:
                return {"error": "未找到该学生"}
            student_id = student.id

        leaves = db.query(LeaveRequest).filter(LeaveRequest.student_id == student_id).all()
        return [
            {
                "id": l.id,
                "start_date": l.start_date,
                "end_date": l.end_date,
                "reason": l.reason,
                "status": l.status,
            }
            for l in leaves
        ]


tool_registry = ToolRegistry()
