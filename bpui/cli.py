"""CLI entry point for Blueprint UI."""

import sys
import argparse
import asyncio
from pathlib import Path


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Blueprint UI - RPBotGenerator Character Compiler"
    )
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
    batch_parser.add_argument("--resume", action="store_true", help="Resume last incomplete batch")
    batch_parser.add_argument("--clean-batch-state", action="store_true", help="Clean up old batch state files")

    args = parser.parse_args()

    # Default to TUI if no command
    if not args.command or args.command == "tui":
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


def run_tui():
    """Run the TUI application."""
    from .tui.app import BlueprintUI

    app = BlueprintUI()
    app.run()


async def run_compile(args):
    """Run compilation from CLI."""
    from .config import Config
    from .llm.litellm_engine import LiteLLMEngine
    from .llm.openai_compat_engine import OpenAICompatEngine
    from .prompting import build_asset_prompt
    from .parse_blocks import extract_single_asset, extract_character_name, ASSET_ORDER
    from .pack_io import create_draft_dir

    config = Config()

    print(f"🌱 Compiling seed: {args.seed}")
    print(f"   Mode: {args.mode or 'Auto'}")
    print(f"   Model: {args.model or config.model}")

    # Create engine
    model = args.model or config.model
    engine_config = {
        "model": model,
        "api_key": config.api_key,
        "temperature": config.temperature,
        "max_tokens": config.max_tokens,
    }

    if config.engine == "litellm":
        engine = LiteLLMEngine(**engine_config)
    else:
        engine_config["base_url"] = config.base_url
        engine = OpenAICompatEngine(**engine_config)

    # Generate each asset sequentially
    print("\n⏳ Starting sequential generation...")
    assets = {}
    character_name = None

    for asset_name in ASSET_ORDER:
        print(f"\n→ Generating {asset_name}...")
        
        # Build prompt with prior assets as context
        system_prompt, user_prompt = build_asset_prompt(
            asset_name, args.seed, args.mode, assets
        )
        
        # Generate
        output_text = await engine.generate(system_prompt, user_prompt)
        
        # Parse this asset
        asset_content = extract_single_asset(output_text, asset_name)
        assets[asset_name] = asset_content
        print(f"✓ {asset_name} complete")
        
        # Extract character name from character_sheet
        if asset_name == "character_sheet" and not character_name:
            character_name = extract_character_name(asset_content)
            if character_name:
                print(f"   Character: {character_name}")

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

    config = Config()

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
        engine = LiteLLMEngine(**engine_config)
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

    print(f"📦 Exporting: {args.character_name}")
    result = export_character(args.character_name, source_dir, args.model)

    print(result["output"])
    if result["errors"]:
        print(f"\nErrors:\n{result['errors']}")

    sys.exit(result["exit_code"])


async def run_batch(args):
    """Run batch compilation from CLI."""
    from .config import Config
    from .llm.litellm_engine import LiteLLMEngine
    from .llm.openai_compat_engine import OpenAICompatEngine
    from .prompting import build_orchestrator_prompt
    from .parse_blocks import parse_blueprint_output, extract_character_name, ASSET_FILENAMES
    from .pack_io import create_draft_dir
    from .batch_state import BatchState

    config = Config()

    # Handle cleanup flag
    if args.clean_batch_state:
        deleted = BatchState.cleanup_old_states(days=7)
        print(f"✓ Cleaned up {deleted} old batch state file(s)")
        return

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
    model = args.model or config.model
    engine_config = {
        "model": model,
        "api_key": config.api_key,
        "temperature": config.temperature,
        "max_tokens": config.max_tokens,
    }

    if config.engine == "litellm":
        engine = LiteLLMEngine(**engine_config)
    else:
        engine_config["base_url"] = config.base_url
        engine = OpenAICompatEngine(**engine_config)

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
                break

    # Mark batch as completed
    batch_state.mark_completed_status()
    batch_state.save()
    
    # Clean up state file on successful completion
    if not failed:
        batch_state.delete_state_file()

    # Summary
    print(f"\n{'='*60}")
    print(f"✓ Batch complete: {successful}/{batch_state.total_seeds} successful")
    if failed:
        print(f"\n✗ Failed ({len(failed)}):")
        for fail_record in failed:
            seed_display = fail_record["seed"][:60]
            print(f"  • {seed_display}... → {fail_record['error']}")

    sys.exit(0 if successful == batch_state.total_seeds else 1)


if __name__ == "__main__":
    main()
