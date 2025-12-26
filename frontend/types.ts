
export interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: number;
  isLoading?: boolean;
  runId?: string; // Track the backend run ID
  steps?: ProcessStep[]; // Thinking steps
  attachments?: FileAttachment[]; // User uploaded files
  generatedFiles?: string[]; // Backend generated files (charts, etc)
  feedback?: 'positive' | 'negative'; // User feedback
}

export interface Chat {
  id: string;
  title: string;
  messages: Message[];
  updatedAt: number;
}

export interface FileAttachment {
  name: string;
  type: string;
  size: number;
  data?: string; // Base64 for preview
  file?: File;   // Actual file object for upload
}

export interface StoredFile {
  id: string;
  name: string;
  size: number;
  type: string;
  uploadedAt: string;
  url?: string;
}

export interface StorageStats {
  used: number; // Bytes
  total: number; // Bytes
  fileCount: number;
}

export interface ProcessStep {
  step_id?: string;
  name: string;
  phase: string;
  status: 'pending' | 'in_progress' | 'completed' | 'failed' | 'cancelled';
  timestamp: string;
  message?: string;
}

export interface StepDetails {
  step_id: string;
  code?: string;
  prompt?: string;
  result?: string;
  metadata?: any;
}

export type Theme = 'light' | 'dark' | 'system';

export type ModelId = 'gemini-1.5-flash' | 'gemini-1.5-pro' | 'gemini-2.0-flash-exp';

export interface AppState {
  currentChatId: string | null;
  chats: Chat[];
  theme: Theme;
  sidebarOpen: boolean;
  selectedModel: ModelId;
}

export interface RunStartResponse {
  success: boolean;
  run_id: string;
  error?: string;
}

export interface RunStatusResponse {
  success: boolean;
  data: {
    status: 'starting' | 'in_progress' | 'completed' | 'failed' | 'cancelled';
    current_phase?: string;
  };
}

export interface RunStepsResponse {
  success: boolean;
  steps: ProcessStep[];
}

export interface RunResultsResponse {
  success: boolean;
  results: {
    output: string;
    files: string[];
    total_steps: number;
  };
}

// Auth Types
export interface User {
  id: string;
  email: string;
  username: string;
  avatar?: string;
}

export interface Dashboard {
  id: string;
  title: string;
  date: string;
  run_id: string;
  file_url: string;
}

export interface DashboardListResponse {
  success: boolean;
  dashboards: Dashboard[];
}
