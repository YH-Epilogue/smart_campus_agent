import os

vue_dir = r"E:\实训\smart_campus_agent\frontend\src"
fixed = 0
for root, dirs, files in os.walk(vue_dir):
    for f in files:
        if not f.endswith(".vue"):
            continue
        path = os.path.join(root, f)
        with open(path, "r", encoding="utf-8") as fh:
            content = fh.read()

        if "<script setup>" in content:
            continue  # Already has script tag

        if "</template>" not in content:
            continue  # No template section

        # Find line after </template>
        lines = content.split("\n")
        insert_idx = None
        for i, line in enumerate(lines):
            if "</template>" in line.strip():
                insert_idx = i + 1
                break

        if insert_idx is None:
            continue

        # Skip empty lines after </template>
        while insert_idx < len(lines) and lines[insert_idx].strip() == "":
            insert_idx += 1

        # Check if the next line is a comment block (start with /** or //)
        if insert_idx < len(lines) and (lines[insert_idx].strip().startswith("/**") or lines[insert_idx].strip().startswith("//") or lines[insert_idx].strip().startswith("*")):
            # Insert <script setup> before the comment
            lines.insert(insert_idx, "<script setup>\n")
            with open(path, "w", encoding="utf-8") as fh:
                fh.write("\n".join(lines))
            print(f"FIXED: {os.path.relpath(path, vue_dir)}")
            fixed += 1

print(f"Total fixed: {fixed}")
