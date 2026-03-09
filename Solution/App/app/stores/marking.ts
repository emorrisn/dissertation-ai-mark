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
        sessionId: "new",
        year: 7,
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

    setCurrentSession(session: MarkingSession) {
      this.currentSession = session;
    },

    addMarkScheme(scheme: { contents?: string; file?: SessionFile }) {
      if (!this.currentSession) return;

      const now = new Date().toISOString();
      const newMarkScheme: MarkScheme = {
        id: crypto.randomUUID(), // Temporary client-side ID
        sessionId: this.currentSession.sessionId || '', // Use empty string if sessionId is null
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
            sessionId: 'session-1',
            year: 2024,
            studentsAmount: 28,
            requiredOutputs: ['exam_paper'],
            notes: 'Year 11 History GCSE Mock Papers. Focus on source analysis.',
            status: 'completed',
            createdAt: new Date(Date.now() - 1000 * 60 * 60 * 24 * 10).toISOString(), // 10 days ago
            updatedAt: new Date(Date.now() - 1000 * 60 * 60 * 24 * 3).toISOString(), // 3 days ago
            markshemes: [],
            studentSubmissions: []
          },
          {
            sessionId: 'session-2',
            year: 2024,
            studentsAmount: 22,
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

    async createSession(formData: FormData) {
      // API call to upload files and start a new marking session.
      // The Flask API will trigger the workers.
    },

    async checkSessionStatus(id: string) {
      // Action to poll the API for the status of a processing job.
    }
  }
});
