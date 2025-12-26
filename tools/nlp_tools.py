"""
NLP Tools for Tahlil Platform.
Provides integration with spaCy and Hugging Face Transformers.
"""

from typing import Any, Dict, List, Optional
import logging
from .base import ToolProvider, ToolCategory, ToolResult

logger = logging.getLogger(__name__)


class SpacyProvider(ToolProvider):
    """
    Integration with spaCy for natural language processing.
    Supports tokenization, NER, POS tagging, and more.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self._nlp = None
        self._model_name = config.get('model', 'en_core_web_sm') if config else 'en_core_web_sm'
    
    @property
    def name(self) -> str:
        return "spacy"
    
    @property
    def category(self) -> ToolCategory:
        return ToolCategory.NLP
    
    @property
    def description(self) -> str:
        return "Natural language processing with spaCy: tokenization, NER, POS tagging"
    
    @property
    def dependencies(self) -> List[str]:
        return ["spacy"]
    
    @property
    def capabilities(self) -> List[str]:
        return [
            "tokenization",
            "named_entity_recognition",
            "pos_tagging",
            "dependency_parsing",
            "lemmatization",
            "sentence_segmentation",
            "similarity_analysis"
        ]
    
    def _check_availability(self) -> bool:
        try:
            # Auto-install spacy if needed
            from .dependency_manager import check_and_install
            success, _ = check_and_install('spacy', 'spacy')
            if not success:
                return False
            
            import spacy
            return True
        except ImportError:
            return False
    
    def _initialize(self) -> ToolResult:
        try:
            import spacy
            
            # Try to load the model
            try:
                self._nlp = spacy.load(self._model_name)
            except OSError:
                # Model not installed, try downloading
                logger.info(f"Downloading spaCy model: {self._model_name}")
                spacy.cli.download(self._model_name)
                self._nlp = spacy.load(self._model_name)
            
            return ToolResult(
                success=True,
                metadata={'model': self._model_name, 'version': spacy.__version__}
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e))
    
    def execute(self, operation: str, **kwargs) -> ToolResult:
        """Execute an NLP operation."""
        operations = {
            'analyze': self._analyze_text,
            'entities': self._extract_entities,
            'pos_tags': self._pos_tagging,
            'tokenize': self._tokenize,
            'lemmatize': self._lemmatize,
            'sentences': self._sentence_segmentation,
            'similarity': self._calculate_similarity,
        }
        
        if operation not in operations:
            return ToolResult(
                success=False,
                error=f"Unknown operation '{operation}'. Available: {list(operations.keys())}"
            )
        
        try:
            return operations[operation](**kwargs)
        except Exception as e:
            logger.error(f"spaCy {operation} failed: {e}")
            return ToolResult(success=False, error=str(e))
    
    def _analyze_text(self, text: str, **kwargs) -> ToolResult:
        """Perform full text analysis."""
        doc = self._nlp(text)
        
        return ToolResult(
            success=True,
            data={
                'tokens': [
                    {
                        'text': token.text,
                        'lemma': token.lemma_,
                        'pos': token.pos_,
                        'tag': token.tag_,
                        'dep': token.dep_,
                        'is_stop': token.is_stop
                    }
                    for token in doc
                ],
                'entities': [
                    {
                        'text': ent.text,
                        'label': ent.label_,
                        'start': ent.start_char,
                        'end': ent.end_char
                    }
                    for ent in doc.ents
                ],
                'sentences': [sent.text for sent in doc.sents],
                'noun_chunks': [chunk.text for chunk in doc.noun_chunks]
            },
            metadata={'token_count': len(doc), 'sentence_count': len(list(doc.sents))}
        )
    
    def _extract_entities(self, text: str, **kwargs) -> ToolResult:
        """Extract named entities from text."""
        doc = self._nlp(text)
        
        entities = [
            {
                'text': ent.text,
                'label': ent.label_,
                'description': ent.label_,
                'start': ent.start_char,
                'end': ent.end_char
            }
            for ent in doc.ents
        ]
        
        # Group by entity type
        by_type = {}
        for ent in entities:
            if ent['label'] not in by_type:
                by_type[ent['label']] = []
            by_type[ent['label']].append(ent['text'])
        
        return ToolResult(
            success=True,
            data={
                'entities': entities,
                'by_type': by_type,
                'entity_count': len(entities)
            }
        )
    
    def _pos_tagging(self, text: str, **kwargs) -> ToolResult:
        """Perform part-of-speech tagging."""
        doc = self._nlp(text)
        
        return ToolResult(
            success=True,
            data={
                'tokens': [
                    {
                        'text': token.text,
                        'pos': token.pos_,
                        'tag': token.tag_,
                        'explanation': token.explain(token.tag_) if hasattr(token, 'explain') else ''
                    }
                    for token in doc
                ]
            }
        )
    
    def _tokenize(self, text: str, **kwargs) -> ToolResult:
        """Tokenize text."""
        doc = self._nlp(text)
        
        return ToolResult(
            success=True,
            data={
                'tokens': [token.text for token in doc],
                'token_count': len(doc)
            }
        )
    
    def _lemmatize(self, text: str, **kwargs) -> ToolResult:
        """Lemmatize text."""
        doc = self._nlp(text)
        
        return ToolResult(
            success=True,
            data={
                'lemmas': [
                    {'original': token.text, 'lemma': token.lemma_}
                    for token in doc
                ]
            }
        )
    
    def _sentence_segmentation(self, text: str, **kwargs) -> ToolResult:
        """Split text into sentences."""
        doc = self._nlp(text)
        
        return ToolResult(
            success=True,
            data={
                'sentences': [sent.text.strip() for sent in doc.sents],
                'sentence_count': len(list(doc.sents))
            }
        )
    
    def _calculate_similarity(self, text1: str, text2: str, **kwargs) -> ToolResult:
        """Calculate similarity between two texts."""
        doc1 = self._nlp(text1)
        doc2 = self._nlp(text2)
        
        similarity = doc1.similarity(doc2)
        
        return ToolResult(
            success=True,
            data={
                'similarity': similarity,
                'text1': text1[:100] + '...' if len(text1) > 100 else text1,
                'text2': text2[:100] + '...' if len(text2) > 100 else text2
            }
        )
    
    def generate_code(self, operation: str, **kwargs) -> str:
        """Generate Python code for NLP operations."""
        code_templates = {
            'entities': '''
import spacy

nlp = spacy.load("en_core_web_sm")
text = """{text}"""

doc = nlp(text)

print("Named Entities:")
for ent in doc.ents:
    print(f"  {{ent.text}} -> {{ent.label_}}")
''',
            'analyze': '''
import spacy

nlp = spacy.load("en_core_web_sm")
text = """{text}"""

doc = nlp(text)

print("Tokens and POS tags:")
for token in doc:
    print(f"  {{token.text}}: {{token.pos_}} ({{token.tag_}})")

print("\\nNamed Entities:")
for ent in doc.ents:
    print(f"  {{ent.text}} -> {{ent.label_}}")
'''
        }
        
        template = code_templates.get(operation, f"# Code for {operation} not available")
        return template.format(**kwargs) if kwargs else template
    
    def get_operations(self) -> List[Dict[str, Any]]:
        return [
            {'name': 'analyze', 'description': 'Full text analysis', 'params': ['text']},
            {'name': 'entities', 'description': 'Named entity recognition', 'params': ['text']},
            {'name': 'pos_tags', 'description': 'Part-of-speech tagging', 'params': ['text']},
            {'name': 'tokenize', 'description': 'Tokenization', 'params': ['text']},
            {'name': 'lemmatize', 'description': 'Lemmatization', 'params': ['text']},
            {'name': 'sentences', 'description': 'Sentence segmentation', 'params': ['text']},
            {'name': 'similarity', 'description': 'Text similarity', 'params': ['text1', 'text2']}
        ]


class HuggingFaceProvider(ToolProvider):
    """
    Integration with Hugging Face Transformers.
    Supports sentiment analysis, classification, summarization, and more.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self._pipelines: Dict[str, Any] = {}
    
    @property
    def name(self) -> str:
        return "huggingface"
    
    @property
    def category(self) -> ToolCategory:
        return ToolCategory.NLP
    
    @property
    def description(self) -> str:
        return "Hugging Face Transformers for sentiment analysis, summarization, translation, and more"
    
    @property
    def dependencies(self) -> List[str]:
        return ["transformers", "torch"]
    
    @property
    def capabilities(self) -> List[str]:
        return [
            "sentiment_analysis",
            "text_classification",
            "summarization",
            "translation",
            "question_answering",
            "text_generation",
            "zero_shot_classification"
        ]
    
    def _check_availability(self) -> bool:
        try:
            # Auto-install transformers and torch if needed
            from .dependency_manager import check_and_install
            transformers_success, _ = check_and_install('transformers', 'transformers')
            torch_success, _ = check_and_install('torch', 'torch')
            
            if not transformers_success or not torch_success:
                return False
            
            import transformers
            return True
        except ImportError:
            return False
    
    def _initialize(self) -> ToolResult:
        try:
            from transformers import pipeline
            self._pipeline_func = pipeline
            return ToolResult(success=True)
        except Exception as e:
            return ToolResult(success=False, error=str(e))
    
    def _get_pipeline(self, task: str, model: str = None):
        """Get or create a pipeline for a task."""
        key = f"{task}:{model}" if model else task
        
        if key not in self._pipelines:
            if model:
                self._pipelines[key] = self._pipeline_func(task, model=model)
            else:
                self._pipelines[key] = self._pipeline_func(task)
        
        return self._pipelines[key]
    
    def execute(self, operation: str, **kwargs) -> ToolResult:
        """Execute an NLP operation."""
        operations = {
            'sentiment': self._sentiment_analysis,
            'summarize': self._summarization,
            'translate': self._translation,
            'qa': self._question_answering,
            'generate': self._text_generation,
            'classify': self._classification,
            'zero_shot': self._zero_shot_classification,
        }
        
        if operation not in operations:
            return ToolResult(
                success=False,
                error=f"Unknown operation '{operation}'. Available: {list(operations.keys())}"
            )
        
        try:
            return operations[operation](**kwargs)
        except Exception as e:
            logger.error(f"HuggingFace {operation} failed: {e}")
            return ToolResult(success=False, error=str(e))
    
    def _sentiment_analysis(self, text: str, model: str = None, **kwargs) -> ToolResult:
        """Perform sentiment analysis."""
        pipe = self._get_pipeline('sentiment-analysis', model)
        
        if isinstance(text, str):
            text = [text]
        
        results = pipe(text)
        
        return ToolResult(
            success=True,
            data={
                'results': [
                    {
                        'text': t[:100] + '...' if len(t) > 100 else t,
                        'label': r['label'],
                        'score': r['score']
                    }
                    for t, r in zip(text, results)
                ]
            }
        )
    
    def _summarization(self, text: str, max_length: int = 130, min_length: int = 30, 
                       model: str = None, **kwargs) -> ToolResult:
        """Summarize text."""
        pipe = self._get_pipeline('summarization', model)
        
        result = pipe(text, max_length=max_length, min_length=min_length, do_sample=False)
        
        return ToolResult(
            success=True,
            data={
                'summary': result[0]['summary_text'],
                'original_length': len(text),
                'summary_length': len(result[0]['summary_text'])
            }
        )
    
    def _translation(self, text: str, src_lang: str = 'en', tgt_lang: str = 'fr',
                     model: str = None, **kwargs) -> ToolResult:
        """Translate text."""
        task = f"translation_{src_lang}_to_{tgt_lang}"
        pipe = self._get_pipeline(task, model)
        
        result = pipe(text)
        
        return ToolResult(
            success=True,
            data={
                'translation': result[0]['translation_text'],
                'source_language': src_lang,
                'target_language': tgt_lang
            }
        )
    
    def _question_answering(self, question: str, context: str, model: str = None, **kwargs) -> ToolResult:
        """Answer questions based on context."""
        pipe = self._get_pipeline('question-answering', model)
        
        result = pipe(question=question, context=context)
        
        return ToolResult(
            success=True,
            data={
                'answer': result['answer'],
                'score': result['score'],
                'start': result['start'],
                'end': result['end']
            }
        )
    
    def _text_generation(self, prompt: str, max_length: int = 50, num_return_sequences: int = 1,
                         model: str = None, **kwargs) -> ToolResult:
        """Generate text from prompt."""
        pipe = self._get_pipeline('text-generation', model)
        
        results = pipe(prompt, max_length=max_length, num_return_sequences=num_return_sequences)
        
        return ToolResult(
            success=True,
            data={
                'generated': [r['generated_text'] for r in results]
            }
        )
    
    def _classification(self, text: str, model: str = None, **kwargs) -> ToolResult:
        """Classify text."""
        pipe = self._get_pipeline('text-classification', model)
        
        if isinstance(text, str):
            text = [text]
        
        results = pipe(text)
        
        return ToolResult(
            success=True,
            data={
                'results': [
                    {'label': r['label'], 'score': r['score']}
                    for r in results
                ]
            }
        )
    
    def _zero_shot_classification(self, text: str, labels: List[str], 
                                   model: str = None, **kwargs) -> ToolResult:
        """Zero-shot text classification."""
        pipe = self._get_pipeline('zero-shot-classification', model)
        
        result = pipe(text, candidate_labels=labels)
        
        return ToolResult(
            success=True,
            data={
                'labels': result['labels'],
                'scores': result['scores'],
                'sequence': result['sequence']
            }
        )
    
    def generate_code(self, operation: str, **kwargs) -> str:
        """Generate Python code for HuggingFace operations."""
        code_templates = {
            'sentiment': '''
from transformers import pipeline

# Initialize sentiment analysis
classifier = pipeline("sentiment-analysis")

text = """{text}"""
result = classifier(text)

print(f"Sentiment: {{result[0]['label']}}")
print(f"Confidence: {{result[0]['score']:.2%}}")
''',
            'summarize': '''
from transformers import pipeline

# Initialize summarization
summarizer = pipeline("summarization")

text = """{text}"""
summary = summarizer(text, max_length={max_length}, min_length={min_length})

print("Summary:")
print(summary[0]['summary_text'])
'''
        }
        
        template = code_templates.get(operation, f"# Code for {operation} not available")
        return template.format(**kwargs) if kwargs else template
    
    def get_operations(self) -> List[Dict[str, Any]]:
        return [
            {'name': 'sentiment', 'description': 'Sentiment analysis', 'params': ['text', 'model']},
            {'name': 'summarize', 'description': 'Text summarization', 'params': ['text', 'max_length', 'min_length']},
            {'name': 'translate', 'description': 'Translation', 'params': ['text', 'src_lang', 'tgt_lang']},
            {'name': 'qa', 'description': 'Question answering', 'params': ['question', 'context']},
            {'name': 'generate', 'description': 'Text generation', 'params': ['prompt', 'max_length']},
            {'name': 'classify', 'description': 'Text classification', 'params': ['text', 'model']},
            {'name': 'zero_shot', 'description': 'Zero-shot classification', 'params': ['text', 'labels']}
        ]
