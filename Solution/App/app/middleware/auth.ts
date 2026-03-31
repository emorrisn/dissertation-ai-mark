import { useAuthStore } from '~/stores/auth';

// This middleware is used to protect routes
// It will redirect authenticated users from the login page to the dashboard
// It will redirect unauthenticated users to the login page
export default defineNuxtRouteMiddleware((to, _from) => {
  const authStore = useAuthStore();

  if (authStore.isAuthenticated && (to.path === '/login' || to.path === '/')) {
    return navigateTo('/dashboard/updates');
  }

  if (!authStore.isAuthenticated && to.path !== '/login' && to.path !== '/') {
    return navigateTo(`/login?redirect=${to.fullPath}`);
  }
});
