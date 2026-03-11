import { defineStore } from 'pinia';
import type { UserUpdate } from '~/types';

export const useUpdatesStore = defineStore('updates', {
  state: () => ({
    updates: [] as UserUpdate[],
    status: 'idle' as 'idle' | 'loading' | 'succeeded' | 'failed'
  }),

  getters: {
    unreadUpdates: (state): UserUpdate[] => state.updates.filter((u) => !u.isRead),
    unreadCount: (state): number => state.updates.filter((u) => !u.isRead).length,
    sortedUpdates: (state): UserUpdate[] => {
      // Return a new sorted array to avoid mutating state
      return [...state.updates].sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());
    }
  },

  actions: {
    /**
     * Fetches updates from the server.
     */
    async fetchUpdates() {
      const { $api } = useNuxtApp();

      this.status = 'loading';

      try {
        const res = await $api<UserUpdate[]>('/user/updates');

        // map backend fields -> frontend fields
        this.updates = res.map((u: any) => ({
          id: u.id,
          type: u.type,
          title: u.title,
          message: u.message,
          link: u.link,
          relatedId: u.relatedId,
          timestamp: u.createdAt,
          isRead: u.isRead
        }));

        this.status = 'succeeded';
      } catch (error) {
        console.error('Failed to fetch updates:', error);
        this.status = 'failed';
      }
    },

    async markAsRead(updateId: string) {
      const { $api } = useNuxtApp();

      const update = this.updates.find((u) => u.id === updateId);
      console.log(update);
      if (!update || update.isRead) return;

      try {
        await $api(`/user/updates/${updateId}/read`, {
          method: 'POST'
        });

        update.isRead = true;
        window.dispatchEvent(new Event('session-updated'));
      } catch (error) {
        console.error('Failed to mark update as read:', error);
      }
    }
  }
});
