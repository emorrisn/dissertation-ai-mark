import { useAuthStore } from '~/stores/auth';

export default defineNuxtRouteMiddleware((to, from) => {
  const authStore = useAuthStore();

  if (authStore.isAuthenticated && to.path === '/login') {
    return navigateTo('/dashboard/updates');
  }

  if (!authStore.isAuthenticated && to.path !== '/login' && to.path !== '/') {
    return navigateTo(`/login?redirect=${to.fullPath}`);
  }
});
