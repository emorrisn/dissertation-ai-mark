<template>
  <div class="w-full max-w-xl mx-auto p-4">
    <UForm :schema="schema" :state="state" class="space-y-4" @submit="onSubmit">
      <UFormField name="year" label="Academic Year">
        <USelectMenu v-model="state.year" class="w-full" :items="yearOptions" placeholder="Select Year" />
      </UFormField>

      <UFormField name="students" label="Student Count">
        <USelectMenu v-model="state.students" class="w-full" :items="studentOptions" placeholder="32 Students" />
      </UFormField>

      <UFormField name="action" label="Action Type">
        <USelectMenu
          v-model="state.action"
          class="w-full"
          :items="actionOptions"
          multiple
          placeholder="Give Feedback, Score Work..."
        />
      </UFormField>

      <UFormField name="notes" label="Additional Notes">
        <UTextarea v-model="state.notes" class="w-full" placeholder="Notes" :rows="4" resize />
      </UFormField>

      <div class="flex justify-start pt-2 gap-3">
        <UButton type="submit" color="primary" size="lg"> Continue </UButton>
      </div>
    </UForm>
  </div>
</template>

<script setup lang="ts">
import { reactive } from 'vue';
import { z } from 'zod';
import type { FormSubmitEvent } from '#ui/types';

const emit = defineEmits(['success']);

const yearOptions = Array.from({ length: 7 }, (_, index) => `Year ${index + 7}`);
const studentOptions = Array.from({ length: 50 }, (_, index) => {
  const count = index + 1;
  return `${count} Student${count === 1 ? '' : 's'}`;
});

const actionOptions = ['Give Feedback', 'Score Work', 'Section by Section', 'What to write'];
const markingStore = useMarkingStore();

// 2. Define the Zod Validation Schema
const schema = z.object({
  year: z.string({ message: 'Please select an academic year.' }),
  students: z.string({ message: 'Please select the student count.' }),
  action: z.array(z.string(), { message: 'Please select at least one action type.' }).min(1),
  // Notes are usually optional, so we use .optional()
  notes: z.string().optional()
});

// Extract the inferred TypeScript type from the Zod schema
type Schema = z.output<typeof schema>;

// 3. Initialize the Reactive Form State
const state = reactive<Partial<Schema>>({
  year: markingStore.currentSession ? `Year ${markingStore.currentSession.year}` : undefined,
  students: markingStore.currentSession ? `${markingStore.currentSession.studentsAmount} Students` : undefined,
  action: markingStore.currentSession ? markingStore.currentSession.requiredOutputs : undefined,
  notes: markingStore.currentSession ? markingStore.currentSession.notes : undefined
});

// 4. Handle Submission
async function onSubmit(event: FormSubmitEvent<Schema>) {
  if (!markingStore.currentSession) return;
  markingStore.setCurrentSession({
    ...markingStore.currentSession,
    year: parseInt(event.data.year.replace('Year ', '')),
    studentsAmount: parseInt(event.data.students.replace(' Students', '').replace(' Student', '')),
    requiredOutputs: event.data.action,
    notes: event.data.notes || 'No Notes'
  });
  emit('success', event.data);
}
</script>
