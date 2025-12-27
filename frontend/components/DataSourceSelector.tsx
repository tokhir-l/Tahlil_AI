
import React, { useState, useEffect } from 'react';
import { Link2, Loader2, CheckCircle, AlertCircle, ExternalLink, Globe, FileSpreadsheet, Database, Users, ChevronDown, ChevronUp } from 'lucide-react';
import { api } from '../services/api';

interface DataSourceSelectorProps {
    onFileImported?: (fileInfo: { id: number; name: string; source: string }) => void;
    onClose?: () => void;
}

type ActiveSource = 'sheets' | 'api' | 'crm' | null;

const DataSourceSelector: React.FC<DataSourceSelectorProps> = ({ onFileImported, onClose }) => {
    const [activeSource, setActiveSource] = useState<ActiveSource>('sheets');

    // Spreadsheet state
    const [sheetUrl, setSheetUrl] = useState('');
    const [sheetLoading, setSheetLoading] = useState(false);

    // API state
    const [apiUrl, setApiUrl] = useState('');
    const [apiMethod, setApiMethod] = useState<'GET' | 'POST'>('GET');
    const [authType, setAuthType] = useState<'none' | 'api_key' | 'bearer' | 'basic'>('none');
    const [authConfig, setAuthConfig] = useState<Record<string, string>>({});
    const [jsonPath, setJsonPath] = useState('');
    const [apiLoading, setApiLoading] = useState(false);
    const [showAdvanced, setShowAdvanced] = useState(false);

    // CRM state
    const [crmPlatforms, setCrmPlatforms] = useState<any[]>([]);
    const [activePlatform, setActivePlatform] = useState<string | null>(null);
    const [crmCredentials, setCrmCredentials] = useState<Record<string, string>>({});
    const [crmEntity, setCrmEntity] = useState('leads');
    const [crmLoading, setCrmLoading] = useState(false);

    useEffect(() => {
        api.getCrmAuthTypes().then(res => {
            if (res.success && res.platforms) {
                setCrmPlatforms(res.platforms);
            }
        });
    }, []);

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

    // API import
    const handleFetchApi = async () => {
        if (!apiUrl.trim()) {
            setError('Please enter an API URL');
            return;
        }

        setApiLoading(true);
        clearMessages();

        try {
            const result = await api.fetchFromApi({
                url: apiUrl,
                method: apiMethod,
                auth_type: authType,
                auth_config: authConfig,
                json_path: jsonPath || undefined
            });

            if (result.success && result.file) {
                setSuccess(`✅ Imported "${result.file.name}" (${result.metadata?.rows || 0} rows)`);
                setApiUrl('');
                setAuthConfig({});
                setJsonPath('');
                onFileImported?.({ id: result.file.id, name: result.file.name, source: 'api' });
            } else {
                setError(result.error || 'Failed to fetch from API');
            }
        } catch (err) {
            setError('Connection failed. Check URL and try again.');
        } finally {
            setApiLoading(false);
        }
    };

    // CRM import
    const handleFetchCrm = async () => {
        if (!activePlatform) return;
        setCrmLoading(true);
        clearMessages();
        try {
            const result = await api.fetchFromCrm({
                platform: activePlatform,
                credentials: crmCredentials,
                entity: crmEntity,
            });
            if (result.success && result.file) {
                setSuccess(`✅ Imported ${result.metadata?.rows || 0} ${crmEntity} from ${activePlatform}`);
                onFileImported?.({ id: result.file.id, name: result.file.name, source: 'crm' });
            } else {
                setError(result.error || 'Failed to fetch from CRM');
            }
        } catch (err) {
            setError('CRM connection failed');
        } finally {
            setCrmLoading(false);
        }
    };

    // Source cards data
    const sources = [
        { id: 'sheets' as const, title: 'Google Sheets', desc: 'Import from public sheets', icon: FileSpreadsheet, color: '#22c55e', available: true },
        { id: 'api' as const, title: 'REST API', desc: 'Connect to any endpoint', icon: Globe, color: '#3b82f6', available: true },
        { id: 'database' as const, title: 'Database', desc: 'SQL & NoSQL', icon: Database, color: '#8b5cf6', available: false },
        { id: 'crm' as const, title: 'CRM', desc: 'Salesforce, HubSpot', icon: Users, color: '#f97316', available: true },
    ];

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

    const selectStyle: React.CSSProperties = {
        ...inputStyle,
        cursor: 'pointer',
        appearance: 'none' as const,
        backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 24 24' fill='none' stroke='%239ca3af' stroke-width='2'%3E%3Cpolyline points='6 9 12 15 18 9'%3E%3C/polyline%3E%3C/svg%3E")`,
        backgroundRepeat: 'no-repeat',
        backgroundPosition: 'right 12px center',
        paddingRight: '36px'
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
                    background: 'linear-gradient(135deg, #3b82f6, #8b5cf6)',
                    display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'white'
                }}>
                    <Link2 size={20} />
                </div>
                <div>
                    <h3 style={{ margin: 0, fontSize: '16px', fontWeight: 600 }}>Connect Data Source</h3>
                    <p style={{ margin: 0, fontSize: '12px', color: '#9ca3af' }}>Import from external sources</p>
                </div>
            </div>

            {/* Source Cards Grid */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '10px' }}>
                {sources.map(source => {
                    const Icon = source.icon;
                    const isActive = activeSource === source.id;
                    return (
                        <div
                            key={source.id}
                            onClick={() => source.available && setActiveSource(source.id as ActiveSource)}
                            style={{
                                display: 'flex', alignItems: 'center', gap: '10px', padding: '12px',
                                background: isActive ? 'rgba(59, 130, 246, 0.15)' : source.available ? 'rgba(75, 85, 99, 0.1)' : 'rgba(75, 85, 99, 0.05)',
                                border: `1px solid ${isActive ? '#3b82f6' : source.available ? 'rgba(75, 85, 99, 0.2)' : 'rgba(75, 85, 99, 0.1)'}`,
                                borderRadius: '10px',
                                opacity: source.available ? 1 : 0.5,
                                cursor: source.available ? 'pointer' : 'not-allowed',
                                transition: 'all 0.2s ease'
                            }}
                        >
                            <div style={{
                                width: '36px', height: '36px', borderRadius: '8px',
                                background: source.color,
                                display: 'flex', alignItems: 'center', justifyContent: 'center',
                                color: 'white', flexShrink: 0
                            }}>
                                <Icon size={18} />
                            </div>
                            <div style={{ flex: 1, minWidth: 0 }}>
                                <div style={{ fontSize: '13px', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '6px' }}>
                                    {source.title}
                                    {!source.available && (
                                        <span style={{
                                            fontSize: '9px', padding: '2px 6px',
                                            background: 'rgba(251, 191, 36, 0.2)', color: '#f59e0b',
                                            borderRadius: '4px', fontWeight: 600, textTransform: 'uppercase'
                                        }}>Soon</span>
                                    )}
                                </div>
                                <div style={{ fontSize: '11px', color: '#9ca3af', marginTop: '2px' }}>{source.desc}</div>
                            </div>
                        </div>
                    );
                })}
            </div>

            {/* Spreadsheet Form */}
            {activeSource === 'sheets' && (
                <div style={{
                    background: 'rgba(34, 197, 94, 0.05)', border: '1px solid rgba(34, 197, 94, 0.15)',
                    borderRadius: '12px', padding: '14px'
                }}>
                    <label style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '12px', fontWeight: 500, color: '#9ca3af', marginBottom: '10px' }}>
                        <FileSpreadsheet size={14} />
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
            )}


            {/* API Form */}
            {activeSource === 'api' && (
                <div style={{
                    background: 'rgba(59, 130, 246, 0.05)', border: '1px solid rgba(59, 130, 246, 0.15)',
                    borderRadius: '12px', padding: '14px'
                }}>
                    <label style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '12px', fontWeight: 500, color: '#9ca3af', marginBottom: '10px' }}>
                        <Globe size={14} />
                        REST API Endpoint
                    </label>

                    {/* URL + Method Row */}
                    <div style={{ display: 'flex', gap: '8px', marginBottom: '10px' }}>
                        <select value={apiMethod} onChange={(e) => setApiMethod(e.target.value as 'GET' | 'POST')} style={{ ...selectStyle, width: '90px', flex: 'none' }}>
                            <option value="GET">GET</option>
                            <option value="POST">POST</option>
                        </select>
                        <input
                            type="url"
                            value={apiUrl}
                            onChange={(e) => { setApiUrl(e.target.value); clearMessages(); }}
                            placeholder="https://api.example.com/data"
                            disabled={apiLoading}
                            style={{ ...inputStyle, flex: 1 }}
                        />
                    </div>

                    {/* Auth Type */}
                    <div style={{ marginBottom: '10px' }}>
                        <label style={{ fontSize: '11px', color: '#9ca3af', marginBottom: '6px', display: 'block' }}>Authentication</label>
                        <select value={authType} onChange={(e) => { setAuthType(e.target.value as any); setAuthConfig({}); }} style={selectStyle}>
                            <option value="none">No Authentication</option>
                            <option value="api_key">API Key</option>
                            <option value="bearer">Bearer Token</option>
                            <option value="basic">Basic Auth</option>
                        </select>
                    </div>

                    {/* Auth Config Fields */}
                    {authType === 'api_key' && (
                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', marginBottom: '10px' }}>
                            <input
                                placeholder="Header name (e.g., X-API-Key)"
                                value={authConfig.key_name || ''}
                                onChange={(e) => setAuthConfig({ ...authConfig, key_name: e.target.value })}
                                style={inputStyle}
                            />
                            <input
                                type="password"
                                placeholder="API Key value"
                                value={authConfig.key_value || ''}
                                onChange={(e) => setAuthConfig({ ...authConfig, key_value: e.target.value })}
                                style={inputStyle}
                            />
                        </div>
                    )}
                    {authType === 'bearer' && (
                        <div style={{ marginBottom: '10px' }}>
                            <input
                                type="password"
                                placeholder="Bearer token"
                                value={authConfig.token || ''}
                                onChange={(e) => setAuthConfig({ ...authConfig, token: e.target.value })}
                                style={inputStyle}
                            />
                        </div>
                    )}
                    {authType === 'basic' && (
                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', marginBottom: '10px' }}>
                            <input
                                placeholder="Username"
                                value={authConfig.username || ''}
                                onChange={(e) => setAuthConfig({ ...authConfig, username: e.target.value })}
                                style={inputStyle}
                            />
                            <input
                                type="password"
                                placeholder="Password"
                                value={authConfig.password || ''}
                                onChange={(e) => setAuthConfig({ ...authConfig, password: e.target.value })}
                                style={inputStyle}
                            />
                        </div>
                    )}

                    {/* Advanced Options Toggle */}
                    <button
                        onClick={() => setShowAdvanced(!showAdvanced)}
                        style={{
                            display: 'flex', alignItems: 'center', gap: '4px',
                            background: 'none', border: 'none', color: '#9ca3af',
                            fontSize: '11px', cursor: 'pointer', padding: '4px 0', marginBottom: showAdvanced ? '10px' : 0
                        }}
                    >
                        {showAdvanced ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
                        Advanced Options
                    </button>

                    {showAdvanced && (
                        <div style={{ marginBottom: '10px' }}>
                            <input
                                placeholder="JSON path to data (e.g., data.items)"
                                value={jsonPath}
                                onChange={(e) => setJsonPath(e.target.value)}
                                style={inputStyle}
                            />
                            <p style={{ fontSize: '10px', color: '#6b7280', marginTop: '4px' }}>
                                Specify the path to the data array in the JSON response
                            </p>
                        </div>
                    )}

                    {/* Submit Button */}
                    <button
                        onClick={handleFetchApi}
                        disabled={!apiUrl.trim() || apiLoading}
                        style={{ ...buttonStyle(apiLoading, !apiUrl.trim()), width: '100%' }}
                    >
                        {apiLoading ? <Loader2 size={16} className="animate-spin" /> : <><ExternalLink size={14} /> Fetch Data</>}
                    </button>
                </div>
            )}

            {/* CRM Form */}
            {activeSource === 'crm' && (
                <div style={{
                    background: 'rgba(249, 115, 22, 0.05)', border: '1px solid rgba(249, 115, 22, 0.15)',
                    borderRadius: '12px', padding: '14px'
                }}>
                    <label style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '12px', fontWeight: 500, color: '#9ca3af', marginBottom: '10px' }}>
                        <Users size={14} />
                        Connect to 1C:Enterprise
                    </label>

                    <p style={{ fontSize: '11px', color: '#6b7280', marginBottom: '15px' }}>
                        Import data from 1C via OData interface.
                    </p>

                    {/* Dynamic Auth Fields (Hardcoded for single platform MVP look, but using dynamic config) */}
                    <div style={{ marginBottom: '15px' }}>
                        {crmPlatforms.length > 0 && crmPlatforms[0]?.fields.map(field => (
                            <div key={field.key} style={{ marginBottom: '8px' }}>
                                <label style={{ fontSize: '11px', color: '#9ca3af', marginBottom: '4px', display: 'block' }}>{field.label}</label>
                                <input
                                    type={field.type}
                                    placeholder={field.placeholder}
                                    value={crmCredentials[field.key] || ''}
                                    onChange={(e) => setCrmCredentials({ ...crmCredentials, [field.key]: e.target.value })}
                                    style={inputStyle}
                                />
                            </div>
                        ))}
                        {crmPlatforms.length === 0 && <div style={{ fontSize: '11px', color: '#9ca3af' }}>Loading configuration...</div>}
                    </div>

                    {/* Submit Button */}
                    <button
                        onClick={handleFetchCrm}
                        disabled={crmLoading || crmPlatforms.length === 0}
                        style={{ ...buttonStyle(crmLoading, false), width: '100%', background: 'linear-gradient(135deg, #f97316, #ea580c)' }}
                    >
                        {crmLoading ? <Loader2 size={16} className="animate-spin" /> : <><ExternalLink size={14} /> Import from 1C</>}
                    </button>
                </div>
            )}

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
