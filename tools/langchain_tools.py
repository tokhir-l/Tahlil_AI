"""
LangChain Integration for Tahlil Platform.
Provides enhanced AI workflow capabilities using LangChain.
"""

from typing import Any, Dict, List, Optional
import logging
from .base import ToolProvider, ToolCategory, ToolResult

logger = logging.getLogger(__name__)


class LangChainProvider(ToolProvider):
    """
    Integration with LangChain for enhanced AI workflows.
    Supports chains, agents, RAG, and more.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self._llm = None
        self._embeddings = None
    
    @property
    def name(self) -> str:
        return "langchain"
    
    @property
    def category(self) -> ToolCategory:
        return ToolCategory.WORKFLOW
    
    @property
    def description(self) -> str:
        return "LangChain for AI chains, agents, RAG, and advanced workflows"
    
    @property
    def dependencies(self) -> List[str]:
        return ["langchain", "langchain-community"]
    
    @property
    def capabilities(self) -> List[str]:
        return [
            "chain_execution",
            "agent_creation",
            "rag_pipeline",
            "document_qa",
            "text_splitting",
            "embedding_generation",
            "prompt_templates"
        ]
    
    def _check_availability(self) -> bool:
        try:
            # Auto-install langchain if needed
            from .dependency_manager import check_and_install
            success, _ = check_and_install('langchain', 'langchain')
            if not success:
                return False
            
            import langchain
            return True
        except ImportError:
            return False
    
    def _initialize(self) -> ToolResult:
        try:
            from langchain.prompts import PromptTemplate
            from langchain.chains import LLMChain
            from langchain.text_splitter import RecursiveCharacterTextSplitter
            
            self._PromptTemplate = PromptTemplate
            self._LLMChain = LLMChain
            self._TextSplitter = RecursiveCharacterTextSplitter
            
            return ToolResult(success=True)
        except Exception as e:
            return ToolResult(success=False, error=str(e))
    
    def execute(self, operation: str, **kwargs) -> ToolResult:
        """Execute a LangChain operation."""
        operations = {
            'prompt_template': self._create_prompt_template,
            'text_split': self._split_text,
            'summarize_chain': self._summarize_chain,
            'qa_chain': self._qa_chain,
            'analyze_documents': self._analyze_documents,
        }
        
        if operation not in operations:
            return ToolResult(
                success=False,
                error=f"Unknown operation '{operation}'. Available: {list(operations.keys())}"
            )
        
        try:
            return operations[operation](**kwargs)
        except Exception as e:
            logger.error(f"LangChain {operation} failed: {e}")
            return ToolResult(success=False, error=str(e))
    
    def _create_prompt_template(self, template: str, input_variables: List[str], **kwargs) -> ToolResult:
        """Create a prompt template."""
        prompt = self._PromptTemplate(
            template=template,
            input_variables=input_variables
        )
        
        # If values provided, format the prompt
        if kwargs:
            formatted = prompt.format(**{k: v for k, v in kwargs.items() if k in input_variables})
            return ToolResult(
                success=True,
                data={
                    'formatted_prompt': formatted,
                    'template': template,
                    'variables': input_variables
                }
            )
        
        return ToolResult(
            success=True,
            data={
                'template': template,
                'variables': input_variables
            }
        )
    
    def _split_text(self, text: str, chunk_size: int = 1000, chunk_overlap: int = 200, **kwargs) -> ToolResult:
        """Split text into chunks."""
        splitter = self._TextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
        
        chunks = splitter.split_text(text)
        
        return ToolResult(
            success=True,
            data={
                'chunks': chunks,
                'chunk_count': len(chunks),
                'chunk_size': chunk_size,
                'overlap': chunk_overlap
            }
        )
    
    def _summarize_chain(self, text: str, **kwargs) -> ToolResult:
        """Create and run a summarization chain."""
        # This would require an LLM to be configured
        # For now, return template code
        return ToolResult(
            success=True,
            data={
                'message': 'Summarization chain created. Configure LLM to execute.',
                'text_length': len(text)
            },
            metadata={'requires_llm': True}
        )
    
    def _qa_chain(self, question: str, context: str, **kwargs) -> ToolResult:
        """Create and run a QA chain."""
        return ToolResult(
            success=True,
            data={
                'message': 'QA chain created. Configure LLM to execute.',
                'question': question,
                'context_length': len(context)
            },
            metadata={'requires_llm': True}
        )
    
    def _analyze_documents(self, documents: List[str], query: str = None, **kwargs) -> ToolResult:
        """Analyze multiple documents."""
        # Split each document
        all_chunks = []
        for i, doc in enumerate(documents):
            chunks = self._TextSplitter(chunk_size=1000, chunk_overlap=200).split_text(doc)
            for j, chunk in enumerate(chunks):
                all_chunks.append({
                    'document_index': i,
                    'chunk_index': j,
                    'content': chunk,
                    'length': len(chunk)
                })
        
        return ToolResult(
            success=True,
            data={
                'total_documents': len(documents),
                'total_chunks': len(all_chunks),
                'chunks': all_chunks[:10],  # Return first 10 for preview
                'query': query
            }
        )
    
    def generate_code(self, operation: str, **kwargs) -> str:
        """Generate Python code for LangChain operations."""
        code_templates = {
            'prompt_template': '''
from langchain.prompts import PromptTemplate

# Create prompt template
template = """{template}"""

prompt = PromptTemplate(
    template=template,
    input_variables={input_variables}
)

# Format with values
formatted = prompt.format({format_args})
print(formatted)
''',
            'text_split': '''
from langchain.text_splitter import RecursiveCharacterTextSplitter

text = """{text}"""

splitter = RecursiveCharacterTextSplitter(
    chunk_size={chunk_size},
    chunk_overlap={chunk_overlap}
)

chunks = splitter.split_text(text)
print(f"Split into {{len(chunks)}} chunks")
for i, chunk in enumerate(chunks):
    print(f"\\nChunk {{i+1}}: {{chunk[:100]}}...")
''',
            'summarize_chain': '''
from langchain.chains.summarize import load_summarize_chain
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.docstore.document import Document

# Initialize LLM
llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash")

# Create documents
docs = [Document(page_content="{text}")]

# Create and run chain
chain = load_summarize_chain(llm, chain_type="stuff")
summary = chain.run(docs)
print(summary)
''',
            'qa_chain': '''
from langchain.chains import RetrievalQA
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings

# Initialize components
llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash")
embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")

# Create vector store from documents
texts = ["{context}"]
vectorstore = FAISS.from_texts(texts, embeddings)

# Create QA chain
qa_chain = RetrievalQA.from_chain_type(
    llm=llm,
    chain_type="stuff",
    retriever=vectorstore.as_retriever()
)

# Ask question
answer = qa_chain.run("{question}")
print(answer)
'''
        }
        
        template = code_templates.get(operation, f"# Code for {operation} not available")
        return template.format(**kwargs) if kwargs else template
    
    def get_operations(self) -> List[Dict[str, Any]]:
        return [
            {
                'name': 'prompt_template',
                'description': 'Create a prompt template',
                'params': ['template', 'input_variables']
            },
            {
                'name': 'text_split',
                'description': 'Split text into chunks',
                'params': ['text', 'chunk_size', 'chunk_overlap']
            },
            {
                'name': 'summarize_chain',
                'description': 'Create summarization chain',
                'params': ['text']
            },
            {
                'name': 'qa_chain',
                'description': 'Create QA chain',
                'params': ['question', 'context']
            },
            {
                'name': 'analyze_documents',
                'description': 'Analyze multiple documents',
                'params': ['documents', 'query']
            }
        ]
