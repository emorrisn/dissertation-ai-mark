<script setup lang="ts">
import type { NavigationMenuItem } from '@nuxt/ui';

useHead({
  meta: [{ name: 'viewport', content: 'width=device-width, initial-scale=1' }],
  link: [{ rel: 'icon', href: '/favicon.ico' }],
  htmlAttrs: {
    lang: 'en'
  }
});
const loading = ref(false);
const updatesStore = useUpdatesStore();
const markingStore = useMarkingStore();

const router = useRouter();
const title = 'Dashboard for Magic Mark';
const description =
  "A powerful and intuitive tool for marking students' work and providing feedback. With Magic Mark, teachers can easily create and manage assignments, grade student work, and provide personalized feedback to help students improve their learning outcomes.";

useSeoMeta({
  title,
  description,
  ogTitle: title,
  ogDescription: description,
  ogImage: 'https://ui.nuxt.com/assets/templates/nuxt/starter-light.png',
  twitterImage: 'https://ui.nuxt.com/assets/templates/nuxt/starter-light.png',
  twitterCard: 'summary_large_image'
});

const items = computed<NavigationMenuItem[]>(() => [
  {
    label: 'Updates',
    icon: 'i-lucide-mail',
    badge: updatesStore.updates.length > 0 ? updatesStore.updates.length : undefined,
    to: '/dashboard/updates'
  },
  {
    label: 'Marking Sessions',
    icon: 'i-lucide-paperclip',
    badge: markingStore.sessions.length > 0 ? markingStore.sessions.length : undefined,
    to: '/dashboard/marking',
    active: router.currentRoute.value.path.startsWith('/dashboard/marking')
  },
  {
    label: 'Settings',
    icon: 'i-lucide-settings',
    to: '/dashboard/settings'
  }
]);
</script>

<template>
  <ClientOnly>
    <UApp>
      <UMain>
        <UDashboardGroup>
          <UDashboardSidebar
            collapsible
            resizable
            :ui="{
              footer: 'border-t border-default',
              header: 'border-b border-default'
            }"
          >
            <template #header="{ collapsed }">
              <span class="text-lg font-semibold tracking-tight mx-auto">{{ 'Magic Mark' }}</span>
            </template>

            <template #default="{ collapsed }">
              <UNavigationMenu :collapsed="collapsed" :items="items" orientation="vertical" />
            </template>

            <template #footer="{ collapsed }">
              <UButton
                label="Log out"
                color="neutral"
                variant="ghost"
                class="w-full"
                icon="i-lucide-log-out"
                :block="collapsed"
                @click="
                  () => {
                    useAuthStore().logout();
                    router.push('/');
                  }
                "
              />
            </template>
          </UDashboardSidebar>

          <template v-if="!loading">
            <slot />
          </template>
          <template v-else>
            <div class="w-full h-full flex items-center justify-center">
              <Icon name="i-lucide-loader-circle" class="animate-spin text-2xl" />
            </div>
          </template>
        </UDashboardGroup>
      </UMain>
    </UApp>
  </ClientOnly>
</template>
