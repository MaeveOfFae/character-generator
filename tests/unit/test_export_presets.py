from bpui.features.export.export_presets import resolve_preset_path


def test_resolve_preset_path_matches_display_name(tmp_path):
    preset_file = tmp_path / "chubai.toml"
    preset_file.write_text(
        """
[preset]
name = "Chub AI"
format = "json"
description = "Test preset"

[[fields]]
asset = "system_prompt"
target = "personality"
""".strip(),
        encoding="utf-8",
    )

    resolved = resolve_preset_path("Chub AI", tmp_path)

    assert resolved == preset_file


def test_resolve_preset_path_matches_file_stem(tmp_path):
    preset_file = tmp_path / "raw.toml"
    preset_file.write_text(
        """
[preset]
name = "Raw Text Files"
format = "text"
description = "Test preset"

[[fields]]
asset = "system_prompt"
target = "system_prompt"
""".strip(),
        encoding="utf-8",
    )

    resolved = resolve_preset_path("raw", tmp_path)

    assert resolved == preset_file