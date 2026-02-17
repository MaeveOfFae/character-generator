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
    compile_parser.add_argument("--template", help="Name of template to use (default: Official Aksho)")
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
    batch_parser.add_argument("--template", help="Name of template to use (default: Official Aksho)")
    batch_parser.add_argument("--out-dir", help="Output directory (default: drafts/)")
    batch_parser.add_argument("--model", help="Model override")
    batch_parser.add_argument("--continue-on-error", action="store_true", help="Continue if a seed fails")
    batch_parser.add_argument("--max-concurrent", type=int, help="Max concurrent compilations (default: from config)")
    batch_parser.add_argument("--resume", action="store_true", help="Resume last incomplete batch")
    batch_parser.add_argument("--clean-batch-state", action="store_true", help="Clean up old batch state files")

    # Offspring command
    offspring_parser = subparsers.add_parser("offspring", help="Generate offspring from two parent characters")
    offspring_parser.add_argument("--parent1", required=True, help="Path or name of parent 1 draft")
    offspring_parser.add_argument("--parent2", required=True, help="Path or name of parent 2 draft")
    offspring_parser.add_argument(
        "--mode",
        choices=["SFW", "NSFW", "Platform-Safe"],
        help="Content mode (default: auto)",
    )
    offspring_parser.add_argument("--template", help="Name of template to use (default: Official Aksho)")
    offspring_parser.add_argument("--out", help="Output directory (default: drafts/)")
    offspring_parser.add_argument("--model", help="Model override")
    
    # Similarity command
    similarity_parser = subparsers.add_parser("similarity", help="Analyze character similarities")
    similarity_parser.add_argument("draft1", help="Path or name of first draft")
    similarity_parser.add_argument("draft2", help="Path or name of second draft")
    similarity_parser.add_argument("--drafts-dir", type=Path, help="Drafts directory (default: ./drafts)")
    similarity_parser.add_argument("--format", choices=["text", "json"], default="text", help="Output format")
    similarity_parser.add_argument("--all", action="store_true", help="Compare all pairs in drafts directory")
    similarity_parser.add_argument("--cluster", action="store_true", help="Cluster similar characters")
    similarity_parser.add_argument("--threshold", type=float, default=0.6, help="Similarity threshold for clustering (0.0-1.0)")
    similarity_parser.add_argument("--use-llm", action="store_true", help="Enable LLM-powered deep analysis")
    
    # List models command
    list_models_parser = subparsers.add_parser("list-models", help="List available AI models")
    list_models_parser.add_argument("--provider", help="Provider (openrouter, openai, google, etc.)")
    list_models_parser.add_argument("--base-url", help="Custom base URL for OpenAI-compatible APIs")
    list_models_parser.add_argument("--api-key", help="API key for authentication")
    list_models_parser.add_argument("--format", choices=["text", "json", "csv"], default="text", help="Output format")
    list_models_parser.add_argument("--filter", help="Filter models by name/pattern (e.g., 'gpt-4' or 'claude')")

    args = parser.parse_args()
    
    # Setup logging before any commands
    from bpui.utils.logging_config import setup_logging
    setup_logging(
        level=args.log_level,
        log_file=args.log_file,
        log_to_console=not args.quiet,
        component_filter=args.log_component
    )
    
    # Setup profiling if requested
    if args.profile:
        from bpui.utils.profiler import get_profiler, enable_profiling
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
        import bpui.cli as cli_compat
        cli_compat.run_tui()
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
    elif args.command == "offspring":
        asyncio.run(run_offspring(args))
    elif args.command == "similarity":
        run_similarity(args)
    elif args.command == "list-models":
        asyncio.run(run_list_models(args))
    
    # Print profiling report if enabled
    if args.profile:
        from bpui.utils.profiler import get_profiler
        profiler = get_profiler()
        profiler.print_report()


def run_tui():
    """Run the TUI application."""
    from bpui.tui.app import BlueprintUI

    app = BlueprintUI()
    app.run()


def run_gui():
    """Run the Qt6 GUI application."""
    logger = logging.getLogger(__name__)
    try:
        try:
            import PySide6  # noqa: F401
        except ModuleNotFoundError:
            logger.error("PySide6 not installed. Install with: pip install PySide6")
            logger.error("Or use TUI mode: bpui tui")
            sys.exit(1)

        from bpui.gui.app import run_gui_app
        run_gui_app()
    except ImportError as exc:
        logger.exception("GUI import failed: %s", exc)
        sys.exit(1)


async def run_compile(args):
    """Run compilation from CLI."""
    from .config import Config
    logger = logging.getLogger(__name__)
    from bpui.prompting import build_asset_prompt
    from bpui.parse_blocks import extract_single_asset, extract_character_name
    from bpui.pack_io import create_draft_dir
    from bpui.features.templates.templates import TemplateManager
    from bpui.utils.topological_sort import topological_sort

    config = Config()

    logger.info("Compiling seed: %s", args.seed)
    logger.info("Mode: %s", args.mode or 'Auto')
    logger.info("Model: %s", args.model or config.model)

    # Load template
    manager = TemplateManager()
    template_name = getattr(args, "template", None) or "Official RPBotGenerator"
    template = manager.get_template(template_name)
    if not template:
        logger.error(f"Template '{template_name}' not found.")
        sys.exit(1)
    logger.info("Template: %s", template.name)

    # Get asset order
    try:
        asset_order = topological_sort(template.assets)
    except ValueError as e:
        logger.error(f"Template error: {e}")
        sys.exit(1)

    # Validate API key
    model = args.model or config.model
    config.validate_api_key(model)

    # Create engine (legacy-compatible paths for tests)
    try:
        if config.engine == "openai_compatible":
            from bpui.llm.openai_compat_engine import OpenAICompatEngine
            engine = OpenAICompatEngine(
                model=model,
                api_key=config.api_key,
                temperature=config.temperature,
                max_tokens=config.max_tokens,
                base_url=getattr(config, "base_url", None),
            )
        else:
            from bpui.llm.litellm_engine import LiteLLMEngine
            engine = LiteLLMEngine(
                model=model,
                api_key=config.api_key,
                temperature=config.temperature,
                max_tokens=config.max_tokens,
            )
    except (ImportError, ValueError) as e:
        logger.error(f"Failed to create engine: {e}")
        sys.exit(1)

    # Generate each asset sequentially
    logger.info("Starting sequential generation...")
    assets = {}
    character_name = None

    for asset_name in asset_order:
        logger.info("Generating %s...", asset_name)
        
        # Get blueprint content from template
        blueprint_content = manager.get_blueprint_content(template, asset_name)
        if not blueprint_content:
            logger.error(f"Blueprint for asset '{asset_name}' not found in template '{template.name}'. Skipping.")
            continue
            
        # Build prompt with prior assets as context
        system_prompt, user_prompt = build_asset_prompt(
            asset_name, 
            args.seed, 
            args.mode, 
            assets,
            blueprint_content=blueprint_content
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
    from bpui.prompting import build_seedgen_prompt

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

    # Create engine (legacy-compatible paths for tests)
    try:
        if config.engine == "openai_compatible":
            from bpui.llm.openai_compat_engine import OpenAICompatEngine
            engine = OpenAICompatEngine(
                model=config.model,
                api_key=config.api_key,
                temperature=config.temperature,
                max_tokens=config.max_tokens,
                base_url=getattr(config, "base_url", None),
            )
        else:
            from bpui.llm.litellm_engine import LiteLLMEngine
            engine = LiteLLMEngine(
                model=config.model,
                api_key=config.api_key,
                temperature=config.temperature,
                max_tokens=config.max_tokens,
            )
    except (ImportError, ValueError) as e:
        logger.error(f"Failed to create engine: {e}")
        sys.exit(1)

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
    from bpui.utils.file_io.validate import validate_pack

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
    from bpui.features.export.export import export_character

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
    from bpui.llm.factory import create_engine
    from .prompting import build_orchestrator_prompt
    from .parse_blocks import parse_blueprint_output, extract_character_name, ASSET_FILENAMES
    from bpui.utils.file_io.pack_io import create_draft_dir
    from .batch_state import BatchState
    from bpui.features.templates.templates import TemplateManager

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
    
    # Load template
    manager = TemplateManager()
    template_name = args.template or "Official Aksho"
    template = manager.get_template(template_name)
    if not template:
        logger.error(f"Template '{template_name}' not found.")
        sys.exit(1)
    logger.info("Template: %s", template.name)

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
                "template": template.name,
            }
        )

    # Create engine using factory
    try:
        engine = create_engine(
            config,
            model_override=model if args.model else None,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
        )
    except (ImportError, ValueError) as e:
        logger.error(f"Failed to create engine: {e}")
        sys.exit(1)

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
            rate_limit_delay=rate_limit_delay,
            template=template
        )
    else:
        # Sequential processing (original behavior)
        await run_batch_sequential(
            seeds=seeds,
            engine=engine,
            batch_state=batch_state,
            args=args,
            model=model,
            template=template
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


async def run_batch_sequential(seeds, engine, batch_state, args, model, template):
    """Run batch compilation sequentially (original behavior)."""
    from .prompting import build_orchestrator_prompt
    from .parse_blocks import parse_blueprint_output, extract_character_name, ASSET_FILENAMES
    from bpui.utils.file_io.pack_io import create_draft_dir
    
    # Compile each seed
    successful = len(batch_state.completed_seeds)
    failed = list(batch_state.failed_seeds)

    for i, seed in enumerate(seeds, 1):
        actual_index = batch_state.current_index + i
        print(f"\n[{actual_index}/{batch_state.total_seeds}] {seed}")

        try:
            # Build prompt
            system_prompt, user_prompt = build_orchestrator_prompt(seed, args.mode, template=template)

            # Generate
            output = ""
            async for chunk in engine.generate_stream(system_prompt, user_prompt):
                output += chunk
                print(".", end="", flush=True)

            print()  # newline

            # Parse
            assets = parse_blueprint_output(output, template=template)
            
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


async def run_batch_parallel(seeds, engine, batch_state, args, model, max_concurrent, rate_limit_delay, template):
    """Run batch compilation with parallel processing."""
    import asyncio
    import random
    from .prompting import build_orchestrator_prompt
    from .parse_blocks import parse_blueprint_output, extract_character_name, ASSET_FILENAMES
    from bpui.utils.file_io.pack_io import create_draft_dir
    
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
                system_prompt, user_prompt = build_orchestrator_prompt(seed, args.mode, template=template)

                # Generate (non-streaming for parallel)
                output = await engine.generate(system_prompt, user_prompt)

                # Parse
                assets = parse_blueprint_output(output, template=template)
                
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
    from bpui.utils.metadata.draft_index import DraftIndex
    
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


async def run_offspring(args):
    """Run offspring generation from CLI."""
    from .config import Config
    from bpui.llm.factory import create_engine
    from .prompting import build_offspring_prompt, build_asset_prompt
    from .parse_blocks import extract_single_asset, extract_character_name
    from bpui.utils.file_io.pack_io import create_draft_dir, load_draft
    from bpui.utils.metadata.metadata import DraftMetadata
    from bpui.features.templates.templates import TemplateManager
    from bpui.utils.topological_sort import topological_sort

    logger = logging.getLogger(__name__)
    config = Config()
    
    # Validate API key
    model = args.model or config.model
    config.validate_api_key(model)
    
    # Find parent drafts
    drafts_root = Path.cwd() / "drafts"
    parent1_path = _find_draft(args.parent1, drafts_root)
    parent2_path = _find_draft(args.parent2, drafts_root)
    
    if not parent1_path:
        print(f"✗ Parent 1 not found: {args.parent1}")
        sys.exit(1)
    if not parent2_path:
        print(f"✗ Parent 2 not found: {args.parent2}")
        sys.exit(1)
    
    # Load parent assets
    parent1_assets = load_draft(parent1_path)
    parent2_assets = load_draft(parent2_path)
    
    # Get parent names
    p1_metadata = DraftMetadata.load(parent1_path)
    p2_metadata = DraftMetadata.load(parent2_path)
    parent1_name = p1_metadata.character_name if p1_metadata and p1_metadata.character_name else parent1_path.name
    parent2_name = p2_metadata.character_name if p2_metadata and p2_metadata.character_name else parent2_path.name
    
    print(f"👶 Generating offspring from:")
    print(f"   Parent 1: {parent1_name}")
    print(f"   Parent 2: {parent2_name}")
    print(f"   Mode: {args.mode or 'Auto'}")
    print(f"   Model: {model}")

    # Load template
    manager = TemplateManager()
    template_name = args.template or "Official Aksho"
    template = manager.get_template(template_name)
    if not template:
        logger.error(f"Template '{template_name}' not found.")
        sys.exit(1)
    logger.info("Template: %s", template.name)

    # Get asset order
    try:
        asset_order = topological_sort(template.assets)
    except ValueError as e:
        logger.error(f"Template error: {e}")
        sys.exit(1)

    # Create engine using factory
    try:
        engine = create_engine(
            config,
            model_override=model if args.model else None,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
        )
    except (ImportError, ValueError) as e:
        logger.error(f"Failed to create engine: {e}")
        sys.exit(1)

    # Step 1: Generate offspring seed
    print("\n⏳ Generating offspring seed...")
    
    system_prompt, user_prompt = build_offspring_prompt(
        parent1_assets=parent1_assets,
        parent2_assets=parent2_assets,
        parent1_name=parent1_name,
        parent2_name=parent2_name,
        mode=args.mode
    )
    
    output_text = await engine.generate(system_prompt, user_prompt)
    offspring_seed = output_text.strip()
    
    if not offspring_seed:
        print("✗ Failed to generate offspring seed")
        sys.exit(1)
    
    print(f"✓ Offspring seed generated ({len(offspring_seed)} chars)")
    print(f"   Preview: {offspring_seed[:100]}{'...' if len(offspring_seed) > 100 else ''}")
    
    # Step 2: Generate full character suite
    print("\n⏳ Generating full character suite...")
    
    assets = {}
    character_name = None
    
    for asset_name in asset_order:
        print(f"   → {asset_name}...", end=" ", flush=True)
        
        # Get blueprint content from template
        blueprint_content = manager.get_blueprint_content(template, asset_name)
        if not blueprint_content:
            logger.error(f"Blueprint for asset '{asset_name}' not found in template '{template.name}'. Skipping.")
            continue
            
        system_prompt, user_prompt = build_asset_prompt(
            asset_name, offspring_seed, args.mode, assets, blueprint_content=blueprint_content
        )
        
        output = await engine.generate(system_prompt, user_prompt)
        asset_content = extract_single_asset(output, asset_name)
        assets[asset_name] = asset_content
        
        print(f"✓")
        
        if asset_name == "character_sheet" and not character_name:
            character_name = extract_character_name(asset_content)
    
    if not character_name:
        character_name = "offspring_character"
    
    # Save draft with lineage metadata
    print(f"\n⏳ Saving draft...")
    
    # Get relative paths for parents
    drafts_root_abs = drafts_root.resolve()
    parent1_rel = str(parent1_path.relative_to(drafts_root_abs)) if parent1_path else ""
    parent2_rel = str(parent2_path.relative_to(drafts_root_abs)) if parent2_path else ""
    
    draft_dir = create_draft_dir(
        assets,
        character_name,
        seed=offspring_seed,
        mode=args.mode,
        model=model
    )
    
    # Update metadata with lineage
    metadata = DraftMetadata.load(draft_dir)
    if metadata:
        metadata.parent_drafts = [parent1_rel, parent2_rel]
        metadata.offspring_type = "generated"
        metadata.save(draft_dir)
    
    print(f"✓ Saved to: {draft_dir}")
    print(f"✓ Lineage: {parent1_rel} + {parent2_rel}")


def _find_draft(identifier: str, drafts_root: Path) -> Path | None:
    """Find a draft by name or path.
    
    Args:
        identifier: Draft name or path
        drafts_root: Root directory for drafts
        
    Returns:
        Path to draft directory or None
    """
    from bpui.utils.metadata.metadata import DraftMetadata
    
    # If it's an absolute path, use it directly
    path = Path(identifier)
    if path.is_absolute() and path.is_dir():
        return path
    
    # If relative path exists, use it
    if path.is_dir():
        return path
    
    # Search in drafts directory by name
    if not drafts_root.exists():
        return None
    
    # Try exact match first
    for draft_path in drafts_root.iterdir():
        if draft_path.is_dir() and not draft_path.name.startswith("."):
            # Check directory name
            if draft_path.name == identifier:
                return draft_path
            
            # Check metadata character name
            metadata = DraftMetadata.load(draft_path)
            if metadata and metadata.character_name == identifier:
                return draft_path
            
            # Check if identifier is in directory name (partial match)
            if identifier.lower() in draft_path.name.lower():
                return draft_path
    
    return None


async def run_list_models(args):
    """Run model listing from CLI."""
    from .config import Config
    from .llm.openai_compat_engine import OpenAICompatEngine
    
    logger = logging.getLogger(__name__)
    
    # Initialize variables
    base_url = None
    api_key = None
    provider = None
    
    logger.debug(f"list-models called with args: provider={args.provider}, base_url={args.base_url}, api_key={'set' if args.api_key else 'not set'}")
    
    # Step 1: Determine provider
    if args.provider:
        provider = args.provider.lower()
        logger.debug(f"Provider specified via --provider: {provider}")
    elif args.base_url:
        # Infer provider from base URL
        if "openrouter.ai" in args.base_url:
            provider = "openrouter"
        elif "api.openai.com" in args.base_url:
            provider = "openai"
        elif "generativelanguage.googleapis.com" in args.base_url:
            provider = "google"
        else:
            provider = "custom"
        logger.debug(f"Provider inferred from base URL: {provider}")
    
    # Step 2: Determine base URL
    if args.base_url:
        base_url = args.base_url.rstrip("/")
        logger.debug(f"Base URL from --base-url: {base_url}")
    elif provider:
        # Use default base URL for provider
        if provider == "openrouter":
            base_url = "https://openrouter.ai/api/v1"
        elif provider == "openai":
            base_url = "https://api.openai.com/v1"
        elif provider == "google":
            base_url = "https://generativelanguage.googleapis.com/v1beta"
        else:
            print(f"✗ Unknown provider: {provider}")
            sys.exit(1)
        logger.debug(f"Base URL from provider default: {base_url}")
    else:
        # Try to infer from config model
        config = Config()
        logger.debug(f"Config model: {config.model}")
        
        if config.model.startswith("openrouter/"):
            provider = "openrouter"
            base_url = "https://openrouter.ai/api/v1"
            logger.debug(f"Inferred OpenRouter from config model: {config.model}")
        elif config.model.startswith("openai/"):
            provider = "openai"
            base_url = "https://api.openai.com/v1"
            logger.debug(f"Inferred OpenAI from config model: {config.model}")
        elif config.model.startswith("google/"):
            provider = "google"
            base_url = "https://generativelanguage.googleapis.com/v1beta"
            logger.debug(f"Inferred Google from config model: {config.model}")
        else:
            print("✗ Cannot determine base URL. Use --provider or --base-url")
            print(f"   Current model: {config.model}")
            print(f"   Examples:")
            print(f"     ./bpui-cli list-models --provider openrouter")
            print(f"     ./bpui-cli list-models --base-url https://openrouter.ai/api/v1")
            sys.exit(1)
    
    # Step 3: Determine API key
    if args.api_key:
        api_key = args.api_key
        logger.debug(f"API key from --api-key: {'set'}")
    elif provider:
        # Get provider-specific key from config
        config = Config()
        api_key = config.get_api_key(provider)
        logger.debug(f"API key from config[{provider}]: {'set' if api_key else 'not set'}")
    
    # Step 4: Validate we have what we need
    if not base_url:
        print("✗ No base URL specified. Use --provider or --base-url")
        sys.exit(1)
    
    # Display what we're using
    print(f"🔍 Listing models from: {base_url}")
    if provider:
        print(f"   Provider: {provider}")
        if provider == "openrouter":
            print(f"   Note: Model IDs shown without 'openrouter/' prefix")
            print(f"         Add 'openrouter/' prefix when using these models")
    if api_key:
        print(f"   API key: {api_key[:10]}...{api_key[-4:]}")
    else:
        print(f"   API key: not provided (may be required for some providers)")
    print()
    
    try:
        # List models
        models = await OpenAICompatEngine.list_models(
            base_url=base_url,
            api_key=api_key,
            timeout=30.0
        )
        
        if not models:
            print("✗ No models found or API does not support model listing")
            sys.exit(1)
        
        # Filter models if filter specified
        if args.filter:
            filter_pattern = args.filter.lower()
            models = [m for m in models if filter_pattern in m.lower()]
        
        # Sort models
        models = sorted(models)
        
        # Output based on format
        if args.format == "json":
            import json
            print(json.dumps({
                "provider": args.provider or "custom",
                "base_url": base_url,
                "total_models": len(models),
                "models": models
            }, indent=2))
        elif args.format == "csv":
            print("model_id")
            for model in models:
                print(model)
        else:  # text format
            print(f"Found {len(models)} model(s):\n")
            for i, model in enumerate(models, 1):
                print(f"  {i:3d}. {model}")
        
        print(f"\n✓ Listed {len(models)} model(s)")
        
    except Exception as e:
        print(f"✗ Failed to list models: {e}")
        logger.error(f"Model listing failed: {e}", exc_info=True)
        sys.exit(1)


def run_similarity(args):
    """Run similarity analysis from CLI."""
    from bpui.features.similarity.engine import SimilarityAnalyzer, format_similarity_report
    
    drafts_root = args.drafts_dir or Path.cwd() / "drafts"
    
    if args.all:
        # Compare all pairs
        print(f"🔍 Comparing all characters in: {drafts_root}")
        
        # Get all draft directories
        draft_dirs = []
        if drafts_root.exists():
            for item in drafts_root.iterdir():
                if item.is_dir() and (item / "character_sheet.txt").exists():
                    draft_dirs.append(item)
        
        if not draft_dirs:
            print("✗ No drafts found")
            sys.exit(1)
        
        analyzer = SimilarityAnalyzer()
        results = analyzer.compare_multiple(draft_dirs)
        
        print(f"\n📊 Analyzed {len(results)} pairs\n")
        print("=" * 60)
        
        # Sort by overall similarity
        sorted_results = sorted(
            results.items(),
            key=lambda x: x[1].overall_score,
            reverse=True
        )
        
        for (char1, char2), result in sorted_results:
            if args.format == "json":
                import json
                print(json.dumps({
                    "character1": char1,
                    "character2": char2,
                    "overall_score": result.overall_score,
                    "compatibility": result.compatibility,
                    "dimension_scores": result.dimension_scores,
                    "conflict_potential": result.conflict_potential,
                    "synergy_potential": result.synergy_potential,
                }, indent=2))
            else:
                print(format_similarity_report(result))
        
        if args.cluster:
            print("\n" + "=" * 60)
            print("📦 Character Clusters")
            print("=" * 60)
            clusters = analyzer.cluster_characters(draft_dirs, min_similarity=args.threshold)
            for i, cluster in enumerate(clusters, 1):
                print(f"\nCluster {i} ({len(cluster)} characters):")
                for char_name in cluster:
                    print(f"  • {char_name}")
    
    elif args.cluster:
        # Cluster characters
        print(f"📦 Clustering characters with {args.threshold:.0%} similarity threshold")
        
        # Get all draft directories
        draft_dirs = []
        if drafts_root.exists():
            for item in drafts_root.iterdir():
                if item.is_dir() and (item / "character_sheet.txt").exists():
                    draft_dirs.append(item)
        
        if not draft_dirs:
            print("✗ No drafts found")
            sys.exit(1)
        
        analyzer = SimilarityAnalyzer()
        clusters = analyzer.cluster_characters(draft_dirs, min_similarity=args.threshold)
        
        print(f"\nFound {len(clusters)} clusters:\n")
        for i, cluster in enumerate(clusters, 1):
            print(f"Cluster {i} ({len(cluster)} characters):")
            for char_name in cluster:
                print(f"  • {char_name}")
    
    else:
        # Pairwise comparison
        print(f"🔍 Comparing two characters:")
        
        # Find drafts
        draft1_path = _find_draft(args.draft1, drafts_root)
        draft2_path = _find_draft(args.draft2, drafts_root)
        
        if not draft1_path:
            print(f"✗ Draft not found: {args.draft1}")
            sys.exit(1)
        if not draft2_path:
            print(f"✗ Draft not found: {args.draft2}")
            sys.exit(1)
        
        # Setup LLM engine if requested
        use_llm = args.use_llm
        llm_engine = None
        
        if use_llm:
            from bpui.llm.factory import create_engine
            from .config import Config

            config = Config()
            model = args.model or config.model
            config.validate_api_key(model)

            try:
                engine = create_engine(
                    config,
                    model_override=model if args.model else None,
                    temperature=config.temperature,
                    max_tokens=config.max_tokens,
                )
            except (ImportError, ValueError) as e:
                print(f"✗ Failed to create engine: {e}")
                sys.exit(1)

            llm_engine = engine
            print("🧠 LLM Deep Analysis enabled")
        
        analyzer = SimilarityAnalyzer()
        result = analyzer.compare_drafts(draft1_path, draft2_path, use_llm=use_llm, llm_engine=llm_engine)
        
        if not result:
            print("✗ Failed to analyze characters")
            sys.exit(1)
        
        if args.format == "json":
            import json
            print(json.dumps({
                "character1": result.character1_name,
                "character2": result.character2_name,
                "overall_score": result.overall_score,
                "compatibility": result.compatibility,
                "dimension_scores": result.dimension_scores,
                "conflict_potential": result.conflict_potential,
                "synergy_potential": result.synergy_potential,
                "commonalities": result.commonalities,
                "differences": result.differences,
                "relationship_suggestions": result.relationship_suggestions,
            }, indent=2))
        else:
            print(format_similarity_report(result))


if __name__ == "__main__":
    main()
