<template>
  <div class="max-w-5xl mx-auto">
    <UEmpty
      v-if="currentSession!.markshemes.length === 0"
      icon="i-lucide-list"
      title="No marking schemes added"
      description="Get started by adding your first marking scheme.."
      :ui="{
        root: 'ring-0 p-4'
      }"
    />

    <UScrollArea
      v-else
      v-slot="{ item: scheme, index }"
      :items="currentSession!.markshemes"
      class="w-full h-full border-l border-r border-default"
    >
      <UPageCard
        :title="'Markscheme #' + (index + 1)"
        :variant="index % 2 === 0 ? 'soft' : 'outline'"
        class="rounded-none"
        :ui="{
          body: 'w-full'
        }"
      >
        <template #description>
          <div class="flex justify-between items-center w-full">
            <div class="flex items gap-1.5">
              {{ scheme.file ? `Upload: ${scheme.file.name}` : 'Text Instructions' }}
            </div>
            <UButton
              icon="i-lucide-trash-2"
              color="primary"
              variant="soft"
              size="sm"
              @click.prevent="handleDelete(scheme.id, index)"
            />
          </div>
        </template>
      </UPageCard>
    </UScrollArea>
  </div>
</template>

<script lang="ts" setup>
import { storeToRefs } from 'pinia';
import { useMarkingStore } from '~/stores/marking';
import { LazyUIConfirmationPopup } from '#components';

const markingStore = useMarkingStore();
const { currentSession } = storeToRefs(markingStore);
const overlay = useOverlay();
const confirmationModal = overlay.create(LazyUIConfirmationPopup);

async function handleDelete(id: string, index: number) {
  const instance = confirmationModal.open({
    description: `Delete markscheme #${index + 1}`
  });
  const shouldDelete = await instance.result;

  if (shouldDelete) {
    markingStore.removeMarkScheme(id);
  }
}
</script>

<style></style>
