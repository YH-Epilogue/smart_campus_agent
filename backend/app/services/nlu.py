"""
NLU: 自然语言理解模块

本模块负责对话前的文本预处理，提升用户输入的质量和可理解性。
包含三个子功能：
1. 意图识别（recognize_intent）：基于关键词匹配判断用户想做什么
2. 语义纠错（correct_typos）：替换同音字/形近字，修正语音输入或打字错误
3. 问题重写（rewrite_question）：统一问题表述、消解代词，提升检索准确率

设计思路：采用规则引擎而非模型推理，因为校园场景词汇量有限、模式固定，
规则方法零延迟、零成本、可解释性强，适合此类结构化场景。
"""
import re


# 意图关键词映射表
# key: 意图标签，value: 触发该意图的关键词列表
# 匹配规则：用户输入包含任一关键词即命中（先到先得，按字典序）
INTENT_KEYWORDS = {
    "help": ["帮助", "怎么用", "使用方法", "功能", "操作", "指南", "教程"],
    "knowledge_base": ["知识库", "创建知识库", "管理知识库"],
    "document": ["文档", "上传", "文件", "解析"],
    "system": ["版本", "系统", "配置", "设置", "参数"],
    "greeting": ["你好", "您好", "hi", "hello", "嗨"],
}

# 问题重写规则列表
# 每条规则为 (正则模式, 替换文本) 元组
# 用于将口语化/模糊表述统一为规范化问题，提升 RAG 检索命中率
REWRITE_RULES = [
    (r"^(这个|那个)文档", "知识库中的文档"),  # 消解指示代词
    (r"^(怎么|如何)(创建|新建|添加)", "如何创建"),  # 统一动作动词
    (r"^(怎么|如何)(删除|移除)", "如何删除"),
    (r"^(怎么|如何)(修改|编辑|更改)", "如何修改"),
]

# 同音字/形近字纠错表（校园场景高频错词）
# 键为错误写法，值为正确写法
# 覆盖：知识库、文档、上传、删除、编辑、课程、成绩、请假、图书馆、宿舍
CORRECTION_MAP = {
    "知势库": "知识库",
    "支势库": "知识库",
    "问档": "文档",
    "纹档": "文档",
    "上传": "上传",
    "上穿": "上传",
    "删楚": "删除",
    "山除": "删除",
    "编即": "编辑",
    "边辑": "编辑",
    "课冲": "课程",
    "科程": "课程",
    "成绩": "成绩",
    "城绩": "成绩",
    "请架": "请假",
    "亲架": "请假",
    "图是馆": "图书馆",
    "图书管": "图书馆",
    "素舍": "宿舍",
    "宿舍": "宿舍",
}


def recognize_intent(query: str) -> str:
    """识别用户意图

    遍历 INTENT_KEYWORDS 中的关键词，命中即返回对应意图标签。
    未命中任何关键词时返回 "query"（通用查询，交给 LLM 处理）。

    Args:
        query: 用户原始输入

    Returns:
        意图标签字符串（help / knowledge_base / document / system / greeting / query）
    """
    query_lower = query.lower().strip()
    for intent, keywords in INTENT_KEYWORDS.items():
        for kw in keywords:
            if kw in query_lower:
                return intent
    return "query"


def correct_typos(query: str) -> str:
    """语义纠错：替换同音字/形近字

    使用简单的字符串替换（replace），按 CORRECTION_MAP 逐项修正。
    适用于语音输入或拼音输入法产生的常见错词。

    注意：替换顺序不影响结果，因为错误词之间无重叠。
    """
    corrected = query
    for wrong, right in CORRECTION_MAP.items():
        corrected = corrected.replace(wrong, right)
    return corrected


def rewrite_question(query: str, history: list[dict] = None) -> str:
    """重写模糊问题，提升检索准确率

    处理流程：
    1. 语义纠错（修正同音字/形近字）
    2. 正则重写（统一口语化表述为规范化问题）
    3. 代词消解（将"它"、"这个"等代词替换为上一轮对话中的实体名词）

    Args:
        query: 用户原始输入
        history: 对话历史列表（可选），用于代词消解

    Returns:
        重写后的规范化问题文本
    """
    # 第一步：语义纠错
    rewritten = correct_typos(query.strip())

    # 第二步：应用正则重写规则
    for pattern, replacement in REWRITE_RULES:
        rewritten = re.sub(pattern, replacement, rewritten)

    # 第三步：代词消解
    # 当用户说"它怎么删除"时，将"它"替换为上一轮提到的具体名词（如"知识库"）
    if history and len(history) > 0:
        # 从历史中找到最近一条用户消息
        last_user_msg = None
        for msg in reversed(history):
            if msg["role"] == "user":
                last_user_msg = msg["content"]
                break

        if last_user_msg:
            pronouns = ["它", "这个", "那个", "这个文档", "那个文档"]
            for pronoun in pronouns:
                if rewritten.startswith(pronoun):
                    # 从上一条用户消息中提取 2~4 个连续汉字作为实体候选
                    # 优先取第一个匹配的名词短语
                    nouns = re.findall(r"[\u4e00-\u9fa5]{2,4}", last_user_msg)
                    if nouns:
                        rewritten = rewritten.replace(pronoun, nouns[0], 1)
                    break

    return rewritten
