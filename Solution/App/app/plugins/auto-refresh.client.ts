export default defineNuxtPlugin(() => {
  const markingSessionsStore = useMarkingStore();
  const updatesStore = useUpdatesStore();
  const authStore = useAuthStore();

  let interval: ReturnType<typeof setInterval> | null = null;
  const REFRESH_INTERVAL = 30000; // 30 seconds

  const refreshStores = async () => {
    if (!authStore.isAuthenticated) return;

    try {
      await Promise.all([markingSessionsStore.fetchSessions(), updatesStore.fetchUpdates()]);
    } catch (err) {
      console.error('Auto refresh failed:', err);
    }
  };

  const start = () => {
    if (interval) return;
    refreshStores();
    interval = setInterval(refreshStores, REFRESH_INTERVAL);
  };

  const stop = () => {
    if (interval) {
      clearInterval(interval);
      interval = null;
    }
  };

  if (import.meta.client) {
    start();

    // Pause when tab inactive
    document.addEventListener('visibilitychange', () => {
      if (document.hidden) {
        stop();
      } else {
        start();
      }
    });
  }

  window.addEventListener('session-updated', refreshStores);
});
