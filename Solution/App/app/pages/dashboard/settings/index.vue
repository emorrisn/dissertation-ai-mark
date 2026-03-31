<template>
  <UForm id="settings" :schema="profileSchema" :state="profile" @submit="onSubmit" @change="changes = true">
    <UPageCard
      title="Profile"
      description="These informations will be displayed publicly."
      variant="naked"
      orientation="horizontal"
      class="mb-4"
    >
    </UPageCard>

    <UPageCard variant="subtle">
      <UFormField
        name="name"
        label="Name"
        description="Will be used in during marking sessions and dashboards."
        required
        class="flex max-sm:flex-col justify-between items-start gap-4"
      >
        <UInput v-model="profile.name" autocomplete="off" />
      </UFormField>
      <USeparator />
      <UFormField
        name="email"
        label="Email"
        description="Email receipts and system updates."
        required
        class="flex max-sm:flex-col justify-between items-start gap-4"
      >
        <UInput v-model="profile.email" type="email" autocomplete="off" />
      </UFormField>
      <USeparator />
      <UFormField
        name="username"
        label="Username"
        description="Your unique username for logging in to your profile."
        required
        class="flex max-sm:flex-col justify-between items-start gap-4"
      >
        <UInput v-model="profile.username" type="username" autocomplete="off" />
      </UFormField>
      <USeparator />
      <UFormField
        name="writingStyle"
        label="Writing Style"
        description="Select 1 to 2 preferred writing styles for the AI to follow."
        class="flex max-sm:flex-col justify-between items-start gap-4"
      >
        <USelect v-model="profile.writingStyle" :items="writingStyleOptions" multiple class="min-w-md" />
      </UFormField>
      <USeparator />
      <UButton label="Save Changes" class="w-fit" type="submit" :disabled="!changes" />
    </UPageCard>
  </UForm>
</template>

<script lang="ts" setup>
import * as z from 'zod';
import type { FormSubmitEvent } from '@nuxt/ui';

const profileSchema = z.object({
  name: z.string().min(2, 'Too short'),
  email: z.string().email('Invalid email'),
  username: z.string().min(2, 'Too short'),
  writingStyle: z
    .array(z.string())
    .min(1, 'Please select at least one style.')
    .max(2, 'You can select a maximum of two styles.')
});
const changes = ref<boolean>(false);
const authStore = useAuthStore();
const writingStyleOptions = ['Strict', 'Balanced', 'Encouraging', 'Technical'];

type ProfileSchema = z.output<typeof profileSchema>;

const profile = reactive<Partial<ProfileSchema>>({
  name: authStore.user?.name || 'John Doe',
  email: authStore.user?.email || 'ben@nuxtlabs.com',
  username: authStore.user?.username || 'benjamincanac',
  writingStyle: authStore.user?.writingStyle || []
});
const toast = useToast();
async function onSubmit(event: FormSubmitEvent<ProfileSchema>) {
  try {
    await authStore.updateProfile(event.data);

    toast.add({
      title: 'Success',
      description: 'Your settings have been updated.',
      icon: 'i-lucide-check',
      color: 'success'
    });

    changes.value = false;
  } catch {
    toast.add({
      title: 'Error',
      description: 'Failed to update settings. Please try again. ',
      icon: 'i-lucide-alert-triangle',
      color: 'error'
    });
  }
}

definePageMeta({
  layout: 'dashboard',
  middleware: ['auth']
});
</script>

<style></style>
