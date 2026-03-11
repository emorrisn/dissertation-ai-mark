<template>
  <UDashboardPanel id="settings" :ui="{ body: 'py-8 lg:py-8' }">
    <template #header>
      <UDashboardNavbar title="Settings">
        <template #leading>
          <UDashboardSidebarCollapse />
        </template>
      </UDashboardNavbar>

      <UDashboardToolbar>
        <UNavigationMenu :items="links" highlight class="-mx-1 flex-1" />
      </UDashboardToolbar>
    </template>

    <template #body>
      <div class="flex flex-col gap-4 sm:gap-6 lg:gap-12 w-full max-w-5xl mx-auto space-y-6">
        <NuxtPage />
      </div>
    </template>

    <template #footer>
      <DashboardMobileNav />
    </template>
  </UDashboardPanel>
</template>

<script lang="ts" setup>
import type { NavigationMenuItem } from '@nuxt/ui';

const links = [
  {
    label: 'Profile',
    icon: 'i-lucide-user',
    to: '/dashboard/settings',
    exact: true
  },
  {
    label: 'Security',
    icon: 'i-lucide-shield',
    to: '/dashboard/settings/security'
  }
] satisfies NavigationMenuItem[];

definePageMeta({
  layout: 'dashboard',
  middleware: ['auth']
});
</script>

<style></style>
