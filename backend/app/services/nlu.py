"""
NLU: 意图识别 + 问题重写 + 语义纠错
"""
import re


# 意图关键词映射
INTENT_KEYWORDS = {
    "help": ["帮助", "怎么用", "使用方法", "功能", "操作", "指南", "教程"],
    "knowledge_base": ["知识库", "创建知识库", "管理知识库"],
    "document": ["文档", "上传", "文件", "解析"],
    "system": ["版本", "系统", "配置", "设置", "参数"],
    "greeting": ["你好", "您好", "hi", "hello", "嗨"],
}

# 问题重写规则
REWRITE_RULES = [
    (r"^(这个|那个)文档", "知识库中的文档"),
    (r"^(怎么|如何)(创建|新建|添加)", "如何创建"),
    (r"^(怎么|如何)(删除|移除)", "如何删除"),
    (r"^(怎么|如何)(修改|编辑|更改)", "如何修改"),
]

# 同音字/形近字纠错表（校园场景常用）
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
    """识别用户意图"""
    query_lower = query.lower().strip()
    for intent, keywords in INTENT_KEYWORDS.items():
        for kw in keywords:
            if kw in query_lower:
                return intent
    return "query"


def correct_typos(query: str) -> str:
    """语义纠错：替换同音字/形近字"""
    corrected = query
    for wrong, right in CORRECTION_MAP.items():
        corrected = corrected.replace(wrong, right)
    return corrected


def rewrite_question(query: str, history: list[dict] = None) -> str:
    """重写模糊问题，提升检索准确率"""
    # 先做语义纠错
    rewritten = correct_typos(query.strip())

    # 应用重写规则
    for pattern, replacement in REWRITE_RULES:
        rewritten = re.sub(pattern, replacement, rewritten)

    # 如果有上下文，尝试代词消解
    if history and len(history) > 0:
        last_user_msg = None
        for msg in reversed(history):
            if msg["role"] == "user":
                last_user_msg = msg["content"]
                break

        if last_user_msg:
            pronouns = ["它", "这个", "那个", "这个文档", "那个文档"]
            for pronoun in pronouns:
                if rewritten.startswith(pronoun):
                    nouns = re.findall(r"[\u4e00-\u9fa5]{2,4}", last_user_msg)
                    if nouns:
                        rewritten = rewritten.replace(pronoun, nouns[0], 1)
                    break

    return rewritten
