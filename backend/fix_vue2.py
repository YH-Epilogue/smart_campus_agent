import os

vue_dir = r"E:\实训\smart_campus_agent\frontend\src"
files_to_check = [
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
for rel in files_to_check:
    path = os.path.join(vue_dir, rel)
    with open(path, 'r', encoding='utf-8') as fh:
        content = fh.read()
    # Find the LAST </template>
    last_idx = content.rfind('</template>')
    if last_idx == -1:
        print(f'{rel}: NO </template> FOUND')
        continue
    # Check what comes after it
    after_text = content[last_idx+11:].lstrip()
    if after_text.startswith('<script') or after_text.startswith('<style'):
        print(f'{rel}: OK - has script/style after template')
    else:
        # Find the position after </template> and its trailing newlines
        lines = content.split('\n')
        template_end_line = None
        for i, line in enumerate(lines):
            if '</template>' in line:
                template_end_line = i
        if template_end_line:
            next_content = lines[template_end_line + 1].strip() if template_end_line + 1 < len(lines) else ''
            print(f'{rel}: BROKEN - line {template_end_line + 2} = "{next_content[:50]}"')
