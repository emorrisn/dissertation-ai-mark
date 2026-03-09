<template>
  <UDashboardPanel id="record">
    <template #header>
      <UDashboardNavbar title="Student 1">
        <template #right>
          <UButton color="primary" variant="outline" size="lg"> Finish Marking </UButton>
        </template>
      </UDashboardNavbar>
    </template>
    <template #body>
      <div class="max-w-5xl mx-auto space-y-4 h-full">
        <UCard
          class="h-3/4 w-full flex items-center justify-center overflow-hidden relative"
          :ui="{ body: 'p-0 sm:p-0 w-full h-full' }"
        >
          <video ref="video" autoplay playsinline class="w-full h-full object-cover object-center rounded-lg" />

          <div class="absolute inset-0 flex items-center justify-center pointer-events-none">
            <div class="w-[85%] h-[85%] border-4 border-white/70 rounded-xl shadow-inner border-dotted"></div>
          </div>
        </UCard>

        <UCarousel v-slot="{ item, index }" dots :items="items" :ui="{ item: 'basis-1/3' }">
          <img
            :src="item"
            class="rounded-lg hover:opacity-75 transition cursor-pointer object-cover w-full"
            loading="lazy"
            @click="removeImage(item, index)"
          />
        </UCarousel>
      </div>
    </template>
    <template #footer>
      <div class="flex justify-center p-4 gap-3 border-t border-default">
        <UButton color="primary" size="lg" class="w-2/3 sm:w-1/3 justify-center" @click="takePicture">
          Take Picture
        </UButton>
        <UButton color="neutral" size="lg"> Next Student (1/32) </UButton>
      </div>
    </template>
  </UDashboardPanel>
</template>

<script lang="ts" setup>
import { ref, onMounted } from 'vue';
import imageCompression from 'browser-image-compression';
import { LazyUIConfirmationPopup } from '#components';

const video = ref<HTMLVideoElement | null>(null);
const items = ref<string[]>([]);
let stream: MediaStream | null = null;
const overlay = useOverlay();
const confirmationModal = overlay.create(LazyUIConfirmationPopup);

onMounted(async () => {
  try {
    stream = await navigator.mediaDevices.getUserMedia({
      video: { facingMode: 'environment' }
    });

    if (video.value) {
      video.value.srcObject = stream;
    }
  } catch (err) {
    console.error('Camera error:', err);
  }
});

async function removeImage(url: string, index: number) {
  const instance = confirmationModal.open({
    description: `Delete image #${index + 1}`
  });
  const shouldDelete = await instance.result;

  if (shouldDelete) {
    items.value = items.value.filter((item) => item !== url);
    URL.revokeObjectURL(url);
  }
}

async function takePicture() {
  if (!video.value) return;

  const canvas = document.createElement('canvas');
  canvas.width = video.value.videoWidth;
  canvas.height = video.value.videoHeight;

  const ctx = canvas.getContext('2d');
  ctx?.drawImage(video.value, 0, 0);

  const blob = await new Promise<Blob>((resolve) => canvas.toBlob((b) => resolve(b!), 'image/jpeg', 0.9));

  const compressed = await imageCompression(blob, {
    maxSizeMB: 1,
    maxWidthOrHeight: 2000
  });

  const url = URL.createObjectURL(compressed);

  items.value.unshift(url);
}

definePageMeta({
  layout: 'dashboard',
  middleware: ['auth']
});
</script>

<style></style>
