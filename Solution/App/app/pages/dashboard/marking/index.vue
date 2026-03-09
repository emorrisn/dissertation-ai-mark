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
          :title="`Marking Session - ${new Date(session.createdAt).toLocaleDateString('en-GB')}`"
          :to="`/dashboard/marking/${session.sessionId}`"
          :badge="{
            label: session.status,
            color: session.status === 'completed' ? 'green' : session.status === 'processing' ? 'orange' : 'gray',
            variant: 'subtle'
          }"
          :variant="index % 2 === 0 ? 'soft' : 'outline'"
          class="rounded-none"
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
                <span>Updated: {{ new Date(session.updatedAt).toLocaleDateString('en-GB') }}</span>
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

const markingStore = useMarkingStore();
const { sessions } = storeToRefs(markingStore);

onMounted(() => {
  if (!markingStore.sessions.length) {
    refresh();
  }
});

async function refresh() {
  await markingStore.fetchSessions();
}

definePageMeta({
  layout: 'dashboard',
  middleware: ['auth']
});
</script>
