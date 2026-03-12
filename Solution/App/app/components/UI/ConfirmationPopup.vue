<template>
  <UModal :title="title" :close="{ onClick: () => emit('close', false) }">
    <template #body>
      <div class="flex flex-col gap-4">
        <img v-if="image" :src="image" class="max-h-64 w-full object-cover rounded-lg border border-default" />

        <p v-if="description">{{ description }}</p>
      </div>
    </template>

    <template v-if="actionsEnabled" #footer>
      <div class="flex gap-2 justify-end">
        <UButton
          v-if="cancelButton !== null"
          color="neutral"
          :label="cancelButton"
          size="xl"
          @click="emit('close', false)"
        />
        <UButton
          v-if="confirmButton !== null"
          color="primary"
          variant="soft"
          :label="confirmButton"
          size="xl"
          @click="emit('close', true)"
        />
      </div>
    </template>
  </UModal>
</template>

<script lang="ts" setup>
withDefaults(
  defineProps<{
    title?: string;
    description?: string;
    image?: string;
    cancelButton?: string;
    confirmButton?: string;
    actionsEnabled?: boolean;
  }>(),
  {
    title: 'Are you sure?',
    cancelButton: 'Cancel',
    confirmButton: 'Confirm',
    actionsEnabled: true
  }
);

const emit = defineEmits<{
  close: [boolean];
}>();
</script>
