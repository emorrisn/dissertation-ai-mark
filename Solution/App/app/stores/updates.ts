import { defineStore } from 'pinia';
import type { AppUpdate } from '~/types';

export const useUpdatesStore = defineStore('updates', {
  state: () => ({
    updates: [] as AppUpdate[],
    status: 'idle' as 'idle' | 'loading' | 'succeeded' | 'failed'
  }),

  getters: {
    unreadUpdates: (state): AppUpdate[] => state.updates.filter((u) => !u.isRead),
    unreadCount: (state): number => state.updates.filter((u) => !u.isRead).length,
    sortedUpdates: (state): AppUpdate[] => {
      // Return a new sorted array to avoid mutating state
      return [...state.updates].sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());
    }
  },

  actions: {
    /**
     * Fetches updates from the server.
     */
    async fetchUpdates() {
      this.status = 'loading';
      try {
        // const fetchedUpdates = await $fetch('/api/updates');
        // this.updates = fetchedUpdates;

        await new Promise((resolve) => setTimeout(resolve, 1000)); // Simulate network delay
        // Mock data for now
        const mockUpdates: AppUpdate[] = [
          {
            id: '1',
            type: 'MarkingSessionUpdate',
            title: 'Marking Complete',
            message: 'Your marking session "History Essay Batch 1" has been completed.',
            relatedId: 'session-123',
            link: '/dashboard/marking/session-123',
            timestamp: new Date(Date.now() - 1000 * 60 * 5).toISOString(), // 5 minutes ago
            isRead: false
          },
          {
            id: '2',
            type: 'NewFeature',
            title: 'New Feature: Bulk Export',
            message: 'You can now export marking results as a CSV file.',
            link: '/dashboard/features',
            timestamp: new Date(Date.now() - 1000 * 60 * 60 * 2).toISOString(), // 2 hours ago
            isRead: false
          },
          {
            id: '3',
            type: 'SystemMessage',
            title: 'Scheduled Maintenance',
            message: 'The system will be down for maintenance on Sunday at 2 AM.',
            timestamp: new Date(Date.now() - 1000 * 60 * 60 * 24).toISOString(), // 1 day ago
            isRead: true
          }
        ];
        this.updates = mockUpdates;
        this.status = 'succeeded';
      } catch (error) {
        this.status = 'failed';
        console.error('Failed to fetch updates:', error);
      }
    },

    markAsRead(updateId: string) {
      const update = this.updates.find((u) => u.id === updateId);
      if (update) {
        update.isRead = true;
        // You would also make an API call here to update the backend
        // await $fetch(`/api/updates/${updateId}`, { method: 'PATCH', body: { isRead: true } });
      }
    }
  }
});
