<template>
  <UDashboardToolbar
    v-if="showNav"
    class="lg:hidden h-(--ui-header-height) justify-end border-t border-default shrink-0 flex items-center border-b px-4 sm:px-6 bg-elevated/25 pb-0"
  >
    <div class="mx-auto flex gap-0 w-full">
      <button
        v-for="item in items"
        :key="item.label"
        class="flex-1 flex flex-col items-center justify-center gap-1"
        :aria-current="isActive(item) ? 'page' : undefined"
        @click="navigate(item.to)"
      >
        <Icon
          :name="item.icon"
          aria-hidden="true"
          :class="isActive(item) ? 'text-primary' : 'text-default'"
        />
        <span :class="isActive(item) ? 'text-primary' : 'text-default'">{{
          item.label
        }}</span>
      </button>
    </div>
  </UDashboardToolbar>
</template>

<script lang="ts" setup>
import { ref, computed } from "vue";
import { useRoute, useRouter } from "vue-router";

type NavItem = {
  label: string;
  icon: string;
  to: string;
};

const route = useRoute();
const router = useRouter();

const items = ref<NavItem[]>([
  { label: "Updates", icon: "i-lucide-mail", to: "/dashboard/updates" },
  { label: "Sessions", icon: "i-lucide-paperclip", to: "/dashboard/marking" },
]);

const showNav = computed(() => {
  const p = route.path || "";
  return p.includes("/dashboard/updates") || p.includes("/dashboard/marking");
});

function navigate(to: string) {
  if (!to) return;
  if (route.path !== to) router.push(to).catch(() => {});
}

function isActive(item: NavItem) {
  const p = route.path || "";
  return p === item.to || p.includes(item.to);
}
</script>

<style></style>
