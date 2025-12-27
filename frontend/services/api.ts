
import { FileAttachment, RunStartResponse, RunStatusResponse, RunResultsResponse, RunStepsResponse, StorageStats, StoredFile, StepDetails } from '../types';

const API_BASE = '/api'; // Assumes proxy or relative path to Flask server

// Mock storage for demo purposes (In real app, this comes from backend DB)
let mockStorageUsed = 45 * 1024 * 1024; // 45 MB used
const mockStorageLimit = 100 * 1024 * 1024; // 100 MB limit

export const api = {
  /**
   * Uploads files to the backend
   */
  uploadFiles: async (files: FileAttachment[]): Promise<string[]> => {
    const fileIds: string[] = [];

    for (const fileObj of files) {
      if (!fileObj.file) continue;

      const formData = new FormData();
      formData.append('file', fileObj.file);
      formData.append('user_id', 'default'); // TODO: Implement user sessions

      try {
        const response = await fetch(`${API_BASE}/data/upload`, {
          method: 'POST',
          body: formData,
        });

        if (!response.ok) throw new Error(`Upload failed for ${fileObj.name}`);

        const data = await response.json();
        if (data.success && data.file?.id) {
          fileIds.push(data.file.id);
          // Update mock storage
          mockStorageUsed += fileObj.size;
        }
      } catch (error) {
        console.error('File upload error:', error);
        throw error;
      }
    }

    return fileIds;
  },

  /**
   * Starts a new analysis run
   */
  startRun: async (query: string, fileIds: string[], model: string): Promise<string> => {
    try {
      const response = await fetch(`${API_BASE}/run/start`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query,
          file_ids: fileIds,
          model,
          user_id: 'default'
        }),
      });

      const data: RunStartResponse = await response.json();
      if (!data.success || !data.run_id) {
        throw new Error(data.error || 'Failed to start analysis');
      }

      return data.run_id;
    } catch (error) {
      console.error('Start run error:', error);
      throw error;
    }
  },

  /**
   * Polls the status of a run
   */
  getRunStatus: async (runId: string): Promise<RunStatusResponse['data']> => {
    const response = await fetch(`${API_BASE}/run/${runId}/status`);
    const data: RunStatusResponse = await response.json();
    return data.data;
  },

  /**
   * Cancels an active run
   */
  cancelRun: async (runId: string): Promise<void> => {
    try {
      await fetch(`${API_BASE}/run/${runId}/cancel`, {
        method: 'POST'
      });
    } catch (error) {
      console.error('Cancel run error:', error);
    }
  },

  /**
   * Gets the intermediate steps
   */
  getRunSteps: async (runId: string): Promise<RunStepsResponse['steps']> => {
    try {
      const response = await fetch(`${API_BASE}/run/${runId}/steps`);
      const data: RunStepsResponse = await response.json();
      // Backend now returns steps in the correct ProcessStep format
      return data.steps || [];
    } catch (e) {
      console.error('Error fetching steps:', e);
      return [];
    }
  },

  /**
   * Gets the final results
   */
  getRunResults: async (runId: string): Promise<RunResultsResponse['results']> => {
    const response = await fetch(`${API_BASE}/run/${runId}/results`);
    const data: RunResultsResponse = await response.json();
    return data.results;
  },

  /**
   * Submits user feedback
   */
  submitFeedback: async (runId: string | undefined, messageId: string, rating: 'positive' | 'negative'): Promise<void> => {
    try {
      await fetch(`${API_BASE}/feedback`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          run_id: runId,
          message_id: messageId,
          rating,
          timestamp: new Date().toISOString()
        }),
      });
    } catch (error) {
      console.warn('Feedback submission failed (backend might not support it yet):', error);
      // Fail silently for UI responsiveness
    }
  },

  /**
   * Get Storage Statistics
   */
  getStorageStats: async (): Promise<StorageStats> => {
    // In a real app, fetch from backend: GET /api/storage/stats
    // return (await fetch(`${API_BASE}/storage/stats`)).json();

    return new Promise(resolve => {
      setTimeout(() => {
        resolve({
          used: mockStorageUsed,
          total: mockStorageLimit,
          fileCount: Math.floor(mockStorageUsed / 1024 / 1024 * 0.5) // Approximate count
        });
      }, 500);
    });
  },

  /**
   * List uploaded files
   */
  getStoredFiles: async (): Promise<StoredFile[]> => {
    // Mock data
    return [
      { id: '1', name: 'sales_data_2023.csv', size: 1024 * 1024 * 5, type: 'text/csv', uploadedAt: new Date().toISOString() },
      { id: '2', name: 'customer_churn.parquet', size: 1024 * 1024 * 15, type: 'application/octet-stream', uploadedAt: new Date(Date.now() - 86400000).toISOString() },
      { id: '3', name: 'report.pdf', size: 1024 * 500, type: 'application/pdf', uploadedAt: new Date(Date.now() - 172800000).toISOString() }
    ];
  },

  /**
   * Delete a file
   */
  deleteFile: async (fileId: string): Promise<void> => {
    // await fetch(`${API_BASE}/storage/files/${fileId}`, { method: 'DELETE' });
    console.log(`Deleted file ${fileId}`);
    mockStorageUsed -= 1024 * 1024 * 5; // Mock reduction
  },

  /**
   * Get detailed information for a specific step
   */
  getStepDetails: async (runId: string, stepId: string): Promise<StepDetails> => {
    try {
      const response = await fetch(`${API_BASE}/run/${runId}/step/${stepId}/details`);
      const data = await response.json();
      if (!data.success) {
        throw new Error(data.error || 'Failed to get step details');
      }
      return data.details;
    } catch (error) {
      console.error('Get step details error:', error);
      throw error;
    }
  },

  /**
   * Helper to construct file download URL
   */
  getFileUrl: (runId: string, filename: string) => {
    return `${API_BASE}/run/${runId}/file/${encodeURIComponent(filename)}`;
  },

  /**
   * Export file to SQL script
   */
  exportToSQL: async (fileId: number, config: {
    dialect?: string;
    database_name?: string;
    table_name?: string;
    schema_name?: string;
    primary_key?: string;
    indexes?: string[];
    include_database?: boolean;
    include_schema?: boolean;
    include_advanced_features?: boolean;
    batch_size?: number;
  }): Promise<{
    success: boolean;
    sql_script?: string;
    filename?: string;
    download_url?: string;
    stats?: {
      rows: number;
      columns: number;
      script_size: number;
      dialect: string;
    };
    error?: string;
  }> => {
    try {
      const response = await fetch(`${API_BASE}/data/export-sql/${fileId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(config),
      });

      const data = await response.json();
      return data;
    } catch (error) {
      console.error('Export to SQL error:', error);
      return { success: false, error: String(error) };
    }
  },

  /**
   * Download SQL file
   */
  downloadSQLFile: (filename: string) => {
    const url = `${API_BASE}/data/download-sql/${encodeURIComponent(filename)}`;
    window.location.href = url;
  },

  /**
   * Get list of generated dashboards
   */
  getDashboards: async (): Promise<import('../types').Dashboard[]> => {
    try {
      const response = await fetch(`${API_BASE}/dashboards/list`);
      const data = await response.json();
      return data.dashboards || [];
    } catch (e) {
      console.error('Error fetching dashboards:', e);
      return [];
    }
  },

  /**
   * Fetch data from external link (Google Sheets, etc.)
   */
  fetchFromLink: async (url: string, options?: {
    worksheet_name?: string;
    user_id?: string;
  }): Promise<{
    success: boolean;
    file?: {
      id: number;
      name: string;
      size: number;
      source_url: string;
      source_type: string;
    };
    preview?: Record<string, any>[];
    metadata?: Record<string, any>;
    error?: string;
  }> => {
    try {
      const response = await fetch(`${API_BASE}/data/from-link`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          url,
          ...options
        }),
      });
      return await response.json();
    } catch (error) {
      console.error('Fetch from link error:', error);
      return { success: false, error: String(error) };
    }
  },

  /**
   * Get list of supported data sources
   */
  getDataSources: async (): Promise<{
    success: boolean;
    sources?: Array<{
      name: string;
      id: string;
      status: 'available' | 'coming_soon';
      requires_auth: boolean;
      icon: string;
      description: string;
    }>;
  }> => {
    try {
      const response = await fetch(`${API_BASE}/data/sources`);
      return await response.json();
    } catch (error) {
      console.error('Get data sources error:', error);
      return { success: false };
    }
  },

  /**
   * Fetch data from external REST API
   */
  fetchFromApi: async (config: {
    url: string;
    method?: 'GET' | 'POST';
    auth_type?: 'none' | 'api_key' | 'bearer' | 'basic';
    auth_config?: Record<string, string>;
    headers?: Record<string, string>;
    params?: Record<string, string>;
    body?: Record<string, any>;
    json_path?: string;
  }): Promise<{
    success: boolean;
    file?: {
      id: number;
      name: string;
      size: number;
      source_url: string;
      source_type: string;
    };
    preview?: Record<string, any>[];
    metadata?: Record<string, any>;
    error?: string;
  }> => {
    try {
      const response = await fetch(`${API_BASE}/data/from-api`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(config),
      });
      return await response.json();
    } catch (error) {
      console.error('Fetch from API error:', error);
      return { success: false, error: String(error) };
    }
  },

  /**
   * Get supported authentication types for APIs
   */
  getAuthTypes: async (): Promise<{
    success: boolean;
    auth_types?: Array<{
      id: string;
      name: string;
      description: string;
    }>;
  }> => {
    try {
      const response = await fetch(`${API_BASE}/data/auth-types`);
      return await response.json();
    } catch (error) {
      console.error('Get auth types error:', error);
      return { success: false };
    }
  }
};
