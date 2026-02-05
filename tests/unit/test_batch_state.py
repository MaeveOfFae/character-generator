"""Tests for batch_state module."""

import pytest
from pathlib import Path
from datetime import datetime
import time

from bpui.batch_state import BatchState


def test_batch_state_creation():
    """Test basic batch state creation."""
    state = BatchState(
        batch_id="test-123",
        start_time="2026-02-05T10:00:00",
        total_seeds=10
    )
    
    assert state.batch_id == "test-123"
    assert state.start_time == "2026-02-05T10:00:00"
    assert state.total_seeds == 10
    assert state.current_index == 0
    assert state.status == "running"
    assert len(state.completed_seeds) == 0
    assert len(state.failed_seeds) == 0


def test_batch_state_auto_init():
    """Test batch state with auto-generated fields."""
    state = BatchState(
        batch_id="",
        start_time="",
        total_seeds=5
    )
    
    assert state.batch_id != ""  # Should be auto-generated
    assert state.start_time != ""  # Should be auto-generated


def test_mark_completed():
    """Test marking a seed as completed."""
    state = BatchState(
        batch_id="test",
        start_time="2026-02-05T10:00:00",
        total_seeds=3
    )
    
    state.mark_completed("Test seed 1", "/path/to/draft1")
    
    assert len(state.completed_seeds) == 1
    assert state.completed_seeds[0]["seed"] == "Test seed 1"
    assert state.completed_seeds[0]["draft_dir"] == "/path/to/draft1"
    assert state.current_index == 1


def test_mark_failed():
    """Test marking a seed as failed."""
    state = BatchState(
        batch_id="test",
        start_time="2026-02-05T10:00:00",
        total_seeds=3
    )
    
    state.mark_failed("Bad seed", "Parse error")
    
    assert len(state.failed_seeds) == 1
    assert state.failed_seeds[0]["seed"] == "Bad seed"
    assert state.failed_seeds[0]["error"] == "Parse error"
    assert state.current_index == 1


def test_get_remaining_seeds():
    """Test getting remaining seeds."""
    state = BatchState(
        batch_id="test",
        start_time="2026-02-05T10:00:00",
        total_seeds=5
    )
    
    all_seeds = ["seed1", "seed2", "seed3", "seed4", "seed5"]
    
    state.mark_completed("seed1", "/draft1")
    state.mark_completed("seed2", "/draft2")
    state.mark_failed("seed3", "error")
    
    remaining = state.get_remaining_seeds(all_seeds)
    
    assert len(remaining) == 2
    assert "seed4" in remaining
    assert "seed5" in remaining
    assert "seed1" not in remaining
    assert "seed2" not in remaining
    assert "seed3" not in remaining


def test_status_transitions():
    """Test status transitions."""
    state = BatchState(
        batch_id="test",
        start_time="2026-02-05T10:00:00",
        total_seeds=1
    )
    
    assert state.status == "running"
    
    state.mark_completed_status()
    assert state.status == "completed"
    
    state2 = BatchState(
        batch_id="test2",
        start_time="2026-02-05T10:00:00",
        total_seeds=1
    )
    state2.mark_cancelled()
    assert state2.status == "cancelled"


def test_save_and_load(tmp_path):
    """Test saving and loading batch state."""
    state_dir = tmp_path / ".bpui-batch-state"
    
    original = BatchState(
        batch_id="test-abc123",
        start_time="2026-02-05T10:30:00",
        total_seeds=10,
        input_file="/path/to/seeds.txt",
        config_snapshot={"model": "gpt-4", "mode": "NSFW"}
    )
    
    original.mark_completed("seed1", "/draft1")
    original.mark_failed("seed2", "error")
    
    # Save
    state_file = original.save(state_dir)
    assert state_file.exists()
    assert "batch_20260205_103000" in state_file.name
    
    # Load
    loaded = BatchState.load(state_file)
    
    assert loaded.batch_id == "test-abc123"
    assert loaded.total_seeds == 10
    assert len(loaded.completed_seeds) == 1
    assert len(loaded.failed_seeds) == 1
    assert loaded.input_file == "/path/to/seeds.txt"
    assert loaded.config_snapshot["model"] == "gpt-4"


def test_load_latest(tmp_path):
    """Test loading the latest batch state."""
    state_dir = tmp_path / ".bpui-batch-state"
    state_dir.mkdir()
    
    # Create multiple state files
    state1 = BatchState(
        batch_id="batch1",
        start_time="2026-02-05T10:00:00",
        total_seeds=5
    )
    state1.save(state_dir)
    
    time.sleep(0.01)  # Ensure different timestamps
    
    state2 = BatchState(
        batch_id="batch2",
        start_time="2026-02-05T11:00:00",
        total_seeds=10
    )
    state2.save(state_dir)
    
    # Load latest
    latest = BatchState.load_latest(state_dir)
    
    assert latest is not None
    assert latest.batch_id == "batch2"  # Most recent
    assert latest.total_seeds == 10


def test_load_latest_no_states(tmp_path):
    """Test loading latest when no states exist."""
    state_dir = tmp_path / ".bpui-batch-state"
    
    latest = BatchState.load_latest(state_dir)
    assert latest is None


def test_find_resumable(tmp_path):
    """Test finding a resumable batch state."""
    state_dir = tmp_path / ".bpui-batch-state"
    state_dir.mkdir()
    
    # Create completed batch
    state1 = BatchState(
        batch_id="batch1",
        start_time="2026-02-05T10:00:00",
        total_seeds=5
    )
    state1.mark_completed_status()
    state1.save(state_dir)
    
    # Create running batch
    state2 = BatchState(
        batch_id="batch2",
        start_time="2026-02-05T11:00:00",
        total_seeds=10
    )
    state2.save(state_dir)
    
    # Find resumable
    resumable = BatchState.find_resumable(state_dir)
    
    assert resumable is not None
    assert resumable.batch_id == "batch2"
    assert resumable.status == "running"


def test_find_resumable_none(tmp_path):
    """Test finding resumable when all are completed."""
    state_dir = tmp_path / ".bpui-batch-state"
    state_dir.mkdir()
    
    state = BatchState(
        batch_id="batch1",
        start_time="2026-02-05T10:00:00",
        total_seeds=5
    )
    state.mark_completed_status()
    state.save(state_dir)
    
    resumable = BatchState.find_resumable(state_dir)
    assert resumable is None


def test_delete_state_file(tmp_path):
    """Test deleting a state file."""
    state_dir = tmp_path / ".bpui-batch-state"
    
    state = BatchState(
        batch_id="test-delete",
        start_time="2026-02-05T10:00:00",
        total_seeds=5
    )
    
    state_file = state.save(state_dir)
    assert state_file.exists()
    
    state.delete_state_file(state_dir)
    assert not state_file.exists()


def test_cleanup_old_states(tmp_path):
    """Test cleaning up old state files."""
    state_dir = tmp_path / ".bpui-batch-state"
    state_dir.mkdir()
    
    # Create old state file
    old_file = state_dir / "batch_20260101_100000_old.json"
    old_file.write_text('{"batch_id": "old"}')
    
    # Make it old by modifying mtime
    old_time = time.time() - (8 * 24 * 60 * 60)  # 8 days ago
    import os
    os.utime(old_file, (old_time, old_time))
    
    # Create recent state file
    recent_file = state_dir / "batch_20260205_100000_recent.json"
    recent_file.write_text('{"batch_id": "recent"}')
    
    # Cleanup with 7 day threshold
    deleted = BatchState.cleanup_old_states(state_dir, days=7)
    
    assert deleted == 1
    assert not old_file.exists()
    assert recent_file.exists()


def test_to_dict():
    """Test converting to dictionary."""
    state = BatchState(
        batch_id="test",
        start_time="2026-02-05T10:00:00",
        total_seeds=5,
        input_file="seeds.txt"
    )
    
    data = state.to_dict()
    
    assert isinstance(data, dict)
    assert data["batch_id"] == "test"
    assert data["total_seeds"] == 5
    assert data["input_file"] == "seeds.txt"


def test_from_dict():
    """Test creating from dictionary."""
    data = {
        "batch_id": "test",
        "start_time": "2026-02-05T10:00:00",
        "total_seeds": 10,
        "completed_seeds": [{"seed": "s1", "draft_dir": "/d1", "timestamp": "2026-02-05T10:30:00"}],
        "failed_seeds": [],
        "current_index": 1,
        "config_snapshot": {"model": "gpt-4"},
        "input_file": "seeds.txt",
        "status": "running"
    }
    
    state = BatchState.from_dict(data)
    
    assert state.batch_id == "test"
    assert state.total_seeds == 10
    assert state.current_index == 1
    assert len(state.completed_seeds) == 1
