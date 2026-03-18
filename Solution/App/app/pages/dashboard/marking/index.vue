<template>
  <UDashboardPanel
    :ui="{
      body: 'sm:p-0 p-0'
    }"
  >
    <template #header>
      <UDashboardNavbar title="Past Sessions">
        <template #right>
          <div class="flex items-center gap-2">
            <UButton
              icon="i-lucide-refresh-cw"
              variant="ghost"
              :loading="markingStore.status == 'loading'"
              @click="refresh"
            />
            <UButton label="New Session" variant="outline" size="lg" to="/dashboard/marking/new" icon="i-lucide-plus" />
          </div>
        </template>
      </UDashboardNavbar>
    </template>
    <template #body>
      <UScrollArea
        v-if="sessions.length && markingStore.status !== 'loading'"
        v-slot="{ item: session, index }"
        :items="sessions"
        class="w-full h-full max-w-5xl mx-auto border-l border-r border-default"
      >
        <UPageCard
          :title="`Year ${session.year} - ${new Date(session.createdAt).toLocaleDateString('en-GB')}`"
          :badge="{
            label: session.status,
            color: session.status === 'completed' ? 'green' : session.status === 'processing' ? 'orange' : 'gray',
            variant: 'subtle'
          }"
          :variant="index % 2 === 0 ? 'soft' : 'outline'"
          class="rounded-none cursor-pointer"
          @click="onMarkingSessionClick(session)"
        >
          <template #description>
            <p class="text-sm text-gray-500 dark:text-gray-400">
              {{ session.notes || `A marking session for ${session.studentsAmount} students.` }}
            </p>
            <div class="flex items-center flex-wrap gap-x-4 gap-y-1 text-sm text-gray-500 dark:text-gray-400 mt-2">
              <div class="flex items-center gap-1.5">
                <UIcon name="i-lucide-users" class="w-4 h-4" />
                <span>{{ session.studentsAmount }} students</span>
              </div>
              <div class="flex items-center gap-1.5">
                <UIcon name="i-lucide-file-check-2" class="w-4 h-4" />
                <span>Outputs: {{ session.requiredOutputs.join(', ').replace('_', ' ') }}</span>
              </div>
              <div class="flex items-center gap-1.5">
                <UIcon name="i-lucide-clock" class="w-4 h-4" />
                <span>Status: {{ getStatusText(session.status) }}</span>
              </div>
            </div>
          </template>
        </UPageCard>
      </UScrollArea>
      <UEmpty
        v-else-if="markingStore.status == 'loading'"
        icon="i-lucide-wifi"
        title="Loading Sessions"
        description="Fetching your marking sessions. Please wait..."
        :ui="{
          header: 'animate-pulse',
          root: 'ring-0'
        }"
      />
      <UEmpty
        v-else
        icon="i-lucide-layout-list"
        title="No Sessions Yet"
        description="Your marking sessions will appear here. Create a new session to get started!"
        :ui="{
          root: 'ring-0'
        }"
      />
    </template>
    <template #footer>
      <DashboardMobileNav />
    </template>
  </UDashboardPanel>
</template>

<script lang="ts" setup>
import { useMarkingStore } from '~/stores/marking';
import { storeToRefs } from 'pinia';
import type { MarkingSession } from '~/types';
import { LazyUIConfirmationPopup } from '#components';

const overlay = useOverlay();
const markingStore = useMarkingStore();
const { sessions } = storeToRefs(markingStore);
const router = useRouter();
const infoModal = overlay.create(LazyUIConfirmationPopup);

onMounted(() => {
  if (!markingStore.sessions.length) {
    refresh();
  }
});

async function onMarkingSessionClick(session: MarkingSession) {
  markingStore.currentSession = session;

  switch (session.status) {
    case 'ready': {
      const canContinue = await infoModal.open({
        title: 'Are you sure you want to continue?',
        description: 'You will continue the session from where it was last left off from.'
      });

      if (!canContinue) {
        return;
      }

      router.push(`/dashboard/marking/record`);
      return;
    }
    case 'completed':
      session.selectedStudent = 1;
      markingStore.setCurrentSession(session);
      router.push(`/dashboard/marking/review`);
      return;
    case 'error':
      await infoModal.open({
        title: 'Session',
        description: 'It appears there was an error with your session. Please contact the admin for support.',
        actionsEnabled: false
      });
      return;
    case 'pending':
      await infoModal.open({
        title: 'Session',
        description: 'Your session is currently in a queue. Please allow some time for it to begin processing.',
        actionsEnabled: false
      });
      return;
    case 'processing':
      await infoModal.open({
        title: 'Session',
        description: 'Your session is currently processing, please allow some time for it to process.',
        actionsEnabled: false
      });
      return 'Processing content';
    default:
      return;
  }
}

function getStatusText(status: MarkingSession['status']) {
  switch (status) {
    case 'ready':
      return 'Ready to start';
    case 'completed':
      return 'Ready to view';
    case 'error':
      return 'Something went wrong';
    case 'pending':
      return 'Waiting to process';
    case 'processing':
      return 'Processing content';
    default:
      return 'Loading';
  }
}

async function refresh() {
  await markingStore.fetchSessions();
}

definePageMeta({
  layout: 'dashboard',
  middleware: ['auth']
});
</script>
