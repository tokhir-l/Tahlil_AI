import React, { useState } from 'react';
import { api } from '../services/api';

interface SQLExportDialogProps {
    fileId: number;
    fileName: string;
    onClose: () => void;
}

export const SQLExportDialog: React.FC<SQLExportDialogProps> = ({
    fileId,
    fileName,
    onClose
}) => {
    const [config, setConfig] = useState({
        dialect: 'postgresql',
        database_name: 'tahlil_db',
        table_name: fileName.replace(/\.[^/.]+$/, '').replace(/[^a-zA-Z0-9_]/g, '_'), // Remove extension and sanitize
        schema_name: '',
        primary_key: '',
        indexes: '',
        include_database: true,
        include_schema: false,
        include_advanced_features: true, // Enable advanced features by default
        batch_size: 100
    });

    const [loading, setLoading] = useState(false);
    const [sqlScript, setSqlScript] = useState<string | null>(null);
    const [stats, setStats] = useState<any>(null);
    const [error, setError] = useState<string | null>(null);

    const handleGenerate = async () => {
        setLoading(true);
        setError(null);

        try {
            const response = await api.exportToSQL(fileId, {
                ...config,
                indexes: config.indexes ? config.indexes.split(',').map(s => s.trim()).filter(Boolean) : []
            });

            if (response.success && response.sql_script) {
                setSqlScript(response.sql_script);
                setStats(response.stats);
            } else {
                setError(response.error || 'Failed to generate SQL script');
            }
        } catch (error) {
            console.error('Failed to generate SQL:', error);
            setError('An error occurred while generating SQL script');
        } finally {
            setLoading(false);
        }
    };

    const handleDownload = () => {
        if (!sqlScript) return;

        const blob = new Blob([sqlScript], { type: 'application/sql' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${config.table_name}_${config.dialect}.sql`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    };

    const handleCopy = async () => {
        if (!sqlScript) return;

        try {
            await navigator.clipboard.writeText(sqlScript);
            alert('✅ SQL script copied to clipboard!');
        } catch (error) {
            console.error('Failed to copy:', error);
            alert('❌ Failed to copy to clipboard');
        }
    };

    return (
        <div className="modal-overlay" onClick={onClose}>
            <div className="sql-export-dialog" onClick={(e) => e.stopPropagation()}>
                <div className="dialog-header">
                    <h2>🗄️ Export to SQL</h2>
                    <button onClick={onClose} className="close-btn">✕</button>
                </div>

                <div className="dialog-body">
                    {!sqlScript ? (
                        <div className="config-form">
                            <div className="form-row">
                                <div className="form-group">
                                    <label>SQL Dialect *</label>
                                    <select
                                        value={config.dialect}
                                        onChange={(e) => setConfig({ ...config, dialect: e.target.value })}
                                    >
                                        <option value="postgresql">PostgreSQL</option>
                                        <option value="mysql">MySQL</option>
                                        <option value="sqlite">SQLite</option>
                                        <option value="sqlserver">SQL Server</option>
                                        <option value="oracle">Oracle</option>
                                    </select>
                                </div>

                                <div className="form-group">
                                    <label>Database Name *</label>
                                    <input
                                        type="text"
                                        value={config.database_name}
                                        onChange={(e) => setConfig({ ...config, database_name: e.target.value })}
                                        placeholder="tahlil_db"
                                    />
                                </div>
                            </div>

                            <div className="form-row">
                                <div className="form-group">
                                    <label>Table Name *</label>
                                    <input
                                        type="text"
                                        value={config.table_name}
                                        onChange={(e) => setConfig({ ...config, table_name: e.target.value })}
                                        placeholder="my_table"
                                    />
                                </div>

                                <div className="form-group">
                                    <label>Schema Name (optional)</label>
                                    <input
                                        type="text"
                                        value={config.schema_name}
                                        onChange={(e) => setConfig({ ...config, schema_name: e.target.value })}
                                        placeholder="public"
                                    />
                                </div>
                            </div>

                            <div className="form-row">
                                <div className="form-group">
                                    <label>Primary Key Column (optional)</label>
                                    <input
                                        type="text"
                                        value={config.primary_key}
                                        onChange={(e) => setConfig({ ...config, primary_key: e.target.value })}
                                        placeholder="id"
                                    />
                                </div>

                                <div className="form-group">
                                    <label>Index Columns (comma-separated)</label>
                                    <input
                                        type="text"
                                        value={config.indexes}
                                        onChange={(e) => setConfig({ ...config, indexes: e.target.value })}
                                        placeholder="email, created_at"
                                    />
                                </div>
                            </div>

                            <div className="checkbox-row">
                                <label className="checkbox-label">
                                    <input
                                        type="checkbox"
                                        checked={config.include_database}
                                        onChange={(e) => setConfig({ ...config, include_database: e.target.checked })}
                                    />
                                    <span>Include CREATE DATABASE statement</span>
                                </label>

                                <label className="checkbox-label">
                                    <input
                                        type="checkbox"
                                        checked={config.include_schema}
                                        onChange={(e) => setConfig({ ...config, include_schema: e.target.checked })}
                                    />
                                    <span>Include CREATE SCHEMA statement</span>
                                </label>

                                <label className="checkbox-label advanced-toggle">
                                    <input
                                        type="checkbox"
                                        checked={config.include_advanced_features}
                                        onChange={(e) => setConfig({ ...config, include_advanced_features: e.target.checked })}
                                    />
                                    <span>🚀 Enable Advanced Features</span>
                                    <small>Auto-detect: Foreign Keys, CHECK Constraints, Indexes, Validation Rules</small>
                                </label>
                            </div>

                            {error && (
                                <div className="error-message">
                                    ❌ {error}
                                </div>
                            )}

                            <button
                                onClick={handleGenerate}
                                disabled={loading || !config.database_name || !config.table_name}
                                className="generate-btn"
                            >
                                {loading ? '⚡ Generating...' : '⚡ Generate SQL Script'}
                            </button>
                        </div>
                    ) : (
                        <div className="sql-output">
                            <div className="output-header">
                                <div className="output-title">
                                    <h3>✅ SQL Script Generated</h3>
                                    {stats && (
                                        <div className="output-stats">
                                            <span>{stats.rows} rows</span>
                                            <span>•</span>
                                            <span>{stats.columns} columns</span>
                                            <span>•</span>
                                            <span>{(stats.script_size / 1024).toFixed(1)} KB</span>
                                        </div>
                                    )}
                                </div>

                                <div className="output-actions">
                                    <button onClick={handleDownload} className="action-btn download-btn">
                                        📥 Download
                                    </button>
                                    <button onClick={handleCopy} className="action-btn copy-btn">
                                        📋 Copy
                                    </button>
                                    <button onClick={() => setSqlScript(null)} className="action-btn back-btn">
                                        ← Back
                                    </button>
                                </div>
                            </div>

                            <div className="sql-preview">
                                <pre><code>{sqlScript}</code></pre>
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};
