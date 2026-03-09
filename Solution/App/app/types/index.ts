export interface UserProfile {
  userId: string;
  username: string;
  name: string;
  instituteCode: string;
  createdAt: string;
  updatedAt: string;
}

export interface Institute {
  code: string;
  name: string;
}

export interface Credentials {
  username: string;
  password: string;
  institute_code: string;
}

// A placeholder for the password change form
export type PasswordUpdate = any;

// Marking Sessions

export interface MarkingFeedback {
  feedbackId: string;
  sessionId: string;
  studentNo: number;
  type: string;
  teacherComments?: string;
  isSelected: boolean;
  confidence: number;
  description: string;
  createdAt: string;
  updatedAt: string;
}

export interface SessionFile {
  id: string;
  url: string;
  name: string;
  storageUrl: string;
  deletedAt?: string;
  size: number;
  uploadedAt: string;
}

export interface StudentSubmission {
  id: string;
  sessionId: string;
  studentNo: number;
  pages: {
    pageNo: number;
    file?: SessionFile;
  }[];
  contents?: string; // Place for when all pages have been converted to text.
  feedback?: MarkingFeedback[];
  createdAt: string;
  updatedAt: string;
}

export interface MarkScheme {
  id: string;
  sessionId: string;
  file?: SessionFile;
  contents?: string; // For text-based mark schemes or once the file has been converted
  createdAt: string;
  updatedAt: string;
}

export interface MarkingSession {
  sessionId: string | null;
  year: number;
  studentsAmount: number;
  requiredOutputs: string[];
  notes: string;
  status: 'pending' | 'processing' | 'completed' | 'error';
  markshemes: MarkScheme[];
  studentSubmissions: StudentSubmission[];
  createdAt: string;
  updatedAt: string;
}

// ^ Marking Sessions

export interface AppUpdate {
  id: string;
  type: 'MarkingSessionUpdate' | 'NewFeature' | 'SystemMessage';
  title: string;
  message: string;
  timestamp: string;
  isRead: boolean;
  link?: string;
  relatedId?: string;
}
