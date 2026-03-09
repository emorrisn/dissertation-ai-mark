<script setup lang="ts">
import { onMounted } from 'vue';
import { useAuthStore } from '~/stores/auth';
import * as z from 'zod';
import type { FormSubmitEvent } from '#ui/types';

const open = ref(true);
const loading = ref(false);
const route = useRoute();

// Set institution from URL query
const institutionQuery = route.query.institution;

const loginSchema = z.object({
  username: z.string().min(2, 'Username is required.'),
  password: z.string().min(2, 'Password is required.'),
  institute_code: z.string().min(2, 'Institution is required.')
});

type Schema = z.output<typeof loginSchema>;

const state = reactive<Partial<Schema>>({
  username: '',
  password: '',
  institute_code: institutionQuery as string | undefined
});

const authStore = useAuthStore();
const router = useRouter();
const toast = useToast();

const institution = computed(() => authStore.institutes.find((i) => i.code === institutionQuery));

onMounted(() => {
  if (!institutionQuery) {
    toast.add({
      title: 'No institution selected',
      description: 'Please select an institution first.'
    });
    router.push('/');
  }
});

async function login(event: FormSubmitEvent<Schema>) {
  loading.value = true;
  try {
    await authStore.login(event.data);
    await router.push({ path: '/dashboard/updates' });
  } catch (error: any) {
    toast.add({
      title: 'Login Failed',
      description: error.data?.message || 'An unexpected error occurred.'
    });
  } finally {
    loading.value = false;
  }
}

definePageMeta({
  layout: 'landing',
  middleware: ['auth']
});
</script>

<template>
  <div class="bg-gradient-to-br from-primary-200 to-white h-full h-screen">
    <USlideover v-model:open="open" side="left" :overlay="false" :dismissible="false" :transition="false">
      <template #content>
        <div class="w-full px-6 py-12 h-full flex flex-col justify-center">
          <p class="text-sm text-muted mb-2">
            Login to
            <span class="capitalize">{{ institution?.name || 'your institution' }}</span>
          </p>
          <h1 class="text-3xl md:text-4xl font-extrabold mb-4">Account</h1>

          <div class="space-y-4">
            <UForm :schema="loginSchema" :state="state" class="space-y-4" @submit="login">
              <UFormField name="username" label="Username">
                <UInput v-model="state.username" placeholder="Username" class="w-full" />
              </UFormField>
              <UFormField name="password" label="Password">
                <UInput v-model="state.password" type="password" placeholder="Password" class="w-full" />
              </UFormField>

              <div class="flex items-center justify-between mt-6">
                <UButton to="/" variant="outline" color="neutral" class="flex items-center">
                  Change Institution
                </UButton>

                <UButton color="primary" :loading="loading" type="submit">Login</UButton>
              </div>
            </UForm>
          </div>
        </div>
      </template>
    </USlideover>
  </div>
</template>
