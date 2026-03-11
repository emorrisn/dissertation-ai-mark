// plugins/api.ts
import { defineNuxtPlugin } from '#app';

export default defineNuxtPlugin((nuxtApp) => {
  const api = $fetch.create({
    onRequest({ request, options }) {
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
      const fetchOptions = options as any;
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
        } catch (error: any) {
          authStore.logout();
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
