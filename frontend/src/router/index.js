/**
 * 前端路由配置
 *
 * 功能：
 * - 定义所有页面路由（登录页、聊天页、学生请假页、管理后台页面）
 * - 路由守卫：未登录跳转 /login，角色无权限跳转首页
 * - 所有管理页面均使用懒加载（动态 import），首屏只加载登录页和聊天页
 *
 * 路由权限设计：
 * - /login：无需登录
 * - /（聊天页）：所有已登录用户可访问
 * - /student/*：仅学生可访问
 * - /admin/*（知识库/文档/请假）：老师和管理员可访问
 * - /admin/*（仪表盘/用户/日志/设置）：仅管理员可访问
 */
import { createRouter, createWebHistory } from "vue-router";
import { useUserStore } from "../stores/userStore";

const routes = [
  // 登录页（无需认证）
  {
    path: "/login",
    name: "Login",
    component: () => import("../views/Login.vue"),
  },
  // 主聊天页面（所有已登录用户）
  {
    path: "/",
    name: "Chat",
    component: () => import("../views/ChatView.vue"),
    meta: { requiresAuth: true, roles: ["student", "teacher", "admin"] },
  },
  // --- 学生页面 ---
  // 学生请假申请页（仅学生）
  {
    path: "/student/leave",
    name: "StudentLeave",
    component: () => import("../views/StudentLeaveView.vue"),
    meta: { requiresAuth: true, roles: ["student"] },
  },
  // --- 老师/管理员页面 ---
  // 知识库管理（老师可查看/编辑，管理员可管理全部）
  {
    path: "/admin/kb",
    name: "KnowledgeBase",
    component: () => import("../views/Admin/KnowledgeBaseManage.vue"),
    meta: { requiresAuth: true, roles: ["teacher", "admin"] },
  },
  // 文档管理（依赖知识库，需选择知识库后操作）
  {
    path: "/admin/doc",
    name: "Document",
    component: () => import("../views/Admin/DocumentManage.vue"),
    meta: { requiresAuth: true, roles: ["teacher", "admin"] },
  },
  // 请假审批管理（老师审批本班，管理员审批全部）
  {
    path: "/admin/leave",
    name: "LeaveManage",
    component: () => import("../views/Admin/LeaveManage.vue"),
    meta: { requiresAuth: true, roles: ["teacher", "admin"] },
  },
  // --- 管理员专属页面 ---
  // 系统仪表盘（展示使用统计和系统状态）
  {
    path: "/admin/dashboard",
    name: "Dashboard",
    component: () => import("../views/Admin/Dashboard.vue"),
    meta: { requiresAuth: true, roles: ["admin"] },
  },
  // 用户管理（增删改查、角色分配）
  {
    path: "/admin/users",
    name: "UserManage",
    component: () => import("../views/Admin/UserManage.vue"),
    meta: { requiresAuth: true, roles: ["admin"] },
  },
  // 操作日志查看（支持筛选和导出）
  {
    path: "/admin/logs",
    name: "Logs",
    component: () => import("../views/Admin/LogsManage.vue"),
    meta: { requiresAuth: true, roles: ["admin"] },
  },
  // 系统设置（配置 API Key 等参数）
  {
    path: "/admin/settings",
    name: "Settings",
    component: () => import("../views/Admin/SettingsManage.vue"),
    meta: { requiresAuth: true, roles: ["admin"] },
  },
];

const router = createRouter({
  history: createWebHistory(), // 使用 HTML5 History 模式（URL 无 #）
  routes,
});

/**
 * 全局路由守卫
 * 每次路由跳转前检查：
 * 1. 需要登录的页面 → 未登录则跳转 /login
 * 2. 有角色限制的页面 → 角色不匹配则跳转首页（静默降级）
 */
router.beforeEach((to, from, next) => {
  const userStore = useUserStore();

  // 1. 需要登录但未登录 → 跳转登录页
  if (to.meta.requiresAuth && !userStore.isLoggedIn) {
    next("/login");
    return;
  }

  // 2. 有角色限制但用户无角色信息（token 无效/过期） → 跳转登录页
  if (to.meta.roles && !userStore.user?.role) {
    userStore.logout();
    next("/login");
    return;
  }

  // 3. 有角色限制但用户角色不在允许列表 → 跳转首页
  if (to.meta.roles && !to.meta.roles.includes(userStore.user?.role)) {
    next("/");
    return;
  }

  // 4. 放行
  next();
});

export default router;
