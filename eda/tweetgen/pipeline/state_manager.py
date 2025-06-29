"""
State Manager for Tweet Generation Pipeline

Handles checkpointing, progress tracking, and resume functionality.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import uuid


class StateManager:
    """Manages pipeline state and checkpointing."""
    
    def __init__(self, conference: str, output_dir: str = "eda/tweetgen/outputs"):
        self.conference = conference
        self.output_dir = Path(output_dir)
        self.conference_dir = self.output_dir / conference
        self.checkpoints_dir = self.conference_dir / "checkpoints"
        self.state_file = self.checkpoints_dir / "processing_state.json"
        
        # Ensure directories exist
        self.checkpoints_dir.mkdir(parents=True, exist_ok=True)
        
        # Pipeline steps in order
        self.pipeline_steps = [
            "initialize",
            "data_extraction", 
            "sqlite_processing",
            "author_enrichment",
            "analytics_processing",
            "tweet_generation",
            "markdown_generation",
            "finalize"
        ]
        
    def initialize_state(self, force_restart: bool = False) -> Dict[str, Any]:
        """Initialize or load existing state."""
        if force_restart or not self.state_file.exists():
            pipeline_id = f"{self.conference}-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
            state = {
                "conference": self.conference,
                "pipeline_id": pipeline_id,
                "started_at": datetime.now().isoformat(),
                "current_step": "initialize",
                "completed_steps": [],
                "failed_steps": [],
                "progress": {
                    "total_papers": 0,
                    "processed_papers": 0,
                    "enriched_authors": 0,
                    "total_authors": 0
                },
                "checkpoints": {},
                "errors": []
            }
            self.save_state(state)
            return state
        else:
            return self.load_state()
    
    def load_state(self) -> Dict[str, Any]:
        """Load existing state from file."""
        if not self.state_file.exists():
            raise FileNotFoundError(f"State file not found: {self.state_file}")
        
        with open(self.state_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def save_state(self, state: Dict[str, Any]) -> None:
        """Save state to file atomically."""
        # Write to temporary file first, then rename for atomicity
        temp_file = self.state_file.with_suffix('.tmp')
        with open(temp_file, 'w', encoding='utf-8') as f:
            json.dump(state, f, indent=2, ensure_ascii=False)
        temp_file.rename(self.state_file)
    
    def mark_step_complete(self, step: str, metadata: Optional[Dict] = None) -> None:
        """Mark a pipeline step as completed."""
        state = self.load_state()
        
        if step not in state["completed_steps"]:
            state["completed_steps"].append(step)
        
        # Remove from failed steps if it was there
        if step in state["failed_steps"]:
            state["failed_steps"].remove(step)
        
        # Update checkpoint timestamp
        state["checkpoints"][step] = datetime.now().isoformat()
        
        # Add metadata if provided
        if metadata:
            if "step_metadata" not in state:
                state["step_metadata"] = {}
            state["step_metadata"][step] = metadata
        
        # Update current step to next step
        try:
            current_index = self.pipeline_steps.index(step)
            if current_index + 1 < len(self.pipeline_steps):
                state["current_step"] = self.pipeline_steps[current_index + 1]
            else:
                state["current_step"] = "completed"
        except ValueError:
            pass  # Step not in pipeline_steps
        
        self.save_state(state)
    
    def mark_step_failed(self, step: str, error: str) -> None:
        """Mark a pipeline step as failed."""
        state = self.load_state()
        
        if step not in state["failed_steps"]:
            state["failed_steps"].append(step)
        
        # Add error information
        error_info = {
            "step": step,
            "error": error,
            "timestamp": datetime.now().isoformat()
        }
        state["errors"].append(error_info)
        
        self.save_state(state)
    
    def update_progress(self, **kwargs) -> None:
        """Update progress counters."""
        state = self.load_state()
        state["progress"].update(kwargs)
        self.save_state(state)
    
    def is_step_completed(self, step: str) -> bool:
        """Check if a step is completed."""
        state = self.load_state()
        return step in state["completed_steps"]
    
    def get_next_step(self) -> Optional[str]:
        """Get the next step to execute."""
        state = self.load_state()
        current_step = state.get("current_step")
        
        if current_step == "completed":
            return None
        
        return current_step
    
    def can_resume_from(self, step: str) -> bool:
        """Check if pipeline can resume from a specific step."""
        if step not in self.pipeline_steps:
            return False
        
        state = self.load_state()
        step_index = self.pipeline_steps.index(step)
        
        # Check if all previous steps are completed
        for i in range(step_index):
            if self.pipeline_steps[i] not in state["completed_steps"]:
                return False
        
        return True
    
    def get_checkpoint_file(self, filename: str) -> Path:
        """Get path to a checkpoint file."""
        return self.checkpoints_dir / filename
    
    def save_checkpoint(self, filename: str, data: Any) -> None:
        """Save data to a checkpoint file."""
        checkpoint_file = self.get_checkpoint_file(filename)
        
        with open(checkpoint_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def load_checkpoint(self, filename: str) -> Any:
        """Load data from a checkpoint file."""
        checkpoint_file = self.get_checkpoint_file(filename)
        
        if not checkpoint_file.exists():
            return None
        
        with open(checkpoint_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def checkpoint_exists(self, filename: str) -> bool:
        """Check if a checkpoint file exists."""
        return self.get_checkpoint_file(filename).exists()
    
    def get_status(self) -> Dict[str, Any]:
        """Get current pipeline status."""
        if not self.state_file.exists():
            return {"status": "not_started"}
        
        state = self.load_state()
        
        total_steps = len(self.pipeline_steps)
        completed_steps = len(state["completed_steps"])
        
        status = {
            "conference": state["conference"],
            "pipeline_id": state["pipeline_id"],
            "started_at": state["started_at"],
            "current_step": state["current_step"],
            "progress_percentage": (completed_steps / total_steps) * 100,
            "completed_steps": state["completed_steps"],
            "failed_steps": state["failed_steps"],
            "progress": state["progress"],
            "errors": state.get("errors", [])
        }
        
        if state["current_step"] == "completed":
            status["status"] = "completed"
            status["completed_at"] = state["checkpoints"].get("finalize")
        elif state["failed_steps"]:
            status["status"] = "failed"
        else:
            status["status"] = "running"
        
        return status
    
    def cleanup_checkpoints(self, keep_final: bool = True) -> None:
        """Clean up checkpoint files."""
        if not keep_final:
            # Remove all checkpoint files
            for file in self.checkpoints_dir.glob("*.json"):
                if file != self.state_file:
                    file.unlink()
        else:
            # Keep only final outputs and state
            keep_files = {
                "processing_state.json",
                "tweet_thread.json", 
                "enriched_authors.json",
                "processed_analytics.json"
            }
            
            for file in self.checkpoints_dir.glob("*.json"):
                if file.name not in keep_files:
                    file.unlink()
