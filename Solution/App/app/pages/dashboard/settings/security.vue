<template>
  <div class="space-y-6">
    <UPageCard
      title="Security"
      description="Change your password, enable two-factor authentication and manage active sessions."
      variant="naked"
      orientation="horizontal"
    >
    </UPageCard>

    <UPageCard title="Password" description="Confirm your current password before setting a new one." variant="subtle">
      <UForm
        ref="passwordChangeForm"
        :schema="passwordSchema"
        :state="passwordState"
        class="flex flex-col gap-4 max-w-xs"
        @submit="onPasswordSubmit"
      >
        <UFormField name="currentPassword">
          <UInput
            v-model="passwordState.currentPassword"
            type="password"
            placeholder="Current password"
            class="w-full"
          />
        </UFormField>

        <UFormField name="newPassword">
          <UInput v-model="passwordState.newPassword" type="password" placeholder="New password" class="w-full" />
        </UFormField>
        <USeparator />

        <UButton
          label="Update Password"
          class="w-fit"
          type="submit"
          :disabled="passwordState.newPassword == '' || passwordState.currentPassword == ''"
        />
      </UForm>
    </UPageCard>

    <UPageCard
      title="Account"
      description="No longer want to use our service? You can delete your account here. This action is not reversible. All information related to this account will be deleted permanently."
      class="bg-gradient-to-tl from-error/10 from-5% to-default"
    >
      <template #footer>
        <UButton label="Delete Account" color="error" class="w-fit mt-2" @click="onDeleteAccount" />
      </template>
    </UPageCard>
  </div>
</template>

<script lang="ts" setup>
import * as z from 'zod';
import type { FormSubmitEvent } from '@nuxt/ui';

const authStore = useAuthStore();
const toast = useToast();
const passwordChangeForm = useTemplateRef('passwordChangeForm');

const passwordSchema = z.object({
  currentPassword: z.string().min(1, 'Current password is required'),
  newPassword: z.string().min(6, 'Must be at least 6 characters')
});

type PasswordSchema = z.output<typeof passwordSchema>;

const passwordState = reactive({
  currentPassword: '',
  newPassword: ''
});

async function onPasswordSubmit(event: FormSubmitEvent<PasswordSchema>) {
  try {
    await authStore.changePassword(event.data);

    toast.add({ title: 'Success', description: 'Your password has been updated.', color: 'success' });

    // Clear the form fields after a successful update
    passwordState.currentPassword = '';
    passwordState.newPassword = '';
  } catch (error: any) {
    // Check if it's our specific 401 "Incorrect current password" error
    const msg = error.response?._data?.error || 'Failed to update password.';
    toast.add({ title: 'Error', description: msg, color: 'error' });

    passwordChangeForm.value?.errors.push({
      name: 'currentPassword',
      message: error.response?._data?.error || 'An unexpected error occurred.'
    });
  }
}

// --- DELETE ACCOUNT LOGIC ---
async function onDeleteAccount() {
  // Simple browser confirm to prevent accidental clicks
  const confirmed = confirm('Are you absolutely sure you want to delete your account? This action cannot be undone.');

  if (confirmed) {
    try {
      await authStore.deleteAccount();
      // Note: No toast needed here because the store redirects them to /login
    } catch {
      toast.add({ title: 'Error', description: 'Failed to delete account. Please try again.', color: 'error' });
    }
  }
}

definePageMeta({
  layout: 'dashboard',
  middleware: ['auth']
});
</script>

<style></style>
