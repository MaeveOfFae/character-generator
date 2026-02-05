"""Batch compilation state management for resume functionality."""

import json
import uuid
from dataclasses import dataclass, asdict, field
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict


@dataclass
class CompletedSeed:
    """Record of a completed seed compilation."""
    seed: str
    draft_dir: str
    timestamp: str


@dataclass
class FailedSeed:
    """Record of a failed seed compilation."""
    seed: str
    error: str
    timestamp: str


@dataclass
class BatchState:
    """State for a batch compilation operation."""
    
    batch_id: str
    start_time: str
    total_seeds: int
    completed_seeds: List[Dict] = field(default_factory=list)
    failed_seeds: List[Dict] = field(default_factory=list)
    current_index: int = 0
    config_snapshot: Dict = field(default_factory=dict)
    input_file: Optional[str] = None
    status: str = "running"  # running, completed, cancelled
    
    def __post_init__(self):
        """Ensure batch_id is set."""
        if not self.batch_id:
            self.batch_id = str(uuid.uuid4())
        if not self.start_time:
            self.start_time = datetime.now().isoformat()
    
    def mark_completed(self, seed: str, draft_dir: str) -> None:
        """Mark a seed as successfully completed.
        
        Args:
            seed: The character seed
            draft_dir: Path to the generated draft directory
        """
        completed = {
            "seed": seed,
            "draft_dir": str(draft_dir),
            "timestamp": datetime.now().isoformat()
        }
        self.completed_seeds.append(completed)
        self.current_index += 1
    
    def mark_failed(self, seed: str, error: str) -> None:
        """Mark a seed as failed.
        
        Args:
            seed: The character seed
            error: Error message
        """
        failed = {
            "seed": seed,
            "error": str(error),
            "timestamp": datetime.now().isoformat()
        }
        self.failed_seeds.append(failed)
        self.current_index += 1
    
    def get_remaining_seeds(self, all_seeds: List[str]) -> List[str]:
        """Get list of seeds that haven't been processed yet.
        
        Args:
            all_seeds: Original list of all seeds
            
        Returns:
            List of unprocessed seeds
        """
        completed_seeds_set = {s["seed"] for s in self.completed_seeds}
        failed_seeds_set = {s["seed"] for s in self.failed_seeds}
        processed = completed_seeds_set | failed_seeds_set
        
        return [s for s in all_seeds if s not in processed]
    
    def mark_completed_status(self) -> None:
        """Mark the batch as completed."""
        self.status = "completed"
    
    def mark_cancelled(self) -> None:
        """Mark the batch as cancelled."""
        self.status = "cancelled"
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> "BatchState":
        """Create from dictionary."""
        return cls(**data)
    
    def save(self, state_dir: Optional[Path] = None) -> Path:
        """Save state to disk.
        
        Args:
            state_dir: Directory to save state file (defaults to .bpui-batch-state)
            
        Returns:
            Path to saved state file
        """
        if state_dir is None:
            state_dir = Path.cwd() / ".bpui-batch-state"
        
        state_dir.mkdir(exist_ok=True)
        
        # Use start time and batch ID for filename
        start_dt = datetime.fromisoformat(self.start_time)
        timestamp = start_dt.strftime("%Y%m%d_%H%M%S")
        filename = f"batch_{timestamp}_{self.batch_id[:8]}.json"
        state_file = state_dir / filename
        
        with open(state_file, "w") as f:
            json.dump(self.to_dict(), f, indent=2)
        
        return state_file
    
    @classmethod
    def load(cls, state_file: Path) -> "BatchState":
        """Load state from file.
        
        Args:
            state_file: Path to state file
            
        Returns:
            BatchState instance
        """
        with open(state_file) as f:
            data = json.load(f)
        return cls.from_dict(data)
    
    @classmethod
    def load_latest(cls, state_dir: Optional[Path] = None) -> Optional["BatchState"]:
        """Load the most recent batch state.
        
        Args:
            state_dir: Directory containing state files
            
        Returns:
            BatchState instance or None if no states found
        """
        if state_dir is None:
            state_dir = Path.cwd() / ".bpui-batch-state"
        
        if not state_dir.exists():
            return None
        
        # Find all state files
        state_files = sorted(state_dir.glob("batch_*.json"), reverse=True)
        
        if not state_files:
            return None
        
        # Load the most recent one
        return cls.load(state_files[0])
    
    @classmethod
    def find_resumable(cls, state_dir: Optional[Path] = None) -> Optional["BatchState"]:
        """Find a resumable batch state (status = running).
        
        Args:
            state_dir: Directory containing state files
            
        Returns:
            BatchState instance or None if no resumable state found
        """
        if state_dir is None:
            state_dir = Path.cwd() / ".bpui-batch-state"
        
        if not state_dir.exists():
            return None
        
        # Find all state files
        state_files = sorted(state_dir.glob("batch_*.json"), reverse=True)
        
        for state_file in state_files:
            try:
                state = cls.load(state_file)
                if state.status == "running":
                    return state
            except (json.JSONDecodeError, KeyError, TypeError):
                continue
        
        return None
    
    def delete_state_file(self, state_dir: Optional[Path] = None) -> None:
        """Delete the state file for this batch.
        
        Args:
            state_dir: Directory containing state files
        """
        if state_dir is None:
            state_dir = Path.cwd() / ".bpui-batch-state"
        
        if not state_dir.exists():
            return
        
        # Find state file matching this batch ID (exact match or prefix)
        for state_file in state_dir.glob("batch_*.json"):
            try:
                # Check if batch_id is in the filename
                if self.batch_id in state_file.name or self.batch_id[:8] in state_file.name:
                    state_file.unlink()
                    break
            except Exception:
                pass
    
    @staticmethod
    def cleanup_old_states(state_dir: Optional[Path] = None, days: int = 7) -> int:
        """Clean up old batch state files.
        
        Args:
            state_dir: Directory containing state files
            days: Delete states older than this many days
            
        Returns:
            Number of state files deleted
        """
        if state_dir is None:
            state_dir = Path.cwd() / ".bpui-batch-state"
        
        if not state_dir.exists():
            return 0
        
        cutoff_time = datetime.now().timestamp() - (days * 24 * 60 * 60)
        deleted_count = 0
        
        for state_file in state_dir.glob("batch_*.json"):
            try:
                if state_file.stat().st_mtime < cutoff_time:
                    state_file.unlink()
                    deleted_count += 1
            except Exception:
                pass
        
        return deleted_count
