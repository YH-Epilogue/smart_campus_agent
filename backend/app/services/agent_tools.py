"""
Agent Tools: 智能体工具注册与执行模块

本模块实现了灵犀智能体的工具系统（Function Calling）。
核心思路：
1. ToolRegistry 管理所有可用工具的注册、描述生成和执行调度
2. 每个工具是一个 Python 函数，接收 db Session + LLM 传入的参数，返回结构化结果
3. 工具定义会转换为 OpenAI Function Calling 格式，让大模型自主决定何时调用哪个工具

当前内置 3 个工具：
- query_student: 按学号或姓名查询学生信息
- create_leave_request: 为指定学生创建请假申请
- get_leave_status: 查询指定学生的请假记录列表

扩展方式：在 _register_builtin 中注册新函数，并在 get_openai_tools 的 schemas 中添加参数定义。
"""
from sqlalchemy.orm import Session
from ..models.tables import Student, LeaveRequest


class ToolRegistry:
    """工具注册与执行中心

    维护一个 name → callable 的映射表，提供：
    - 注册/查询工具
    - 生成 OpenAI function calling 格式的工具描述（供 LLM 选择工具时使用）
    - 统一的工具执行入口（含异常捕获和结果格式化）
    """

    def __init__(self):
        self._tools: dict[str, callable] = {}
        # 初始化时自动注册所有内置工具
        self._register_builtin()

    def _register_builtin(self):
        """注册内置工具：学生查询、请假创建、请假状态查询"""
        self.register("query_student", self._query_student)
        self.register("create_leave_request", self._create_leave_request)
        self.register("get_leave_status", self._get_leave_status)

    def register(self, name: str, func: callable):
        """注册一个工具函数

        Args:
            name: 工具名称，LLM 通过此名称调用工具
            func: 工具函数，签名需接受 db: Session，其余参数由 LLM 传入
        """
        self._tools[name] = func

    def get_tool_descriptions(self) -> list[dict]:
        """返回所有工具的简要描述列表

        格式为 [{"name": "...", "description": "..."}]，
        供 build_system_prompt 中拼接到系统提示词中，让模型了解可用工具。
        """
        return [
            {"name": name, "description": func.__doc__ or ""}
            for name, func in self._tools.items()
        ]

    def get_openai_tools(self) -> list[dict]:
        """返回 OpenAI Function Calling 格式的工具定义

        每个工具包含 name、description 和 JSON Schema 格式的 parameters。
        模型根据此定义决定调用哪个工具、传入哪些参数。

        注意：schemas 字典需与各工具函数的参数名严格对应，
        否则 LLM 传入的参数名会与函数签名不匹配导致执行失败。
        """
        # 各工具的参数 Schema 定义
        schemas = {
            "query_student": {
                "type": "object",
                "properties": {
                    "student_id": {"type": "string", "description": "学生学号，如 2023001"},
                    "name": {"type": "string", "description": "学生姓名，如 张三"},
                },
            },
            "create_leave_request": {
                "type": "object",
                "properties": {
                    "student_id_str": {"type": "string", "description": "学生学号，如 2023001"},
                    "start_date": {"type": "string", "description": "请假开始日期，格式 YYYY-MM-DD"},
                    "end_date": {"type": "string", "description": "请假结束日期，格式 YYYY-MM-DD"},
                    "reason": {"type": "string", "description": "请假原因"},
                },
                # start_date 和 end_date 为必填，reason 可选
                "required": ["student_id_str", "start_date", "end_date"],
            },
            "get_leave_status": {
                "type": "object",
                "properties": {
                    "student_id_str": {"type": "string", "description": "学生学号，如 2023001"},
                },
                "required": ["student_id_str"],
            },
        }
        return [
            {
                "type": "function",
                "function": {
                    "name": name,
                    "description": func.__doc__ or "",
                    # 未定义 schema 的工具使用空 object 作为兜底
                    "parameters": schemas.get(name, {"type": "object", "properties": {}}),
                },
            }
            for name, func in self._tools.items()
        ]

    async def execute(self, tool_name: str, arguments: dict, db: Session) -> dict:
        """执行指定工具并返回结构化结果

        Args:
            tool_name: 工具名称（与注册名一致）
            arguments: LLM 传入的参数字典
            db: SQLAlchemy 数据库会话

        Returns:
            dict: {"success": True, "result": ...} 或 {"success": False, "error": "..."}
        """
        if tool_name not in self._tools:
            return {"success": False, "error": f"未知工具: {tool_name}"}
        try:
            # 将 db 作为关键字参数传入，其余参数由 LLM 决定
            result = self._tools[tool_name](db=db, **arguments)
            # 工具函数内部返回 {"error": ...} 时视为执行失败
            if isinstance(result, dict) and "error" in result:
                return {"success": False, "error": result["error"]}
            return {"success": True, "result": result}
        except Exception as e:
            # 捕获所有异常，避免工具执行失败导致整个对话流程中断
            return {"success": False, "error": str(e)}

    def _query_student(self, db: Session, student_id: str = None, name: str = None) -> dict:
        """查询学生信息

        支持两种查询方式：
        - 按学号精确匹配（优先）
        - 按姓名模糊匹配（contains）
        两者至少提供其一。
        """
        if student_id:
            student = db.query(Student).filter(Student.student_id == student_id).first()
        elif name:
            # 使用 contains 做模糊匹配，如输入"张"可匹配"张三"
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
        """创建请假申请

        参数说明：
        - student_id_str: 学号字符串（LLM 通常传入此参数）
        - student_id: 内部主键 ID（备用参数，一般不直接使用）
        - start_date / end_date: 请假起止日期，格式 YYYY-MM-DD
        - reason: 请假原因（可选）

        流程：先通过学号查找学生 → 获取内部 ID → 创建 LeaveRequest 记录 → 返回结果
        """
        # LLM 传入的是学号字符串，需要先转换为内部主键 ID
        if student_id_str:
            student = db.query(Student).filter(Student.student_id == student_id_str).first()
            if not student:
                return {"error": "未找到该学生"}
            student_id = student.id

        if not student_id:
            return {"error": "必须提供有效的学号"}

        # 创建请假记录，默认状态为 pending（待审批）
        leave = LeaveRequest(
            student_id=student_id,
            start_date=start_date,
            end_date=end_date,
            reason=reason,
            status="pending",
        )
        db.add(leave)
        db.commit()
        db.refresh(leave)  # refresh 以获取数据库生成的 ID
        return {
            "leave_id": leave.id,
            "status": leave.status,
            "message": "请假申请已提交",
        }

    def _get_leave_status(self, db: Session, student_id: int = None, student_id_str: str = None) -> dict:
        """查询指定学生的请假记录列表

        返回该学生所有请假记录，包含日期、原因和审批状态。
        """
        if student_id_str:
            student = db.query(Student).filter(Student.student_id == student_id_str).first()
            if not student:
                return {"error": "未找到该学生"}
            student_id = student.id

        if not student_id:
            return {"error": "必须提供有效的学号"}

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


# 模块级单例，供 chat 路由等调用方共享
tool_registry = ToolRegistry()
