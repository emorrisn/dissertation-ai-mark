import { defineStore } from 'pinia';
import type { MarkingSession, MarkScheme, SessionFile, StudentSubmission } from '~/types';

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
        status: 'pending',
        createdAt: now,
        updatedAt: now,
        markshemes: [],
        studentSubmissions: []
      };
    },

    async createSession() {
      if (!this.currentSession) return;

      const formData = new FormData();

      formData.append('year', String(this.currentSession.year));
      formData.append('studentsAmount', String(this.currentSession.studentsAmount));
      formData.append('notes', this.currentSession.notes);

      this.currentSession.requiredOutputs.forEach((o) => formData.append('requiredOutputs[]', o));

      this.currentSession.markshemes.forEach(async (scheme, i) => {
        if (scheme.contents) {
          formData.append(`markschemes[${i}][contents]`, scheme.contents);
        }

        if (scheme.file) {
          const blob = await fetch(scheme.file.url).then((r) => r.blob());

          formData.append(`markschemes[${i}][file]`, blob, scheme.file.name);
        }
      });

      const session = await $fetch('/api/marking', {
        method: 'POST',
        body: formData
      });

      this.currentSession = session;

      return session;
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

    removeMarkScheme(id: string) {
      if (!this.currentSession) return;
      const index = this.currentSession.markshemes.findIndex((scheme) => scheme.id === id);
      if (index !== -1) this.currentSession.markshemes.splice(index, 1);
    },

    addStudentSubmission(submission: StudentSubmission) {
      if (!this.currentSession) return;

      const existingIndex = this.currentSession.studentSubmissions.findIndex(
        (s) => s.studentNo === submission.studentNo
      );

      if (existingIndex !== -1) {
        this.currentSession.studentSubmissions[existingIndex] = submission;
      } else {
        this.currentSession.studentSubmissions.push(submission);
      }
    },

    async fetchSessions() {
      this.status = 'loading';
      try {
        // API call to get all marking sessions for the user
        // const sessions = await $fetch('/api/marking-sessions');
        // this.sessions = sessions;

        await new Promise((resolve) => setTimeout(resolve, 1000)); // Simulate network delay

        // Mock data for now
        const mockSessions: MarkingSession[] = [
          {
            id: 'session-1',
            year: 2024,
            studentsAmount: 28,
            selectedStudent: 28,
            requiredOutputs: ['exam_paper'],
            notes: 'Year 11 History GCSE Mock Papers. Focus on source analysis.',
            status: 'completed',
            createdAt: new Date(Date.now() - 1000 * 60 * 60 * 24 * 10).toISOString(), // 10 days ago
            updatedAt: new Date(Date.now() - 1000 * 60 * 60 * 24 * 3).toISOString(), // 3 days ago
            markshemes: [],
            studentSubmissions: []
          },
          {
            id: 'session-2',
            year: 2024,
            studentsAmount: 22,
            selectedStudent: 28,
            requiredOutputs: ['coursework', 'report'],
            notes: 'Year 13 A-Level Computer Science coursework submissions.',
            status: 'processing',
            createdAt: new Date(Date.now() - 1000 * 60 * 60 * 24 * 2).toISOString(), // 2 days ago
            updatedAt: new Date(Date.now() - 1000 * 60 * 45).toISOString(), // 45 minutes ago
            markshemes: [],
            studentSubmissions: []
          }
        ];
        this.sessions = mockSessions.sort((a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime());
        this.status = 'succeeded';
      } catch (error) {
        this.status = 'failed';
        console.error('Failed to fetch marking sessions:', error);
      }
    },

    async fetchSession(id: string) {
      // API call to get a single session's details, including results
      // const session = await $fetch(`/api/marking-sessions/${id}`);
      // this.currentSession = session;
    },

    async checkSessionStatus(id: string) {
      // Action to poll the API for the status of a processing job.
    }
  }
});
