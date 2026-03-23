import { describe, it, expect, vi, beforeEach } from 'vitest';
import apiPlugin from '~/plugins/api';

// --- Mock auth store ---
const mockAuthStore = {
  token: 'test-token',
  activeApiUrl: 'https://api.test.com',
  refreshAccessToken: vi.fn(),
  logout: vi.fn()
};

vi.mock('~/stores/auth', () => ({
  useAuthStore: () => mockAuthStore
}));

// --- Mock global $fetch ---
const mockFetch = vi.fn();

(global as any).$fetch = Object.assign(mockFetch, {
  create: vi.fn((config) => config)
});

describe('API Plugin', () => {
  beforeEach(() => {
    vi.clearAllMocks();

    // reset default token before each test
    mockAuthStore.token = 'test-token';
  });

  it('adds baseURL and Authorization header on request', () => {
    const plugin = apiPlugin();
    const { onRequest } = plugin.provide.api;

    const options: any = {
      headers: {}
    };

    onRequest({ options });

    expect(options.baseURL).toBe('https://api.test.com');

    const headers = options.headers as Headers;
    expect(headers.get('Authorization')).toBe('Bearer test-token');
  });

  it('warns if no token is present', () => {
    const warnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});
    mockAuthStore.token = null as any;

    const plugin = apiPlugin();
    const { onRequest } = plugin.provide.api;

    onRequest({ options: {} as any });

    expect(warnSpy).toHaveBeenCalledWith('No token found in store during request intercept!');
  });

  it('refreshes token and retries on 401', async () => {
    const plugin = apiPlugin();
    const { onResponseError } = plugin.provide.api;

    // 🔑 IMPORTANT: update token during refresh
    mockAuthStore.refreshAccessToken.mockImplementation(async () => {
      mockAuthStore.token = 'test-token';
    });

    const request = '/test';
    const options: any = { headers: {}, _retry: false };

    mockFetch.mockResolvedValue({ success: true });

    const result = await onResponseError({
      request,
      response: { status: 401 },
      options
    });

    expect(mockAuthStore.refreshAccessToken).toHaveBeenCalled();
    expect(mockFetch).toHaveBeenCalledWith(request, options);

    const headers = options.headers as Headers;
    expect(headers.get('Authorization')).toBe('Bearer test-token');

    expect(result).toEqual({ success: true });
  });

  it('logs out if refresh fails', async () => {
    const plugin = apiPlugin();
    const { onResponseError } = plugin.provide.api;

    mockAuthStore.refreshAccessToken.mockRejectedValue(new Error('fail'));

    const request = '/test';
    const options: any = { headers: {}, _retry: false };

    await expect(
      onResponseError({
        request,
        response: { status: 401 },
        options
      })
    ).rejects.toThrow();

    expect(mockAuthStore.logout).toHaveBeenCalled();
  });

  it('does not retry if already retried', async () => {
    const plugin = apiPlugin();
    const { onResponseError } = plugin.provide.api;

    const result = await onResponseError({
      request: '/test',
      response: { status: 401 },
      options: { _retry: true }
    });

    expect(result).toBeUndefined();
    expect(mockAuthStore.refreshAccessToken).not.toHaveBeenCalled();
  });

  it('does not retry refresh endpoint', async () => {
    const plugin = apiPlugin();
    const { onResponseError } = plugin.provide.api;

    const result = await onResponseError({
      request: '/auth/refresh',
      response: { status: 401 },
      options: {}
    });

    expect(result).toBeUndefined();
    expect(mockAuthStore.refreshAccessToken).not.toHaveBeenCalled();
  });
});
