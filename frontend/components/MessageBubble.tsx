
import React, { useState, useRef, useEffect } from 'react';
import { Message, ProcessStep, StepDetails } from '../types';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { User, Bot, Loader2, Copy, ThumbsUp, ThumbsDown, FileText, ChevronDown, ChevronRight, CheckCircle2, CircleDashed, Terminal, BarChart2, AlertCircle, XCircle, Check, Code, FileCode, MessageSquare } from 'lucide-react';
import { extractTableFromText } from '../utils/formatters';
import { api } from '../services/api';

interface MessageBubbleProps {
  message: Message;
  onFeedback?: (rating: 'positive' | 'negative') => void;
}

const ExpandableStep: React.FC<{ step: ProcessStep; runId?: string }> = ({ step, runId }) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const [details, setDetails] = useState<StepDetails | null>(null);
  const [loadingDetails, setLoadingDetails] = useState(false);
  const [copied, setCopied] = useState<string | null>(null);

  useEffect(() => {
    if (isExpanded && step.step_id && runId && !details && !loadingDetails) {
      setLoadingDetails(true);
      api.getStepDetails(runId, step.step_id)
        .then(data => {
          setDetails(data);
          setLoadingDetails(false);
        })
        .catch(err => {
          console.error('Error loading step details:', err);
          setLoadingDetails(false);
        });
    }
  }, [isExpanded, step.step_id, runId, details, loadingDetails]);

  const handleCopy = (text: string, type: string) => {
    navigator.clipboard.writeText(text);
    setCopied(type);
    setTimeout(() => setCopied(null), 2000);
  };

  return (
    <div className="border border-border/50 bg-secondary/20 rounded-lg overflow-hidden hover:border-border transition-colors">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full flex items-start gap-3 p-3 hover:bg-secondary/50 transition-colors text-left cursor-pointer group"
        title={step.step_id ? "Click to view code, prompt, and execution details" : "Click to view details"}
      >
        <div className="mt-0.5 flex-shrink-0">
          {step.status === 'completed' && <CheckCircle2 size={16} className="text-green-500" />}
          {step.status === 'in_progress' && <Loader2 size={16} className="animate-spin text-orange-500" />}
          {step.status === 'pending' && <CircleDashed size={16} className="text-gray-400" />}
          {step.status === 'failed' && <div className="w-4 h-4 rounded-full bg-red-500" />}
          {step.status === 'cancelled' && <XCircle size={16} className="text-gray-400" />}
        </div>
        <div className="flex-1 min-w-0">
          <div className={`font-semibold text-sm mb-1 ${step.status === 'in_progress' ? 'text-foreground' : step.status === 'completed' ? 'text-green-600 dark:text-green-400' : 'text-gray-600 dark:text-gray-300'}`}>
            {step.name}
          </div>
          <div className="text-[11px] text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-1.5 flex justify-between items-center">
            <span className="font-medium">{step.phase}</span>
            <span className="font-mono">{step.timestamp ? (() => {
              try {
                const date = new Date(step.timestamp);
                return isNaN(date.getTime()) ? '—' : date.toLocaleTimeString();
              } catch {
                return '—';
              }
            })() : '—'}</span>
          </div>
          {step.message && !isExpanded && (
            <div className="mt-2 text-xs text-gray-600 dark:text-gray-400 font-mono bg-secondary/50 p-2 rounded border border-border/30 whitespace-pre-wrap break-words line-clamp-2">
              {step.message}
            </div>
          )}
          {step.step_id && !isExpanded && (
            <div className="mt-1.5 text-[10px] text-blue-500 dark:text-blue-400 opacity-0 group-hover:opacity-100 transition-opacity">
              Click to view code and details →
            </div>
          )}
        </div>
        <div className="flex-shrink-0 ml-2 flex items-center">
          {isExpanded ? (
            <ChevronDown size={18} className="text-gray-500 group-hover:text-foreground transition-colors" />
          ) : (
            <ChevronRight size={18} className="text-gray-500 group-hover:text-foreground transition-colors" />
          )}
        </div>
      </button>
      
      {isExpanded && (
        <div className="border-t border-border bg-background p-4 space-y-4">
          {step.step_id && runId ? (
            loadingDetails ? (
              <div className="flex items-center gap-2 text-gray-500">
                <Loader2 size={16} className="animate-spin" />
                <span className="text-sm">Loading details...</span>
              </div>
            ) : details ? (
            <>
              {details.code && (
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2 text-sm font-semibold">
                      <Code size={16} className="text-blue-500" />
                      <span>Generated Code</span>
                    </div>
                    <button
                      onClick={() => handleCopy(details.code!, 'code')}
                      className="flex items-center gap-1 text-xs text-gray-400 hover:text-foreground transition-colors"
                    >
                      {copied === 'code' ? <Check size={14} className="text-green-500" /> : <Copy size={14} />}
                      <span>{copied === 'code' ? 'Copied' : 'Copy'}</span>
                    </button>
                  </div>
                  <pre className="bg-secondary/50 p-3 rounded border border-border overflow-x-auto text-xs font-mono">
                    <code>{details.code}</code>
                  </pre>
                </div>
              )}
              
              {details.prompt && (
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2 text-sm font-semibold">
                      <MessageSquare size={16} className="text-purple-500" />
                      <span>Prompt</span>
                    </div>
                    <button
                      onClick={() => handleCopy(details.prompt!, 'prompt')}
                      className="flex items-center gap-1 text-xs text-gray-400 hover:text-foreground transition-colors"
                    >
                      {copied === 'prompt' ? <Check size={14} className="text-green-500" /> : <Copy size={14} />}
                      <span>{copied === 'prompt' ? 'Copied' : 'Copy'}</span>
                    </button>
                  </div>
                  <div className="bg-secondary/50 p-3 rounded border border-border text-xs whitespace-pre-wrap break-words">
                    {details.prompt}
                  </div>
                </div>
              )}
              
              {details.result && (
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2 text-sm font-semibold">
                      <Terminal size={16} className="text-green-500" />
                      <span>Execution Result</span>
                    </div>
                    <button
                      onClick={() => handleCopy(details.result!, 'result')}
                      className="flex items-center gap-1 text-xs text-gray-400 hover:text-foreground transition-colors"
                    >
                      {copied === 'result' ? <Check size={14} className="text-green-500" /> : <Copy size={14} />}
                      <span>{copied === 'result' ? 'Copied' : 'Copy'}</span>
                    </button>
                  </div>
                  <div className="bg-secondary/50 p-3 rounded border border-border text-xs font-mono whitespace-pre-wrap break-words max-h-[400px] overflow-y-auto">
                    {details.result}
                  </div>
                </div>
              )}
              
              {!details.code && !details.prompt && !details.result && (
                <div className="text-sm text-gray-500 italic">No detailed information available for this step.</div>
              )}
            </>
            ) : (
              <div className="flex items-center gap-2 text-gray-500">
                <Loader2 size={16} className="animate-spin" />
                <span className="text-sm">Loading details...</span>
              </div>
            )
          ) : (
            <>
              {step.message && (
                <div className="space-y-2">
                  <div className="flex items-center gap-2 text-sm font-semibold">
                    <Terminal size={16} className="text-green-500" />
                    <span>Message</span>
                  </div>
                  <div className="bg-secondary/50 p-3 rounded border border-border text-xs font-mono whitespace-pre-wrap break-words max-h-[400px] overflow-y-auto">
                    {step.message}
                  </div>
                </div>
              )}
              {!step.message && (
                <div className="text-sm text-gray-500 italic">
                  {step.step_id ? 'No detailed information available. This step may not have generated code or results yet.' : 'No detailed information available for this step.'}
                </div>
              )}
            </>
          )}
        </div>
      )}
    </div>
  );
};

const StepsAccordion: React.FC<{ steps: ProcessStep[]; runId?: string }> = ({ steps, runId }) => {
  const [isOpen, setIsOpen] = useState(true); // Open by default to show process details
  
  if (!steps || steps.length === 0) return null;

  const currentStep = steps.find(s => s.status === 'in_progress') || steps[steps.length - 1];
  const isComplete = steps.every(s => s.status === 'completed');
  const isCancelled = steps.some(s => s.status === 'cancelled');

  return (
    <div className="mb-4 rounded-lg border border-border bg-secondary/30 overflow-hidden transition-all">
      <button 
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center justify-between p-3 text-xs md:text-sm font-medium hover:bg-secondary/50 transition-colors"
      >
        <div className="flex items-center gap-2">
          {isComplete ? (
            <CheckCircle2 size={16} className="text-green-500" />
          ) : isCancelled ? (
            <XCircle size={16} className="text-gray-400" />
          ) : (
            <Loader2 size={16} className="animate-spin text-orange-500" />
          )}
          <span>
             {isComplete ? 'Analysis Completed' : isCancelled ? 'Analysis Cancelled' : currentStep ? currentStep.name : 'Processing...'}
          </span>
          {steps.length > 0 && <span className="text-gray-400 ml-1">({steps.filter(s => s.status === 'completed').length}/{steps.length})</span>}
        </div>
        <div className="flex items-center gap-1 text-gray-400">
          <span className="text-[10px] uppercase tracking-wider">{isComplete ? 'Details' : 'Thinking'}</span>
          {isOpen ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
        </div>
      </button>
      
      {isOpen && (
        <div className="border-t border-border bg-background p-3 max-h-[600px] overflow-y-auto">
          <div className="space-y-2">
             {steps.map((step, idx) => (
               <ExpandableStep key={step.step_id || idx} step={step} runId={runId} />
             ))}
          </div>
        </div>
      )}
    </div>
  );
};

const GeneratedFilesGrid: React.FC<{ runId?: string, files?: string[] }> = ({ runId, files }) => {
  if (!runId || !files || files.length === 0) return null;

  return (
    <div className="mt-4 grid grid-cols-1 md:grid-cols-2 gap-4">
      {files.map((file, idx) => {
        const isImage = file.endsWith('.png') || file.endsWith('.jpg');
        const fileUrl = api.getFileUrl(runId, file);
        
        return (
          <div key={idx} className="rounded-xl border border-border overflow-hidden bg-background">
             {isImage ? (
               <div className="relative group cursor-pointer" onClick={() => window.open(fileUrl, '_blank')}>
                 <img src={fileUrl} alt={file} className="w-full h-auto object-cover max-h-[300px]" />
                 <div className="absolute inset-0 bg-black/0 group-hover:bg-black/10 transition-colors flex items-center justify-center opacity-0 group-hover:opacity-100">
                    <span className="bg-black/70 text-white text-xs px-2 py-1 rounded">View Full</span>
                 </div>
               </div>
             ) : (
               <div className="p-4 flex flex-col items-center justify-center gap-2 h-[150px] bg-secondary/30">
                  <BarChart2 size={32} className="text-gray-400" />
                  <span className="text-sm font-medium">{file}</span>
                  <a 
                    href={fileUrl} 
                    target="_blank" 
                    rel="noopener noreferrer"
                    className="text-xs text-blue-500 hover:underline"
                  >
                    Download
                  </a>
               </div>
             )}
             <div className="px-3 py-2 bg-secondary/50 border-t border-border flex justify-between items-center">
                <span className="text-xs font-medium truncate" title={file}>{file}</span>
                <span className="text-[10px] text-gray-400 uppercase">Generated</span>
             </div>
          </div>
        );
      })}
    </div>
  );
};

// Custom Pre block with Copy functionality
const PreBlock: React.FC<any> = ({ children, ...props }) => {
  const [copied, setCopied] = useState(false);
  const preRef = useRef<HTMLPreElement>(null);

  const handleCopy = () => {
    if (preRef.current) {
        // We want to copy the text content. 
        // Note: pre contains a code element usually. innerText should work.
        const codeElement = preRef.current.querySelector('code');
        const text = codeElement ? codeElement.innerText : preRef.current.innerText;
        
        navigator.clipboard.writeText(text);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <div className="my-4 overflow-hidden rounded-lg border border-border bg-secondary/50 relative group">
      <div className="bg-secondary px-4 py-2 text-xs font-mono text-gray-500 flex items-center justify-between border-b border-border">
        <div className="flex items-center gap-2">
          <Terminal size={12} />
          <span>Code</span>
        </div>
        <button 
          onClick={handleCopy}
          className="flex items-center gap-1.5 text-gray-400 hover:text-foreground transition-colors opacity-0 group-hover:opacity-100"
          title="Copy code"
        >
            {copied ? <Check size={12} className="text-green-500" /> : <Copy size={12} />}
            <span className="text-[10px] font-medium">{copied ? 'Copied' : 'Copy'}</span>
        </button>
      </div>
      <pre ref={preRef} {...props} className="p-4 overflow-x-auto text-sm">
        {children}
      </pre>
    </div>
  );
};

const MessageBubble: React.FC<MessageBubbleProps> = ({ message, onFeedback }) => {
  const isUser = message.role === 'user';
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(message.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };
  
  // Custom renderer for table if detected in plain text
  const renderContent = () => {
    // If no content but has steps, don't show empty box
    if (!message.content && message.steps && message.steps.length > 0 && message.isLoading) {
      return null;
    }

    if (message.role === 'assistant') {
       const tableData = extractTableFromText(message.content);
       if (tableData) {
         return (
           <>
             <div dangerouslySetInnerHTML={{ __html: tableData.tableHtml }} />
             <div className="mt-4 whitespace-pre-wrap">{tableData.explanation}</div>
           </>
         );
       }
    }

    return (
      <div className="prose dark:prose-invert prose-sm max-w-none break-words">
        <ReactMarkdown 
          remarkPlugins={[remarkGfm]}
          components={{
            pre: PreBlock,
            code: ({node, inline, className, children, ...props}: any) => {
              return inline ? (
                <code className="bg-secondary px-1.5 py-0.5 rounded text-sm font-mono text-accent-foreground" {...props}>
                  {children}
                </code>
              ) : (
                <code className="block bg-transparent p-0 font-mono" {...props}>
                  {children}
                </code>
              );
            },
            table: ({node, ...props}) => (
              <div className="overflow-x-auto my-4 border border-border rounded-lg">
                <table className="w-full text-sm text-left" {...props} />
              </div>
            ),
            thead: ({node, ...props}) => <thead className="bg-primary text-xs uppercase font-semibold text-accent" {...props} />,
            th: ({node, ...props}) => <th className="px-4 py-3 border-b border-border" {...props} />,
            td: ({node, ...props}) => <td className="px-4 py-2 border-b border-border last:border-0" {...props} />,
            tr: ({node, ...props}) => <tr className="hover:bg-primary/50 transition-colors" {...props} />,
            a: ({node, ...props}) => <a className="text-blue-500 hover:underline" target="_blank" rel="noopener noreferrer" {...props} />,
          }}
        >
          {message.content}
        </ReactMarkdown>
      </div>
    );
  };

  return (
    <div className={`flex w-full px-4 md:px-8 py-6 gap-4 md:gap-6 ${isUser ? 'bg-transparent' : 'bg-primary/30 border-y border-transparent'}`}>
      <div className="flex-shrink-0 flex flex-col items-center">
        <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${isUser ? 'bg-accent/10 text-foreground' : 'bg-orange-500 text-white'}`}>
          {isUser ? <User size={18} /> : <Bot size={18} />}
        </div>
      </div>
      
      <div className="flex-1 min-w-0 space-y-2">
        <div className="flex items-center gap-2 mb-1">
          <span className="font-semibold text-sm">{isUser ? 'You' : 'Tahlil'}</span>
          <span className="text-xs text-gray-400">{new Date(message.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
        </div>

        {message.attachments && message.attachments.length > 0 && (
          <div className="flex flex-wrap gap-2 mb-3">
            {message.attachments.map((file, idx) => (
              <div key={idx} className="flex items-center gap-2 bg-secondary/50 border border-border rounded-lg px-3 py-2 text-xs font-medium">
                <FileText size={14} className="text-gray-500" />
                <span>{file.name}</span>
                <span className="text-gray-400">({(file.size / 1024).toFixed(1)}KB)</span>
              </div>
            ))}
          </div>
        )}
        
        {/* Process Steps Accordion (for AI response) */}
        {!isUser && message.steps && message.steps.length > 0 && (
          <StepsAccordion steps={message.steps} runId={message.runId} />
        )}
        
        {message.isLoading && (!message.steps || message.steps.length === 0) ? (
          <div className="flex items-center gap-2 text-gray-500">
             <Loader2 size={16} className="animate-spin" />
             <span className="text-sm animate-pulse">Initializing analysis...</span>
          </div>
        ) : (
          <div className="text-base leading-relaxed text-foreground">
            {renderContent()}
          </div>
        )}

        {/* Generated Files/Charts */}
        {!isUser && message.generatedFiles && message.generatedFiles.length > 0 && (
          <GeneratedFilesGrid runId={message.runId} files={message.generatedFiles} />
        )}

        {!isUser && !message.isLoading && (
          <div className="flex items-center gap-2 mt-4 pt-2">
             <button 
               onClick={handleCopy}
               className={`p-1.5 rounded transition-colors ${copied ? 'text-green-500 bg-green-500/10' : 'text-gray-400 hover:bg-secondary hover:text-foreground'}`} 
               title="Copy Message"
             >
               {copied ? <CheckCircle2 size={14} /> : <Copy size={14} />}
             </button>
             
             {onFeedback && (
               <>
                 <button 
                   onClick={() => onFeedback('positive')}
                   className={`p-1.5 rounded transition-colors ${message.feedback === 'positive' ? 'text-green-500 bg-green-500/10' : 'text-gray-400 hover:bg-secondary hover:text-foreground'}`} 
                   title="Helpful"
                 >
                   <ThumbsUp size={14} className={message.feedback === 'positive' ? 'fill-current' : ''} />
                 </button>
                 <button 
                   onClick={() => onFeedback('negative')}
                   className={`p-1.5 rounded transition-colors ${message.feedback === 'negative' ? 'text-red-500 bg-red-500/10' : 'text-gray-400 hover:bg-secondary hover:text-foreground'}`} 
                   title="Not helpful"
                 >
                   <ThumbsDown size={14} className={message.feedback === 'negative' ? 'fill-current' : ''} />
                 </button>
               </>
             )}
          </div>
        )}
      </div>
    </div>
  );
};

export default MessageBubble;
