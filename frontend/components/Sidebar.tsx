
import React, { useState, useEffect } from 'react';
import { Chat, ModelId, StorageStats } from '../types';
import { Plus, MessageSquare, Trash2, Settings, ChevronLeft, ChevronRight, Search, Database, HardDrive, LayoutDashboard } from 'lucide-react';
import { api } from '../services/api';

interface SidebarProps {
  isOpen: boolean;
  onToggle: () => void;
  chats: Chat[];
  currentChatId: string | null;
  onSelectChat: (id: string) => void;
  onNewChat: () => void;
  onDeleteChat: (id: string, e: React.MouseEvent) => void;
  onOpenSettings: () => void;
  onOpenFileManager: () => void;
  model: ModelId;
  searchTerm: string;
  onSearchChange: (term: string) => void;
  activeView: 'chat' | 'dashboards';
  onViewChange: (view: 'chat' | 'dashboards') => void;
}

const Sidebar: React.FC<SidebarProps> = ({
  isOpen, onToggle, chats, currentChatId, onSelectChat, onNewChat, onDeleteChat, onOpenSettings, onOpenFileManager, model, searchTerm, onSearchChange, activeView, onViewChange
}) => {
  const filteredChats = chats.filter(chat =>
    chat.title.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const [stats, setStats] = useState<StorageStats>({ used: 0, total: 100, fileCount: 0 });

  useEffect(() => {
    // Fetch stats on mount
    api.getStorageStats().then(setStats);
  }, []);

  const usedPercent = Math.min((stats.used / stats.total) * 100, 100);
  const isHighUsage = usedPercent > 80;

  const formatBytes = (bytes: number) => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
  };

  return (
    <aside
      className={`${isOpen ? 'w-[280px]' : 'w-[70px]'} flex-shrink-0 bg-primary border-r border-border flex flex-col transition-all duration-300 ease-in-out h-full overflow-hidden relative`}
    >
      {/* Header */}
      <div className="p-4 flex items-center justify-between gap-2 h-[68px]">
        {isOpen && (
          <div className="relative flex-1 group">
            <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 group-focus-within:text-foreground transition-colors" />
            <input
              type="text"
              placeholder="Search..."
              value={searchTerm}
              onChange={(e) => onSearchChange(e.target.value)}
              className="w-full bg-secondary border border-transparent focus:border-border rounded-lg pl-9 pr-3 py-1.5 text-sm outline-none transition-all"
            />
          </div>
        )}
        <button
          onClick={onToggle}
          className={`p-2 hover:bg-secondary rounded-lg text-gray-500 hover:text-foreground transition-colors ${!isOpen ? 'mx-auto' : ''}`}
          title={isOpen ? "Close sidebar" : "Open sidebar"}
        >
          {isOpen ? <ChevronLeft size={18} /> : <ChevronRight size={18} />}
        </button>
      </div>

      {/* New Chat Button */}
      <div className="px-3 pb-2 space-y-1">
        <button
          onClick={onNewChat}
          className={`flex items-center gap-3 w-full p-2 rounded-lg hover:bg-secondary transition-colors group ${!isOpen ? 'justify-center' : ''}`}
        >
          <div className="w-8 h-8 rounded-full bg-background border border-border flex items-center justify-center text-orange-500 shadow-sm group-hover:border-orange-200 transition-colors">
            <Plus size={18} />
          </div>
          {isOpen && <span className="text-sm font-medium">New Chat</span>}
        </button>

        {/* View Switcher */}
        <div className="pt-2">
          <button
            onClick={() => onViewChange('chat')}
            className={`flex items-center gap-3 w-full p-2 rounded-lg transition-colors ${activeView === 'chat' ? 'bg-secondary text-foreground font-medium' : 'text-gray-500 hover:bg-secondary/50 hover:text-foreground'} ${!isOpen ? 'justify-center' : ''}`}
          >
            <div className={`flex items-center justify-center ${!isOpen ? '' : 'w-5'}`}>
              <MessageSquare size={18} />
            </div>
            {isOpen && <span className="text-sm">Chat</span>}
          </button>
          <button
            onClick={() => onViewChange('dashboards')}
            className={`flex items-center gap-3 w-full p-2 rounded-lg transition-colors ${activeView === 'dashboards' ? 'bg-secondary text-foreground font-medium' : 'text-gray-500 hover:bg-secondary/50 hover:text-foreground'} ${!isOpen ? 'justify-center' : ''}`}
          >
            <div className={`flex items-center justify-center ${!isOpen ? '' : 'w-5'}`}>
              <LayoutDashboard size={18} />
            </div>
            {isOpen && <span className="text-sm">Dashboards</span>}
          </button>
        </div>
      </div>

      {/* Chat List */}
      <div className="flex-1 overflow-y-auto px-3 py-2 space-y-1 scrollbar-hide">
        {isOpen && <div className="px-2 py-2 text-xs font-semibold text-gray-400 uppercase tracking-wider">Recent</div>}

        {filteredChats.length === 0 && isOpen && (
          <div className="text-center py-8 text-gray-400 text-sm">
            No chats found
          </div>
        )}

        {filteredChats.map(chat => (
          <div
            key={chat.id}
            onClick={() => onSelectChat(chat.id)}
            className={`group flex items-center gap-3 p-2 rounded-lg cursor-pointer transition-colors ${currentChatId === chat.id
                ? 'bg-secondary text-foreground font-medium'
                : 'text-gray-500 hover:bg-secondary/50 hover:text-foreground'
              } ${!isOpen ? 'justify-center' : ''}`}
          >
            {isOpen ? (
              <>
                <MessageSquare size={16} className={currentChatId === chat.id ? 'text-foreground' : 'text-gray-400'} />
                <span className="flex-1 truncate text-sm">{chat.title}</span>
                <button
                  onClick={(e) => onDeleteChat(chat.id, e)}
                  className="opacity-0 group-hover:opacity-100 p-1 hover:bg-background rounded text-gray-400 hover:text-red-500 transition-all"
                >
                  <Trash2 size={14} />
                </button>
              </>
            ) : (
              <div className="relative">
                <MessageSquare size={20} className={currentChatId === chat.id ? 'text-foreground' : 'text-gray-400'} />
                {currentChatId === chat.id && (
                  <div className="absolute -right-1 -top-1 w-2.5 h-2.5 bg-foreground rounded-full border-2 border-primary" />
                )}
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Storage & Settings Footer */}
      <div className="p-3 border-t border-border bg-primary space-y-2">

        {/* Storage Indicator */}
        <button
          onClick={onOpenFileManager}
          className={`w-full p-2 rounded-lg bg-secondary/30 hover:bg-secondary/60 border border-border transition-all group ${!isOpen ? 'justify-center flex' : ''}`}
          title="Manage Files"
        >
          {isOpen ? (
            <div className="space-y-1.5">
              <div className="flex justify-between items-center text-xs">
                <span className="font-medium flex items-center gap-1.5">
                  <Database size={12} className="text-accent" />
                  Storage
                </span>
                <span className="text-gray-500">{formatBytes(stats.used)} / {formatBytes(stats.total)}</span>
              </div>
              <div className="h-1.5 w-full bg-border rounded-full overflow-hidden">
                <div
                  className={`h-full rounded-full transition-all duration-500 ${isHighUsage ? 'bg-red-500' : 'bg-orange-500'}`}
                  style={{ width: `${usedPercent}%` }}
                />
              </div>
            </div>
          ) : (
            <div className="relative">
              <Database size={18} className="text-gray-500 group-hover:text-foreground" />
              {isHighUsage && <div className="absolute -top-1 -right-1 w-2 h-2 bg-red-500 rounded-full" />}
            </div>
          )}
        </button>

        {isOpen && (
          <div className="px-1">
            <div className="flex items-center justify-between bg-secondary/50 rounded-lg p-2 border border-border">
              <span className="text-xs font-medium truncate max-w-[140px] flex items-center gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-green-500"></span>
                {model.replace(/-/g, ' ')}
              </span>
            </div>
          </div>
        )}

        <button
          onClick={onOpenSettings}
          className={`flex items-center gap-3 w-full p-2 rounded-lg hover:bg-secondary text-gray-500 hover:text-foreground transition-colors ${!isOpen ? 'justify-center' : ''}`}
        >
          <Settings size={20} />
          {isOpen && <span className="text-sm font-medium">Settings</span>}
        </button>
      </div>
    </aside>
  );
};

export default Sidebar;
