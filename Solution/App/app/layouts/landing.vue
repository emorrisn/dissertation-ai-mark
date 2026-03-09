<script setup>
useHead({
  meta: [{ name: "viewport", content: "width=device-width, initial-scale=1" }],
  link: [{ rel: "icon", href: "/favicon.ico" }],
  htmlAttrs: {
    lang: "en",
  },
});

const title = "Login to Magic Mark";
const description =
  "A powerful and intuitive tool for marking students' work and providing feedback. With Magic Mark, teachers can easily create and manage assignments, grade student work, and provide personalized feedback to help students improve their learning outcomes.";

useSeoMeta({
  title,
  description,
  ogTitle: title,
  ogDescription: description,
  ogImage: "https://ui.nuxt.com/assets/templates/nuxt/starter-light.png",
  twitterImage: "https://ui.nuxt.com/assets/templates/nuxt/starter-light.png",
  twitterCard: "summary_large_image",
});
</script>

<template>
  <ClientOnly>
    <UApp>
      <UMain>
        <slot />
      </UMain>
    </UApp>
  </ClientOnly>
</template>
