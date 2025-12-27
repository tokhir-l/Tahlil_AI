
import React, { useEffect, useState } from 'react';
import { X, FileText, Trash2, HardDrive, AlertCircle, CheckCircle, Upload, Eye, Database, Link2 } from 'lucide-react';
import { StoredFile, StorageStats } from '../types';
import { api } from '../services/api';
import { SQLExportDialog } from './SQLExportDialog';
import DataSourceSelector from './DataSourceSelector';

interface FileManagerModalProps {
  isOpen: boolean;
  onClose: () => void;
}

const FileManagerModal: React.FC<FileManagerModalProps> = ({ isOpen, onClose }) => {
  const [files, setFiles] = useState<StoredFile[]>([]);
  const [stats, setStats] = useState<StorageStats>({ used: 0, total: 100, fileCount: 0 });
  const [isLoading, setIsLoading] = useState(true);
  const [exportingFile, setExportingFile] = useState<{ id: number; name: string } | null>(null);
  const [showDataSources, setShowDataSources] = useState(false);

  const loadData = async () => {
    setIsLoading(true);
    try {
      const [fetchedFiles, fetchedStats] = await Promise.all([
        api.getStoredFiles(),
        api.getStorageStats()
      ]);
      setFiles(fetchedFiles);
      setStats(fetchedStats);
    } catch (error) {
      console.error("Failed to load files", error);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen) {
      loadData();
    }
  }, [isOpen]);

  const handleDelete = async (id: string) => {
    if (confirm('Are you sure you want to delete this file? It will be removed from future analyses.')) {
      try {
        await api.deleteFile(id);
        await loadData(); // Refresh
      } catch (error) {
        console.error("Delete failed", error);
      }
    }
  };

  const formatBytes = (bytes: number) => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
  };

  const handleFileImported = () => {
    loadData(); // Refresh file list
    setShowDataSources(false);
  };

  if (!isOpen) return null;

  const usedPercent = (stats.used / stats.total) * 100;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="bg-background w-full max-w-2xl rounded-xl border border-border shadow-2xl overflow-hidden animate-in zoom-in-95 duration-200 flex flex-col max-h-[80vh]">

        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-border bg-primary/30">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-orange-500/10 rounded-lg text-orange-500">
              <HardDrive size={20} />
            </div>
            <div>
              <h2 className="text-lg font-semibold">File Manager</h2>
              <p className="text-xs text-gray-500">Manage your dataset storage</p>
            </div>
          </div>
          <button onClick={onClose} className="p-1 hover:bg-secondary rounded-lg transition-colors">
            <X size={20} />
          </button>
        </div>

        {/* Storage Bar */}
        <div className="px-6 py-4 border-b border-border bg-background">
          <div className="flex justify-between text-sm mb-2">
            <span className="font-medium">Storage Usage</span>
            <span className="text-gray-500">{formatBytes(stats.used)} used of {formatBytes(stats.total)}</span>
          </div>
          <div className="h-2 w-full bg-secondary rounded-full overflow-hidden">
            <div
              className={`h-full rounded-full transition-all duration-500 ${usedPercent > 90 ? 'bg-red-500' : 'bg-orange-500'}`}
              style={{ width: `${usedPercent}%` }}
            />
          </div>
          <div className="flex justify-between items-center mt-2">
            <p className="text-xs text-gray-400 flex items-center gap-1">
              <AlertCircle size={12} />
              Files are automatically deleted after 30 days to save space.
            </p>
            <button
              onClick={() => setShowDataSources(!showDataSources)}
              className={`text-xs px-3 py-1.5 rounded-lg flex items-center gap-1.5 transition-colors ${showDataSources
                  ? 'bg-blue-500 text-white'
                  : 'bg-secondary text-gray-400 hover:text-white hover:bg-blue-500/20'
                }`}
            >
              <Link2 size={14} />
              {showDataSources ? 'Hide Sources' : 'Add from Link'}
            </button>
          </div>
        </div>

        {/* Data Source Selector (Collapsible) */}
        {showDataSources && (
          <div className="px-6 py-4 border-b border-border bg-secondary/30">
            <DataSourceSelector onFileImported={handleFileImported} />
          </div>
        )}

        {/* File List */}
        <div className="flex-1 overflow-y-auto p-4 space-y-2 bg-secondary/20">
          {isLoading ? (
            <div className="flex justify-center py-10 text-gray-400">Loading files...</div>
          ) : files.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-16 text-gray-400">
              <HardDrive size={48} className="mb-4 opacity-20" />
              <p>No files stored</p>
            </div>
          ) : (
            files.map(file => (
              <div key={file.id} className="flex items-center justify-between p-3 bg-background border border-border rounded-lg hover:border-orange-500/30 transition-all group">
                <div className="flex items-center gap-3 overflow-hidden">
                  <div className="p-2 bg-secondary rounded text-gray-500">
                    <FileText size={18} />
                  </div>
                  <div className="min-w-0">
                    <h4 className="font-medium text-sm truncate max-w-[200px] md:max-w-[300px]">{file.name}</h4>
                    <div className="flex items-center gap-2 text-xs text-gray-400">
                      <span>{formatBytes(file.size)}</span>
                      <span>•</span>
                      <span>{new Date(file.uploadedAt).toLocaleDateString()}</span>
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                  <button
                    onClick={() => setExportingFile({ id: parseInt(file.id), name: file.name })}
                    className="p-2 text-gray-400 hover:text-blue-500 hover:bg-blue-500/10 rounded-lg transition-colors"
                    title="Export to SQL"
                  >
                    <Database size={16} />
                  </button>
                  <button
                    onClick={() => handleDelete(file.id)}
                    className="p-2 text-gray-400 hover:text-red-500 hover:bg-red-500/10 rounded-lg transition-colors"
                    title="Delete file"
                  >
                    <Trash2 size={16} />
                  </button>
                </div>
              </div>
            ))
          )}
        </div>

        <div className="bg-background px-6 py-4 border-t border-border flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-secondary text-foreground rounded-lg text-sm font-medium hover:bg-secondary/80 transition-opacity"
          >
            Close
          </button>
        </div>
      </div>

      {/* SQL Export Dialog */}
      {exportingFile && (
        <SQLExportDialog
          fileId={exportingFile.id}
          fileName={exportingFile.name}
          onClose={() => setExportingFile(null)}
        />
      )}
    </div>
  );
};

export default FileManagerModal;
