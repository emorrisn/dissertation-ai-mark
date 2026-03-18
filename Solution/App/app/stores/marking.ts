import { defineStore } from 'pinia';
import type { MarkingSession, MarkScheme, SessionFile } from '~/types';

export const useMarkingStore = defineStore('marking', {
  state: () => ({
    sessions: [] as MarkingSession[],
    currentSession: null as MarkingSession | null,
    status: 'idle' as 'idle' | 'loading' | 'succeeded' | 'failed'
  }),

  actions: {
    /**
     * Initializes a new, blank marking session in the state.
     * This can be used to bind to a "create new session" form before saving.
     */
    initializeNewSession() {
      const now = new Date().toISOString();
      this.currentSession = {
        id: 'new',
        year: 7,
        selectedStudent: 1,
        studentsAmount: 34,
        requiredOutputs: [],
        notes: '',
        stage: 'Conversion Pending',
        status: 'pending',
        createdAt: now,
        updatedAt: now,
        markshemes: [],
        studentSubmissions: []
      };
    },

    async createSession(): Promise<MarkingSession | undefined> {
      if (!this.currentSession) return;

      const session = this.currentSession;
      const formData = new FormData();

      formData.append('year', String(session.year));
      formData.append('studentsAmount', String(session.studentsAmount));
      formData.append('notes', session.notes);

      session.requiredOutputs.forEach((o) => formData.append('requiredOutputs[]', o));

      for (const [i, scheme] of session.markshemes.entries()) {
        if (scheme.contents) {
          formData.append(`markschemes[${i}][contents]`, scheme.contents);
        }

        if (scheme.file) {
          if (scheme.file.blob) {
            formData.append(`markschemes[${i}][file]`, scheme.file.blob, scheme.file.name);
          } else {
            // fallback for uploaded files
            const blob = await fetch(scheme.file.url).then((r) => r.blob());

            formData.append(`markschemes[${i}][file]`, blob, scheme.file.name);
          }
        }
      }

      const { $api } = useNuxtApp();
      const result: MarkingSession = await $api('/marking/start', {
        method: 'POST',
        body: formData
      });

      this.currentSession.id = result.id;

      window.dispatchEvent(new Event('session-updated'));

      return result;
    },

    incrementSelectedStudent() {
      if (!this.currentSession) return;
      if (this.currentSession.selectedStudent < this.currentSession.studentsAmount) {
        this.currentSession.selectedStudent += 1;
      }
    },

    setCurrentSession(session: MarkingSession) {
      this.currentSession = session;
    },

    addMarkScheme(scheme: { contents?: string; file?: SessionFile }) {
      if (!this.currentSession) return;

      const now = new Date().toISOString();
      const newMarkScheme: MarkScheme = {
        id: crypto.randomUUID(), // Temporary client-side ID
        sessionId: this.currentSession.id || '', // Use empty string if id is null
        contents: scheme.contents,
        file: scheme.file,
        createdAt: now,
        updatedAt: now
      };
      this.currentSession.markshemes.push(newMarkScheme);
    },

    async addStudentSubmission(sessionId: string, studentNo: number, files: Blob[]) {
      this.status = 'loading';

      const formData = new FormData();
      // Append the session ID to the form data here
      formData.append('sessionId', sessionId);
      formData.append('studentNo', String(studentNo));

      // Append each file to the form data
      files.forEach((blob, index) => {
        formData.append(`pages[${index}]`, blob, `page_${index + 1}.jpg`);
      });

      try {
        const { $api } = useNuxtApp();

        // Pointing to the new route without the ID in the URL
        const response: any = await $api('/marking/submission', {
          method: 'POST',
          body: formData
        });

        if (this.currentSession) {
          // Update the session's current student based on backend source of truth
          this.currentSession.selectedStudent = response.nextStudent;

          // Expand the max students amount if we bypassed it
          if (response.nextStudent > this.currentSession.studentsAmount) {
            this.currentSession.studentsAmount = response.nextStudent;
          }

          // Update or push the new submission into the local state
          const existingIndex = this.currentSession.studentSubmissions.findIndex((s) => s.studentNo === studentNo);

          if (existingIndex !== -1) {
            this.currentSession.studentSubmissions[existingIndex] = response.submission;
          } else {
            this.currentSession.studentSubmissions.push(response.submission);
          }
        }

        this.status = 'succeeded';
        window.dispatchEvent(new Event('session-updated'));
        return response;
      } catch (error) {
        this.status = 'failed';
        console.error('Failed to submit student work:', error);
        throw error;
      }
    },

    removeMarkScheme(id: string) {
      if (!this.currentSession) return;
      const index = this.currentSession.markshemes.findIndex((scheme) => scheme.id === id);
      if (index !== -1) this.currentSession.markshemes.splice(index, 1);
    },

    async fetchSessions() {
      this.status = 'loading';

      try {
        const { $api } = useNuxtApp();

        const sessions: MarkingSession[] = await $api('/marking/sessions', {
          method: 'GET'
        });

        // ensure arrays exist
        this.sessions = sessions
          .map((s) => ({
            ...s,
            markshemes: s.markshemes ?? [],
            studentSubmissions: s.studentSubmissions ?? []
          }))
          .sort((a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime());

        this.status = 'succeeded';
      } catch (error) {
        this.status = 'failed';
        console.error('Failed to fetch marking sessions:', error);
      }
    },

    async finishSession(sessionId: string) {
      this.status = 'loading';

      try {
        const { $api } = useNuxtApp();
        const response: any = await $api('/marking/finish', {
          method: 'POST',
          body: { sessionId } // Sending as JSON payload
        });

        // Update the current session status locally
        if (this.currentSession && this.currentSession.id === sessionId) {
          this.currentSession.status = 'pending';
          this.currentSession.updatedAt = response.session.updatedAt;
        }

        // Also update it in the sessions list if it's there
        const sessionInList = this.sessions.find((s) => s.id === sessionId);
        if (sessionInList) {
          sessionInList.status = 'pending';
        }

        this.status = 'succeeded';
        window.dispatchEvent(new Event('session-updated'));

        return response;
      } catch (error) {
        this.status = 'failed';
        console.error('Failed to finish marking session:', error);
        throw error;
      }
    },

    async selectFeedbackOption(submissionId: string, feedbackId: string | null) {
      try {
        const { $api } = useNuxtApp();

        // Adjust the endpoint URL to match your Flask backend
        const response = await $api('/marking/select-feedback', {
          method: 'POST',
          body: {
            submissionId,
            feedbackId
          }
        });

        return response;
      } catch (error) {
        console.error('Failed to update selected feedback on the server:', error);
        throw error;
      }
    }
  }
});
