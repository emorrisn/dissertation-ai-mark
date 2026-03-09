<template>
  <UModal :close="{ onClick: () => emit('close', false) }" title="Are you sure?">
    <template #body>
      <p>{{ description }}</p>
    </template>
    <template #footer>
      <div class="flex gap-2">
        <UButton color="primary" label="Cancel" size="xl" @click="emit('close', false)" />
        <UButton color="secondary" variant="soft" label="Confirm" size="xl" @click="emit('close', true)" />
      </div>
    </template>
  </UModal>
</template>

<script lang="ts" setup>
defineProps<{
  description: string;
}>();

const emit = defineEmits<{ close: [boolean] }>();
</script>

<style></style>
