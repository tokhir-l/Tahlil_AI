import os
import json
import subprocess
import re
import uuid
from typing import List, Dict, Tuple, Optional, Any
from pathlib import Path
import sys
import atexit
import yaml
from dataclasses import dataclass, asdict, field
from datetime import datetime
from provider import ModelProvider, GeminiProvider, OllamaProvider, OpenAIProvider

# =============================================================================
# CONFIGURATION & PROMPT TEMPLATES
# =============================================================================

with open("prompt.yaml", "r") as f:
    PROMPT_TEMPLATES = yaml.safe_load(f)

class ProgressTracker:
    """Tracks and persists progress of analysis pipeline."""
    
    def __init__(self, run_id: str, runs_dir: str = "runs"):
        self.run_id = run_id
        self.progress_file = Path(runs_dir) / run_id / "progress.json"
        self.progress_file.parent.mkdir(parents=True, exist_ok=True)
        self.steps = []
        self.current_step = None
        self._save_progress()
    
    def add_step(self, phase: str, step_name: str, status: str = "in_progress"):
        """Add a new step to progress tracking."""
        step = {
            "phase": phase,
            "name": step_name,
            "status": status,
            "timestamp": datetime.now().isoformat(),
            "message": ""
        }
        self.steps.append(step)
        self.current_step = len(self.steps) - 1
        self._save_progress()
        return step
    
    def update_step(self, status: str, message: str = ""):
        """Update the current step's status."""
        if self.current_step is not None:
            self.steps[self.current_step]["status"] = status
            self.steps[self.current_step]["message"] = message
            self.steps[self.current_step]["timestamp"] = datetime.now().isoformat()
            self._save_progress()
    
    def _save_progress(self):
        """Save progress to JSON file."""
        total_steps = len(self.steps)
        completed_steps = sum(1 for s in self.steps if s["status"] == "completed")
        progress_percentage = int((completed_steps / total_steps * 100)) if total_steps > 0 else 0
        
        progress_data = {
            "run_id": self.run_id,
            "total_steps": total_steps,
            "completed_steps": completed_steps,
            "progress_percentage": progress_percentage,
            "current_phase": self.steps[-1]["phase"] if self.steps else None,
            "current_step_name": self.steps[-1]["name"] if self.steps else None,
            "steps": self.steps
        }
        with open(self.progress_file, "w") as f:
            json.dump(progress_data, f, indent=2)
    
    def get_progress(self) -> Dict[str, Any]:
        """Get current progress data."""
        if self.progress_file.exists():
            with open(self.progress_file, "r") as f:
                data = json.load(f)
                # Calculate progress percentage
                total = data.get('total_steps', 0)
                completed = data.get('completed_steps', 0)
                if total > 0:
                    data['progress_percentage'] = int((completed / total) * 100)
                else:
                    data['progress_percentage'] = 0
                return data
        return {"run_id": self.run_id, "total_steps": 0, "completed_steps": 0, "steps": [], "progress_percentage": 0}

@dataclass
class DSConfig:
    """Centralized configuration for the entire pipeline."""
    run_id: str = None
    max_refinement_rounds: int = 5
    api_key: Optional[str] = None
    model_name: str = None
    interactive: bool = False
    auto_debug: bool = False
    # debug attempts set to 2 for reasonable iteration without infinite loops
    debug_attempts: float = 2
    execution_timeout: int = 60
    preserve_artifacts: bool = True
    runs_dir: str = "runs"
    data_dir: str = "data"
    code_library_dir: str = "code_library"
    agent_models: Dict[str, str] = field(default_factory=dict)
    
    def __post_init__(self):
        if self.run_id is None:
            self.run_id = datetime.now().strftime("%Y%m%d_%H%M%S") + f"_{uuid.uuid4().hex[:6]}"
        if self.agent_models is None:
            self.agent_models = {}




# =============================================================================
# ARTIFACT STORAGE SYSTEM
# =============================================================================

class ArtifactStorage:
    """Persistently stores every step of the pipeline for reproducibility."""
    
    def __init__(self, config: DSConfig):
        self.config = config
        self.run_dir = Path(config.runs_dir) / config.run_id
        self._setup_directories()
        
    def _setup_directories(self):
        """Create directory structure for this run."""
        dirs = [
            self.run_dir,
            self.run_dir / "steps",
            self.run_dir / "data_cache",
            self.run_dir / "logs",
            self.run_dir / "final_output"
        ]
        for d in dirs:
            d.mkdir(parents=True, exist_ok=True)
            
    def save_step(self, step_id: str, step_type: str, prompt: str, 
                  code: Optional[str], result: str, metadata: Dict[str, Any]):
        """Save all artifacts for a single pipeline step."""
        step_dir = self.run_dir / "steps" / step_id
        step_dir.mkdir(exist_ok=True)
        
        # Save prompt
        (step_dir / "prompt.md").write_text(prompt, encoding='utf-8')
        
        # Save generated code
        if code:
            (step_dir / "code.py").write_text(code, encoding='utf-8')
            
        # Save execution result
        (step_dir / "result.txt").write_text(result, encoding='utf-8')
        
        # Save metadata
        metadata.update({
            "timestamp": datetime.now().isoformat(),
            "step_type": step_type,
            "step_id": step_id
        })
        with open(step_dir / "metadata.json", "w") as f:
            json.dump(metadata, f, indent=2)
            
    def get_step(self, step_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a previous step's artifacts."""
        step_dirs = list(self.run_dir.glob(f"steps/{step_id}_*"))
        if not step_dirs:
            return None
        
        step_dir = step_dirs[0]
        return {
            "prompt": (step_dir / "prompt.md").read_text(encoding='utf-8'),
            "code": (step_dir / "code.py").read_text(encoding='utf-8') 
                   if (step_dir / "code.py").exists() else None,
            "result": (step_dir / "result.txt").read_text(encoding='utf-8'),
            "metadata": json.loads((step_dir / "metadata.json").read_text())
        }
    
    def list_steps(self) -> List[Dict[str, Any]]:
        """List all steps in chronological order."""
        steps = []
        for step_path in sorted(self.run_dir.glob("steps/*")):
            with open(step_path / "metadata.json") as f:
                metadata = json.load(f)
                steps.append(metadata)
        return steps
    
    def get_current_state(self) -> Dict[str, Any]:
        """Load the pipeline state."""
        state_file = self.run_dir / "pipeline_state.json"
        if state_file.exists():
            return json.loads(state_file.read_text())
        return {"current_step": 0, "completed_steps": [], "plan": [], "data_descriptions": {}}
    
    def save_state(self, state: Dict[str, Any]):
        """Save the pipeline state."""
        state_file = self.run_dir / "pipeline_state.json"
        state_file.write_text(json.dumps(state, indent=2))

# =============================================================================
# STATE MANAGEMENT & EXECUTION CONTROL
# =============================================================================

class PipelineController:
    """Manages pipeline execution with resume and editing capabilities."""
    
    def __init__(self, config: DSConfig, storage: ArtifactStorage, agent: 'TahlilAgent'):
        self.config = config
        self.storage = storage
        self.agent = agent
        self.logger = self._setup_logger()
        
    def _setup_logger(self):
        """Setup structured logging."""
        import logging
        log_file = self.storage.run_dir / "logs" / "pipeline.log"
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )
        return logging.getLogger(__name__)
    
    def should_execute_step(self, step_index: int) -> bool:
        """Check if step should be executed (for resuming)."""
        state = self.storage.get_current_state()
        return step_index >= state["current_step"]
    
    def execute_step(self, step_name: str, step_func, **kwargs) -> Any:
        """Execute a single step with full artifact preservation."""
        step_id = f"{self._get_next_step_index():03d}_{step_name}"
        
        self.logger.info(f"{'='*50}")
        self.logger.info(f"STEP {step_id}")
        self.logger.info(f"{'='*50}")
        
        # Execute the step
        result = step_func(**kwargs)
        
        # Save artifacts
        if self.config.preserve_artifacts:
            metadata = kwargs.copy()
            code = result.get("code") if isinstance(result, dict) else None
            self.storage.save_step(
                step_id=step_id,
                step_type=step_name,
                prompt=kwargs.get("prompt", ""),
                code=code,
                result=str(result.get("result") if isinstance(result, dict) else result),
                metadata=metadata
            )
        
        # Update state
        state = self.storage.get_current_state()
        state["current_step"] = self._get_next_step_index()
        state["completed_steps"].append(step_id)
        self.storage.save_state(state)
        
        # Interactive mode
        if self.config.interactive:
            input(f"Step {step_id} complete. Press Enter to continue...")
            
        return result
    
    def _get_next_step_index(self) -> int:
        """Get the next step index."""
        steps = self.storage.list_steps()
        return len(steps)
    
    def edit_last_step_code(self):
        """Allow manual editing of the last generated code."""
        steps = self.storage.list_steps()
        if not steps:
            return
        
        last_step = steps[-1]
        step_dir = self.storage.run_dir / "steps" / f"{last_step['step_id']}_{last_step['step_type']}"
        code_file = step_dir / "code.py"
        
        if code_file.exists():
            self.logger.info(f"Opening {code_file} for editing...")
            # Use system editor
            editor = os.environ.get('EDITOR', 'nano')
            subprocess.run([editor, str(code_file)])
            self.logger.info("Code updated. Re-executing step...")
            # Re-execute the modified code
            code = code_file.read_text()
            result, error = self.agent._execute_code(code)
            (step_dir / "result.txt").write_text(result)
            (step_dir / "metadata.json").write_text(json.dumps({**last_step, "edited": True}, indent=2))

# =============================================================================
# CORE AGENT (Refactored)
# =============================================================================

class TahlilAgent:
    """Tahlil Agent with persistent artifact storage."""
    
    def __init__(self, config: DSConfig):
        self.config = config
        self.storage = ArtifactStorage(config)
        self.progress = ProgressTracker(config.run_id, config.runs_dir)
        self.controller = PipelineController(config, self.storage, self)
        # Initialize providers for each agent type
        self.providers = {}
        default_model = config.model_name
        
        # List of known agents
        agents = ["ANALYZER", "PLANNER", "CODER", "VERIFIER", "ROUTER", "DEBUGGER", "FINALIZER"]
        
        def get_provider_for_model(model_name: str, config: DSConfig) -> ModelProvider:
            provider_cls = None
            for provider in [OllamaProvider, OpenAIProvider, GeminiProvider]:
                if provider.provider_instance(model_name):
                    provider_cls = provider
                    break

            if not provider_cls:
                raise ValueError(f"No provider found for model {model_name}")
            
            return provider_cls(config.api_key, model_name)

        for agent in agents:
            model_name = config.agent_models.get(agent, default_model)
            self.providers[agent] = get_provider_for_model(model_name, config)
            self.controller.logger.info(f"Initialized {agent} with model: {model_name}")
        
        # Setup execution environment
        self.exec_dir = Path(config.runs_dir) / config.run_id / "exec_env"
        self.exec_dir.mkdir(exist_ok=True)
        
        self._setup_tee_logging()
        
    def _setup_tee_logging(self):
        """Tee stdout/stderr to both console and log file."""
        log_path = self.storage.run_dir / "logs" / "execution.log"
        self.log_file = open(log_path, 'a', encoding='utf-8')
        
        class _Tee:
            def __init__(self, *writers):
                self.writers = writers
            def write(self, data):
                for w in self.writers:
                    try:
                        w.write(data)
                        w.flush()
                    except Exception:
                        pass
            def flush(self):
                for w in self.writers:
                    try:
                        w.flush()
                    except Exception:
                        pass
        
        sys.stdout = _Tee(sys.stdout, self.log_file)
        sys.stderr = _Tee(sys.stderr, self.log_file)
        
        atexit.register(lambda: self.log_file.close())
    
    def _call_model(self, agent_name: str, prompt: str) -> str:
        """Call the appropriate model provider for the agent."""
        try:
            provider = self.providers[agent_name]
            response_text = provider.generate_content(prompt)
            self.controller.logger.info(f"[{agent_name}] Response received ({len(response_text)} chars)")
            return response_text
        except Exception as e:
            error_msg = f"Error calling model for {agent_name}: {str(e)}"
            self.controller.logger.error(error_msg)
            raise
    
    def _extract_code_block(self, response: str, data_files: Optional[List[str]] = None) -> str:
        """Extract Python code from markdown blocks."""
        code_blocks = re.findall(r'```(?:python)?\n(.*?)\n```', response, re.DOTALL)
        code = code_blocks[0] if code_blocks else response.strip()
        # Fix common issues in generated code
        code = self._fix_generated_code(code, data_files)
        return code
    
    def _fix_generated_code(self, code: str, data_files: Optional[List[str]] = None) -> str:
        """Fix common issues in AI-generated code: typos, incorrect paths, and string escaping."""
        # Fix common typos
        code = code.replace('pd.read_read_csv', 'pd.read_csv')
        code = code.replace('read_read_csv', 'read_csv')
        
        # CRITICAL: Fix corrupted filenames - AI sometimes modifies hash filenames
        # Get list of actual files in data directory
        data_dir = Path(self.config.data_dir)
        actual_filenames = set()
        if data_dir.exists():
            actual_filenames = {f.name for f in data_dir.glob('*') if f.is_file()}
        
        # Also get correct filenames from data_files parameter
        correct_filenames = set()
        if data_files:
            for f in data_files:
                if Path(f).is_absolute():
                    correct_filenames.add(Path(f).name)
                else:
                    correct_filenames.add(f)
        
        # Combine both sources
        all_correct_filenames = actual_filenames | correct_filenames
        
        # Fix corrupted filenames in code
        if all_correct_filenames:
            def fix_corrupted_filename(match):
                quote = match.group(1)
                base_path = match.group(2) if match.group(2) else ''
                filename = match.group(3)
                closing_quote = match.group(4)
                
                # Check if this exact filename exists
                if filename in all_correct_filenames:
                    # Filename is correct, just fix path separators
                    fixed_path = base_path.replace('\\', '/') + filename
                    return f'{quote}{fixed_path}{closing_quote}'
                
                # Filename doesn't match - try to find correct one
                # Look for files with same extension and similar hash length
                file_ext = Path(filename).suffix
                for correct_filename in all_correct_filenames:
                    if correct_filename.endswith(file_ext) and len(correct_filename) > 30:
                        # Check if they're similar (corrupted hash - extra/missing characters)
                        # If lengths are close and extensions match, likely the same file
                        if abs(len(filename) - len(correct_filename)) <= 5:
                            # Replace with correct filename
                            fixed_path = base_path.replace('\\', '/') + correct_filename
                            self.controller.logger.warning(f"Fixed corrupted filename: {filename} -> {correct_filename}")
                            return f'{quote}{fixed_path}{closing_quote}'
                
                # No match found, return original (will fail at runtime with clear error)
                return match.group(0)
            
            # Match file paths in code: quote + (optional path) + filename + quote
            filename_pattern = r'(["\'])(.*?[/\\])([^/\\"\']+\.(?:csv|json|xlsx?|parquet|txt))(["\'])'
            code = re.sub(filename_pattern, fix_corrupted_filename, code)
        
        # CRITICAL: Fix Windows path string escaping issues
        # Python interprets backslashes in regular strings as escape sequences
        # We need to ensure paths use raw strings (r"...") or forward slashes
        
        # Pattern: Find file path assignments with Windows backslashes in regular strings
        # Match: variable = "path\with\backslashes" (not raw string)
        def fix_path_string(match):
            var_name = match.group(1)
            quote = match.group(2)  # Opening quote
            path = match.group(3)
            closing_quote = match.group(4)
            
            # Check if path contains backslashes that could cause escape issues
            if '\\' in path and not path.startswith('r'):
                # Convert to raw string or use forward slashes
                # Prefer raw string for Windows paths
                return f'{var_name} = r{quote}{path}{closing_quote}'
            return match.group(0)  # No change needed
        
        # Match: variable = "path" or variable = 'path' with backslashes
        path_assign_pattern = r'(\w+\s*=\s*)(["\'])([^"\']*\\[^"\']+\.(?:csv|json|xlsx?|parquet|txt))(["\'])'
        code = re.sub(path_assign_pattern, fix_path_string, code)
        
        # Also fix paths in function calls like pd.read_csv("path\with\backslashes")
        def fix_path_in_call(match):
            func_call = match.group(1)  # Function call part
            quote = match.group(2)
            path = match.group(3)
            closing_quote = match.group(4)
            
            if '\\' in path:
                # Use forward slashes instead (works on Windows too)
                path = path.replace('\\', '/')
                return f'{func_call}{quote}{path}{closing_quote}'
            return match.group(0)
        
        # Match: function("path\with\backslashes")
        path_call_pattern = r'(\w+\([^)]*)(["\'])([^"\']*\\[^"\']+\.(?:csv|json|xlsx?|parquet|txt))(["\'])'
        code = re.sub(path_call_pattern, fix_path_in_call, code)
        
        # Get actual data directory as absolute path
        data_dir = Path(self.config.data_dir).resolve()
        data_files_dir = data_dir  # data/files directory
        
        # Pattern 1: Fix paths that have "data/" but missing "files/"
        # Match: quote + (path with Tahlil) + "data/" + filename + quote
        # This handles: C:\...\Tahlil\data\file.csv -> C:\...\Tahlil\data\files\file.csv
        def fix_missing_files_dir(match):
            quote = match.group(1)
            base_path = match.group(2)  # Everything before "data/"
            filename = match.group(3)
            closing_quote = match.group(4)
            
            # Reconstruct path with data/files/
            # Use forward slashes to avoid escape issues, or ensure raw string
            if '\\' in base_path or '/' in base_path:
                # It's an absolute path, add data/files/
                # Use forward slashes (works on Windows)
                fixed_path = f'{base_path}data/files/{filename}'
                # If the original was a raw string, keep it raw
                if quote == "'" or quote == '"':
                    # Check if we need to make it a raw string
                    if '\\' in fixed_path:
                        return f'r{quote}{fixed_path}{closing_quote}'
                return f'{quote}{fixed_path}{closing_quote}'
            else:
                # Relative path, use absolute data_dir with forward slashes
                return f'{quote}{str(data_files_dir).replace(chr(92), "/")}/{filename}{closing_quote}'
        
        # Match: "data/" or "data\" followed by filename (but NOT "data/files/")
        pattern1 = r'(["\'])(.*?[/\\])?data[/\\](?!files[/\\])([^"\']+\.(?:csv|json|xlsx?|parquet|txt))(["\'])'
        code = re.sub(pattern1, fix_missing_files_dir, code)
        
        # Pattern 2: Fix paths that already have "data/files/" but with backslashes
        # Convert backslashes to forward slashes to avoid escape issues
        def normalize_path_sep(match):
            quote = match.group(1)
            full_path = match.group(2)
            closing_quote = match.group(3)
            # Convert backslashes to forward slashes (works on Windows)
            normalized = full_path.replace('\\', '/')
            # If original had backslashes, ensure it's a raw string or use forward slashes
            if '\\' in full_path and quote in ['"', "'"]:
                # Check if already raw string
                # If not, convert to forward slashes
                return f'{quote}{normalized}{closing_quote}'
            return f'{quote}{normalized}{closing_quote}'
        
        # Match paths with data/files/ that might have backslashes
        pattern2 = r'(["\'])(.*?data[/\\]files[/\\][^"\']+\.(?:csv|json|xlsx?|parquet|txt))(["\'])'
        code = re.sub(pattern2, normalize_path_sep, code)
        
        # Pattern 3: Fix absolute Windows paths specifically for Tahlil project
        # Handles: C:\...\Tahlil\data\file.csv
        pattern3 = r'(["\'])(.*?[Tt]ahlil[_\s\-]*[/\\])data[/\\](?!files[/\\])([^"\']+\.(?:csv|json|xlsx?|parquet|txt))(["\'])'
        def fix_tahlil_path(match):
            quote1 = match.group(1)
            prefix = match.group(2)  # Up to and including "Tahlil/"
            filename = match.group(3)
            quote2 = match.group(4)
            # Use forward slashes to avoid escape issues
            fixed_path = f'{prefix}data/files/{filename}'
            # If original had backslashes, ensure raw string or forward slashes
            if '\\' in fixed_path:
                fixed_path = fixed_path.replace('\\', '/')
            return f'{quote1}{fixed_path}{quote2}'
        code = re.sub(pattern3, fix_tahlil_path, code, flags=re.IGNORECASE)
        
        self.controller.logger.info("Code fixes applied: typos, path corrections, and string escaping")
        return code
    
    def _execute_code(self, code_script: str, data_files: Optional[List[str]] = None) -> Tuple[str, Optional[str]]:
        """Execute code in isolated environment."""
        self.controller.logger.info("Executing code...")
        
        # Extract file paths from code to validate (in case code uses different paths than data_files param)
        # This handles cases where finalizer generates code with absolute paths
        code_file_paths = []
        if data_files:
            # Also check for file paths mentioned in the code itself
            import re
            # Find file paths in code (look for patterns like r"path" or "path" with .csv, .xlsx, etc.)
            path_pattern = r'["\']([^"\']*[/\\][^"\']+\.(?:csv|json|xlsx?|parquet|txt))["\']'
            code_paths = re.findall(path_pattern, code_script)
            code_file_paths.extend(code_paths)
            
            # Add paths from data_files parameter
            for f in data_files:
                p = Path(f)
                if p.is_absolute():
                    code_file_paths.append(str(p))
                else:
                    # Resolve relative path
                    resolved = Path(self.config.data_dir) / f
                    code_file_paths.append(str(resolved.resolve()))
        
        # Validate all file paths (from both code and parameter)
        # But don't block execution - let Python handle file errors naturally
        if code_file_paths:
            missing = []
            for file_path in code_file_paths:
                p = Path(file_path)
                # Try exact path first
                if not p.exists():
                    # Try fixing path if it's missing files/ directory
                    if 'data' in str(p) and 'files' not in str(p):
                        # Try adding files/ directory
                        parts = list(p.parts)
                        try:
                            data_idx = next(i for i, part in enumerate(parts) if part == 'data')
                            # Insert 'files' after 'data'
                            fixed_parts = parts[:data_idx+1] + ['files'] + parts[data_idx+1:]
                            fixed_path = Path(*fixed_parts)
                            if fixed_path.exists():
                                continue  # File exists at fixed path, skip missing error
                        except (StopIteration, ValueError):
                            pass
                    missing.append(file_path)
            if missing:
                # Log warning but don't block - the code might have correct paths
                # The path fix function should have corrected them
                self.controller.logger.warning(f"Some file paths may not exist (will be checked at runtime): {missing}")
                # Continue execution - Python will raise FileNotFoundError if file truly missing
        
        # Write to persistent location
        exec_id = uuid.uuid4().hex[:8]
        exec_path = self.exec_dir / f"exec_{exec_id}.py"
        exec_path.write_text(code_script, encoding='utf-8')
        
        try:
            result = subprocess.run(
                [sys.executable, str(exec_path)],
                capture_output=True,
                text=True,
                timeout=self.config.execution_timeout,
                cwd=Path.cwd()
            )
            
            if result.returncode == 0:
                self.controller.logger.info("Execution successful")
                return result.stdout, None
            else:
                error_msg = result.stderr or "Unknown execution error"
                self.controller.logger.error(f"Execution failed: {error_msg}")
                return "", error_msg
                
        except subprocess.TimeoutExpired:
            return "", f"Timeout after {self.config.execution_timeout}s"
        except Exception as e:
            return "", f"Execution error: {str(e)}"

    def _execute_and_debug_code(self, code: str, data_files: List[str], data_desc: str) -> str:
        self.progress.add_step("PHASE 2", "Executing generated code", "in_progress")
        
        exec_result, error = self._execute_code(code, data_files)

        # Debug loop
        attempts = 0
        while error and self.config.auto_debug and attempts < self.config.debug_attempts:
            self.progress.update_step("in_progress", f"Debugging code (attempt {attempts + 1})")
            self.controller.logger.warning("Debugging...")
            code = self._debug_code(code, error, data_desc, data_files)
            exec_result, error = self._execute_code(code, data_files)
            attempts += 1

        if error:
            self.controller.logger.fatal(f"Execution error: {error}")
        return exec_result


    def analyze_data(self, filename: str, display_name: Optional[str] = None) -> Dict[str, str]:
        # Use display_name if provided (original filename), otherwise use stored filename
        file_name = display_name if display_name else Path(filename).name
        self.progress.add_step("PHASE 1", f"Analyzing data file: {file_name}", "in_progress")
        
        prompt = PROMPT_TEMPLATES["analyzer"].format(filename=filename)
        
        result = self.controller.execute_step(
            "analyzer",
            step_func=lambda prompt=prompt, **kwargs: self._call_model("ANALYZER", prompt),  # FIXED
            prompt=prompt,
            filename=filename
        )
        
        code = self._extract_code_block(result, [filename])
        exec_result = self._execute_and_debug_code(code, [filename], data_desc="")
        
        return {"code": code, "result": exec_result, "filename": filename}

    def plan_next_step(self, query: str, data_desc: str, current_plan: List[str], last_result: Optional[str]) -> str:
        if not current_plan:
            self.progress.add_step("PHASE 2", "Planning initial analysis strategy", "in_progress")
            prompt = PROMPT_TEMPLATES["planner_init"].format(question=query, summaries=data_desc)
            step_type = "planner_init"
        else:
            self.progress.add_step("PHASE 2", f"Planning refinement round {len(current_plan)}", "in_progress")
            plan_str = "\n".join(f"{i+1}. {step}" for i, step in enumerate(current_plan))
            prompt = PROMPT_TEMPLATES["planner_next"].format(
                question=query, summaries=data_desc,
                plan=plan_str, result=last_result, current_step=current_plan[-1]
            )
            step_type = "planner_next"
        
        return self.controller.execute_step(
            step_type,
            step_func=lambda prompt=prompt, **kwargs: self._call_model("PLANNER", prompt),  # FIXED
            prompt=prompt,
            query=query,
            plan_length=len(current_plan)
        )

    def generate_code(self, plan: List[str], data_desc: str, base_code: Optional[str] = None, data_files: Optional[List[str]] = None) -> str:
        self.progress.add_step("PHASE 2", f"Generating code for {len(plan)} step(s)", "in_progress")
        
        plan_str = "\n".join(f"{i+1}. {step}" for i, step in enumerate(plan))
        
        if not base_code:
            prompt = PROMPT_TEMPLATES["coder_init"].format(
                summaries=data_desc, plan=plan_str
            )
        else:
            prompt = PROMPT_TEMPLATES["coder_next"].format(
                summaries=data_desc, base_code=base_code,
                plan=plan_str, current_plan=plan[-1]
            )
        
        result = self.controller.execute_step(
            "coder",
            step_func=lambda prompt=prompt, **kwargs: self._call_model("CODER", prompt),  # FIXED
            prompt=prompt,
            plan_length=len(plan),
            has_base_code=base_code is not None
        )
        
        return self._extract_code_block(result, data_files)
        
    def verify_plan(self, plan: List[str], code: str, result: str, query: str, data_desc: str) -> str:
        self.progress.add_step("PHASE 2", "Verifying results", "in_progress")
        
        plan_str = "\n".join(f"{i+1}. {step}" for i, step in enumerate(plan))
        prompt = PROMPT_TEMPLATES["verifier"].format(
            plan=plan_str, code=code, result=result, question=query, summaries=data_desc, current_step=plan[-1]
        )
        
        return self.controller.execute_step(
            "verifier",
            step_func=lambda prompt=prompt, **kwargs: self._call_model("VERIFIER", prompt),  # FIXED
            prompt=prompt,
            plan_length=len(plan)
        ).strip()

    def route_plan(self, plan: List[str], query: str, result: str, data_desc: str) -> str:
        self.progress.add_step("PHASE 2", f"Routing (refinement round {len(plan)})", "in_progress")
        
        plan_str = "\n".join(f"{i+1}. {step}" for i, step in enumerate(plan))
        prompt = PROMPT_TEMPLATES["router"].format(
            question=query, summaries=data_desc,
            plan=plan_str, result=result, current_step=plan[-1]
        )
        
        return self.controller.execute_step(
            "router",
            step_func=lambda prompt=prompt, **kwargs: self._call_model("ROUTER", prompt),  # FIXED
            prompt=prompt,
            plan_length=len(plan)
        ).strip()

    def _debug_code(self, code: str, error: str, data_desc: str, filenames: List[str]) -> str:
        prompt = PROMPT_TEMPLATES["debugger"].format(
            summaries=data_desc, code=code,
            bug=error, filenames=", ".join(filenames)
        )
        
        result = self.controller.execute_step(
            "debugger",
            step_func=lambda prompt=prompt, **kwargs: self._call_model("DEBUGGER", prompt),  # FIXED
            prompt=prompt,
            error_type=error.split(":")[0]
        )
        
        return self._extract_code_block(result, filenames)

    def _generate_output_guidelines(self, query: str) -> str:
        """Generate output format guidelines based on user's query."""
        query_lower = query.lower()
        run_id = self.config.run_id
        
        # Check if user wants a dashboard
        if any(word in query_lower for word in ['dashboard', 'complete dashboard', 'full dashboard', 'comprehensive dashboard', 'multi-chart', 'multiple charts']):
            return f"""Generate code that creates a comprehensive interactive dashboard with multiple visualizations.
- Use plotly.graph_objects and plotly.subplots.make_subplots to create multiple charts in a single HTML file
- Create 4-6 relevant charts based on the data that answer different aspects of the question
- Arrange charts in a grid layout (2x2 or 2x3) using make_subplots
- Include key metrics/KPIs at the top if applicable
- Save the dashboard to 'runs/{run_id}/final_output/dashboard.html'
- CRITICAL: The code MUST print a clear, human-readable description of what the dashboard shows
- Print the description using print() statements - this is what will be displayed to the user
- Example: print("Dashboard created with 4 charts: (1) Sales trends over time, (2) Top products by revenue, (3) Sales by region, (4) Monthly comparison")
- Use appropriate chart types (bar, line, pie, scatter) based on the data
- Make charts interactive with hover tooltips
- The dashboard should comprehensively answer the user's question
- The code will be executed and only print() output will be shown"""
        
        # Check if user wants a graph/chart/visualization
        if any(word in query_lower for word in ['graph', 'chart', 'plot', 'visualize', 'visualization', 'bar chart', 'line chart', 'pie chart', 'scatter', 'histogram']):
            return f"""Generate code that creates and saves a visualization (chart/graph) based on the data.
- Use matplotlib or plotly to create the visualization
- Save the chart to 'runs/{run_id}/final_output/chart.png' (or .html for plotly)
- CRITICAL: The code MUST print a clear, human-readable description of what the chart shows
- Print the description using print() statements - this is what will be displayed to the user
- DO NOT just save the file without printing anything
- REMEMBER: If you don't use print(), nothing will be displayed to the user
- Example: print("Chart created showing the oldest 3 resigned employees with their ages and years of experience.")
- The chart should clearly answer the user's question
- The code will be executed and only print() output will be shown"""
        
        # Check if user wants a table (show, find, identify, give, list, display)
        if any(word in query_lower for word in ['table', 'list', 'show', 'show me', 'display', 'find', 'identify', 'give']):
            return """Generate code that prints the results in a clear, readable table format.
- CRITICAL: The code MUST use print() statements to output the results - this is the ONLY way the output will be visible
- DO NOT just process data - you MUST print() the results
- Print the data as a well-formatted table with clear column headers
- Use tab-separated or pipe-separated format for easy parsing, OR use pandas DataFrame print format
- After printing the table, print a brief explanation on a new line
- Format: First print the table, then print an explanation sentence
- Example format:
  print("Column1\\tColumn2\\tColumn3")
  print("Value1\\tValue2\\tValue3")
  print("\\nThe table above shows...")
- Make it easy to read and understand
- REMEMBER: If you don't use print(), nothing will be displayed to the user
- The code will be executed and only print() output will be shown"""
        
        # Check if user wants text/narrative answer
        if any(word in query_lower for word in ['explain', 'describe', 'tell me', 'what', 'how', 'why']):
            return """Generate code that prints a clear, natural language answer to the question.
- CRITICAL: The code MUST use print() statements to output the answer - this is the ONLY way the output will be visible
- DO NOT just process data - you MUST print() the answer
- Write in plain, conversational language
- Explain the findings clearly
- Avoid technical jargon when possible
- Make it easy for non-technical users to understand
- REMEMBER: If you don't use print(), nothing will be displayed to the user
- The code will be executed and only print() output will be shown"""
        
        # Default: flexible format based on what makes sense
        return f"""Generate code that provides the answer in the most appropriate format for the question.
- IMPORTANT: The code MUST use print() statements to output the answer or description
- If the question asks for a visualization, create and save a chart/graph to 'runs/{run_id}/final_output/' AND print a description
- If the question asks for data, present it in a clear table or list format using print() statements
- If the question asks for an explanation, provide a clear text answer using print() statements
- Save any charts/images to 'runs/{run_id}/final_output/'
- Always print a clear description of what was generated or what the results show
- Do NOT just save files or process data without printing anything - the printed output is what users see"""

    def finalize_solution(self, code: str, result: str, query: str, 
                        guidelines: str, data_desc: str, data_files: Optional[List[str]] = None) -> str:
        self.progress.add_step("PHASE 3", "Finalizing solution", "in_progress")
        
        prompt = PROMPT_TEMPLATES["finalizer"].format(
            summaries=data_desc, code=code,
            result=result, question=query, guidelines=guidelines
        )
        
        result = self.controller.execute_step(
            "finalizer",
            step_func=lambda prompt=prompt, **kwargs: self._call_model("FINALIZER", prompt),  # FIXED
            prompt=prompt
        )
        
        return self._extract_code_block(result, data_files)

    def run_pipeline(self, query: str, data_files: List[str]) -> Dict[str, Any]:
        """Main pipeline with full persistence and resume capability."""
        self.controller.logger.info(f"Starting pipeline: {self.config.run_id}")
        self.controller.logger.info(f"Query: {query}")
        self.controller.logger.info(f"Data files: {data_files}")
        
        # Check for resume state
        state = self.storage.get_current_state()
        if state["completed_steps"]:
            self.controller.logger.info(f"Resuming from step {state['current_step']}")
        
        # Ensure data directory exists
        Path(self.config.data_dir).mkdir(exist_ok=True)
        
        # Initialize variables that might be loaded from previous runs
        code = None
        exec_result = None
        
        # PHASE 1: Data Analysis
        if self.controller.should_execute_step(0):
            self.controller.logger.info("=== PHASE 1: ANALYZING DATA FILES ===")
            data_descriptions = {}
            absolute_data_files = []
            
            # Try to load original filenames from metadata
            filename_map = {}  # Maps stored filename -> original filename
            try:
                metadata_path = Path(self.config.runs_dir) / self.config.run_id / 'metadata.json'
                if metadata_path.exists():
                    import json
                    with open(metadata_path, 'r') as f:
                        metadata = json.load(f)
                        file_names = metadata.get('file_names', [])
                        # Create mapping: stored_filename -> original_filename
                        for i, stored_file in enumerate(data_files):
                            if i < len(file_names):
                                stored_name = Path(stored_file).name
                                filename_map[stored_name] = file_names[i]
            except Exception as e:
                self.controller.logger.warning(f"Could not load original filenames from metadata: {e}")
            
            for i, f in enumerate(data_files):
                self.controller.logger.info(f"Analyzing {f}...")
                abs_path = str(Path(self.config.data_dir).joinpath(f).resolve())
                absolute_data_files.append(abs_path)
                stored_name = Path(f).name
                display_name = filename_map.get(stored_name)
                analysis = self.analyze_data(abs_path, display_name=display_name)
                data_descriptions[abs_path] = analysis["result"]
            
            state = self.storage.get_current_state()
            state["data_descriptions"] = data_descriptions
            self.storage.save_state(state)
        else:
            # Load from previous run
            data_descriptions = state["data_descriptions"]
            absolute_data_files = list(data_descriptions.keys())
        
        data_desc_str = "\n".join([f"File: {k}\n{v}" for k, v in data_descriptions.items()])
        
        # PHASE 2: Iterative Planning & Execution
        if self.controller.should_execute_step(len(absolute_data_files)):
            self.controller.logger.info("=== PHASE 2: ITERATIVE PLANNING & VERIFICATION ===")
            plan = []
            plan.append(self.plan_next_step(query, data_desc_str, plan, ""))
            
            code = self.generate_code(plan, data_desc_str, data_files=absolute_data_files)
            exec_result = self._execute_and_debug_code(code, absolute_data_files, data_desc_str)
            
            # Refinement rounds
            for round_idx in range(self.config.max_refinement_rounds):
                self.controller.logger.info(f"--- Refinement Round {round_idx+1} ---")
                
                verdict = self.verify_plan(plan, code, exec_result, query, data_desc_str)
                
                if verdict.lower() == "yes":
                    self.controller.logger.info("Plan verified as sufficient!")
                    break
                
                routing = self.route_plan(plan, query, exec_result, data_desc_str)
                
                if "is wrong!" in routing:
                    # Truncate plan and retry
                    try:
                        step_to_remove = int(routing.split()[1]) - 1
                        plan = plan[:step_to_remove]
                        self.controller.logger.info(f"Truncated plan to step {step_to_remove}")
                    except:
                        plan = []
                else:
                    self.controller.logger.info("Adding new step...")
                
                # Generate next step
                next_plan = self.plan_next_step(query, data_desc_str, plan, exec_result)
                plan.append(next_plan)
                
                # Generate and execute new code
                code = self.generate_code(plan, data_desc_str, base_code=code, data_files=absolute_data_files)
                exec_result = self._execute_and_debug_code(code, absolute_data_files, data_desc_str)
            else:
                self.controller.logger.warning("Max refinement rounds reached")
        
        # Load code and exec_result from previous run if not defined (resuming case)
        if code is None or exec_result is None:
            steps = self.storage.list_steps()
            
            # Find the last step with code
            for step in reversed(steps):
                step_data = self.storage.get_step(step['step_id'])
                if step_data and step_data.get('code'):
                    code = step_data['code']
                    exec_result = step_data.get('result', '')
                    self.controller.logger.info(f"Loaded code and results from step {step['step_id']}")
                    break
            
            # If still not found, this is an error
            if code is None:
                raise ValueError("Could not load code from previous steps. Please ensure the pipeline has been run before.")
            if exec_result is None:
                exec_result = ""  # Default to empty string if not found
        
        # PHASE 3: Finalization
        self.controller.logger.info("=== PHASE 3: FINALIZING ===")
        
        # Generate dynamic guidelines based on user's request
        guidelines = self._generate_output_guidelines(query)
        
        final_code = self.finalize_solution(
            code, exec_result, query,
            guidelines,
            data_desc_str,
            absolute_data_files
        )
        
        # Execute the finalizer code
        final_result, final_error = self._execute_code(final_code, absolute_data_files)
        
        # CRITICAL: The finalizer code MUST produce output via print() statements
        # If execution failed or returned empty, log the error
        if final_error:
            self.controller.logger.error(f"Finalizer execution failed: {final_error}")
            # If there's an error, try to use previous result as fallback
            if exec_result and exec_result.strip():
                self.controller.logger.warning("Using previous execution result due to finalizer error")
                final_result = exec_result
            else:
                final_result = f"Error executing final code: {final_error}"
        elif not final_result or not final_result.strip():
            self.controller.logger.warning("Final execution returned empty result - code may not have print() statements")
            # Use previous result if available
            if exec_result and exec_result.strip():
                final_result = exec_result
            else:
                final_result = "No output generated. The code may need print() statements to display results."
        
        # Ensure we're not saving code as result
        # Check if result looks like code (has imports/definitions but no actual output)
        if final_result and any(keyword in final_result for keyword in ['import ', 'def ', 'class ', 'if __name__']):
            lines = final_result.split('\n')
            # Count actual output lines (not code structure)
            output_lines = [l for l in lines if l.strip() and 
                          not l.strip().startswith('#') and 
                          not any(kw in l for kw in ['import', 'def', 'class', 'if ', 'for ', 'while ', '=', 'try:', 'except:'])]
            
            # If mostly code with little output, it's likely the code itself
            if len(output_lines) < len(lines) * 0.3:  # Less than 30% actual output
                self.controller.logger.warning("Final result appears to be code, not execution output")
                if exec_result and exec_result.strip():
                    final_result = exec_result
                else:
                    final_result = "Code was generated but execution produced no output. Please ensure the code includes print() statements."
        
        # Save final output
        output_file = self.storage.run_dir / "final_output" / "result.json"
        # Ensure we're saving the execution output, not the code
        # If final_result looks like code (has imports but no actual output), try to get execution output from step
        if final_result and any(keyword in final_result for keyword in ['import ', 'def ', 'class ']):
            # Check if this is actually code without output
            lines = final_result.split('\n')
            # Count print statements vs code lines
            print_count = sum(1 for line in lines if 'print(' in line)
            code_count = sum(1 for line in lines if any(kw in line for kw in ['import ', 'def ', 'class ', 'if ', 'for ', 'while ']))
            
            # If it's mostly code with few/no print statements, it's likely the code itself
            if code_count > 5 and print_count < 3:
                self.controller.logger.warning("Final result appears to be code, checking for execution output in finalizer step")
                # Try to get the actual execution result from the finalizer step
                finalizer_steps = [s for s in self.storage.list_steps() if 'finalizer' in s.get('step_type', '').lower()]
                if finalizer_steps:
                    last_finalizer = finalizer_steps[-1]
                    step_dir = self.storage.run_dir / "steps" / f"{last_finalizer.get('step_id', '')}"
                    result_file = step_dir / "result.txt"
                    if result_file.exists():
                        step_result = result_file.read_text(encoding='utf-8').strip()
                        if step_result and not any(kw in step_result for kw in ['import ', 'def ', 'class ']):
                            # This looks like actual output, use it
                            final_result = step_result
                            self.controller.logger.info("Using execution output from finalizer step")
        
        # Save the result (should be execution output, not code)
        output_file.write_text(final_result, encoding='utf-8')
        
        self.controller.logger.info("Pipeline completed successfully!")
        
        return {
            "run_id": self.config.run_id,
            "final_result": final_result,
            "output_file": str(output_file),
            "total_steps": len(self.storage.list_steps())
        }
# =============================================================================
# CLI & USAGE
# =============================================================================

def main():
    """CLI interface with resume and edit capabilities."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Tahlil Data Science Agent")
    parser.add_argument("--resume", type=str, help="Resume from run ID")
    parser.add_argument("--interactive", action="store_true", help="Pause between steps")
    parser.add_argument("--edit-last", action="store_true", help="Edit last generated code")
    parser.add_argument("--data-files", nargs="+", help="Data files to analyze")
    parser.add_argument("--query", type=str, help="Analysis query")
    parser.add_argument("--max-rounds", type=int, help="Max refinement rounds")
    parser.add_argument("--config", type=str, help="Path to config file", default="config.yaml")
    args = parser.parse_args()

    # Load config from file to set defaults
    try:
        with open(args.config, 'r') as f:
            config_defaults = yaml.safe_load(f) or {}
    except FileNotFoundError:
        config_defaults = {}
    
    # Combine config sources (CLI args take precedence)
    config_params = {
        'run_id': args.resume or config_defaults.get('run_id'),
        'interactive': args.interactive or config_defaults.get('interactive', False),
        'max_refinement_rounds': args.max_rounds or config_defaults.get('max_refinement_rounds', 5),
        'model_name': config_defaults.get('model_name'),
        'preserve_artifacts': config_defaults.get('preserve_artifacts', True),
        # Load API key from config file or environment variable
        'api_key': config_defaults.get('api_key') or os.getenv('GEMINI_API_KEY') or os.getenv('OPENAI_API_KEY')
    }
    
    # Filter out None values so dataclass defaults are used
    config_params = {k: v for k, v in config_params.items() if v is not None}
    
    config = DSConfig(**config_params)
    if not config.model_name:
        parser.error("Model name must be specified via config file.")
    
    agent = TahlilAgent(config)
    
    # Edit mode
    if args.edit_last and config.run_id:
        agent.controller.edit_last_step_code()
        return

    # Check for required arguments for a new run
    query = args.query or config_defaults.get('query')
    data_files = args.data_files or config_defaults.get('data_files')

    if not (data_files and query):
        parser.error("--data-files and --query are required for a new run.")

    # Run pipeline
    result = agent.run_pipeline(query, data_files)
    print(f"\n{'='*60}")
    print(f"RUN COMPLETED: {result['run_id']}")
    print(f"OUTPUT: {result['output_file']}")
    print(f"FINAL RESULT:\n{result['final_result']}")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()