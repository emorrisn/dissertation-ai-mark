<template>
  <UDashboardPanel id="record">
    <template #header>
      <UDashboardNavbar :title="`Student ${markingStore.currentSession?.selectedStudent ?? 1}`">
        <template #right>
          <UButton color="primary" variant="outline" size="lg" @click="finishMarking"> Finish Marking </UButton>
        </template>
      </UDashboardNavbar>
    </template>
    <template #body>
      <div class="max-w-5xl mx-auto h-full flex flex-col gap-4">
        <SessionCamera ref="camera" class="grow flex-1" />

        <div class="shrink-0 w-full mb-2">
          <UCarousel v-slot="{ item, index }" dots :items="items" :ui="{ item: 'basis-1/3 px-2' }">
            <div class="relative w-full aspect-[4/3] rounded-lg overflow-hidden">
              <template v-if="!item.isPlaceholder">
                <img
                  :src="item.url"
                  class="object-cover w-full h-full hover:opacity-75 transition cursor-pointer"
                  loading="lazy"
                  @click="removeImage(item, index)"
                />
                <div class="absolute top-2 left-2 bg-black/70 text-white text-xs px-2 py-1 rounded-md">
                  Page {{ realItems.length - index }}
                </div>
              </template>

              <div
                v-else
                class="w-full h-full flex flex-col items-center justify-center text-gray-400 border-2 border-dashed border-gray-500/50 bg-gray-500/10"
              >
                <UIcon name="i-lucide-camera" class="w-6 h-6 opacity-50" />
              </div>
            </div>
          </UCarousel>
        </div>
      </div>
    </template>
    <template #footer>
      <div class="flex justify-center p-4 gap-3 border-t border-default">
        <UButton
          color="primary"
          size="lg"
          class="w-2/3 sm:w-1/3 justify-center"
          :disabled="takingPhoto"
          @click="takePicture"
        >
          Take Picture
        </UButton>
        <UButton
          color="neutral"
          size="lg"
          :disabled="items.length === 0"
          :loading="switchingStudent"
          @click="nextStudent"
        >
          {{ isLastStudent ? 'Add Student' : 'Next Student' }} ({{
            markingStore.currentSession?.selectedStudent ?? 1
          }}/{{ markingStore.currentSession?.studentsAmount ? markingStore.currentSession.studentsAmount - 1 : 1 }})
        </UButton>
      </div>
    </template>
  </UDashboardPanel>
</template>

<script lang="ts" setup>
import { ref, onMounted, computed } from 'vue';
import { LazyUIConfirmationPopup, SessionCamera } from '#components';
import { onBeforeRouteLeave } from 'vue-router';

const router = useRouter();
const overlay = useOverlay();
const toast = useToast();
const markingStore = useMarkingStore();

const confirmationModal = overlay.create(LazyUIConfirmationPopup);

type CameraItem = {
  url?: string;
  blob?: Blob;
  isPlaceholder?: boolean;
  id: string;
};

const items = ref<CameraItem[]>([
  { isPlaceholder: true, id: 'ph-1' },
  { isPlaceholder: true, id: 'ph-2' },
  { isPlaceholder: true, id: 'ph-3' }
]);

const realItems = computed(() => items.value.filter((i) => !i.isPlaceholder));

const switchingStudent = ref(false);
const takingPhoto = ref(false);

const isLastStudent = computed(() => {
  if (!markingStore.currentSession) return false;
  return (markingStore.currentSession.selectedStudent ?? 1) >= markingStore.currentSession.studentsAmount;
});

onMounted(async () => {
  if (!markingStore.currentSession) {
    await router.push('/dashboard/marking');
    toast.add({
      title: 'No session found',
      description: 'Please select a marking session first.'
    });
    return;
  }
});

onBeforeRouteLeave(async () => {
  // If there are no unsaved images, allow the route change
  if (items.value.length === 0) return true;
  if (markingStore.currentSession?.status == 'pending') {
    markingStore.currentSession = null;
    return true;
  }

  // Otherwise, prompt the user
  const instance = confirmationModal.open({
    title: 'Unsaved Progress',
    description: 'You have unsaved photos for the current student. Are you sure you want to leave and discard them?'
  });

  const shouldLeave = await instance.result;

  // If they click confirm, allow navigation. If cancel, block navigation.
  return shouldLeave;
});

const camera = ref<InstanceType<typeof SessionCamera> | null>(null);

async function takePicture() {
  const photo = await camera.value?.takePhoto();
  if (!photo) return;

  // Create the new real item
  const newItem: CameraItem = {
    url: photo.url,
    blob: photo.blob,
    id: crypto.randomUUID()
  };

  // If there are placeholders, remove the last one so the array stays at a minimum of 3
  const placeholderIndex = items.value.findLastIndex((i) => i.isPlaceholder);
  if (placeholderIndex !== -1) {
    items.value.splice(placeholderIndex, 1);
  }

  // Add the new photo to the front
  items.value.unshift(newItem);
}

async function removeImage(item: CameraItem, index: number) {
  const instance = confirmationModal.open({
    title: `Delete this page?`,
    image: item.url
  });
  const shouldDelete = await instance.result;

  if (shouldDelete) {
    // Remove the item
    items.value = items.value.filter((i) => i.id !== item.id);
    if (item.url) URL.revokeObjectURL(item.url);

    // If we have fewer than 3 items, push a placeholder back in to maintain the layout
    if (items.value.length < 3) {
      items.value.push({ isPlaceholder: true, id: crypto.randomUUID() });
    }
  }
}

async function nextStudent() {
  if (!markingStore.currentSession) return;
  if (switchingStudent.value) return;

  switchingStudent.value = true;

  const sessionId = markingStore.currentSession.id;

  if (!sessionId) {
    return;
  }

  const currentStudentNo = markingStore.currentSession.selectedStudent ?? 1;

  // Because takePicture uses unshift, the newest photo is at index 0.
  // We reverse the array so the backend gets Page 1 first, Page 2 second, etc.
  const orderedBlobs = [...items.value].reverse().map((item) => item.blob);

  try {
    // Send the data to the backend via the store action
    await markingStore.addStudentSubmission(sessionId, currentStudentNo, orderedBlobs);

    // If successful, cleanup URLs and clear the array
    items.value.forEach((item) => URL.revokeObjectURL(item.url));
    items.value = [];
  } catch (error) {
    toast.add({
      title: 'Upload Failed',
      description: 'Could not save student submission. Please try again.',
      color: 'error'
    });
  } finally {
    switchingStudent.value = false;
  }
}

async function finishMarking() {
  if (items.value.length > 0) {
    const instance = confirmationModal.open({
      title: 'Are you sure?',
      description:
        'You have unsaved pages for the current student. Are you sure you want to finish marking and discard them?'
    });
    const shouldContinue = await instance.result;

    if (!shouldContinue) {
      return;
    }
  } else if (
    markingStore.currentSession &&
    markingStore.currentSession.selectedStudent < markingStore.currentSession.studentsAmount
  ) {
    const instance = confirmationModal.open({
      title: 'Are you sure?',
      description: 'You not marked all of your students for this session.'
    });
    const shouldContinue = await instance.result;

    if (!shouldContinue) {
      return;
    }
  }

  const instance = confirmationModal.open({
    title: 'Are you finished?',
    description:
      'Setting this marking session as finished means you can no longer make changes or add students so only do this if you are sure.'
  });
  const shouldContinue = await instance.result;

  if (!shouldContinue) {
    return;
  }

  // Ensure we have a session to finish
  if (!markingStore.currentSession?.id) return;

  try {
    // Call the backend to lock the session and change status to 'pending'
    await markingStore.finishSession(markingStore.currentSession.id);

    toast.add({
      title: 'Session Submitted',
      description: 'Your marking session has been queued for processing.',
      color: 'success'
    });

    // Navigate away
    router.push('/dashboard/marking');
  } catch (error) {
    toast.add({
      title: 'Error',
      description: 'Failed to complete the marking session. Please try again.',
      color: 'error'
    });
  }
}

definePageMeta({
  layout: 'dashboard',
  middleware: ['auth']
});
</script>

<style></style>
