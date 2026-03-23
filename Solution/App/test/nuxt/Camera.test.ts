import { describe, it, expect, vi, beforeEach } from 'vitest';
import { mountSuspended } from '@nuxt/test-utils/runtime';
import Camera from '~/components/Session/Camera.vue';
import { nextTick } from 'vue';

// --- Fix: allow srcObject assignment in happy-dom ---
Object.defineProperty(window.HTMLMediaElement.prototype, 'srcObject', {
  writable: true,
  value: null
});

// --- Stable MediaStream mock ---
const stopMock = vi.fn();

const mockStream = {
  getTracks: vi.fn(() => [{ stop: stopMock }])
};

// --- Mock getUserMedia ---
const mockGetUserMedia = vi.fn();

vi.stubGlobal('navigator', {
  mediaDevices: {
    getUserMedia: mockGetUserMedia
  }
});

// --- Canvas mocks ---
const mockDrawImage = vi.fn();
const mockToDataURL = vi.fn(() => 'data:image/png;base64,mock-image-data');

window.HTMLCanvasElement.prototype.getContext = vi.fn(() => ({
  drawImage: mockDrawImage
}));

window.HTMLCanvasElement.prototype.toDataURL = mockToDataURL;

// ✅ Mock toBlob (used in your component)
HTMLCanvasElement.prototype.toBlob = function (callback) {
  callback(new Blob(['mock'], { type: 'image/jpeg' }));
};

// ✅ Mock URL.createObjectURL
global.URL.createObjectURL = vi.fn(() => 'blob:mock-url');

// ✅ Mock image compression
vi.mock('browser-image-compression', () => ({
  default: vi.fn(async (file) => file)
}));

// --- Stub UI components ---
const UButtonStub = {
  name: 'UButton',
  template: '<button @click="$emit(\'click\')"><slot /></button>'
};

const UCardStub = {
  name: 'UCard',
  template: '<div><slot /></div>'
};

describe('Camera.vue', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockGetUserMedia.mockResolvedValue(mockStream);
  });

  it('requests camera access on mount and plays the stream', async () => {
    const wrapper = await mountSuspended(Camera, {
      global: {
        stubs: {
          UButton: UButtonStub,
          UCard: UCardStub
        }
      }
    });

    await vi.waitUntil(() => mockGetUserMedia.mock.calls.length > 0);

    expect(mockGetUserMedia).toHaveBeenCalledWith({
      video: { facingMode: { exact: 'environment' } }
    });

    await nextTick();

    const videoElement = wrapper.find('video').element as HTMLVideoElement;
    expect(videoElement.srcObject).toBe(mockStream);
  });

  it('takes a picture and returns image data', async () => {
    const wrapper = await mountSuspended(Camera, {
      global: {
        stubs: {
          UButton: UButtonStub,
          UCard: UCardStub
        }
      }
    });

    await vi.waitUntil(() => mockGetUserMedia.mock.calls.length > 0);
    await nextTick();

    const videoElement = wrapper.find('video').element;

    // Mock dimensions (JSDOM doesn't provide them)
    Object.defineProperty(videoElement, 'videoWidth', { value: 640 });
    Object.defineProperty(videoElement, 'videoHeight', { value: 480 });

    const result = await wrapper.vm.takePhoto();

    expect(mockDrawImage).toHaveBeenCalledWith(videoElement, 0, 0);
    expect(result).toBeTruthy();
    expect(result?.url).toBe('blob:mock-url');
  });

  it('stops the camera stream when the component is unmounted', async () => {
    const wrapper = await mountSuspended(Camera, {
      global: {
        stubs: {
          UCard: UCardStub
        }
      }
    });

    await vi.waitUntil(() => mockGetUserMedia.mock.calls.length > 0);
    await nextTick();

    wrapper.unmount();

    expect(stopMock).toHaveBeenCalled();
  });
});
