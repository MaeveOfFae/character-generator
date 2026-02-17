"""Template/blueprint system for custom asset types."""

from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass, field
import sys

# Use built-in tomllib for Python 3.11+, fallback to tomli for older versions
if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

import tomli_w


def _resolve_official_blueprints_dir() -> Path:
    """Resolve path to official blueprints directory.

    Tries parent directories of this file first (source checkout), then cwd
    (runtime execution from project root). Returns best-effort fallback.
    """
    marker_file = "rpbotgenerator.md"

    # Walk up from this module location to support source checkout execution.
    file_path = Path(__file__).resolve()
    for parent in file_path.parents:
        candidate = parent / "blueprints"
        if (candidate / marker_file).exists():
            return candidate

    # Fallback to current working directory (common for CLI/TUI runtime).
    cwd_candidate = Path.cwd() / "blueprints"
    if (cwd_candidate / marker_file).exists():
        return cwd_candidate

    # Best-effort default.
    return cwd_candidate


OFFICIAL_BLUEPRINTS_DIR = _resolve_official_blueprints_dir()


@dataclass
class AssetDefinition:
    """Definition of a single asset in a template."""
    name: str
    required: bool = True
    depends_on: List[str] = field(default_factory=list)
    description: str = ""
    blueprint_file: Optional[str] = None


@dataclass
class Template:
    """A template defining a custom set of assets."""
    name: str
    version: str
    description: str
    assets: List[AssetDefinition]
    path: Path
    
    @property
    def is_official(self) -> bool:
        """Check if this is an official template."""
        official_dir = OFFICIAL_BLUEPRINTS_DIR
        try:
            # Resolve both paths to handle symlinks, etc.
            return self.path.resolve().is_relative_to(official_dir.resolve())
        except Exception:
            # Fallback for any issues with resolving paths on weird filesystems.
            return "official" in str(self.path) or "blueprints" in str(self.path)


class TemplateManager:
    """Manager for custom blueprint templates."""
    
    def __init__(self, config_dir: Optional[Path] = None):
        """Initialize template manager.
        
        Args:
            config_dir: Configuration directory (default: ~/.config/bpui)
        """
        if config_dir is None:
            config_dir = Path.home() / ".config" / "bpui"
        
        self.config_dir = config_dir
        self.templates_dir = config_dir / "templates"
        self.custom_dir = self.templates_dir / "custom"
        self.official_dir = OFFICIAL_BLUEPRINTS_DIR
        
        # Ensure directories exist
        self.custom_dir.mkdir(parents=True, exist_ok=True)
    
    def list_templates(self) -> List[Template]:
        """List all available templates (official + custom).
        
        Returns:
            List of Template objects
        """
        templates = []
        
        # Add official template (default 7 assets)
        official_template = self._create_official_template()
        if official_template:
            templates.append(official_template)

        # Add templates from the blueprints directory
        if self.official_dir.exists():
            for template_dir in self.official_dir.iterdir():
                if template_dir.is_dir():
                    template = self._load_template(template_dir)
                    if template:
                        # Avoid adding duplicates
                        if not any(t.name == template.name for t in templates):
                            templates.append(template)
        
        # Add custom templates
        if self.custom_dir.exists():
            for template_dir in self.custom_dir.iterdir():
                if template_dir.is_dir():
                    template = self._load_template(template_dir)
                    if template:
                        # Avoid adding duplicates from project blueprints
                        if not any(t.name == template.name for t in templates):
                            templates.append(template)
        
        return templates
    
    def get_template(self, name: str) -> Optional[Template]:
        """Get a specific template by name.
        
        Args:
            name: Template name
            
        Returns:
            Template object or None if not found
        """
        templates = self.list_templates()
        for template in templates:
            if template.name == name:
                return template
        return None
    
    def _create_official_template(self) -> Optional[Template]:
        """Create template definition for official/default blueprints.
        
        Returns:
            Template object for official assets
        """
        if not self.official_dir.exists():
            return None
        
        # Define the default 7 assets with hierarchy
        # Note: These reference the shared blueprints from templates/example_minimal
        assets = [
            AssetDefinition(
                name="system_prompt",
                required=True,
                depends_on=[],
                description="System-level behavioral instructions",
                blueprint_file="templates/example_minimal/system_prompt.md"
            ),
            AssetDefinition(
                name="post_history",
                required=True,
                depends_on=["system_prompt"],
                description="Conversation context and relationship state",
                blueprint_file="templates/example_minimal/post_history.md"
            ),
            AssetDefinition(
                name="character_sheet",
                required=True,
                depends_on=["system_prompt", "post_history"],
                description="Structured character data",
                blueprint_file="templates/example_minimal/character_sheet.md"
            ),
            AssetDefinition(
                name="intro_scene",
                required=True,
                depends_on=["system_prompt", "post_history", "character_sheet"],
                description="First interaction scenario",
                blueprint_file="templates/example_minimal/intro_scene.md"
            ),
            AssetDefinition(
                name="intro_page",
                required=True,
                depends_on=["character_sheet"],
                description="Visual character introduction page",
                blueprint_file="templates/example_minimal/intro_page.md"
            ),
            AssetDefinition(
                name="a1111",
                required=True,
                depends_on=["character_sheet"],
                description="Stable Diffusion image generation prompt",
                blueprint_file="examples/a1111_sdxl_comfyui.md"
            ),
            AssetDefinition(
                name="suno",
                required=True,
                depends_on=["character_sheet"],
                description="Suno music generation prompt",
                blueprint_file="templates/example_music_only/suno.md"
            ),
        ]
        
        return Template(
            name="Official RPBotGenerator",
            version="3.1",
            description="Official 7-asset template for RPBotGenerator",
            assets=assets,
            path=self.official_dir / "templates" / "example_minimal"
        )
    
    def _load_template(self, template_dir: Path) -> Optional[Template]:
        """Load a custom template from directory.
        
        Args:
            template_dir: Path to template directory
            
        Returns:
            Template object or None if invalid
        """
        manifest_path = template_dir / "template.toml"
        
        if not manifest_path.exists():
            return None
        
        try:
            with open(manifest_path, "rb") as f:
                data = tomllib.load(f)
            
            # Parse template metadata
            template_meta = data.get("template", {})
            name = template_meta.get("name", template_dir.name)
            version = template_meta.get("version", "1.0.0")
            description = template_meta.get("description", "")
            
            # Parse assets
            assets = []
            for asset_data in data.get("assets", []):
                asset = AssetDefinition(
                    name=asset_data["name"],
                    required=asset_data.get("required", True),
                    depends_on=asset_data.get("depends_on", []),
                    description=asset_data.get("description", ""),
                    blueprint_file=asset_data.get("blueprint_file")
                )
                assets.append(asset)
            
            return Template(
                name=name,
                version=version,
                description=description,
                assets=assets,
                path=template_dir
            )
        
        except Exception:
            return None
    
    def create_template(
        self,
        name: str,
        description: str,
        assets: List[AssetDefinition]
    ) -> Template:
        """Create a new custom template.
        
        Args:
            name: Template name
            description: Template description
            assets: List of asset definitions
            
        Returns:
            Created Template object
        """
        # Sanitize name for directory
        dir_name = name.lower().replace(" ", "_")
        template_dir = self.custom_dir / dir_name
        template_dir.mkdir(parents=True, exist_ok=True)
        
        # Create assets directory
        assets_dir = template_dir / "assets"
        assets_dir.mkdir(exist_ok=True)
        
        # Create manifest
        manifest_data = {
            "template": {
                "name": name,
                "version": "1.0.0",
                "description": description
            },
            "assets": [
                {
                    "name": asset.name,
                    "required": asset.required,
                    "depends_on": asset.depends_on,
                    "description": asset.description,
                    "blueprint_file": asset.blueprint_file or f"{asset.name}.md"
                }
                for asset in assets
            ]
        }
        
        manifest_path = template_dir / "template.toml"
        with open(manifest_path, "wb") as f:
            tomli_w.dump(manifest_data, f)
        
        return Template(
            name=name,
            version="1.0.0",
            description=description,
            assets=assets,
            path=template_dir
        )
    
    def save_template(self, template: Template):
        """Save a template to its path.

        Args:
            template: The template to save.
        """
        if not template.path.exists():
            template.path.mkdir(parents=True, exist_ok=True)

        manifest_data = {
            "template": {
                "name": template.name,
                "version": template.version,
                "description": template.description
            },
            "assets": [
                {
                    "name": asset.name,
                    "required": asset.required,
                    "depends_on": asset.depends_on,
                    "description": asset.description,
                    "blueprint_file": asset.blueprint_file or f"{asset.name}.md"
                }
                for asset in template.assets
            ]
        }
        
        manifest_path = template.path / "template.toml"
        with open(manifest_path, "wb") as f:
            tomli_w.dump(manifest_data, f)
    
    def validate_template(self, template: Template) -> Dict[str, List[str]]:
        """Validate a template for correctness.

        Args:
            template: Template to validate

        Returns:
            Dict with 'errors' and 'warnings' lists
        """
        errors = []
        warnings = []

        # Check for empty assets
        if not template.assets:
            errors.append("Template has no assets defined")

        # Check for duplicate asset names
        asset_names = [asset.name for asset in template.assets]
        if len(asset_names) != len(set(asset_names)):
            errors.append("Template has duplicate asset names")

        # Check dependencies
        for asset in template.assets:
            for dep in asset.depends_on:
                if dep not in asset_names:
                    errors.append(f"Asset '{asset.name}' depends on unknown asset '{dep}'")

        # Check for circular dependencies using topological sort
        try:
            from bpui.utils.topological_sort import topological_sort
            topological_sort(template.assets)
        except ValueError as e:
            errors.append(f"Circular dependency detected: {e}")

        # Check blueprint files exist and validate syntax
        for asset in template.assets:
            # Check if blueprint file is specified
            if not asset.blueprint_file:
                warnings.append(f"Asset '{asset.name}' has no blueprint file specified")
                continue

            # Try to find blueprint file
            blueprint_content = self.get_blueprint_content(template, asset.name)

            if not blueprint_content:
                errors.append(
                    f"Blueprint file for '{asset.name}' not found: {asset.blueprint_file}. "
                    f"Expected at: {template.path / 'assets' / asset.blueprint_file}"
                )
            else:
                # Validate blueprint syntax (check for frontmatter)
                if not blueprint_content.strip().startswith('---'):
                    warnings.append(
                        f"Blueprint '{asset.name}' missing frontmatter (should start with '---')"
                    )

            # Check for missing asset description
            if not asset.description:
                warnings.append(f"Asset '{asset.name}' has no description")

        return {"errors": errors, "warnings": warnings}
    
    def _has_circular_dependencies(self, assets: List[AssetDefinition]) -> bool:
        """Check if assets have circular dependencies.
        
        Args:
            assets: List of asset definitions
            
        Returns:
            True if circular dependencies exist
        """
        asset_map = {asset.name: asset.depends_on for asset in assets}
        
        def has_cycle(asset_name: str, visited: set, stack: set) -> bool:
            visited.add(asset_name)
            stack.add(asset_name)
            
            for dep in asset_map.get(asset_name, []):
                if dep not in visited:
                    if has_cycle(dep, visited, stack):
                        return True
                elif dep in stack:
                    return True
            
            stack.remove(asset_name)
            return False
        
        visited = set()
        for asset in assets:
            if asset.name not in visited:
                if has_cycle(asset.name, visited, set()):
                    return True
        
        return False
    
    def export_template(self, template: Template, output_path: Path) -> None:
        """Export a template to a directory.
        
        Args:
            template: Template to export
            output_path: Output directory path
        """
        import shutil
        
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Copy manifest
        manifest_src = template.path / "template.toml"
        if manifest_src.exists():
            shutil.copy2(manifest_src, output_path / "template.toml")
        
        # Copy assets
        assets_src = template.path / "assets"
        if assets_src.exists():
            assets_dst = output_path / "assets"
            if assets_dst.exists():
                shutil.rmtree(assets_dst)
            shutil.copytree(assets_src, assets_dst)
    
    def import_template(self, source_path: Path) -> Optional[Template]:
        """Import a template from a directory.
        
        Args:
            source_path: Source directory path
            
        Returns:
            Imported Template object or None if invalid
        """
        import shutil
        
        # Load template to validate
        template = self._load_template(source_path)
        if not template:
            return None
        
        # Validate before importing
        validation = self.validate_template(template)
        if validation["errors"]:
            return None
        
        # Copy to custom templates directory
        dir_name = template.name.lower().replace(" ", "_")
        dest_path = self.custom_dir / dir_name
        
        if dest_path.exists():
            shutil.rmtree(dest_path)
        
        shutil.copytree(source_path, dest_path)
        
        # Reload from new location
        return self._load_template(dest_path)
    
    def delete_template(self, template: Template) -> bool:
        """Delete a custom template.
        
        Args:
            template: Template to delete
            
        Returns:
            True if deleted successfully
        """
        import shutil
        
        # Don't allow deleting official template
        if template.is_official:
            return False
        
        if template.path.exists():
            shutil.rmtree(template.path)
            return True
        
        return False
    
    def get_blueprint_content(self, template: Template, asset_name: str) -> Optional[str]:
        """Get blueprint content for a specific asset.
        
        Args:
            template: Template containing the asset
            asset_name: Name of the asset
            
        Returns:
            Blueprint content as string or None if not found
        """
        # Find asset definition
        asset = None
        for a in template.assets:
            if a.name == asset_name:
                asset = a
                break
        
        if not asset or not asset.blueprint_file:
            return None
        
        # For official templates, try direct path from blueprints root first
        if template.is_official:
            root_path = self.official_dir / asset.blueprint_file
            print(f"Checking for official blueprint at: {root_path}, exists: {root_path.exists()}")
            if root_path.exists():
                return root_path.read_text(encoding='utf-8')
        
        # Try template's assets directory
        blueprint_path = template.path / "assets" / asset.blueprint_file
        if blueprint_path.exists():
            return blueprint_path.read_text(encoding='utf-8')
        
        # Handle relative paths (like ../../system/system_prompt.md)
        if "/" in asset.blueprint_file:
            # Resolve relative to template path
            resolved_path = (template.path / asset.blueprint_file).resolve()
            if resolved_path.exists():
                return resolved_path.read_text(encoding='utf-8')
        
        # Try official blueprints directories as fallback for custom templates
        if not template.is_official:
            # Try direct path from blueprints root
            root_path = self.official_dir / asset.blueprint_file
            if root_path.exists():
                return root_path.read_text(encoding='utf-8')
            
            # Try in template-specific blueprint directories
            for blueprint_dir in self.official_dir.glob("templates/*/"):
                official_path = blueprint_dir / asset.blueprint_file
                if official_path.exists():
                    return official_path.read_text(encoding='utf-8')
            
            # Try in system directory
            system_path = self.official_dir / "system" / asset.blueprint_file
            if system_path.exists():
                return system_path.read_text(encoding='utf-8')
            
            # Try in examples directory
            examples_path = self.official_dir / "examples" / asset.blueprint_file
            if examples_path.exists():
                return examples_path.read_text(encoding='utf-8')
        
        return None
