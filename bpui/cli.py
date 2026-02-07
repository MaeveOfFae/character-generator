"""CLI entry point for Blueprint UI."""

import sys
import argparse
import asyncio
from pathlib import Path
import logging


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Blueprint UI - RPBotGenerator Character Compiler"
    )
    
    # Global logging options
    parser.add_argument("--log-level", choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                       default="INFO", help="Set logging level (default: INFO)")
    parser.add_argument("--log-file", type=Path, help="Write logs to file")
    parser.add_argument("--log-component", help="Filter logs by component (e.g., bpui.cli)")
    parser.add_argument("--quiet", action="store_true", help="Suppress console output (except errors)")
    
    # Performance profiling
    parser.add_argument("--profile", action="store_true", help="Enable performance profiling")
    
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # TUI command (default)
    subparsers.add_parser("tui", help="Launch terminal UI (default)")

    # Compile command
    compile_parser = subparsers.add_parser("compile", help="Compile character from seed")
    compile_parser.add_argument("--seed", required=True, help="Character seed")
    compile_parser.add_argument(
        "--mode",
        choices=["SFW", "NSFW", "Platform-Safe"],
        help="Content mode (default: auto)",
    )
    compile_parser.add_argument("--out", help="Output directory (default: drafts/)")
    compile_parser.add_argument("--model", help="Model override")

    # Seed generator command
    seedgen_parser = subparsers.add_parser("seed-gen", help="Generate seeds from genre lines")
    seedgen_parser.add_argument("--input", required=True, help="Input file with genre lines")
    seedgen_parser.add_argument("--out", help="Output file for seeds")

    # Validate command
    validate_parser = subparsers.add_parser("validate", help="Validate a pack directory")
    validate_parser.add_argument("directory", help="Directory to validate")

    # Export command
    export_parser = subparsers.add_parser("export", help="Export a character")
    export_parser.add_argument("character_name", help="Character name")
    export_parser.add_argument("source_dir", help="Source directory")
    export_parser.add_argument("--model", help="Model name for output directory")
    export_parser.add_argument("--preset", help="Export preset name (e.g., chubai, tavernai, raw)")
    
    # Index rebuild command
    index_parser = subparsers.add_parser("rebuild-index", help="Rebuild draft index from disk")
    index_parser.add_argument("--drafts-dir", type=Path, help="Drafts directory (default: ./drafts)")

    # Batch command
    batch_parser = subparsers.add_parser("batch", help="Batch compile from seed file")
    batch_parser.add_argument("--input", help="File with seeds (one per line)")
    batch_parser.add_argument(
        "--mode",
        choices=["SFW", "NSFW", "Platform-Safe"],
        help="Content mode for all seeds (default: auto)",
    )
    batch_parser.add_argument("--out-dir", help="Output directory (default: drafts/)")
    batch_parser.add_argument("--model", help="Model override")
    batch_parser.add_argument("--continue-on-error", action="store_true", help="Continue if a seed fails")
    batch_parser.add_argument("--max-concurrent", type=int, help="Max concurrent compilations (default: from config)")
    batch_parser.add_argument("--resume", action="store_true", help="Resume last incomplete batch")
    batch_parser.add_argument("--clean-batch-state", action="store_true", help="Clean up old batch state files")

    args = parser.parse_args()
    
    # Setup logging before any commands
    from .logging_config import setup_logging
    setup_logging(
        level=args.log_level,
        log_file=args.log_file,
        log_to_console=not args.quiet,
        component_filter=args.log_component
    )
    
    # Setup profiling if requested
    if args.profile:
        from .profiler import get_profiler, enable_profiling
        enable_profiling()
        logger = logging.getLogger(__name__)
        logger.info("Performance profiling enabled")
    
    logger = logging.getLogger(__name__)

    # Default to GUI if no command
    if not args.command:
        logger.debug("No command specified, launching GUI")
        run_gui()
    elif args.command == "tui":
        logger.debug("Launching TUI")
        run_tui()
    elif args.command == "compile":
        asyncio.run(run_compile(args))
    elif args.command == "batch":
        asyncio.run(run_batch(args))
    elif args.command == "seed-gen":
        asyncio.run(run_seedgen(args))
    elif args.command == "validate":
        run_validate(args)
    elif args.command == "export":
        run_export(args)
    elif args.command == "rebuild-index":
        run_rebuild_index(args)
    
    # Print profiling report if enabled
    if args.profile:
        from .profiler import get_profiler
        profiler = get_profiler()
        profiler.print_report()


def run_tui():
    """Run the TUI application."""
    from .tui.app import BlueprintUI

    app = BlueprintUI()
    app.run()


def run_gui():
    """Run the Qt6 GUI application."""
    logger = logging.getLogger(__name__)
    try:
        from .gui.app import run_gui_app
        run_gui_app()
    except ImportError:
        logger.error("PySide6 not installed. Install with: pip install PySide6")
        logger.error("Or use TUI mode: bpui tui")
        sys.exit(1)


async def run_compile(args):
    """Run compilation from CLI."""
    from .config import Config
    logger = logging.getLogger(__name__)
    from .llm.litellm_engine import LiteLLMEngine
    from .llm.openai_compat_engine import OpenAICompatEngine
    from .prompting import build_asset_prompt
    from .parse_blocks import extract_single_asset, extract_character_name, ASSET_ORDER
    from .pack_io import create_draft_dir

    config = Config()

    logger.info("Compiling seed: %s", args.seed)
    logger.info("Mode: %s", args.mode or 'Auto')
    logger.info("Model: %s", args.model or config.model)

    # Validate API key
    model = args.model or config.model
    config.validate_api_key(model)

    # Create engine
    engine_config = {
        "model": model,
        "api_key": config.api_key,
        "temperature": config.temperature,
        "max_tokens": config.max_tokens,
    }

    if config.engine == "litellm":
        try:
            engine = LiteLLMEngine(**engine_config)
        except ImportError as e:
            logger.error("LiteLLM not installed. Install with: pip install litellm")
            logger.error("Or configure engine=openai-compat in .bpui.toml for OpenAI-compatible APIs")
            sys.exit(1)
    else:
        engine_config["base_url"] = config.base_url
        engine = OpenAICompatEngine(**engine_config)

    # Generate each asset sequentially
    logger.info("Starting sequential generation...")
    assets = {}
    character_name = None

    for asset_name in ASSET_ORDER:
        logger.info("Generating %s...", asset_name)
        
        # Build prompt with prior assets as context
        system_prompt, user_prompt = build_asset_prompt(
            asset_name, args.seed, args.mode, assets
        )
        
        # Generate
        output_text = await engine.generate(system_prompt, user_prompt)
        
        # Parse this asset
        asset_content = extract_single_asset(output_text, asset_name)
        assets[asset_name] = asset_content
        logger.info("%s complete", asset_name)
        
        # Extract character name from character_sheet
        if asset_name == "character_sheet" and not character_name:
            character_name = extract_character_name(asset_content)
            if character_name:
                logger.info("Character: %s", character_name)

    if not character_name:
        character_name = "unnamed_character"

    # Save
    if args.out:
        draft_dir = Path(args.out)
        draft_dir.mkdir(parents=True, exist_ok=True)
        for asset_name, content in assets.items():
            from .parse_blocks import ASSET_FILENAMES
            filename = ASSET_FILENAMES.get(asset_name)
            if filename:
                (draft_dir / filename).write_text(content)
    else:
        draft_dir = create_draft_dir(assets, character_name)

    print(f"\n✓ Saved to: {draft_dir}")


async def run_seedgen(args):
    """Run seed generator from CLI."""
    from .config import Config
    from .llm.litellm_engine import LiteLLMEngine
    from .llm.openai_compat_engine import OpenAICompatEngine
    from .prompting import build_seedgen_prompt

    logger = logging.getLogger(__name__)
    config = Config()

    # Validate API key
    config.validate_api_key(config.model)

    # Read input
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"✗ Input file not found: {input_path}")
        sys.exit(1)

    genre_lines = input_path.read_text()

    print(f"🎲 Generating seeds from: {input_path}")

    # Build prompt
    system_prompt, user_prompt = build_seedgen_prompt(genre_lines)

    # Create engine
    engine_config = {
        "model": config.model,
        "api_key": config.api_key,
        "temperature": config.temperature,
        "max_tokens": config.max_tokens,
    }

    if config.engine == "litellm":
        try:
            engine = LiteLLMEngine(**engine_config)
        except ImportError as e:
            logger.error("LiteLLM not installed. Install with: pip install litellm")
            logger.error("Or configure engine=openai-compat in .bpui.toml for OpenAI-compatible APIs")
            sys.exit(1)
    else:
        engine_config["base_url"] = config.base_url
        engine = OpenAICompatEngine(**engine_config)

    # Generate
    print("⏳ Generating...")
    output = await engine.generate(system_prompt, user_prompt)

    # Parse seeds
    seeds = [
        line.strip()
        for line in output.split("\n")
        if line.strip() and not line.strip().startswith("#")
    ]

    # Save or print
    if args.out:
        output_path = Path(args.out)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text("\n".join(seeds))
        print(f"✓ Saved {len(seeds)} seeds to: {output_path}")
    else:
        print(f"\n✓ Generated {len(seeds)} seeds:\n")
        for seed in seeds:
            print(f"  • {seed}")


def run_validate(args):
    """Run validation from CLI."""
    from .validate import validate_pack

    pack_dir = Path(args.directory)
    if not pack_dir.exists():
        print(f"✗ Directory not found: {pack_dir}")
        sys.exit(1)

    print(f"✓ Validating: {pack_dir}")
    result = validate_pack(pack_dir)

    print(result["output"])
    if result["errors"]:
        print(f"\nErrors:\n{result['errors']}")

    sys.exit(result["exit_code"])


def run_export(args):
    """Run export from CLI."""
    from .export import export_character

    source_dir = Path(args.source_dir)
    if not source_dir.exists():
        print(f"✗ Source directory not found: {source_dir}")
        sys.exit(1)

    preset_name = getattr(args, 'preset', None)
    if preset_name:
        print(f"📦 Exporting: {args.character_name} (using {preset_name} preset)")
    else:
        print(f"📦 Exporting: {args.character_name}")
    
    result = export_character(
        character_name=args.character_name,
        source_dir=source_dir,
        model=args.model,
        preset_name=preset_name
    )

    print(result["output"])
    if result["errors"]:
        print(f"\nErrors:\n{result['errors']}")

    sys.exit(result["exit_code"])


async def run_batch(args):
    """Run batch compilation from CLI."""
    import asyncio
    from .config import Config
    from .llm.litellm_engine import LiteLLMEngine
    from .llm.openai_compat_engine import OpenAICompatEngine
    from .prompting import build_orchestrator_prompt
    from .parse_blocks import parse_blueprint_output, extract_character_name, ASSET_FILENAMES
    from .pack_io import create_draft_dir
    from .batch_state import BatchState

    logger = logging.getLogger(__name__)
    config = Config()

    # Handle cleanup flag
    if args.clean_batch_state:
        deleted = BatchState.cleanup_old_states(days=7)
        print(f"✓ Cleaned up {deleted} old batch state file(s)")
        return

    # Get concurrent settings
    max_concurrent = args.max_concurrent if hasattr(args, 'max_concurrent') and args.max_concurrent else config.batch_max_concurrent
    rate_limit_delay = config.batch_rate_limit_delay

    # Validate API key
    model = args.model or config.model
    config.validate_api_key(model)

    # Handle resume
    batch_state = None
    if args.resume:
        batch_state = BatchState.find_resumable()
        if not batch_state:
            print("✗ No resumable batch found")
            sys.exit(1)
        
        # Load seeds from original input file
        if not batch_state.input_file:
            print("✗ Cannot resume: batch state missing input file")
            sys.exit(1)
        
        input_path = Path(batch_state.input_file)
        if not input_path.exists():
            print(f"✗ Original input file not found: {input_path}")
            sys.exit(1)
        
        seeds_raw = input_path.read_text().strip().split("\n")
        all_seeds = [s.strip() for s in seeds_raw if s.strip()]
        
        # Filter to remaining seeds
        seeds = batch_state.get_remaining_seeds(all_seeds)
        
        print(f"📦 Resuming batch: {batch_state.batch_id[:8]}")
        print(f"   Started: {batch_state.start_time}")
        print(f"   Progress: {len(batch_state.completed_seeds)}/{batch_state.total_seeds} completed")
        print(f"   Failed: {len(batch_state.failed_seeds)}")
        print(f"   Remaining: {len(seeds)} seeds")
        
        # Use config from batch state
        args.mode = batch_state.config_snapshot.get("mode")
        if "model" in batch_state.config_snapshot:
            args.model = batch_state.config_snapshot["model"]
    else:
        # New batch
        if not args.input:
            print("✗ --input required (or use --resume)")
            sys.exit(1)
        
        # Load seeds
        input_path = Path(args.input)
        if not input_path.exists():
            print(f"✗ Input file not found: {input_path}")
            sys.exit(1)

        seeds_raw = input_path.read_text().strip().split("\n")
        seeds = [s.strip() for s in seeds_raw if s.strip()]

        if not seeds:
            print("✗ No seeds found in file")
            sys.exit(1)

        print(f"📦 Batch compiling {len(seeds)} seeds")
        print(f"   Mode: {args.mode or 'Auto'}")
        print(f"   Model: {args.model or config.model}")
        print(f"   Continue on error: {args.continue_on_error}")
        
        # Create new batch state
        batch_state = BatchState(
            batch_id=str(__import__('uuid').uuid4()),
            start_time=__import__('datetime').datetime.now().isoformat(),
            total_seeds=len(seeds),
            input_file=str(input_path.absolute()),
            config_snapshot={
                "mode": args.mode,
                "model": args.model or config.model,
                "temperature": config.temperature,
                "max_tokens": config.max_tokens,
            }
        )

    # Create engine
    engine_config = {
        "model": model,
        "api_key": config.api_key,
        "temperature": config.temperature,
        "max_tokens": config.max_tokens,
    }

    if config.engine == "litellm":
        try:
            engine = LiteLLMEngine(**engine_config)
        except ImportError as e:
            logger.error("LiteLLM not installed. Install with: pip install litellm")
            logger.error("Or configure engine=openai-compat in .bpui.toml for OpenAI-compatible APIs")
            sys.exit(1)
    else:
        engine_config["base_url"] = config.base_url
        engine = OpenAICompatEngine(**engine_config)

    # Use parallel processing if max_concurrent > 1
    if max_concurrent > 1:
        print(f"📦 Parallel batch processing: {max_concurrent} concurrent")
        await run_batch_parallel(
            seeds=seeds,
            engine=engine,
            batch_state=batch_state,
            args=args,
            model=model,
            max_concurrent=max_concurrent,
            rate_limit_delay=rate_limit_delay
        )
    else:
        # Sequential processing (original behavior)
        await run_batch_sequential(
            seeds=seeds,
            engine=engine,
            batch_state=batch_state,
            args=args,
            model=model
        )

    # Summary
    successful = len(batch_state.completed_seeds)
    failed = batch_state.failed_seeds
    
    print(f"\n{'='*60}")
    print(f"✓ Batch complete: {successful}/{batch_state.total_seeds} successful")
    if failed:
        print(f"✗ {len(failed)} failed:")
        for fail in failed[:5]:  # Show first 5
            print(f"   - {fail['seed']}: {fail['error'][:50]}")
        if len(failed) > 5:
            print(f"   ... and {len(failed) - 5} more")

    # Exit with error code if any failed
    sys.exit(1 if failed else 0)


async def run_batch_sequential(seeds, engine, batch_state, args, model):
    """Run batch compilation sequentially (original behavior)."""
    from .prompting import build_orchestrator_prompt
    from .parse_blocks import parse_blueprint_output, extract_character_name, ASSET_FILENAMES
    from .pack_io import create_draft_dir
    
    # Compile each seed
    successful = len(batch_state.completed_seeds)
    failed = list(batch_state.failed_seeds)

    for i, seed in enumerate(seeds, 1):
        actual_index = batch_state.current_index + i
        print(f"\n[{actual_index}/{batch_state.total_seeds}] {seed}")

        try:
            # Build prompt
            system_prompt, user_prompt = build_orchestrator_prompt(seed, args.mode)

            # Generate
            output = ""
            async for chunk in engine.generate_stream(system_prompt, user_prompt):
                output += chunk
                print(".", end="", flush=True)

            print()  # newline

            # Parse
            assets = parse_blueprint_output(output)
            
            # Extract character name
            character_name = extract_character_name(assets.get("character_sheet", ""))
            if not character_name:
                character_name = f"character_{actual_index:03d}"

            # Save with metadata
            if args.out_dir:
                draft_dir = Path(args.out_dir) / f"{character_name}"
                draft_dir.mkdir(parents=True, exist_ok=True)
                for asset_name, content in assets.items():
                    filename = ASSET_FILENAMES.get(asset_name)
                    if filename:
                        (draft_dir / filename).write_text(content)
            else:
                draft_dir = create_draft_dir(
                    assets, 
                    character_name,
                    seed=seed,
                    mode=args.mode,
                    model=model
                )

            print(f"✓ Saved to {draft_dir.name}")
            successful += 1
            
            # Mark as completed in batch state
            batch_state.mark_completed(seed, str(draft_dir))
            batch_state.save()

        except Exception as e:
            print(f"✗ Failed: {e}")
            error_msg = str(e)
            failed.append({"seed": seed, "error": error_msg})
            
            # Mark as failed in batch state
            batch_state.mark_failed(seed, error_msg)
            batch_state.save()
            
            if not args.continue_on_error:
                print("\n✗ Stopping due to error (use --continue-on-error to continue)")
                batch_state.mark_cancelled()
                batch_state.save()
                return

    # Mark batch as completed
    batch_state.mark_completed_status()
    batch_state.save()
    
    # Clean up state file on successful completion
    if not failed:
        batch_state.delete_state_file()


async def run_batch_parallel(seeds, engine, batch_state, args, model, max_concurrent, rate_limit_delay):
    """Run batch compilation with parallel processing."""
    import asyncio
    import random
    from .prompting import build_orchestrator_prompt
    from .parse_blocks import parse_blueprint_output, extract_character_name, ASSET_FILENAMES
    from .pack_io import create_draft_dir
    
    # Simple rate limiter using time-based delays
    class RateLimiter:
        """Simple time-based rate limiter with thread safety."""
        
        def __init__(self, calls_per_second: float = 1.0):
            """Initialize rate limiter.
            
            Args:
                calls_per_second: Maximum calls per second
            """
            self.min_interval = 1.0 / calls_per_second if calls_per_second > 0 else 0
            self.last_call = 0.0
            self._lock = asyncio.Lock()
        
        async def acquire(self):
            """Wait until next call is allowed."""
            if self.min_interval <= 0:
                return
            
            async with self._lock:
                now = asyncio.get_event_loop().time()
                elapsed = now - self.last_call
                
                if elapsed < self.min_interval:
                    await asyncio.sleep(self.min_interval - elapsed)
                
                self.last_call = asyncio.get_event_loop().time()
    
    def is_transient_error(error: Exception) -> bool:
        """Check if error is transient (worth retrying).
        
        Args:
            error: Exception to check
            
        Returns:
            True if error is transient
        """
        error_str = str(error).lower()
        transient_patterns = [
            "timeout", "connection", "network", "rate limit",
            "429", "503", "502", "504", "temporarily unavailable"
        ]
        return any(pattern in error_str for pattern in transient_patterns)
    
    # Create rate limiter (default 1 call per second, configurable via rate_limit_delay)
    calls_per_second = 1.0 / rate_limit_delay if rate_limit_delay > 0 else 10.0
    rate_limiter = RateLimiter(calls_per_second)
    
    semaphore = asyncio.Semaphore(max_concurrent)
    successful = len(batch_state.completed_seeds)
    
    async def compile_one_seed(seed, index):
        """Compile a single seed with semaphore control."""
        async with semaphore:
            # Rate limiting
            await rate_limiter.acquire()
            
            print(f"\n[{index}/{batch_state.total_seeds}] Starting: {seed}")
            
            try:
                # Build prompt
                system_prompt, user_prompt = build_orchestrator_prompt(seed, args.mode)

                # Generate (non-streaming for parallel)
                output = await engine.generate(system_prompt, user_prompt)

                # Parse
                assets = parse_blueprint_output(output)
                
                # Extract character name
                character_name = extract_character_name(assets.get("character_sheet", ""))
                if not character_name:
                    character_name = f"character_{index:03d}"

                # Save with metadata
                if args.out_dir:
                    draft_dir = Path(args.out_dir) / f"{character_name}"
                    draft_dir.mkdir(parents=True, exist_ok=True)
                    for asset_name, content in assets.items():
                        filename = ASSET_FILENAMES.get(asset_name)
                        if filename:
                            (draft_dir / filename).write_text(content)
                else:
                    draft_dir = create_draft_dir(
                        assets, 
                        character_name,
                        seed=seed,
                        mode=args.mode,
                        model=model
                    )

                print(f"✓ [{index}/{batch_state.total_seeds}] Saved: {draft_dir.name}")
                
                # Mark as completed in batch state
                batch_state.mark_completed(seed, str(draft_dir))
                batch_state.save()
                
                return (True, seed, None)

            except Exception as e:
                print(f"✗ [{index}/{batch_state.total_seeds}] Failed: {seed}: {e}")
                error_msg = str(e)
                
                # Mark as failed in batch state
                batch_state.mark_failed(seed, error_msg)
                batch_state.save()
                
                return (False, seed, error_msg)
    
    # Create tasks for all seeds
    tasks = [
        compile_one_seed(seed, batch_state.current_index + i + 1)
        for i, seed in enumerate(seeds)
    ]
    
    # Wait for all tasks
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Process results
    failed = []
    for result in results:
        if isinstance(result, Exception):
            print(f"✗ Unexpected error: {result}")
            failed.append({"seed": "unknown", "error": str(result)})
        elif isinstance(result, tuple) and len(result) == 3:
            success, seed, error = result
            if not success:  # Failed compilation
                failed.append({"seed": seed, "error": error})
    
    # Mark batch as completed
    batch_state.mark_completed_status()
    batch_state.save()
    
    # Clean up state file on successful completion
    if not failed:
        batch_state.delete_state_file()


def run_rebuild_index(args):
    """Rebuild the draft index from disk."""
    from .draft_index import DraftIndex
    
    logger = logging.getLogger(__name__)
    
    logger.info("Rebuilding draft index...")
    
    index = DraftIndex()
    result = index.rebuild_index(drafts_root=args.drafts_dir)
    
    if result:
        logger.info("Index rebuilt: %d indexed, %d skipped", result["indexed"], result["skipped"])
        
        # Show stats
        stats = index.get_stats()
        logger.info("Total drafts: %d", stats["total"])
        logger.info("Favorites: %d", stats["favorites"])
        for mode, count in stats["by_mode"].items():
            logger.info("  %s: %d", mode, count)
    else:
        logger.info("Index rebuilt successfully")


if __name__ == "__main__":
    main()
