"""Tests for bpui/parse_blocks.py."""

import pytest
from bpui.parse_blocks import (
    extract_codeblocks,
    parse_blueprint_output,
    extract_single_asset,
    extract_character_name,
    ParseError,
    ASSET_ORDER,
)


class TestExtractCodeblocks:
    """Tests for extract_codeblocks function."""
    
    def test_extract_single_block(self):
        """Test extracting a single codeblock."""
        text = "```\nblock1\n```"
        blocks = extract_codeblocks(text)
        assert len(blocks) == 1
        assert blocks[0] == "block1"
    
    def test_extract_multiple_blocks(self):
        """Test extracting multiple codeblocks."""
        text = "```\nblock1\n```\n\nSome text\n\n```\nblock2\n```"
        blocks = extract_codeblocks(text)
        assert len(blocks) == 2
        assert blocks[0] == "block1"
        assert blocks[1] == "block2"
    
    def test_extract_with_language_tag(self):
        """Test extracting codeblock with language tag."""
        text = "```python\ncode here\n```"
        blocks = extract_codeblocks(text)
        assert len(blocks) == 1
        assert blocks[0] == "code here"
    
    def test_extract_with_markdown_tag(self):
        """Test extracting codeblock with markdown tag."""
        text = "```markdown\n# Title\nContent\n```"
        blocks = extract_codeblocks(text)
        assert len(blocks) == 1
        assert blocks[0] == "# Title\nContent"
    
    def test_extract_empty_block(self):
        """Test extracting empty codeblock."""
        text = "```\n```"
        blocks = extract_codeblocks(text)
        assert len(blocks) == 1
        assert blocks[0] == ""
    
    def test_extract_no_blocks(self):
        """Test when no codeblocks present."""
        text = "Just some regular text"
        blocks = extract_codeblocks(text)
        assert len(blocks) == 0
    
    def test_extract_preserves_whitespace(self):
        """Test that whitespace is preserved."""
        text = "```\n  indented\n    more indent\n```"
        blocks = extract_codeblocks(text)
        assert blocks[0] == "indented\n    more indent"


class TestParseRBlueprintOutput:
    """Tests for parse_blueprint_output function."""
    
    def test_parse_seven_blocks(self):
        """Test parsing exactly 7 asset blocks."""
        output = "\n".join([f"```\nasset{i}\n```" for i in range(7)])
        assets = parse_blueprint_output(output)
        
        assert len(assets) == 7
        assert all(name in assets for name in ASSET_ORDER)
        assert assets["system_prompt"] == "asset0"
        assert assets["suno"] == "asset6"
    
    def test_parse_with_adjustment_note(self):
        """Test parsing with adjustment note as first block."""
        output = "```\nAdjustment Note: Seed augmented\n```\n"
        output += "\n".join([f"```\nasset{i}\n```" for i in range(7)])
        
        assets = parse_blueprint_output(output)
        assert len(assets) == 7
        assert "system_prompt" in assets
    
    def test_parse_wrong_count_too_few(self):
        """Test error when too few blocks."""
        output = "\n".join([f"```\nasset{i}\n```" for i in range(5)])
        
        with pytest.raises(ParseError, match="Expected 7 asset blocks, found 5"):
            parse_blueprint_output(output)
    
    def test_parse_wrong_count_too_many(self):
        """Test error when too many blocks."""
        output = "\n".join([f"```\nasset{i}\n```" for i in range(10)])
        
        with pytest.raises(ParseError, match="Expected 7 asset blocks, found 10"):
            parse_blueprint_output(output)
    
    def test_parse_no_blocks(self):
        """Test error when no blocks found."""
        output = "Just regular text with no codeblocks"
        
        with pytest.raises(ParseError, match="No codeblocks found"):
            parse_blueprint_output(output)
    
    def test_parse_maps_to_correct_names(self):
        """Test that blocks map to correct asset names in order."""
        output = "\n".join([f"```\n{name}_content\n```" for name in ASSET_ORDER])
        assets = parse_blueprint_output(output)
        
        for name in ASSET_ORDER:
            assert assets[name] == f"{name}_content"


class TestExtractSingleAsset:
    """Tests for extract_single_asset function."""
    
    def test_extract_without_adjustment_note(self):
        """Test extracting when no adjustment note present."""
        output = "```\nasset content\n```"
        asset = extract_single_asset(output, "system_prompt")
        assert asset == "asset content"
    
    def test_extract_with_adjustment_note(self):
        """Test extracting when adjustment note is first block."""
        output = "```\nAdjustment Note: Test\n```\n```\nasset content\n```"
        asset = extract_single_asset(output, "system_prompt")
        assert asset == "asset content"
    
    def test_extract_no_blocks(self):
        """Test error when no codeblocks found."""
        output = "No codeblocks here"
        
        with pytest.raises(ParseError, match="No codeblocks found"):
            extract_single_asset(output, "system_prompt")
    
    def test_extract_only_adjustment_note(self):
        """Test error when only adjustment note present."""
        output = "```\nAdjustment Note: Test\n```"
        
        with pytest.raises(ParseError, match="No asset block found"):
            extract_single_asset(output, "system_prompt")


class TestExtractCharacterName:
    """Tests for extract_character_name function."""
    
    def test_extract_simple_name(self):
        """Test extracting simple name."""
        sheet = "name: John Doe\nage: 25"
        name = extract_character_name(sheet)
        assert name == "john_doe"
    
    def test_extract_complex_name(self):
        """Test extracting name with special characters."""
        sheet = "name: Dr. Jane Smith-O'Connor\nage: 35"
        name = extract_character_name(sheet)
        assert name == "dr_jane_smith_o_connor"
    
    def test_extract_name_with_quotes(self):
        """Test extracting name with quotes."""
        sheet = 'name: "Rin" Kuroda\nage: 22'
        name = extract_character_name(sheet)
        assert name == "rin_kuroda"
    
    def test_extract_single_word_name(self):
        """Test extracting single word name."""
        sheet = "name: Maren\nage: 34"
        name = extract_character_name(sheet)
        assert name == "maren"
    
    def test_extract_name_case_insensitive(self):
        """Test that field name is case insensitive."""
        sheet = "Name: Test Character\nage: 25"
        name = extract_character_name(sheet)
        assert name == "test_character"
    
    def test_extract_missing_name(self):
        """Test when name field is missing."""
        sheet = "age: 25\noccupation: Detective"
        name = extract_character_name(sheet)
        assert name is None
    
    def test_extract_name_with_numbers(self):
        """Test extracting name with numbers."""
        sheet = "name: Agent 47\nage: Unknown"
        name = extract_character_name(sheet)
        assert name == "agent_47"
    
    def test_extract_sanitizes_multiple_underscores(self):
        """Test that multiple underscores are collapsed."""
        sheet = "name: Test___Multiple___Underscores\nage: 30"
        name = extract_character_name(sheet)
        assert name == "test_multiple_underscores"
    
    def test_extract_strips_leading_trailing_underscores(self):
        """Test that leading/trailing underscores are removed."""
        sheet = "name: _Test Name_\nage: 30"
        name = extract_character_name(sheet)
        assert name == "test_name"
