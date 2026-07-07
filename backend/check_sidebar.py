with open(r"E:\实训\smart_campus_agent\frontend\src\components\layout\Sidebar.vue", "r", encoding="utf-8") as f:
    content = f.read()

print("=== SFC Structure ===")
for tag in ["<template>", "</template>", "<script setup>", "</script>", "<style scoped>", "</style>"]:
    count = content.count(tag)
    status = "OK" if count == 1 else f"FOUND {count} TIMES"
    print(f"  {tag}: {status}")

print("\n=== Key Imports ===")
for imp in ["chatStore", "userStore", "useChatStore", "useUserStore", "ElMessageBox", "collapsed"]:
    found = imp in content
    print(f"  {imp}: {'FOUND' if found else 'MISSING'}")

print("\n=== Key Functions ===")
for fn in ["handleNew", "handleDelete", "createSession", "collapse"]:
    found = fn in content
    print(f"  {fn}: {'FOUND' if found else 'MISSING'}")
