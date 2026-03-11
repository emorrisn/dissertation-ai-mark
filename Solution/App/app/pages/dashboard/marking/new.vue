<template>
  <UDashboardPanel
    id="setup"
    :ui="{
      body: 'sm:p-0 p-0'
    }"
  >
    <template #header>
      <UDashboardNavbar title="Setup Session">
        <template #right>
          <UButton color="neutral" variant="outline" size="lg" @click="handleBack()">
            {{ currentStep == 0 ? 'Exit' : 'Back' }}
          </UButton>
        </template>
      </UDashboardNavbar>

      <UDashboardToolbar>
        <UStepper v-model="currentStep" :items="items" disabled class="w-full py-2" />
      </UDashboardToolbar>
    </template>
    <template #body>
      <div v-if="currentStep === 0" class="space-y-4 p-4">
        <SessionDetailsForm @success="() => (currentStep = 1)" />
      </div>

      <div v-else-if="currentStep === 1" class="space-y-4">
        <SessionMarkSchemes />
      </div>

      <div v-else-if="currentStep === 2" class="p-4 flex flex-col items-center justify-center text-center h-full">
        <div class="flex flex-col items-center gap-4">
          <UIcon name="i-lucide-party-popper" class="text-5xl text-primary" />
          <h2 class="text-2xl font-bold">Ready to begin?</h2>
          <p class="text-gray-500 dark:text-gray-400">
            Please review your session details and marking schemes before starting the session.
          </p>
          <UAlert
            class="text-left"
            icon="i-lucide-lightbulb"
            title="Pro Tip"
            variant="soft"
            description="Make sure you have good lighting and keep a mental note of the order you scan work in."
          />
          <UButton to="/dashboard/marking/record" label="Begin Session" icon="i-lucide-play" size="lg" />
        </div>
      </div>
    </template>

    <!-- Mark schemes footer -->
    <template v-if="currentStep === 1" #footer>
      <div class="flex justify-start p-4 gap-3 border-t border-default">
        <UButton color="primary" size="lg" @click="openMarkSchemeModal"> Add Marking Scheme </UButton>

        <UButton
          color="primary"
          size="lg"
          variant="outline"
          :disabled="markingStore.currentSession?.markshemes.length === 0"
          @click="currentStep++"
        >
          Continue
        </UButton>
      </div>
    </template>
  </UDashboardPanel>
</template>

<script lang="ts" setup>
import type { StepperItem } from '@nuxt/ui';
import AddMarkSchemeModal from '~/components/Session/AddMarkSchemeModal.vue';

const currentStep = ref(0);
const markingStore = useMarkingStore();
const overlay = useOverlay();
const addMarkschemeModal = overlay.create(AddMarkSchemeModal);

const items = ref<StepperItem[]>([
  {
    title: 'Details',
    icon: 'i-lucide-file-text'
  },
  {
    title: 'Marking Schemes',
    icon: 'i-lucide-check-square'
  },
  {
    title: 'Begin',
    icon: 'i-lucide-flag'
  }
]);

async function openMarkSchemeModal() {
  addMarkschemeModal.open();
}

onMounted(async () => {
  if (!markingStore.currentSession) {
    markingStore.initializeNewSession();
  }
});

const router = useRouter();

function handleBack() {
  if (currentStep.value === 0) {
    router.push('/dashboard/marking');
  } else {
    currentStep.value--;
  }
}

definePageMeta({
  layout: 'dashboard',
  middleware: ['auth']
});
</script>

<style></style>
