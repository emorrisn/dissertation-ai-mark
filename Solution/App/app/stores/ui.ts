import { defineStore } from 'pinia';

interface Notification {
  id: string;
  title: string;
  description: string;
  type: 'success' | 'error' | 'info';
}

export const useUiStore = defineStore('ui', {
  state: () => ({
    isAppLoading: false,
    notifications: [] as Notification[]
  }),
  actions: {
    setAppLoading(isLoading: boolean) {
      this.isAppLoading = isLoading;
    },
    addNotification(notification: Omit<Notification, 'id'>) {
      const id = new Date().toISOString() + Math.random();
      this.notifications.push({ id, ...notification });
    },
    removeNotification(id: string) {
      this.notifications = this.notifications.filter((n) => n.id !== id);
    }
  }
});
