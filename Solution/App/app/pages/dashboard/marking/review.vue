<template>
  <UDashboardPanel
    id="setup"
    :ui="{
      body: 'sm:p-0 p-0'
    }"
  >
    <template #header>
      <UDashboardNavbar
        :title="`Review Session: Student ${markingStore.currentSession?.selectedStudent ?? 1}/${
          markingStore.currentSession?.studentsAmount ? markingStore.currentSession.studentsAmount : 1
        }`"
      >
        <template #right>
          <UButton color="neutral" variant="outline" size="lg" @click="handleBack()"> Exit </UButton>
        </template>
      </UDashboardNavbar>
    </template>
    <template #body>
      <div class="max-w-5xl mx-auto h-full flex flex-col gap-4 py-4">
        <div v-if="loadingImages" class="flex-1 flex items-center justify-center text-gray-500">
          <UIcon name="i-heroicons-arrow-path" class="animate-spin size-8" />
        </div>
        <div v-else-if="items.length > 0" class="flex-1 w-full">
          <UCarousel
            ref="carousel"
            v-slot="{ item }"
            arrows
            :items="items"
            :prev="{ onClick: onClickPrev }"
            :next="{ onClick: onClickNext }"
            class="w-full max-w-md mx-auto"
            @select="onSelect"
          >
            <img
              :src="item"
              width="640"
              height="640"
              class="rounded-lg object-contain bg-gray-100 dark:bg-gray-800"
              loading="lazy"
            />
          </UCarousel>

          <div class="flex gap-1 justify-center pt-4 max-w-md mx-auto flex-wrap">
            <div
              v-for="(item, index) in items"
              :key="index"
              class="size-24 opacity-25 hover:opacity-100 transition-opacity cursor-pointer flex-shrink-0"
              :class="{ 'opacity-100 ring-2 ring-primary rounded-lg': activeIndex === index }"
              @click="select(index)"
            >
              <img :src="item" width="88" height="88" class="rounded-lg object-cover h-full w-full" loading="lazy" />
            </div>
          </div>
        </div>
        <div v-else class="flex-1 flex items-center justify-center text-gray-500">
          No images available for this student.
        </div>
      </div>
    </template>
    <template #footer>
      <div class="flex justify-center p-4 gap-3 border-t border-default">
        <UButton
          color="neutral"
          size="lg"
          :disabled="!(markingStore.currentSession && markingStore.currentSession.selectedStudent != 1)"
          @click="prevStudent"
        >
          {{ 'Previous Student' }}
        </UButton>
        <UButton color="primary" size="lg" class="w-2/3 sm:w-1/3 justify-center" @click="feedbackModal.open()">
          View Feedback (3)
        </UButton>
        <UButton
          color="neutral"
          size="lg"
          :disabled="!(markingStore.currentSession.selectedStudent < markingStore.currentSession.studentsAmount)"
          @click="nextStudent"
        >
          {{ 'Next Student' }}
        </UButton>
      </div>
    </template>
  </UDashboardPanel>
</template>

<script lang="ts" setup>
import { ref, watch, onMounted, onBeforeUnmount, useTemplateRef } from 'vue';
import { SessionFeedbackModal } from '#components';

const currentStep = ref(0);
const markingStore = useMarkingStore();
const overlay = useOverlay();
const feedbackModal = overlay.create(SessionFeedbackModal);
const router = useRouter();
const toast = useToast();

// Use the custom Nuxt plugin we created for API calls
const { $api } = useNuxtApp();

const items = ref<string[]>([]);
const loadingImages = ref(false);
const carousel = useTemplateRef('carousel');
const activeIndex = ref(0);

// Helper to clean up blob URLs from memory to prevent memory leaks
const revokeImageUrls = () => {
  items.value.forEach((url) => URL.revokeObjectURL(url));
};

// Function to fetch images as blobs through the authenticated $api plugin
const loadImagesForStudent = async () => {
  const session = markingStore.currentSession;
  if (!session || !session.studentSubmissions) {
    revokeImageUrls();
    items.value = [];
    return;
  }

  const submission = session.studentSubmissions.find((sub: any) => sub.studentNo === session.selectedStudent);

  if (!submission || !submission.pages || submission.pages.length === 0) {
    revokeImageUrls();
    items.value = [];
    return;
  }

  loadingImages.value = true;
  revokeImageUrls(); // Clean up old images before loading new ones

  try {
    const fetchedUrls = await Promise.all(
      submission.pages.map(async (page: any) => {
        try {
          // Make sure we add a leading slash if it's missing in your JSON
          const path = page.file.url.startsWith('/') ? page.file.url : `/${page.file.url}`;

          // Request the file as a Blob using your authenticated $api fetcher
          const blob: Blob = await $api(path, { responseType: 'blob' });
          return URL.createObjectURL(blob);
        } catch (err) {
          console.error(`Failed to fetch image: ${page.file.url}`, err);
          return ''; // Return empty string on failure
        }
      })
    );

    // Filter out any failed requests
    items.value = fetchedUrls.filter((url) => url !== '');
    activeIndex.value = 0; // Reset carousel index
  } finally {
    loadingImages.value = false;
  }
};

// Watch for changes in the selected student and trigger image loading
watch(
  () => markingStore.currentSession?.selectedStudent,
  () => {
    loadImagesForStudent();
  },
  { immediate: true }
);

// Clean up blobs when leaving the page
onBeforeUnmount(() => {
  revokeImageUrls();
});

function onClickPrev() {
  if (activeIndex.value > 0) activeIndex.value--;
}
function onClickNext() {
  if (activeIndex.value < items.value.length - 1) activeIndex.value++;
}
function onSelect(index: number) {
  activeIndex.value = index;
}

function select(index: number) {
  activeIndex.value = index;
  carousel.value?.emblaApi?.scrollTo(index);
}

function prevStudent() {
  if (markingStore.currentSession && markingStore.currentSession.selectedStudent != 1) {
    markingStore.currentSession.selectedStudent--;
  }
}

function nextStudent() {
  if (
    markingStore.currentSession &&
    markingStore.currentSession.selectedStudent < markingStore.currentSession.studentsAmount
  ) {
    markingStore.currentSession.selectedStudent++;
  }
}

function handleBack() {
  if (currentStep.value === 0) {
    markingStore.currentSession = null;
    router.push('/dashboard/marking');
  } else {
    currentStep.value--;
  }
}

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

definePageMeta({
  layout: 'dashboard',
  middleware: ['auth']
});
</script>
