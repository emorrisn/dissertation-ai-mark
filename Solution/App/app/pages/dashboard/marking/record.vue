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
        <SessionCamera ref="camera" />

        <UCarousel v-slot="{ item, index }" dots :items="items" :ui="{ item: 'basis-1/3' }">
          <div class="relative">
            <img
              :src="item.url"
              class="rounded-lg hover:opacity-75 transition cursor-pointer object-cover w-full"
              loading="lazy"
              @click="removeImage(item, index)"
            />

            <div class="absolute top-2 left-2 bg-black/70 text-white text-xs px-2 py-1 rounded-md">
              Page {{ items.length - index }}
            </div>
          </div>
        </UCarousel>
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
import type { SessionFile, StudentSubmission } from '~/types';

const router = useRouter();
const overlay = useOverlay();
const toast = useToast();
const markingStore = useMarkingStore();

const confirmationModal = overlay.create(LazyUIConfirmationPopup);

const items = ref<{ url: string; blob: Blob }[]>([]);

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

const camera = ref<InstanceType<typeof SessionCamera> | null>(null);

async function takePicture() {
  const photo = await camera.value?.takePhoto();
  if (!photo) return;
  items.value.unshift(photo);
}

async function removeImage(item: { url: string }, index: number) {
  const instance = confirmationModal.open({
    title: `Delete page #${items.value.length - index}?`,
    image: item.url
  });
  const shouldDelete = await instance.result;

  if (shouldDelete) {
    items.value = items.value.filter((i) => i !== item);
    URL.revokeObjectURL(item.url);
  }
}

function createDummySessionFile(blob: Blob, pageNo: number): SessionFile {
  const selectedStudent = markingStore.currentSession?.selectedStudent ?? 1;
  return {
    id: crypto.randomUUID(),
    url: URL.createObjectURL(blob),
    name: `student-${selectedStudent}-page-${pageNo}.jpg`,
    storageUrl: `/mock-storage/${markingStore.currentSession?.id}/student-${selectedStudent}-page-${pageNo}.jpg`,
    size: blob.size,
    uploadedAt: new Date().toISOString()
  };
}

async function nextStudent() {
  if (!markingStore.currentSession) return;
  if (switchingStudent.value) return;
  switchingStudent.value = true;

  await new Promise((resolve) => setTimeout(resolve, 1000)); // simulate processing/uploading time

  const now = new Date().toISOString();

  const submission: StudentSubmission = {
    id: crypto.randomUUID(),
    sessionId: markingStore.currentSession.id || '',
    studentNo: markingStore.currentSession?.selectedStudent ?? 1,
    pages: items.value.map((item, index) => ({
      pageNo: index + 1,
      file: createDummySessionFile(item.blob, index + 1)
    })),
    createdAt: now,
    updatedAt: now
  };

  markingStore.addStudentSubmission(submission);

  // cleanup URLs
  items.value.forEach((item) => URL.revokeObjectURL(item.url));
  items.value = [];

  if (isLastStudent.value) {
    markingStore.currentSession.studentsAmount++;
  }

  markingStore.incrementSelectedStudent();
  switchingStudent.value = false;
}

async function finishMarking() {
  if (items.value.length > 0) {
    const instance = confirmationModal.open({
      title: 'Are you sure?',
      description: 'You have not submitted all students work, are you sure you want to finish marking?'
    });
    const shouldContinue = await instance.result;

    if (!shouldContinue) {
      return;
    }
  }

  router.push('/dashboard/marking');
}

definePageMeta({
  layout: 'dashboard',
  middleware: ['auth']
});
</script>

<style></style>
