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
        :ui="{ trigger: 'grow p-4', content: 'p-4 max-w-5xl mx-auto space-y-4 pt-0' }"
        class="gap-4 w-full"
        :unmount="false"
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
            layout="list"
            label="
              Drop your mark scheme here
            "
            description="PDF, PNG, DOCX, ETC (max. 10MB)"
            :limit="1"
            accept=".pdf, .docx, .png, .jpg"
            :ui="{
              base: state.file ? 'hidden' : '',
              files: 'h-full'
            }"
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

        <template #camera="{ item }">
          <UAlert
            icon="i-lucide-camera"
            color="primary"
            variant="soft"
            title="Camera Capture"
            :description="item.description"
          />

          <div class="w-full max-w-5xl mx-auto">
            <SessionCamera v-if="!cameraImage" ref="camera" min-height="0" />

            <!-- CAPTURED IMAGE -->
            <img v-else :src="cameraImage" class="max-w-[75dvh] mx-auto" />

            <div class="flex gap-3 mt-4">
              <!-- TAKE PHOTO -->
              <UButton v-if="!cameraImage" icon="i-lucide-camera" label="Take Picture" @click="takeCameraPicture" />

              <!-- RETRY -->
              <UButton
                v-if="cameraImage"
                icon="i-lucide-rotate-ccw"
                variant="outline"
                label="Retry"
                @click="retryCamera"
              />

              <!-- SAVE -->
              <UButton
                v-if="cameraImage"
                icon="i-lucide-check"
                color="primary"
                label="Save Mark Scheme"
                @click="saveCameraImage"
              />
            </div>
          </div>
        </template>
      </UTabs>
    </template>
  </UModal>
</template>

<script setup lang="ts">
import type { TabsItem, FormSubmitEvent } from '@nuxt/ui';
import { z } from 'zod';
import { storeToRefs } from 'pinia';
import { useMarkingStore } from '~/stores/marking';
import type { SessionFile } from '~/types';
import { SessionCamera } from '#components';

const emit = defineEmits<{ close: [boolean] }>();

const cameraImage = ref<string | null>(null);
const camera = ref<InstanceType<typeof SessionCamera> | null>(null);
let cameraBlob: Blob | null = null;
const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB

const state = ref({
  contents: '',
  file: null as File | null
});

async function takeCameraPicture() {
  const photo = await camera.value?.takePhoto();
  if (!photo) return;

  cameraImage.value = photo.url;
  cameraBlob = photo.blob;
}

watch(
  () => state.value.file,
  (file) => {
    if (!file) return;

    if (file.size > MAX_FILE_SIZE) {
      alert('File must be smaller than 10MB');

      state.value.file = null;
    }
  }
);

const items = [
  {
    label: 'Text',
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
  },
  {
    label: 'Camera',
    description: 'Take photos of a physical mark scheme.',
    icon: 'i-lucide-camera',
    slot: 'camera' as const
  }
] satisfies TabsItem[];

const markingStore = useMarkingStore();
const { currentSession } = storeToRefs(markingStore);

const schema = z.object({
  contents: z.string().min(10, 'Please provide more detailed contents for the marking scheme.')
});

type Schema = z.output<typeof schema>;
const fileUploading = ref(false);
const toast = useToast();

function handleTextSubmit(event: FormSubmitEvent<Schema>) {
  if (!currentSession.value) return;

  markingStore.addMarkScheme({ contents: event.data.contents });
  resetAndClose();
}

async function handleFileSubmit() {
  if (!state.value.file || !currentSession.value) return;

  if (state.value.file.size > MAX_FILE_SIZE) {
    alert('File exceeds the 10MB limit');
    return;
  }
  fileUploading.value = true;
  try {
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
    toast.add({
      title: 'Error',
      description: 'Failed to add file. Please try again.',
      color: 'error'
    });
  } finally {
    fileUploading.value = false;
  }
}

function retryCamera() {
  if (cameraImage.value) {
    URL.revokeObjectURL(cameraImage.value);
  }

  cameraImage.value = null;
}

function saveCameraImage() {
  if (!cameraImage.value || !cameraBlob || !currentSession.value) return;

  const now = new Date().toISOString();

  const file: SessionFile = {
    id: crypto.randomUUID(),
    url: cameraImage.value,
    name: `markscheme-${Date.now()}.jpg`,
    storageUrl: '',
    size: cameraBlob.size,
    uploadedAt: now,
    blob: cameraBlob
  };

  markingStore.addMarkScheme({ file });

  resetAndClose();
}

function resetAndClose() {
  state.value = { contents: '', file: null };
  emit('close', false);
}
</script>
