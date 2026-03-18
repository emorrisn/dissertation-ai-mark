<template>
  <UModal
    :title="`Student ${markingStore.currentSession?.selectedStudent} Feedback`"
    :ui="{ body: 'p-0 sm:p-0' }"
    fullscreen
    :close="{ onClick: () => emit('close', false) }"
  >
    <template #body>
      <div v-if="!isFeedbackSelected" class="p-4 space-y-4 flex flex-col max-w-5xl mx-auto">
        <UAlert
          title="Select Feedback"
          description="Please select the feedback you feel is most relevant for this student."
          icon="i-heroicons-information-circle"
          color="primary"
          variant="subtle"
        />

        <div class="space-y-3 h-full">
          <UScrollArea v-slot="{ item, index }" :items="feedbackOptions" class="w-full min-h-96 h-full p-2">
            <UPageCard
              :key="item.id"
              class="cursor-pointer mb-4"
              :ui="{
                header: 'w-full mb-0'
              }"
              @click="selectFeedback(item.id)"
            >
              <template #header>
                <div class="flex justify-between items-center">
                  <h3 class="font-medium text-gray-900 dark:text-white">Option {{ index + 1 }}</h3>
                  <UBadge color="primary" variant="subtle">
                    {{ Math.round(item.confidence * 100) }}% Confidence
                  </UBadge>
                </div>
              </template>

              <p class="text-sm text-gray-600 dark:text-gray-300">
                {{ item.description }}
              </p>
            </UPageCard>
          </UScrollArea>

          <div v-if="feedbackOptions.length === 0" class="text-center text-gray-500 py-6">
            No feedback generated for this student yet.
          </div>
        </div>
      </div>

      <div v-else class="p-4 space-y-4 max-w-5xl mx-auto">
        <div class="flex items-center justify-between border-b border-gray-200 dark:border-gray-800 pb-3">
          <h3 class="font-semibold text-lg">Feedback Details</h3>
          <UButton color="neutral" variant="soft" icon="i-lucide-circle-x" @click="clearSelection">
            Change Selection
          </UButton>
        </div>

        <p class="text-sm text-gray-600 dark:text-gray-300">
          {{ selectedFeedback!.description }}
        </p>

        <div class="mt-8 flex items-center justify-between border-b border-gray-200 dark:border-gray-800 pb-3">
          <h3 class="font-semibold text-lg">Feedback Items</h3>
        </div>

        <UAccordion
          :items="selectedFeedback!.items.map((item) => ({ label: item.type, content: item.contents }))"
          multiple
        >
          <template #item="{ item }">
            <div
              class="text-sm text-gray-700 dark:text-gray-200 whitespace-pre-wrap leading-relaxed bg-gray-50 dark:bg-gray-800 p-3 rounded-md"
            >
              {{ item.content }}
            </div>
          </template>
        </UAccordion>
      </div>
    </template>
  </UModal>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useMarkingStore } from '~/stores/marking';

const emit = defineEmits<{ close: [boolean] }>();
const markingStore = useMarkingStore();

// Find the submission for the currently selected student
const currentSubmission = computed(() => {
  const session = markingStore.currentSession;
  if (!session || !session.studentSubmissions) return null;

  return session.studentSubmissions.find((sub: any) => sub.studentNo === session.selectedStudent);
});

// Get all available feedback options for this student to display in the list
const feedbackOptions = computed(() => {
  const feedback = currentSubmission.value?.feedback || [];

  // Create a shallow copy and sort by confidence in descending order (highest first)
  return [...feedback].sort((a, b) => b.confidence - a.confidence);
});

// Determine if a feedback option is currently selected
// This drives the v-if/v-else in your template to swap between the list and the details
const selectedFeedback = computed(() => {
  return feedbackOptions.value.find((f: any) => f.isSelected === true);
});

const isFeedbackSelected = computed(() => {
  return !!selectedFeedback.value;
});

// Action: Handle the user clicking a feedback card
const selectFeedback = async (feedbackId: string) => {
  if (!currentSubmission.value) return;

  // 1. Optimistically update the UI instantly for a snappy experience
  currentSubmission.value.feedback!.forEach((f: any) => {
    f.isSelected = f.id === feedbackId;
  });

  // 2. Sync with the backend
  try {
    await markingStore.selectFeedbackOption(currentSubmission.value.id, feedbackId);
  } catch (error) {
    // If the API call fails, revert the UI and alert the user
    currentSubmission.value.feedback!.forEach((f: any) => {
      f.isSelected = false;
    });

    const toast = useToast();
    toast.add({
      title: 'Error',
      description: 'Failed to save feedback selection. Please try again.',
      color: 'error'
    });
  }
};
// Action: Handle the user clicking the "Back" or "Change Selection" button
const clearSelection = async () => {
  if (!currentSubmission.value) return;

  // 1. Optimistically clear the UI
  currentSubmission.value.feedback!.forEach((f: any) => {
    f.isSelected = false;
  });

  // 2. Sync with the backend (pass null/empty to clear the selection on the server)
  try {
    await markingStore.selectFeedbackOption(currentSubmission.value.id, null);
  } catch (error) {
    console.error('Failed to clear feedback selection on server');
  }
};
</script>
