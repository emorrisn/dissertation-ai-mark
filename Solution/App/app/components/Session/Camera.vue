<template>
  <UCard
    class="w-full overflow-hidden relative"
    :ui="{ body: 'p-0 sm:p-0 w-full h-full', root: `flex-grow max-w-[75dvh] mx-auto min-h-[${minHeight}]` }"
  >
    <div class="relative w-full h-full">
      <!-- Video element -->
      <video ref="videoRef" autoplay playsinline class="inset-0 w-full h-full object-cover" />

      <!-- Overlay frame -->
      <div class="absolute inset-0 flex items-center justify-center pointer-events-none">
        <div class="w-[85%] h-[85%] border-4 border-white/70 rounded-xl shadow-inner border-dotted"></div>
      </div>

      <!-- Flash -->
      <div
        v-if="flash"
        class="absolute inset-0 bg-white/20 transition ease-in z-20 animate-camera-flash pointer-events-none rounded-lg"
      />

      <!-- Loading -->
      <div
        v-if="cameraLoading"
        class="absolute inset-0 flex items-center justify-center bg-black/40 text-white text-lg font-medium rounded-lg"
      >
        <span v-if="!error">Loading camera...</span>
        <span v-else>{{ error }}</span>
      </div>

      <!-- Controls -->
      <div class="absolute bottom-4 right-4 flex gap-2">
        <UButton color="neutral" :disabled="cameraLoading" @click="switchCamera"> Switch </UButton>
      </div>
    </div>
  </UCard>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue';
import { LazyUIConfirmationPopup } from '#components';
import imageCompression from 'browser-image-compression';

withDefaults(
  defineProps<{
    minHeight?: string;
  }>(),
  {
    minHeight: '75dvh'
  }
);

const router = useRouter();
const overlay = useOverlay();

const videoRef = ref<HTMLVideoElement | null>(null);
const facingMode = ref<'environment' | 'user'>('environment');
const error = ref<string | null>(null);
const cameraLoading = ref(true);
const flash = ref(false);

let mounted = true;
let stream: MediaStream | null = null;

const confirmationModal = overlay.create(LazyUIConfirmationPopup);

// Init camera
async function initCamera() {
  cameraLoading.value = true;
  error.value = null;
  stopCamera();

  await new Promise((r) => setTimeout(r, 300));

  const constraintsList = [
    { video: { facingMode: { exact: facingMode.value } } },
    { video: { facingMode: facingMode.value } },
    { video: true }
  ];

  let lastError: any = null;

  for (const constraints of constraintsList) {
    try {
      stream = await navigator.mediaDevices.getUserMedia(constraints);

      if (!mounted) {
        stopCamera();
        return;
      }
      if (videoRef.value) {
        videoRef.value.srcObject = stream;
        await videoRef.value.play().catch(() => {});
      }
      cameraLoading.value = false;
      return;
    } catch (err: any) {
      console.error('Camera error:', err);
      lastError = err;
      await new Promise((r) => setTimeout(r, 200));
    }
  }

  cameraLoading.value = false;

  if (lastError?.name === 'NotAllowedError') {
    await showCameraPermissionModal();
  } else if (lastError?.name === 'NotReadableError') {
    await showCameraBusyModal();
  } else {
    error.value = 'No camera available';
  }
}

// Stop camera
function stopCamera() {
  if (stream) {
    stream.getTracks().forEach((track) => track.stop());
    stream = null;
  }

  if (videoRef.value) {
    videoRef.value.srcObject = null;
  }
}

// Switch camera
async function switchCamera() {
  facingMode.value = facingMode.value === 'environment' ? 'user' : 'environment';
  await initCamera();
}

// Flash effect
function triggerFlash() {
  flash.value = true;
  setTimeout(() => (flash.value = false), 120);
}

async function takePhoto(): Promise<{ url: string; blob: Blob } | null> {
  if (!videoRef.value) return null;

  const canvas = document.createElement('canvas');
  canvas.width = videoRef.value.videoWidth;
  canvas.height = videoRef.value.videoHeight;

  const ctx = canvas.getContext('2d');
  ctx?.drawImage(videoRef.value, 0, 0);

  const blob = await new Promise<Blob>((resolve) => canvas.toBlob((b) => resolve(b!), 'image/jpeg', 0.9));
  const file = new File([blob], 'captured-photo.jpg', { type: 'image/jpeg' });

  triggerFlash();

  const compressed = await imageCompression(file, { maxSizeMB: 1, maxWidthOrHeight: 2000 });

  const url = URL.createObjectURL(blob);

  return {
    url,
    blob: compressed
  };
}

async function showCameraBusyModal() {
  const instance = confirmationModal.open({
    title: 'Camera Already In Use',
    description:
      'Your camera is currently being used by another application.\n\n' +
      'Please close other apps using the camera (Zoom, Teams, browser tabs) and press Retry.',
    confirmButton: 'Retry',
    cancelButton: 'Cancel Session'
  });
  const retry = await instance.result;
  if (retry) {
    await new Promise((r) => setTimeout(r, 1000));
    await initCamera();
  } else {
    stopCamera();
    router.push('/dashboard/marking');
  }
}

async function showCameraPermissionModal() {
  const instance = confirmationModal.open({
    title: 'Camera Permission Required',
    description:
      'This app requires access to your camera to capture exam pages.\n\n' +
      'Please allow camera access in your browser settings.\n\n' +
      'Steps:\n' +
      '1. Click the camera icon in your browser address bar.\n' +
      '2. Allow camera access.\n' +
      '3. Press Retry.\n\n' +
      'If the issue continues, try refreshing the page.',
    confirmButton: 'Retry',
    cancelButton: 'Cancel Session'
  });
  const retry = await instance.result;
  if (retry) {
    await initCamera();
  } else {
    stopCamera();
    router.push('/dashboard/marking');
  }
}

onMounted(() => initCamera());
onUnmounted(() => {
  mounted = false;
  stopCamera();
});

// Expose refs and methods for parent
defineExpose({
  videoRef,
  initCamera,
  stopCamera,
  triggerFlash,
  takePhoto,
  facingMode
});
</script>

<style>
@keyframes camera-flash {
  0% {
    opacity: 0.5;
  }
  50% {
    opacity: 1;
  }
  100% {
    opacity: 0;
  }
}
.animate-camera-flash {
  animation: camera-flash 0.2s ease-out;
}
</style>
