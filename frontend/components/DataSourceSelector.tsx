
import React, { useState } from 'react';
import { Link2, Loader2, CheckCircle, AlertCircle, ExternalLink, FileSpreadsheet } from 'lucide-react';
import { api } from '../services/api';

interface DataSourceSelectorProps {
    onFileImported?: (fileInfo: { id: number; name: string; source: string }) => void;
    onClose?: () => void;
}

const DataSourceSelector: React.FC<DataSourceSelectorProps> = ({ onFileImported, onClose }) => {
    // Spreadsheet state
    const [sheetUrl, setSheetUrl] = useState('');
    const [sheetLoading, setSheetLoading] = useState(false);

    // Shared state
    const [success, setSuccess] = useState<string | null>(null);
    const [error, setError] = useState<string | null>(null);

    const clearMessages = () => {
        setError(null);
        setSuccess(null);
    };

    // Spreadsheet import
    const handleFetchSheet = async () => {
        if (!sheetUrl.trim()) {
            setError('Please enter a URL');
            return;
        }

        setSheetLoading(true);
        clearMessages();

        try {
            const result = await api.fetchFromLink(sheetUrl);

            if (result.success && result.file) {
                setSuccess(`✅ Imported "${result.file.name}" (${result.metadata?.rows || 0} rows)`);
                setSheetUrl('');
                onFileImported?.({ id: result.file.id, name: result.file.name, source: 'spreadsheet' });
            } else {
                setError(result.error || 'Failed to fetch spreadsheet');
            }
        } catch (err) {
            setError('Connection failed. Check URL and try again.');
        } finally {
            setSheetLoading(false);
        }
    };

    const inputStyle: React.CSSProperties = {
        width: '100%',
        padding: '10px 12px',
        background: 'var(--bg-primary, #1a1a1a)',
        border: '1px solid rgba(75, 85, 99, 0.3)',
        borderRadius: '8px',
        color: 'inherit',
        fontSize: '13px',
        outline: 'none'
    };

    const buttonStyle = (loading: boolean, disabled: boolean): React.CSSProperties => ({
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        gap: '6px',
        padding: '10px 18px',
        background: loading || disabled ? 'rgba(59, 130, 246, 0.3)' : 'linear-gradient(135deg, #3b82f6, #2563eb)',
        color: 'white',
        border: 'none',
        borderRadius: '8px',
        fontSize: '13px',
        fontWeight: 500,
        cursor: loading || disabled ? 'not-allowed' : 'pointer',
        opacity: loading || disabled ? 0.6 : 1,
        transition: 'all 0.2s ease',
        minWidth: '100px'
    });

    return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            {/* Header */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                <div style={{
                    width: '40px', height: '40px', borderRadius: '10px',
                    background: 'linear-gradient(135deg, #22c55e, #16a34a)',
                    display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'white'
                }}>
                    <FileSpreadsheet size={20} />
                </div>
                <div>
                    <h3 style={{ margin: 0, fontSize: '16px', fontWeight: 600 }}>Import from Google Sheets</h3>
                    <p style={{ margin: 0, fontSize: '12px', color: '#9ca3af' }}>Paste a link to import data</p>
                </div>
            </div>

            {/* Spreadsheet Form */}
            <div style={{
                background: 'rgba(34, 197, 94, 0.05)', border: '1px solid rgba(34, 197, 94, 0.15)',
                borderRadius: '12px', padding: '14px'
            }}>
                <label style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '12px', fontWeight: 500, color: '#9ca3af', marginBottom: '10px' }}>
                    <Link2 size={14} />
                    Google Sheets URL
                </label>
                <div style={{ display: 'flex', gap: '8px' }}>
                    <input
                        type="url"
                        value={sheetUrl}
                        onChange={(e) => { setSheetUrl(e.target.value); clearMessages(); }}
                        placeholder="https://docs.google.com/spreadsheets/d/..."
                        disabled={sheetLoading}
                        onKeyDown={(e) => e.key === 'Enter' && handleFetchSheet()}
                        style={inputStyle}
                    />
                    <button onClick={handleFetchSheet} disabled={!sheetUrl.trim() || sheetLoading} style={buttonStyle(sheetLoading, !sheetUrl.trim())}>
                        {sheetLoading ? <Loader2 size={16} className="animate-spin" /> : <><ExternalLink size={14} /> Import</>}
                    </button>
                </div>
                <p style={{ margin: '10px 0 0', fontSize: '11px', color: '#9ca3af', padding: '8px', background: 'rgba(34, 197, 94, 0.08)', borderRadius: '6px', borderLeft: '3px solid #22c55e' }}>
                    💡 Set sheet to <strong style={{ color: '#d1d5db' }}>"Anyone with the link"</strong> for access
                </p>
            </div>

            {/* Status Messages */}
            {error && (
                <div style={{
                    display: 'flex', alignItems: 'center', gap: '8px', padding: '10px',
                    background: 'rgba(239, 68, 68, 0.1)', border: '1px solid rgba(239, 68, 68, 0.2)',
                    borderRadius: '8px', fontSize: '12px', color: '#f87171'
                }}>
                    <AlertCircle size={14} /> {error}
                </div>
            )}
            {success && (
                <div style={{
                    display: 'flex', alignItems: 'center', gap: '8px', padding: '10px',
                    background: 'rgba(34, 197, 94, 0.1)', border: '1px solid rgba(34, 197, 94, 0.2)',
                    borderRadius: '8px', fontSize: '12px', color: '#4ade80'
                }}>
                    <CheckCircle size={14} /> {success}
                </div>
            )}
        </div>
    );
};

export default DataSourceSelector;
