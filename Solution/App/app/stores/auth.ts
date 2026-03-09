import { defineStore } from 'pinia';
import type { Credentials, Institute, PasswordUpdate, UserProfile } from '~/types';

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: null as UserProfile | null,
    token: null as string | null,
    status: 'idle',
    institutes: [] as Institute[]
  }),

  getters: {
    isAuthenticated: (state): boolean => !!state.token && !!state.user,
    currentUser: (state) => state.user
  },

  actions: {
    async login(credentials: Credentials) {
      this.status = 'loading';
      try {
        // Example: const { user, token } = await $fetch('/api/login', { method: 'POST', body: credentials });
        // this.token = token;
        const newToken = 'mock-jwt-token-string-for-dev';
        this.token = newToken;

        this.status = 'succeeded';
        await this.fetchProfile(); // Fetch user profile after login
      } catch (error) {
        this.status = 'failed';
        console.error('Login failed:', error);
      }
    },

    async fetchProfile() {
      if (!this.token) return;
      // API call to get user profile from your Flask server
      // const profile = await $fetch('/api/me');
      // this.user = profile;

      // For now, we can use mock data based on your new UserProfile type
      this.user = {
        userId: 'c8a9f3b2-9e4d-4f7c-8a2b-1e9f8c7d6a5b',
        username: 'benjamincanac',
        name: 'Benjamin Canac',
        instituteCode: 'NUXT_UNI',
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString()
      };
    },

    async updateProfile(profileData: Partial<UserProfile>) {
      // API call to update profile
    },

    async changePassword(passwords: PasswordUpdate) {
      // API call to change password
    },

    async fetchInstitutes() {
      // API call to get a list of institutes
      // const institutes = await $fetch('/api/institutes');
      // this.institutes = institutes;

      // For now, provide dummy data
      this.institutes = [
        { name: 'University of Cambridge', code: 'cambridge' },
        { name: 'University of Oxford', code: 'oxford' },
        { name: 'Imperial College London', code: 'imperial' }
      ];
    },

    logout() {
      this.user = null;
      this.token = null;
      // Use Nuxt's navigateTo to redirect
      // navigateTo('/login');
    }
  },

  persist: {
    storage: piniaPluginPersistedstate.cookies()
  }
});
