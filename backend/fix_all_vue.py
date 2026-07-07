import os

vue_dir = r"E:\实训\smart_campus_agent\frontend\src"
files_to_fix = [
    'components/chat/ChatBubble.vue',
    'components/layout/Sidebar.vue',
    'components/upload/FileUploader.vue',
    'views/StudentLeaveView.vue',
    'views/Admin/DocumentManage.vue',
    'views/Admin/KnowledgeBaseManage.vue',
    'views/Admin/LeaveManage.vue',
    'views/Admin/LogsManage.vue',
    'views/Admin/UserManage.vue',
]
fixed = 0
for rel in files_to_fix:
    path = os.path.join(vue_dir, rel)
    with open(path, "r", encoding="utf-8") as fh:
        lines = fh.readlines()

    # Find last </template> line
    template_end_idx = None
    for i, line in enumerate(lines):
        if "</template>" in line:
            template_end_idx = i

    if template_end_idx is None:
        print(f"SKIP {rel}: no </template>")
        continue

    # Find next non-empty line
    next_idx = template_end_idx + 1
    while next_idx < len(lines) and lines[next_idx].strip() == "":
        next_idx += 1

    if next_idx >= len(lines):
        print(f"SKIP {rel}: nothing after template")
        continue

    next_line = lines[next_idx].strip()
    if next_line.startswith("<script") or next_line.startswith("<style"):
        print(f"OK {rel}: already has script/style")
        continue

    # Insert <script setup> before the comment block
    lines.insert(next_idx, "<script setup>\n")
    with open(path, "w", encoding="utf-8") as fh:
        fh.writelines(lines)
    print(f"FIXED {rel}")
    fixed += 1

print(f"\nTotal fixed: {fixed}")
