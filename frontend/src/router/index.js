import { createRouter, createWebHistory } from "vue-router";
import { useUserStore } from "../stores/userStore";

const routes = [
  {
    path: "/login",
    name: "Login",
    component: () => import("../views/Login.vue"),
  },
  {
    path: "/",
    name: "Chat",
    component: () => import("../views/ChatView.vue"),
    meta: { requiresAuth: true },
  },
  {
    path: "/admin/kb",
    name: "KnowledgeBase",
    component: () => import("../views/Admin/KnowledgeBaseManage.vue"),
    meta: { requiresAuth: true, requiresAdmin: true },
  },
  {
    path: "/admin/doc",
    name: "Document",
    component: () => import("../views/Admin/DocumentManage.vue"),
    meta: { requiresAuth: true, requiresAdmin: true },
  },
  {
    path: "/admin/dashboard",
    name: "Dashboard",
    component: () => import("../views/Admin/Dashboard.vue"),
    meta: { requiresAuth: true, requiresAdmin: true },
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

router.beforeEach((to, from, next) => {
  const userStore = useUserStore();
  if (to.meta.requiresAuth && !userStore.isLoggedIn) {
    next("/login");
  } else if (to.meta.requiresAdmin && userStore.user?.role !== "admin") {
    next("/");
  } else {
    next();
  }
});

export default router;
