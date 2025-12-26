
import React, { useRef, useState, useEffect } from 'react';
import { Paperclip, ArrowUp, X, FileText, UploadCloud } from 'lucide-react';
import { FileAttachment } from '../types';

interface InputAreaProps {
  onSendMessage: (text: string, attachments: FileAttachment[]) => void;
  isLoading: boolean;
  onStop: () => void;
}

const InputArea: React.FC<InputAreaProps> = ({ onSendMessage, isLoading, onStop }) => {
  const [text, setText] = useState('');
  const [attachments, setAttachments] = useState<FileAttachment[]>([]);
  const [isDragging, setIsDragging] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = Math.min(textareaRef.current.scrollHeight, 200) + 'px';
    }
  }, [text]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleSend = () => {
    if ((!text.trim() && attachments.length === 0) || isLoading) return;
    onSendMessage(text, attachments);
    setText('');
    setAttachments([]);
    if (textareaRef.current) textareaRef.current.style.height = 'auto';
  };

  const processFiles = (fileList: FileList | File[]) => {
    const newAttachments: FileAttachment[] = [];
    const files = Array.from(fileList);
    
    // Valid extensions for data analysis
    const validTypes = ['.csv', '.json', '.txt', '.md', '.js', '.py', '.html', '.css', '.xml', '.xlsx', '.xls', '.parquet', '.pdf'];

    let processedCount = 0;
    files.forEach((file: File) => {
       // Basic validation
       const extension = '.' + file.name.split('.').pop()?.toLowerCase();
       if (!validTypes.includes(extension)) {
          // You might want to show a toast here in a real app
          console.warn(`Skipped ${file.name}: Unsupported file type`);
          processedCount++;
          if (processedCount === files.length && newAttachments.length > 0) {
            setAttachments(prev => [...prev, ...newAttachments]);
          }
          return;
       }

       const reader = new FileReader();
       reader.onload = (readerEvent) => {
           newAttachments.push({
               name: file.name,
               size: file.size,
               type: file.type,
               data: readerEvent.target?.result as string, // For preview
               file: file // For actual upload
           });
           processedCount++;
           if (processedCount === files.length) {
               setAttachments(prev => [...prev, ...newAttachments]);
           }
       };
       reader.readAsDataURL(file);
    });
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      processFiles(e.target.files);
    }
    // Reset input
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  // Drag and Drop Handlers
  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      processFiles(e.dataTransfer.files);
    }
  };

  const removeAttachment = (index: number) => {
    setAttachments(prev => prev.filter((_, i) => i !== index));
  };

  return (
    <div className="w-full max-w-4xl mx-auto px-4 pb-4">
      <div 
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        className={`relative flex flex-col gap-2 bg-secondary/40 border rounded-xl p-3 shadow-sm transition-all duration-200 
          ${isDragging 
            ? 'border-orange-500 bg-orange-500/5 ring-2 ring-orange-500/20 border-dashed' 
            : 'border-border focus-within:ring-1 focus-within:ring-gray-300 focus-within:border-gray-400 dark:focus-within:ring-gray-600 dark:focus-within:border-gray-500'
          }`}
      >
        
        {/* Drag Overlay */}
        {isDragging && (
          <div className="absolute inset-0 z-10 flex items-center justify-center bg-background/80 backdrop-blur-sm rounded-xl border-2 border-dashed border-orange-500">
            <div className="flex flex-col items-center gap-2 text-orange-500 animate-bounce">
              <UploadCloud size={32} />
              <span className="font-semibold">Drop files to analyze</span>
            </div>
          </div>
        )}

        {/* Attachment Preview */}
        {attachments.length > 0 && (
          <div className="flex flex-wrap gap-2 px-1 pb-2">
            {attachments.map((file, idx) => (
              <div key={idx} className="group relative flex items-center gap-2 bg-background border border-border rounded-lg px-3 py-2 pr-8 text-xs font-medium shadow-sm animate-in fade-in zoom-in duration-200">
                <FileText size={14} className="text-orange-500" />
                <span className="truncate max-w-[150px]">{file.name}</span>
                <button 
                  onClick={() => removeAttachment(idx)}
                  className="absolute right-1 top-1/2 -translate-y-1/2 p-1 text-gray-400 hover:text-red-500 rounded-full hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors"
                >
                  <X size={14} />
                </button>
              </div>
            ))}
          </div>
        )}

        <div className="flex items-end gap-2">
          <input 
            type="file" 
            ref={fileInputRef} 
            onChange={handleFileChange} 
            multiple 
            className="hidden" 
            accept=".csv,.json,.txt,.md,.js,.py,.html,.css,.xml,.xlsx,.xls,.parquet,.pdf"
          />
          <button 
            onClick={() => fileInputRef.current?.click()}
            className="p-2 mb-0.5 text-gray-500 hover:text-foreground hover:bg-background rounded-lg transition-colors group relative"
            title="Attach file"
          >
            <Paperclip size={20} className="group-hover:text-orange-500 transition-colors" />
          </button>
          
          <textarea
            ref={textareaRef}
            value={text}
            onChange={(e) => setText(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={attachments.length > 0 ? "Ask a question about your files..." : "Message Tahlil or drag files here..."}
            className="flex-1 bg-transparent border-none outline-none resize-none py-2.5 max-h-[200px] text-sm md:text-base scrollbar-thin scrollbar-thumb-gray-300 dark:scrollbar-thumb-gray-600 placeholder:text-gray-400"
            rows={1}
          />
          
          {isLoading ? (
            <button 
              onClick={onStop}
              className="w-9 h-9 mb-0.5 rounded-lg bg-secondary border border-border text-gray-500 hover:text-foreground hover:bg-secondary/80 transition-all shadow-sm flex items-center justify-center"
              title="Stop generating"
            >
              <div className="w-3 h-3 bg-current rounded-[1px]" />
            </button>
          ) : (
            <button 
              onClick={handleSend}
              disabled={!text.trim() && attachments.length === 0}
              className={`p-2 mb-0.5 rounded-lg transition-all duration-200 ${
                (!text.trim() && attachments.length === 0)
                  ? 'bg-secondary text-gray-400 cursor-not-allowed'
                  : 'bg-orange-500 text-white hover:bg-orange-600 shadow-md hover:shadow-lg'
              }`}
              title="Send message"
            >
              <ArrowUp size={20} strokeWidth={3} />
            </button>
          )}
        </div>
      </div>
      
      <div className="text-center mt-2">
         <p className="text-[10px] md:text-xs text-gray-400">
           Supported files: CSV, Excel, JSON, Parquet, PDF & Text.
         </p>
      </div>
    </div>
  );
};

export default InputArea;
