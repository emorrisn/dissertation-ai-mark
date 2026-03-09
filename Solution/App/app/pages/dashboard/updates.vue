<template>
  <UDashboardPanel
    :ui="{
      body: 'sm:p-0 p-0'
    }"
  >
    <template #header>
      <UDashboardNavbar title="Latest Updates">
        <template #right>
          <div class="flex items-center gap-2">
            <UButton
              icon="i-lucide-refresh-cw"
              variant="ghost"
              :loading="updatesStore.status == 'loading'"
              @click="refresh"
            />
          </div>
        </template>
      </UDashboardNavbar>
    </template>
    <template #body>
      <UScrollArea
        v-if="items.length && updatesStore.status !== 'loading'"
        v-slot="{ item, index }"
        :items="items"
        class="w-full h-full max-w-5xl mx-auto border-l border-r border-default"
      >
        <UPageCard v-bind="item" :variant="index % 2 === 0 ? 'soft' : 'outline'" class="rounded-none" />
      </UScrollArea>
      <UEmpty
        v-else-if="updatesStore.status == 'loading'"
        icon="i-lucide-wifi"
        title="Loading Updates"
        description="Fetching your latest updates. Please wait..."
        :ui="{
          header: 'animate-pulse',
          root: 'ring-0'
        }"
      />
      <UEmpty
        v-else
        icon="i-lucide-bell-off"
        title="No Updates Yet"
        description="Your latest updates will appear here. Check back soon for notifications about your marking sessions, feedback, and more!"
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
import { storeToRefs } from 'pinia';
import { useUpdatesStore } from '~/stores/updates';

definePageMeta({
  layout: 'dashboard'
});

const updatesStore = useUpdatesStore();
const { sortedUpdates } = storeToRefs(updatesStore);

onMounted(() => {
  if (!updatesStore.updates.length) {
    refresh();
  }
});

const refresh = () => {
  updatesStore.fetchUpdates();
};

const items = computed(() => {
  // Filter out any potential undefined values in the array to prevent runtime errors.
  // This is a defensive measure against unexpected states in the store.
  return sortedUpdates.value.filter(Boolean).map((update) => {
    const iconMap: Record<string, string> = {
      MarkingSessionUpdate: 'i-lucide-check-circle-2',
      NewFeature: 'i-lucide-sparkles',
      SystemMessage: 'i-lucide-info'
    };

    return {
      ...update,
      icon: iconMap[update.type] || 'i-lucide-bell',
      description: update.message,
      to: update.link,
      badge: update.isRead ? null : { label: 'New', color: 'primary' as const }
    };
  });
});
</script>

<style></style>
