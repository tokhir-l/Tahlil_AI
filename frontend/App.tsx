
import React, { useState, useEffect, useRef } from 'react';
import { v4 as uuidv4 } from 'uuid';
import Sidebar from './components/Sidebar';
import MessageBubble from './components/MessageBubble';
import InputArea from './components/InputArea';
import SettingsModal from './components/SettingsModal';
import FileManagerModal from './components/FileManagerModal';
import AuthScreen from './components/AuthScreen';
import LandingPage from './components/LandingPage';
import { Chat, Message, Theme, ModelId, FileAttachment, ProcessStep } from './types';
import { api } from './services/api';
import { useAuth } from './contexts/AuthContext';

const App: React.FC = () => {
  // Auth
  const { user, isLoading: isAuthLoading, logout } = useAuth();

  // State
  const [showLanding, setShowLanding] = useState(true);
  const [theme, setTheme] = useState<Theme>('system');
  const [sidebarOpen, setSidebarOpen] = useState(window.innerWidth > 768);
  const [selectedModel, setSelectedModel] = useState<ModelId>('gemini-2.5-flash');
  const [chats, setChats] = useState<Chat[]>([]);
  const [currentChatId, setCurrentChatId] = useState<string | null>(null);
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [isFileManagerOpen, setIsFileManagerOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  
  // Active Run State
  const [activeRunId, setActiveRunId] = useState<string | null>(null);
  const pollIntervalRef = useRef<number | null>(null);
  
  // Auto-scroll ref
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Initial Load
  useEffect(() => {
    if (!user) return;

    // Load Chats
    const savedChats = localStorage.getItem(`tahlil_chats_${user.id}`);
    if (savedChats) {
      try {
        const parsed = JSON.parse(savedChats);
        setChats(parsed);
        if (parsed.length > 0) {
          setCurrentChatId(parsed[0].id);
        } else {
          createNewChat();
        }
      } catch (e) {
        createNewChat();
      }
    } else {
      createNewChat();
    }
  }, [user]);
  
  // Theme load independent of user
  useEffect(() => {
    const savedTheme = localStorage.getItem('tahlil_theme') as Theme;
    if (savedTheme) setTheme(savedTheme);
  }, []);

  // Theme effect
  useEffect(() => {
    const root = window.document.documentElement;
    root.classList.remove('light', 'dark');
    
    if (theme === 'system') {
      const systemTheme = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
      root.classList.add(systemTheme);
    } else {
      root.classList.add(theme);
    }
    localStorage.setItem('tahlil_theme', theme);
  }, [theme]);

  // Persist chats per user
  useEffect(() => {
    if (user && chats.length > 0) {
      localStorage.setItem(`tahlil_chats_${user.id}`, JSON.stringify(chats));
    }
  }, [chats, user]);
  
  // Auto-scroll effect
  useEffect(() => {
     if (messagesEndRef.current) {
         messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
     }
  }, [chats, currentChatId, isLoading]);

  // Polling Effect
  useEffect(() => {
    if (!activeRunId) {
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current);
        pollIntervalRef.current = null;
      }
      return;
    }

    const poll = async () => {
      if (!currentChatId) return;

      try {
        const statusData = await api.getRunStatus(activeRunId);
        
        // Fetch steps to show progress
        const steps = await api.getRunSteps(activeRunId);
        
        // Update the assistant message with new steps
        setChats(prev => prev.map(chat => {
          if (chat.id === currentChatId) {
            const lastMsg = chat.messages[chat.messages.length - 1];
            if (lastMsg && lastMsg.role === 'assistant' && lastMsg.runId === activeRunId) {
              const updatedMessages = [...chat.messages];
              updatedMessages[updatedMessages.length - 1] = {
                ...lastMsg,
                steps: steps
              };
              return { ...chat, messages: updatedMessages };
            }
          }
          return chat;
        }));

        if (statusData.status === 'completed') {
           // Fetch final results
           const results = await api.getRunResults(activeRunId);
           
           setChats(prev => prev.map(chat => {
             if (chat.id === currentChatId) {
               const lastMsg = chat.messages[chat.messages.length - 1];
               if (lastMsg && lastMsg.role === 'assistant') {
                 const updatedMessages = [...chat.messages];
                 updatedMessages[updatedMessages.length - 1] = {
                   ...lastMsg,
                   isLoading: false,
                   content: results.output || "Analysis completed.",
                   generatedFiles: results.files,
                   steps: steps // Ensure steps are final
                 };
                 return { ...chat, messages: updatedMessages };
               }
             }
             return chat;
           }));
           
           setActiveRunId(null);
           setIsLoading(false);
        } else if (statusData.status === 'failed' || statusData.status === 'cancelled') {
           setChats(prev => prev.map(chat => {
             if (chat.id === currentChatId) {
               const lastMsg = chat.messages[chat.messages.length - 1];
               if (lastMsg && lastMsg.role === 'assistant') {
                 const updatedMessages = [...chat.messages];
                 updatedMessages[updatedMessages.length - 1] = {
                   ...lastMsg,
                   isLoading: false,
                   content: statusData.status === 'cancelled' 
                     ? "Analysis cancelled by user." 
                     : `Analysis ${statusData.status}. Please try again.`
                 };
                 return { ...chat, messages: updatedMessages };
               }
             }
             return chat;
           }));
           setActiveRunId(null);
           setIsLoading(false);
        }
      } catch (error) {
        console.error("Polling error", error);
        // Don't stop polling immediately on one error, but maybe warn
      }
    };

    pollIntervalRef.current = window.setInterval(poll, 2000); // Poll every 2s

    return () => {
      if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);
    };
  }, [activeRunId, currentChatId]);

  // Chat Helpers
  const createNewChat = () => {
    // Prevent creating duplicate empty chats
    if (chats.length > 0) {
       const latestChat = chats[0];
       if (latestChat.messages.length === 0) {
          setCurrentChatId(latestChat.id);
          if (window.innerWidth < 768) setSidebarOpen(false);
          return;
       }
    }

    const newChat: Chat = {
      id: uuidv4(),
      title: 'New Analysis',
      messages: [],
      updatedAt: Date.now()
    };
    setChats(prev => [newChat, ...prev]);
    setCurrentChatId(newChat.id);
    if (window.innerWidth < 768) setSidebarOpen(false);
  };

  const deleteChat = (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    setChats(prev => prev.filter(c => c.id !== id));
    if (currentChatId === id) {
      const remaining = chats.filter(c => c.id !== id);
      if (remaining.length > 0) setCurrentChatId(remaining[0].id);
      else createNewChat();
    }
  };

  const currentChat = chats.find(c => c.id === currentChatId);

  const handleFeedback = (messageId: string, rating: 'positive' | 'negative') => {
    if (!currentChatId) return;

    // 1. Update local state
    setChats(prev => prev.map(chat => {
      if (chat.id === currentChatId) {
        return {
          ...chat,
          messages: chat.messages.map(msg => {
            if (msg.id === messageId) {
              return { ...msg, feedback: rating };
            }
            return msg;
          })
        };
      }
      return chat;
    }));

    // 2. Send to API (fire and forget)
    const msg = currentChat?.messages.find(m => m.id === messageId);
    if (msg) {
      api.submitFeedback(msg.runId, messageId, rating);
    }
  };

  const handleSendMessage = async (text: string, attachments: FileAttachment[]) => {
    if (!currentChatId) return;

    // --- TEXT-ONLY INTERCEPTION START ---
    // If user sends text without files, give immediate guidance without backend call
    if (attachments.length === 0) {
        const userMsg: Message = {
            id: uuidv4(),
            role: 'user',
            content: text,
            timestamp: Date.now(),
            attachments: []
        };
        
        const systemMsg: Message = {
            id: uuidv4(),
            role: 'assistant',
            content: "Please **upload a file** to start the analysis. I specialize in working with your data directly—attach a CSV, Excel, or Parquet file, and I can uncover trends, visualize data, and answer your questions!",
            timestamp: Date.now() + 100 // Slight delay
        };

        setChats(prev => prev.map(c => {
            if (c.id === currentChatId) {
                const isFirst = c.messages.length === 0;
                return {
                    ...c,
                    title: isFirst ? (text.slice(0, 30) || 'New Analysis') : c.title,
                    messages: [...c.messages, userMsg, systemMsg],
                    updatedAt: Date.now()
                };
            }
            return c;
        }));
        return;
    }
    // --- TEXT-ONLY INTERCEPTION END ---

    const userMsg: Message = {
      id: uuidv4(),
      role: 'user',
      content: text,
      timestamp: Date.now(),
      attachments: attachments
    };

    // Optimistic Update
    setChats(prev => prev.map(c => {
      if (c.id === currentChatId) {
        const isFirst = c.messages.length === 0;
        return {
          ...c,
          title: isFirst ? (text.slice(0, 30) || 'New Analysis') : c.title,
          messages: [...c.messages, userMsg],
          updatedAt: Date.now()
        };
      }
      return c;
    }));

    setIsLoading(true);

    try {
      // 1. Upload files
      let fileIds: string[] = [];
      if (attachments.length > 0) {
        fileIds = await api.uploadFiles(attachments);
      }

      // 2. Start Run
      // Pass user ID to backend if available
      const runId = await api.startRun(text, fileIds, selectedModel);
      setActiveRunId(runId);

      // 3. Create Placeholder Assistant Message
      const aiMsg: Message = {
        id: uuidv4(),
        role: 'assistant',
        content: '', // Will be filled when completed
        timestamp: Date.now(),
        isLoading: true,
        runId: runId,
        steps: []
      };

      setChats(prev => prev.map(c => {
        if (c.id === currentChatId) {
          return {
            ...c,
            messages: [...c.messages, aiMsg],
            updatedAt: Date.now()
          };
        }
        return c;
      }));

    } catch (error) {
      console.error(error);
      const errorMsg: Message = {
        id: uuidv4(),
        role: 'assistant',
        content: "I'm sorry, I encountered an error starting the analysis. Please check the backend connection.",
        timestamp: Date.now()
      };
      setChats(prev => prev.map(c => {
        if (c.id === currentChatId) {
          return { ...c, messages: [...c.messages, errorMsg] };
        }
        return c;
      }));
      setIsLoading(false);
    }
  };

  const handleStop = async () => {
    if (activeRunId) {
      await api.cancelRun(activeRunId);
    }
    
    setActiveRunId(null);
    setIsLoading(false);
    
    setChats(prev => prev.map(chat => {
       if (chat.id === currentChatId) {
         const lastMsg = chat.messages[chat.messages.length - 1];
         if (lastMsg.isLoading) {
           // Mark steps as cancelled if needed
           const updatedSteps = lastMsg.steps ? lastMsg.steps.map(step => 
              step.status === 'in_progress' ? { ...step, status: 'cancelled' as const, message: 'Cancelled by user' } : step
           ) : [];

           return {
             ...chat,
             messages: chat.messages.map(m => m.id === lastMsg.id ? { 
                ...m, 
                isLoading: false, 
                content: m.content || "Analysis cancelled by user.",
                steps: updatedSteps
             } : m)
           };
         }
       }
       return chat;
    }));
  };

  // Auth Guard
  if (isAuthLoading) {
    return (
      <div className="min-h-screen bg-black flex items-center justify-center">
         <div className="w-8 h-8 border-2 border-orange-500 border-t-transparent rounded-full animate-spin"></div>
      </div>
    );
  }

  // If not logged in
  if (!user) {
    if (showLanding) {
      return <LandingPage onGetStarted={() => setShowLanding(false)} />;
    }
    return <AuthScreen />;
  }

  // Main App
  return (
    <div className="flex h-screen bg-background text-foreground font-sans overflow-hidden">
      <Sidebar 
        isOpen={sidebarOpen}
        onToggle={() => setSidebarOpen(!sidebarOpen)}
        chats={chats}
        currentChatId={currentChatId}
        onSelectChat={setCurrentChatId}
        onNewChat={createNewChat}
        onDeleteChat={deleteChat}
        onOpenSettings={() => setIsSettingsOpen(true)}
        onOpenFileManager={() => setIsFileManagerOpen(true)}
        model={selectedModel}
        searchTerm={searchTerm}
        onSearchChange={setSearchTerm}
      />
      
      <main className="flex-1 flex flex-col relative h-full w-full">
        <div className="flex-1 overflow-y-auto scrollbar-thin scrollbar-thumb-border scroll-smooth">
          {currentChat && currentChat.messages.length > 0 ? (
            <div className="max-w-4xl mx-auto w-full pb-32 pt-6">
              {currentChat.messages.map(msg => (
                <MessageBubble 
                  key={msg.id} 
                  message={msg} 
                  onFeedback={(rating) => handleFeedback(msg.id, rating)}
                />
              ))}
              {isLoading && !chats.find(c => c.id === currentChatId)?.messages.some(m => m.isLoading) && (
                 <div className="flex w-full px-4 md:px-8 py-6 gap-4 md:gap-6 bg-primary/30">
                    <div className="w-8 h-8 bg-orange-500 rounded-lg flex items-center justify-center text-white">
                      <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    </div>
                    <div className="flex items-center">
                       <span className="text-gray-500 animate-pulse text-sm">Initializing analysis...</span>
                    </div>
                 </div>
              )}
              {/* Invisible element to scroll to */}
              <div ref={messagesEndRef} />
            </div>
          ) : (
            <div className="h-full flex flex-col items-center justify-center p-8 text-center space-y-6 opacity-0 animate-in fade-in zoom-in duration-500 fill-mode-forwards">
               <div className="w-16 h-16 bg-gradient-to-tr from-orange-400 to-red-500 rounded-2xl shadow-lg flex items-center justify-center mb-4">
                  <span className="text-3xl font-bold text-white">T</span>
               </div>
               <div>
                  <h1 className="text-3xl font-bold mb-2 text-white">Welcome back, {user.username}</h1>
                  <p className="text-gray-500 max-w-md mx-auto">
                    Your AI-powered data science analyst. Attach a CSV or Excel file to get started, or just ask a question.
                  </p>
               </div>
               
               <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 max-w-2xl w-full mt-8">
                  {["Analyze this sales data", "Help me understand this CSV", "What trends do you see?", "Summarize this report"].map((suggestion, i) => (
                    <button 
                      key={i}
                      onClick={() => handleSendMessage(suggestion, [])}
                      className="p-4 bg-secondary/50 hover:bg-secondary border border-border rounded-xl text-left text-sm transition-all hover:shadow-md"
                    >
                      {suggestion}
                    </button>
                  ))}
               </div>
            </div>
          )}
        </div>

        <div className="absolute bottom-0 left-0 w-full bg-gradient-to-t from-background via-background to-transparent pt-10">
           <InputArea 
             onSendMessage={handleSendMessage}
             isLoading={isLoading}
             onStop={handleStop}
           />
        </div>
      </main>

      <SettingsModal 
        isOpen={isSettingsOpen}
        onClose={() => setIsSettingsOpen(false)}
        theme={theme}
        onThemeChange={setTheme}
        model={selectedModel}
        onModelChange={setSelectedModel}
        onLogout={() => {
          setIsSettingsOpen(false);
          logout();
          setShowLanding(true); // Return to landing page on logout
        }}
      />

      <FileManagerModal 
        isOpen={isFileManagerOpen}
        onClose={() => setIsFileManagerOpen(false)}
      />
    </div>
  );
};

export default App;
