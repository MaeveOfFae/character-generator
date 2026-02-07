"""Tests for batch state persistence and concurrency."""

import pytest
import asyncio
import json
from pathlib import Path
from datetime import datetime
from bpui.batch_state import BatchState


@pytest.fixture
def temp_state_dir(tmp_path):
    """Provide temporary state directory for tests."""
    return tmp_path / ".bpui-batch-state"


@pytest.mark.asyncio
async def test_concurrent_save(temp_state_dir):
    """Test concurrent saves don't corrupt state."""
    state = BatchState(
        batch_id="test_concurrent",
        start_time=datetime.now().isoformat(),
        total_seeds=10
    )
    
    # Simulate concurrent saves
    async def save_multiple():
        for i in range(5):
            state.mark_completed(f"seed{i}", f"dir{i}")
            await asyncio.sleep(0.01)
            state.save(state_dir=temp_state_dir)
    
    # Run multiple concurrent save operations
    await asyncio.gather(*[save_multiple() for _ in range(3)])
    
    # Verify state is consistent
    state_file = temp_state_dir / "batch_*.json"
    state_files = list(state_file.glob("batch_*.json"))
    assert len(state_files) == 1
    
    loaded = BatchState.load(state_files[0])
    assert len(loaded.completed_seeds) == 15
    assert loaded.batch_id == "test_concurrent"


def test_load_corrupted_state(temp_state_dir):
    """Test loading corrupted state file returns None or raises."""
    temp_state_dir.mkdir(exist_ok=True)
    state_file = temp_state_dir / "test_corrupt.json"
    state_file.write_text("invalid json {{{")
    
    result = BatchState.load(state_file)
    assert result is None


def test_exact_match_delete(temp_state_dir):
    """Test delete uses exact match, not substring match."""
    temp_state_dir.mkdir(exist_ok=True)
    
    # Create two states with similar IDs
    state1 = BatchState(
        batch_id="abc123",
        start_time=datetime.now().isoformat(),
        total_seeds=5
    )
    state1.save(state_dir=temp_state_dir)
    
    state2 = BatchState(
        batch_id="abc12345",
        start_time=datetime.now().isoformat(),
        total_seeds=5
    )
    state2.save(state_dir=temp_state_dir)
    
    # Delete first state
    state1.delete_state_file(state_dir=temp_state_dir)
    
    # Verify only first state was deleted
    remaining = list(temp_state_dir.glob("batch_*.json"))
    assert len(remaining) == 1
    
    loaded = BatchState.load(remaining[0])
    assert loaded.batch_id == "abc12345"


def test_resume_functionality(temp_state_dir):
    """Test find_resumable finds running state."""
    temp_state_dir.mkdir(exist_ok=True)
    
    # Create a running state
    running_state = BatchState(
        batch_id="running_batch",
        start_time=datetime.now().isoformat(),
        total_seeds=10,
        status="running"
    )
    running_state.save(state_dir=temp_state_dir)
    
    # Create a completed state
    completed_state = BatchState(
        batch_id="completed_batch",
        start_time=datetime.now().isoformat(),
        total_seeds=10,
        status="completed"
    )
    completed_state.save(state_dir=temp_state_dir)
    
    # Find resumable
    resumable = BatchState.find_resumable(state_dir=temp_state_dir)
    assert resumable is not None
    assert resumable.batch_id == "running_batch"


def test_cleanup_old_states(temp_state_dir):
    """Test cleanup removes only old states."""
    temp_state_dir.mkdir(exist_ok=True)
    
    # Create an old state (mocked by setting old mtime)
    old_state = BatchState(
        batch_id="old_batch",
        start_time=datetime.now().isoformat(),
        total_seeds=5
    )
    old_file = old_state.save(state_dir=temp_state_dir)
    
    # Create a recent state
    recent_state = BatchState(
        batch_id="recent_batch",
        start_time=datetime.now().isoformat(),
        total_seeds=5
    )
    recent_state.save(state_dir=temp_state_dir)
    
    # Manually set old file mtime to 10 days ago
    import time
    ten_days_ago = time.time() - (10 * 24 * 60 * 60)
    import os
    os.utime(old_file, (ten_days_ago, ten_days_ago))
    
    # Cleanup states older than 7 days
    deleted = BatchState.cleanup_old_states(state_dir=temp_state_dir, days=7)
    
    # Verify only old state was deleted
    assert deleted == 1
    remaining = list(temp_state_dir.glob("batch_*.json"))
    assert len(remaining) == 1
    loaded = BatchState.load(remaining[0])
    assert loaded.batch_id == "recent_batch"


def test_state_serialization_roundtrip(temp_state_dir):
    """Test state survives save/load cycle."""
    original = BatchState(
        batch_id="test_roundtrip",
        start_time=datetime.now().isoformat(),
        total_seeds=10
    )
    
    # Add some completed and failed seeds
    original.mark_completed("seed1", "dir1")
    original.mark_completed("seed2", "dir2")
    original.mark_failed("seed3", "Error occurred")
    
    # Save
    state_file = original.save(state_dir=temp_state_dir)
    
    # Load
    loaded = BatchState.load(state_file)
    
    # Verify all data preserved
    assert loaded.batch_id == original.batch_id
    assert loaded.start_time == original.start_time
    assert loaded.total_seeds == original.total_seeds
    assert len(loaded.completed_seeds) == 2
    assert len(loaded.failed_seeds) == 1
    assert loaded.current_index == 3
    assert loaded.status == original.status


def test_get_remaining_seeds(temp_state_dir):
    """Test get_remaining_seeds filters correctly."""
    state = BatchState(
        batch_id="test_remaining",
        start_time=datetime.now().isoformat(),
        total_seeds=10
    )
    
    # Mark some as completed and failed
    state.mark_completed("seed1", "dir1")
    state.mark_completed("seed2", "dir2")
    state.mark_failed("seed3", "Error")
    
    all_seeds = ["seed1", "seed2", "seed3", "seed4", "seed5"]
    remaining = state.get_remaining_seeds(all_seeds)
    
    assert remaining == ["seed4", "seed5"]