"""Tests for parser template integration."""

import pytest
from pathlib import Path
from bpui.core.parse_blocks import parse_blueprint_output, get_asset_filename, ParseError
from bpui.features.templates.templates import TemplateManager, Template, AssetDefinition


@pytest.fixture
def minimal_template():
    """Create a minimal template for testing."""
    return Template(
        name="Test Template",
        version="1.0.0",
        description="Test template",
        assets=[
            AssetDefinition(
                name="asset1",
                required=True,
                depends_on=[],
                description="First asset",
                blueprint_file="asset1.md"
            ),
            AssetDefinition(
                name="asset2",
                required=True,
                depends_on=["asset1"],
                description="Second asset",
                blueprint_file="asset2.md"
            ),
            AssetDefinition(
                name="asset3",
                required=True,
                depends_on=["asset1", "asset2"],
                description="Third asset",
                blueprint_file="asset3.md"
            )
        ],
        path=Path("test")
    )


class TestParserTemplateSupport:
    """Tests for parser template support."""
    
    def test_parse_with_default_template(self):
        """Test parsing with default 7-asset template."""
        output = """
```
Asset 1 content
```

```
Asset 2 content
```

```
Asset 3 content
```

```
Asset 4 content
```

```
Asset 5 content
```

```
Asset 6 content
```

```
Asset 7 content
```
"""
        
        assets = parse_blueprint_output(output)
        assert len(assets) == 7
        assert "system_prompt" in assets
        assert "suno" in assets
    
    def test_parse_with_custom_template(self, minimal_template):
        """Test parsing with custom 3-asset template."""
        output = """
```
Asset 1 content
```

```
Asset 2 content
```

```
Asset 3 content
```
"""
        
        assets = parse_blueprint_output(output, template=minimal_template)
        assert len(assets) == 3
        assert "asset1" in assets
        assert "asset2" in assets
        assert "asset3" in assets
        assert assets["asset1"] == "Asset 1 content"
    
    def test_parse_wrong_count_with_template(self, minimal_template):
        """Test parsing fails with wrong asset count."""
        output = """
```
Asset 1 content
```

```
Asset 2 content
```
"""
        
        with pytest.raises(ParseError) as excinfo:
            parse_blueprint_output(output, template=minimal_template)
        
        assert "Test Template" in str(excinfo.value)
        assert "expects 3 asset blocks, found 2" in str(excinfo.value)
    
    def test_parse_with_adjustment_note_and_template(self, minimal_template):
        """Test parsing with adjustment note and custom template."""
        output = """
```
Adjustment Note: Made some changes
```

```
Asset 1 content
```

```
Asset 2 content
```

```
Asset 3 content
```
"""
        
        assets = parse_blueprint_output(output, template=minimal_template)
        assert len(assets) == 3
        assert "asset1" in assets


class TestAssetFilenameMapping:
    """Tests for asset filename mapping."""
    
    def test_get_asset_filename_default(self):
        """Test getting filename for default asset."""
        filename = get_asset_filename("system_prompt")
        assert filename == "system_prompt.txt"
    
    def test_get_asset_filename_custom(self, minimal_template):
        """Test getting filename with template."""
        filename = get_asset_filename("asset1", minimal_template)
        assert filename == "asset1.md"
    
    def test_get_asset_filename_unknown(self):
        """Test getting filename for unknown asset."""
        filename = get_asset_filename("unknown_asset")
        assert filename == "unknown_asset.txt"


class TestTemplateManager:
    """Tests for TemplateManager."""
    
    def test_template_manager_creation(self):
        """Test template manager can be created."""
        manager = TemplateManager()
        assert manager is not None
        assert manager.custom_dir.exists()
    
    def test_list_templates(self):
        """Test listing templates."""
        manager = TemplateManager()
        templates = manager.list_templates()
        
        # Should have at least the official template
        assert len(templates) >= 1
        
        # Check official template
        official = next((t for t in templates if t.is_official), None)
        assert official is not None
        assert official.name == "Official RPBotGenerator"
        assert len(official.assets) == 7
    
    def test_get_template_by_name(self):
        """Test getting template by name."""
        manager = TemplateManager()
        template = manager.get_template("Official RPBotGenerator")
        
        assert template is not None
        assert template.name == "Official RPBotGenerator"
    
    def test_validate_valid_template(self, minimal_template):
        """Test validating a valid template."""
        manager = TemplateManager()
        result = manager.validate_template(minimal_template)
        
        assert len(result["errors"]) == 0
    
    def test_validate_circular_dependency(self):
        """Test validation catches circular dependencies."""
        template = Template(
            name="Circular Test",
            version="1.0.0",
            description="Test",
            assets=[
                AssetDefinition(
                    name="asset1",
                    required=True,
                    depends_on=["asset2"],
                    description="First"
                ),
                AssetDefinition(
                    name="asset2",
                    required=True,
                    depends_on=["asset1"],
                    description="Second"
                )
            ],
            path=Path("test")
        )
        
        manager = TemplateManager()
        result = manager.validate_template(template)
        
        assert len(result["errors"]) > 0
        assert any("circular" in err.lower() for err in result["errors"])
    
    def test_validate_missing_dependency(self):
        """Test validation catches missing dependencies."""
        template = Template(
            name="Missing Dep Test",
            version="1.0.0",
            description="Test",
            assets=[
                AssetDefinition(
                    name="asset1",
                    required=True,
                    depends_on=["nonexistent"],
                    description="First"
                )
            ],
            path=Path("test")
        )
        
        manager = TemplateManager()
        result = manager.validate_template(template)
        
        assert len(result["errors"]) > 0
        assert any("nonexistent" in err for err in result["errors"])


class TestPackIOTemplateSupport:
    """Tests for pack_io template support."""
    
    def test_create_draft_dir_with_template(self, minimal_template, tmp_path):
        """Test creating draft directory with template."""
        from bpui.utils.file_io.pack_io import create_draft_dir
        
        assets = {
            "asset1": "Content 1",
            "asset2": "Content 2",
            "asset3": "Content 3"
        }
        
        draft_dir = create_draft_dir(
            assets,
            "test_char",
            drafts_root=tmp_path,
            seed="test seed",
            mode="NSFW",
            model="gpt-4",
            template=minimal_template
        )
        
        assert draft_dir.exists()
        assert (draft_dir / "asset1.md").exists()
        assert (draft_dir / "asset2.md").exists()
        assert (draft_dir / "asset3.md").exists()
        
        # Check metadata includes template name
        from bpui.utils.metadata.metadata import DraftMetadata
        metadata = DraftMetadata.load(draft_dir)
        assert metadata is not None
        assert metadata.template_name == "Test Template"
    
    def test_load_draft_with_template(self, minimal_template, tmp_path):
        """Test loading draft with template."""
        from bpui.utils.file_io.pack_io import load_draft
        
        assets = {
            "asset1": "Content 1",
            "asset2": "Content 2",
            "asset3": "Content 3"
        }
        
        draft_dir = create_draft_dir(
            assets,
            "test_char",
            drafts_root=tmp_path,
            template=minimal_template
        )
        
        # Load back
        loaded_assets = load_draft(draft_dir, template=minimal_template)
        
        assert len(loaded_assets) == 3
        assert loaded_assets["asset1"] == "Content 1"
        assert loaded_assets["asset2"] == "Content 2"
        assert loaded_assets["asset3"] == "Content 3"
