<template>
  <UModal
    title="Add Marking Scheme"
    fullscreen
    :ui="{ body: 'p-0 sm:p-0' }"
    :close="{ onClick: () => emit('close', false) }"
  >
    <template #body>
      <UTabs
        :items="items"
        variant="link"
        :ui="{ trigger: 'grow p-4', content: 'p-4 max-w-5xl mx-auto space-y-4' }"
        class="gap-4 w-full"
      >
        <template #text="{ item }">
          <UForm :schema="schema" :state="state" class="space-y-4" @submit="handleTextSubmit">
            <UAlert
              icon="i-lucide-info"
              title="Text-based Instructions"
              variant="soft"
              :description="item.description"
            />
            <UFormField name="contents" required>
              <UTextarea
                v-model="state.contents"
                placeholder="Paste your marking scheme here..."
                class="w-full"
                :rows="10"
                autoresize
              />
            </UFormField>
            <div class="flex justify-start gap-3 pt-4">
              <UButton type="submit" size="lg" label="Save as Mark Scheme Item" />
            </div>
          </UForm>
        </template>

        <template #file="{ item }">
          <UAlert
            icon="i-lucide-upload-cloud"
            color="primary"
            variant="soft"
            title="File Upload"
            :description="item.description"
          />
          <UFileUpload
            v-model="state.file"
            class="w-full min-h-48"
            label="Drop your mark scheme here"
            description="PDF, PNG, DOCX, ETC (max. 2MB)"
            :limit="1"
            accept=".pdf, .docx, .png, .jpg"
          />
          <div class="flex justify-start gap-3 pt-4">
            <UButton
              type="submit"
              size="lg"
              :loading="fileUploading"
              label="Upload as Mark Scheme Item"
              :disabled="!state.file"
              @click="handleFileSubmit"
            />
          </div>
        </template>
      </UTabs>
    </template>
  </UModal>
</template>

<script setup lang="ts">
// TODO: Make sure files save with proper sessionIds

import type { TabsItem, FormSubmitEvent } from '@nuxt/ui';
import { z } from 'zod';
import { storeToRefs } from 'pinia';
import { useMarkingStore } from '~/stores/marking';
import type { SessionFile } from '~/types';

const emit = defineEmits<{ close: [boolean] }>();

const items = [
  {
    label: 'Text Instructions',
    description:
      'Provide a detailed marking scheme or rubric as plain text. This will be used by the AI to understand the criteria for marking.',
    icon: 'i-lucide-whole-word',
    slot: 'text' as const
  },
  {
    label: 'File Upload',
    description: 'Upload documents (.pdf, .docx) or images to be used as marking schemes. ',
    icon: 'i-lucide-file-up',
    slot: 'file' as const
  }
] satisfies TabsItem[];

const markingStore = useMarkingStore();
const { currentSession } = storeToRefs(markingStore);

const schema = z.object({
  contents: z.string().min(10, 'Please provide more detailed contents for the marking scheme.')
});

type Schema = z.output<typeof schema>;
const fileUploading = ref(false);

const state = ref({
  contents: '',
  file: null as File | null
});

function handleTextSubmit(event: FormSubmitEvent<Schema>) {
  if (!currentSession.value) return;
  markingStore.addMarkScheme({ contents: event.data.contents });
  resetAndClose();
}

async function handleFileSubmit() {
  if (!state.value.file || !currentSession.value) return;
  fileUploading.value = true;
  try {
    // Simulate API call to upload the file
    await new Promise((resolve) => setTimeout(resolve, 1500));

    const now = new Date().toISOString();
    const mockSessionFile: SessionFile = {
      id: crypto.randomUUID(),
      url: URL.createObjectURL(state.value.file), // Temporary local URL
      name: state.value.file.name,
      storageUrl: `uploads/mark-schemes/${state.value.file.name}`,
      size: state.value.file.size,
      uploadedAt: now
    };

    markingStore.addMarkScheme({ file: mockSessionFile });
    resetAndClose();
  } catch (error) {
    console.error('File upload failed:', error);
    // In a real app, show a toast notification to the user
  } finally {
    fileUploading.value = false;
  }
}

function resetAndClose() {
  state.value = { contents: '', file: null };
  emit('close', false);
}
</script>
