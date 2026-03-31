import { defineNuxtPlugin } from '#app';
import type { FetchOptions } from 'ofetch';

// This plugin creates a custom `$fetch` instance that can be used to make API calls.
// It automatically adds the base URL and the authentication token to every request.
// It also handles 401 errors by trying to refresh the access token.

interface CustomFetchOptions extends FetchOptions {
  _retry?: boolean;
}

export default defineNuxtPlugin(() => {
  const api = $fetch.create({
    onRequest({ options }) {
      const authStore = useAuthStore();

      if (authStore.activeApiUrl) {
        options.baseURL = authStore.activeApiUrl;
      }

      if (authStore.token) {
        // Safely set headers using the standard Headers API
        const headers = new Headers(options.headers);
        headers.set('Authorization', `Bearer ${authStore.token}`);

        // Reassign the fully constructed headers back to options
        options.headers = headers;
      } else {
        console.warn('No token found in store during request intercept!');
      }
    },

    async onResponseError({ request, response, options }) {
      const authStore = useAuthStore();
      const fetchOptions = options as CustomFetchOptions;
      const hasRetried = fetchOptions._retry;

      if (response.status === 401 && !request.toString().includes('/auth/refresh') && !hasRetried) {
        fetchOptions._retry = true;
        try {
          await authStore.refreshAccessToken();

          // Apply the same safe Header assignment here for the retry!
          const headers = new Headers(options.headers);
          headers.set('Authorization', `Bearer ${authStore.token}`);
          options.headers = headers;

          if (authStore.activeApiUrl) {
            options.baseURL = authStore.activeApiUrl;
          }

          return $fetch(request, options);
        } catch (error: unknown) {
          authStore.logout();
          throw error;
        }
      }
    }
  });

  return {
    provide: {
      api
    }
  };
});
