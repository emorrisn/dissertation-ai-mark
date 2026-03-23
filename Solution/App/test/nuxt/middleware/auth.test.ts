import { describe, it, expect, vi, beforeEach } from 'vitest';
import middleware from '~/middleware/auth';

// --- Mock store ---
const mockAuthStore = {
  isAuthenticated: false
};

vi.mock('~/stores/auth', () => ({
  useAuthStore: () => mockAuthStore
}));

// --- Mock navigateTo (CORRECT WAY) ---
const navigateTo = vi.fn();

vi.mock('#app', () => ({
  navigateTo
}));

describe('Auth Middleware', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('allows unauthenticated access to login', () => {
    mockAuthStore.isAuthenticated = false;

    middleware({ path: '/login', fullPath: '/login' } as any, {} as any);

    expect(navigateTo).not.toHaveBeenCalled();
  });

  it('allows unauthenticated access to root', () => {
    mockAuthStore.isAuthenticated = false;

    middleware({ path: '/', fullPath: '/' } as any, {} as any);

    expect(navigateTo).not.toHaveBeenCalled();
  });
});
