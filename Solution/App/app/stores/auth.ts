import { defineStore } from 'pinia';
import type { Credentials, Institute, PasswordUpdate, UserProfile } from '~/types';
import institutesData from '~/data/institutes.json';

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: null as UserProfile | null,
    token: null as string | null,
    refreshToken: null as string | null,
    status: 'idle',
    institutes: institutesData as Institute[],
    activeApiUrl: null as string | null
  }),

  getters: {
    isAuthenticated: (state): boolean => !!state.token && !!state.user,
    currentUser: (state) => state.user
  },

  actions: {
    async login(credentials: Credentials) {
      this.status = 'loading';

      try {
        const selectedInstitute = this.institutes.find((inst) => inst.code === credentials.institute_code);

        if (!selectedInstitute) {
          throw new Error('Invalid institution code.');
        }

        this.activeApiUrl = selectedInstitute.api_url;

        const res = await $fetch<{ access_token: string; refresh_token: string; user: UserProfile }>('/auth/login', {
          baseURL: this.activeApiUrl,
          method: 'POST',
          body: credentials
        });

        this.refreshToken = res.refresh_token;
        this.token = res.access_token;
        this.user = res.user;
        this.status = 'succeeded';

        window.dispatchEvent(new Event('session-updated'));
      } catch (error) {
        this.status = 'failed';
        throw error;
      }
    },

    async refreshAccessToken() {
      if (!this.refreshToken || !this.activeApiUrl) throw new Error('No refresh token available');

      try {
        const res = await $fetch<{ access_token: string }>('/auth/refresh', {
          baseURL: this.activeApiUrl,
          method: 'POST',
          headers: {
            Authorization: `Bearer ${this.refreshToken}` // Send the refresh token
          }
        });

        this.token = res.access_token; // Save the new access token
        return res.access_token;
      } catch (error) {
        // If the refresh token itself is expired or invalid, log them out entirely
        this.logout();
        throw error;
      }
    },

    async fetchProfile() {
      if (!this.token || !this.activeApiUrl) return;
      const { $api } = useNuxtApp();

      const profile = await $api<UserProfile>('/auth/session');

      this.user = profile;
    },

    async updateProfile(profileData: Partial<UserProfile>) {
      if (!this.token || !this.activeApiUrl) {
        throw new Error('Not authenticated');
      }

      const { $api } = useNuxtApp();

      try {
        const updatedUser = await $api<UserProfile>('/user/profile', {
          method: 'PUT',
          body: profileData
        });

        if (this.user) {
          this.user = { ...this.user, ...updatedUser };
        }

        window.dispatchEvent(new Event('session-updated'));

        return updatedUser;
      } catch (error) {
        console.error('Failed to update profile:', error);
        throw error; // Re-throw so the UI can catch and display an error toast
      }
    },

    async changePassword(passwords: PasswordUpdate) {
      if (!this.token || !this.activeApiUrl) throw new Error('Not authenticated');

      const { $api } = useNuxtApp();

      try {
        await $api('/user/password', {
          method: 'PUT',
          body: passwords // Expects { currentPassword, newPassword }
        });

        window.dispatchEvent(new Event('session-updated'));
      } catch (error) {
        console.error('Failed to change password:', error);
        throw error;
      }
    },

    async deleteAccount() {
      if (!this.token || !this.activeApiUrl) throw new Error('Not authenticated');

      const { $api } = useNuxtApp();

      try {
        await $api('/user/profile', {
          method: 'DELETE'
        });

        // If successful, wipe the local state and boot them to login
        this.user = null;
        this.token = null;
        this.refreshToken = null;
        this.activeApiUrl = null;

        navigateTo('/login');
      } catch (error) {
        console.error('Failed to delete account:', error);
        throw error;
      }
    },

    async logout() {
      if (!this.token || !this.activeApiUrl) return;

      const { $api } = useNuxtApp();

      try {
        await $api('/auth/logout', {
          method: 'POST'
        });
      } catch (error) {
        alert('Logout failed. Please try again.' + (error instanceof Error ? error.message : ''));
      }

      // Clear everything
      this.user = null;
      this.token = null;
      this.activeApiUrl = null;

      navigateTo('/login');
    }
  },

  persist: {
    storage: piniaPluginPersistedstate.cookies()
  }
});
