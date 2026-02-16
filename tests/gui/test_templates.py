"""Tests for GUI template components."""

import pytest
from pathlib import Path
from PySide6.QtWidgets import QApplication
from bpui.gui.blueprint_editor import BlueprintEditor
from bpui.gui.template_wizard import TemplateWizard, AssetDef
from bpui.gui.asset_designer import AssetDesignerDialog
from bpui.gui.dependency_dialog import DependencyDialog


@pytest.fixture(scope="module")
def qapp():
    """Create QApplication for GUI tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app
    

class TestBlueprintEditor:
    """Tests for BlueprintEditor."""
    
    def test_blueprint_editor_creation(self, qapp):
        """Test blueprint editor can be created."""
        editor = BlueprintEditor()
        assert editor is not None
        assert editor.windowTitle() == "Blueprint Editor"
    
    def test_frontmatter_generation(self, qapp):
        """Test frontmatter generation."""
        editor = BlueprintEditor()
        editor.name_edit.setText("Test Blueprint")
        editor.description_edit.setText("A test blueprint")
        editor.version_major.setValue(2)
        editor.version_minor.setValue(5)
        editor.invokable_check.setChecked(True)
        
        frontmatter = editor.generate_frontmatter()
        
        assert "name: Test Blueprint" in frontmatter
        assert "description: A test blueprint" in frontmatter
        assert "version: 2.5" in frontmatter
        assert "invokable: true" in frontmatter
    
    def test_parse_blueprint(self, qapp):
        """Test parsing existing blueprint."""
        editor = BlueprintEditor()
        content = """---
name: Character Sheet
description: Generate character sheet
invokable: true
version: 3.1
---

# Blueprint Agent

Content here..."""
        
        frontmatter, body = editor.parse_blueprint(content)
        
        assert frontmatter["name"] == "Character Sheet"
        assert frontmatter["description"] == "Generate character sheet"
        assert frontmatter["invokable"] is True
        assert frontmatter["version"] == "3.1"
        assert "# Blueprint Agent" in body
    
    def test_get_full_content(self, qapp):
        """Test getting full content with frontmatter."""
        editor = BlueprintEditor()
        editor.name_edit.setText("Test")
        editor.description_edit.setText("Test desc")
        editor.content_edit.setPlainText("# Content")
        
        content = editor.get_full_content()
        
        assert "---" in content
        assert "name: Test" in content
        assert "# Content" in content


class TestTemplateWizard:
    """Tests for TemplateWizard."""
    
    def test_wizard_creation(self, qapp):
        """Test wizard can be created."""
        wizard = TemplateWizard()
        assert wizard is not None
        assert wizard.current_step == 0
        assert len(wizard.assets) == 0
    
    def test_validate_basic_info_empty(self, qapp):
        """Test basic info validation with empty name."""
        wizard = TemplateWizard()
        wizard.name_input.setText("")
        
        assert not wizard.validate_basic_info()
    
    def test_validate_basic_info_valid(self, qapp):
        """Test basic info validation with valid name."""
        wizard = TemplateWizard()
        wizard.name_input.setText("My Template")
        
        assert wizard.validate_basic_info()
    
    def test_save_basic_info(self, qapp):
        """Test saving basic info."""
        wizard = TemplateWizard()
        wizard.name_input.setText("Test Template")
        wizard.version_input.setText("2.0.0")
        wizard.description_input.setPlainText("Test description")
        
        wizard.save_basic_info()
        
        assert wizard.template_name == "Test Template"
        assert wizard.template_version == "2.0.0"
        assert wizard.template_description == "Test description"
    
    def test_generate_toml(self, qapp):
        """Test TOML generation."""
        wizard = TemplateWizard()
        wizard.template_name = "My Template"
        wizard.template_version = "1.0.0"
        wizard.template_description = "A test template"
        wizard.assets = [
            AssetDef(
                name="asset1",
                required=True,
                depends_on=[],
                description="First asset"
            ),
            AssetDef(
                name="asset2",
                required=True,
                depends_on=["asset1"],
                description="Second asset"
            )
        ]
        
        toml = wizard.generate_toml()
        
        assert 'name = "My Template"' in toml
        assert 'version = "1.0.0"' in toml
        assert 'name = "asset1"' in toml
        assert 'name = "asset2"' in toml
        assert 'depends_on = ["asset1"]' in toml


class TestAssetDesignerDialog:
    """Tests for AssetDesignerDialog."""
    
    def test_asset_designer_creation(self, qapp):
        """Test asset designer can be created."""
        dialog = AssetDesignerDialog()
        assert dialog is not None
        assert not dialog.editing
    
    def test_asset_designer_with_existing(self, qapp):
        """Test asset designer with existing asset names."""
        dialog = AssetDesignerDialog(existing_assets=["asset1", "asset2"])
        assert dialog.existing_assets == ["asset1", "asset2"]
    
    def test_load_asset(self, qapp):
        """Test loading an existing asset."""
        asset = AssetDef(
            name="test_asset",
            required=False,
            description="Test description",
            blueprint_source="custom",
            blueprint_file="custom.md"
        )
        
        dialog = AssetDesignerDialog(asset=asset)
        
        assert dialog.name_input.text() == "test_asset"
        assert dialog.description_input.toPlainText() == "Test description"
        assert not dialog.required_check.isChecked()
        assert dialog.custom_radio.isChecked()
        assert dialog.custom_filename_input.text() == "custom.md"


class TestDependencyDialog:
    """Tests for DependencyDialog."""
    
    def test_dependency_dialog_creation(self, qapp):
        """Test dependency dialog can be created."""
        dialog = DependencyDialog(
            None,
            "asset2",
            ["asset1"],
            []
        )
        assert dialog is not None
        assert dialog.asset_name == "asset2"
        assert dialog.available_deps == ["asset1"]
    
    def test_get_selected_dependencies_empty(self, qapp):
        """Test getting dependencies when none selected."""
        dialog = DependencyDialog(
            None,
            "asset2",
            ["asset1"],
            []
        )
        
        selected = dialog.get_selected_dependencies()
        assert selected == []
    
    def test_get_selected_dependencies_with_selection(self, qapp):
        """Test getting dependencies with selection."""
        dialog = DependencyDialog(
            None,
            "asset3",
            ["asset1", "asset2"],
            ["asset1"]
        )
        
        # The checkbox for asset1 should be checked
        selected = dialog.get_selected_dependencies()
        assert "asset1" in selected


class TestTemplateIntegration:
    """Integration tests for template system."""
    
    def test_template_manager_loads_templates(self, qapp):
        """Test template manager can load templates."""
        from bpui.gui.template_manager import TemplateManagerScreen
        from bpui.config import Config
        
        config = Config()
        manager_screen = TemplateManagerScreen(None, config)
        
        assert manager_screen is not None
        # Should have at least the official template
        assert len(manager_screen.templates) >= 1
    
    def test_example_minimal_template_exists(self):
        """Test example_minimal template exists."""
        template_path = Path("blueprints/templates/example_minimal/template.toml")
        assert template_path.exists()
        
        # Check assets exist
        assets_dir = Path("blueprints/templates/example_minimal/assets")
        assert assets_dir.exists()
        assert (assets_dir / "system_prompt.md").exists()
        assert (assets_dir / "character_sheet.md").exists()
        assert (assets_dir / "intro_scene.md").exists()
    
    def test_example_image_only_template_exists(self):
        """Test example_image_only template exists."""
        template_path = Path("blueprints/templates/example_image_only/template.toml")
        assert template_path.exists()
        
        assets_dir = Path("blueprints/templates/example_image_only/assets")
        assert assets_dir.exists()
        assert (assets_dir / "system_prompt.md").exists()
        assert (assets_dir / "character_sheet.md").exists()
        assert (assets_dir / "a1111.md").exists()
    
    def test_example_music_only_template_exists(self):
        """Test example_music_only template exists."""
        template_path = Path("blueprints/templates/example_music_only/template.toml")
        assert template_path.exists()
        
        assets_dir = Path("blueprints/templates/example_music_only/assets")
        assert assets_dir.exists()
        assert (assets_dir / "system_prompt.md").exists()
        assert (assets_dir / "character_sheet.md").exists()
        assert (assets_dir / "suno.md").exists()
