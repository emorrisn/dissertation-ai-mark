<script setup lang="ts">
import type { Institute } from '~/types';

const open = ref(true);
const value = ref<{ label: string; value: string } | undefined>(undefined);
const authStore = useAuthStore();
const institutes: ComputedRef<Institute[]> = computed(() => authStore.institutes);

async function fetchInstitutes() {
  await authStore.fetchInstitutes();
}
onMounted(() => {
  fetchInstitutes();
});

function login() {
  if (value.value) {
    useRouter().push({
      path: '/login',
      query: { institution: value.value.value }
    });
  }
}

definePageMeta({
  layout: 'landing',
  middleware: ['auth']
});
</script>

<template>
  <div class="bg-gradient-to-br from-primary-200 to-white h-screen">
    <USlideover v-model:open="open" side="left" :overlay="false" :dismissible="false" :transition="false">
      <template #content>
        <div class="w-full px-6 py-12 h-full flex flex-col justify-center">
          <p class="text-sm text-muted mb-2">Welcome to</p>
          <h1 class="text-3xl md:text-4xl font-extrabold mb-4">Magic Mark</h1>
          <p class="text-sm text-muted mb-6">
            Lorem ipsum dolor sit amet, consectetur adipiscing elit. Integer nec odio. Praesent libero.
          </p>

          <div class="space-y-4">
            <UInputMenu
              v-model="value"
              placeholder="Select Institution"
              :items="institutes.map((item) => ({ label: item.name, value: item.code }))"
              class="w-full"
              :loading="institutes.length === 0"
            />

            <UButton @click="login()" color="primary" :disabled="value == null">Continue</UButton>
          </div>
        </div>
      </template>
    </USlideover>
  </div>
</template>
