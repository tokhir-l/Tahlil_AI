import React from 'react';
import { Theme, ModelId } from '../types';
import { X, Monitor, Sun, Moon, LogOut } from 'lucide-react';

interface SettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
  theme: Theme;
  onThemeChange: (theme: Theme) => void;
  model: ModelId;
  onModelChange: (model: ModelId) => void;
  onLogout: () => void;
}

const SettingsModal: React.FC<SettingsModalProps> = ({
  isOpen, onClose, theme, onThemeChange, model, onModelChange, onLogout
}) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="bg-background w-full max-w-md rounded-xl border border-border shadow-2xl overflow-hidden animate-in zoom-in-95 duration-200">
        <div className="flex items-center justify-between px-6 py-4 border-b border-border">
          <h2 className="text-lg font-semibold">Settings</h2>
          <button onClick={onClose} className="p-1 hover:bg-secondary rounded-lg transition-colors">
            <X size={20} />
          </button>
        </div>

        <div className="p-6 space-y-6">
          {/* Theme Section */}
          <div className="space-y-3">
            <label className="text-sm font-medium text-accent uppercase tracking-wider">Appearance</label>
            <div className="grid grid-cols-3 gap-2 bg-secondary/50 p-1 rounded-lg border border-border">
              <button
                onClick={() => onThemeChange('system')}
                className={`flex items-center justify-center gap-2 py-2 px-3 rounded-md text-sm transition-all ${theme === 'system' ? 'bg-background shadow-sm text-foreground' : 'text-gray-500 hover:text-foreground'}`}
              >
                <Monitor size={16} />
                <span>System</span>
              </button>
              <button
                onClick={() => onThemeChange('light')}
                className={`flex items-center justify-center gap-2 py-2 px-3 rounded-md text-sm transition-all ${theme === 'light' ? 'bg-background shadow-sm text-foreground' : 'text-gray-500 hover:text-foreground'}`}
              >
                <Sun size={16} />
                <span>Light</span>
              </button>
              <button
                onClick={() => onThemeChange('dark')}
                className={`flex items-center justify-center gap-2 py-2 px-3 rounded-md text-sm transition-all ${theme === 'dark' ? 'bg-background shadow-sm text-foreground' : 'text-gray-500 hover:text-foreground'}`}
              >
                <Moon size={16} />
                <span>Dark</span>
              </button>
            </div>
          </div>

          {/* Model Section */}
          <div className="space-y-3">
            <label className="text-sm font-medium text-accent uppercase tracking-wider">AI Model</label>
            <div className="relative">
              <select
                value={model}
                onChange={(e) => onModelChange(e.target.value as ModelId)}
                className="w-full appearance-none bg-background border border-border rounded-lg px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-accent/20 transition-all"
              >
                <option value="gemini-1.5-flash">Gemini 1.5 Flash (Recommended)</option>
                <option value="gemini-1.5-pro">Gemini 1.5 Pro</option>
                <option value="gemini-2.0-flash-exp">Gemini 2.0 Flash Exp</option>
              </select>
              <div className="absolute right-4 top-1/2 -translate-y-1/2 pointer-events-none text-gray-400">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M6 9l6 6 6-6" />
                </svg>
              </div>
            </div>
            <p className="text-xs text-gray-500">
              Gemini 2.5 Flash offers the best balance of speed and reasoning capabilities for data analysis tasks.
            </p>
          </div>

          <hr className="border-border" />

          {/* Account Section */}
          <div className="space-y-3">
            <button
              onClick={onLogout}
              className="w-full flex items-center justify-between px-4 py-3 text-red-500 bg-red-500/5 hover:bg-red-500/10 border border-red-500/20 rounded-lg transition-colors"
            >
              <span className="font-medium">Sign Out</span>
              <LogOut size={18} />
            </button>
          </div>
        </div>

        <div className="bg-secondary/30 px-6 py-4 border-t border-border flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-foreground text-background rounded-lg text-sm font-medium hover:opacity-90 transition-opacity"
          >
            Done
          </button>
        </div>
      </div>
    </div>
  );
};

export default SettingsModal;