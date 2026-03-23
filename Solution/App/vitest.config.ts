import { defineVitestConfig } from '@nuxt/test-utils/config';

export default defineVitestConfig({
  test: {
    exclude: ['test/e2e/**'],
  },
});
