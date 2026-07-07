with open(r"E:\实训\smart_campus_agent\frontend\src\views\ChatView.vue", "r", encoding="utf-8") as f:
    content = f.read()

# Check SFC structure
print("=== SFC Structure ===")
for tag in ["<template>", "</template>", "<script setup>", "</script>", "<style scoped>", "</style>"]:
    count = content.count(tag)
    status = "OK" if count == 1 else f"FOUND {count} TIMES"
    print(f"  {tag}: {status}")

# Check key imports
print("\n=== Key Imports ===")
for imp in ["chatStore", "Sidebar", "Header", "ChatBubble", "useChatStore", "http", "axios", "ElMessage"]:
    found = imp in content
    print(f"  {imp}: {'FOUND' if found else 'MISSING'}")

# Check for handleSend
print("\n=== Key Functions ===")
for fn in ["handleSend", "handleFileUpload", "handleNew", "triggerFileUpload"]:
    found = fn in content
    print(f"  {fn}: {'FOUND' if found else 'MISSING'}")
