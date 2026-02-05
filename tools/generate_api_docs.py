#!/usr/bin/env python3
"""Generate API documentation for Blueprint UI."""

import ast
import inspect
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional


class DocGenerator:
    """Generate documentation from Python source code."""
    
    def __init__(self, output_dir: Path):
        """Initialize documentation generator."""
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_module_docs(self, module_path: Path) -> Dict[str, Any]:
        """Generate documentation for a Python module."""
        source = module_path.read_text()
        tree = ast.parse(source)
        
        docs = {
            "module": module_path.stem,
            "docstring": ast.get_docstring(tree),
            "functions": [],
            "classes": [],
        }
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and self._is_toplevel(node, tree):
                docs["functions"].append(self._parse_function(node))
            elif isinstance(node, ast.ClassDef):
                docs["classes"].append(self._parse_class(node))
        
        return docs
    
    def _is_toplevel(self, node: ast.AST, tree: ast.Module) -> bool:
        """Check if node is at top level of module."""
        return node in tree.body
    
    def _parse_function(self, node: ast.FunctionDef) -> Dict[str, Any]:
        """Parse function documentation."""
        return {
            "name": node.name,
            "docstring": ast.get_docstring(node),
            "args": [arg.arg for arg in node.args.args],
            "returns": ast.unparse(node.returns) if node.returns else None,
            "lineno": node.lineno,
        }
    
    def _parse_class(self, node: ast.ClassDef) -> Dict[str, Any]:
        """Parse class documentation."""
        class_doc = {
            "name": node.name,
            "docstring": ast.get_docstring(node),
            "methods": [],
            "properties": [],
        }
        
        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                method_type = "property" if any(
                    isinstance(d, ast.Name) and d.id == "property" for d in item.decorator_list
                ) else "method"
                
                if method_type == "property":
                    class_doc["properties"].append({
                        "name": item.name,
                        "docstring": ast.get_docstring(item),
                    })
                else:
                    class_doc["methods"].append({
                        "name": item.name,
                        "docstring": ast.get_docstring(item),
                        "args": [arg.arg for arg in item.args.args[1:]] if item.args.args else [],  # Skip self
                        "returns": ast.unparse(item.returns) if item.returns else None,
                    })
        
        return class_doc
    
    def generate_markdown(self, docs: Dict[str, Any], module_name: str) -> str:
        """Generate markdown documentation."""
        lines = []
        
        lines.append(f"# {module_name}")
        lines.append("")
        
        if docs["docstring"]:
            lines.append(docs["docstring"])
            lines.append("")
        
        # Classes
        if docs["classes"]:
            lines.append("## Classes")
            lines.append("")
            
            for cls in docs["classes"]:
                lines.append(f"### `{cls['name']}`")
                lines.append("")
                
                if cls["docstring"]:
                    lines.append(cls["docstring"])
                    lines.append("")
                
                if cls["properties"]:
                    lines.append("#### Properties")
                    lines.append("")
                    for prop in cls["properties"]:
                        lines.append(f"- **{prop['name']}**")
                        if prop["docstring"]:
                            lines.append(f"  {prop['docstring']}")
                    lines.append("")
                
                if cls["methods"]:
                    lines.append("#### Methods")
                    lines.append("")
                    for method in cls["methods"]:
                        args_str = ", ".join(method["args"]) if method["args"] else ""
                        returns_str = f" → {method['returns']}" if method["returns"] else ""
                        lines.append(f"- **{method['name']}**(`{args_str}`){returns_str}")
                        if method["docstring"]:
                            lines.append(f"  {method['docstring']}")
                    lines.append("")
        
        # Functions
        if docs["functions"]:
            lines.append("## Functions")
            lines.append("")
            
            for func in docs["functions"]:
                args_str = ", ".join(func["args"]) if func["args"] else ""
                returns_str = f" → {func['returns']}" if func["returns"] else ""
                lines.append(f"### `{func['name']}({args_str}){returns_str}`")
                lines.append("")
                
                if func["docstring"]:
                    lines.append(func["docstring"])
                    lines.append("")
        
        return "\n".join(lines)
    
    def generate_index(self, all_modules: List[str]) -> str:
        """Generate index markdown."""
        lines = []
        lines.append("# Blueprint UI API Documentation")
        lines.append("")
        lines.append("This documentation is automatically generated from the source code.")
        lines.append("")
        lines.append("## Modules")
        lines.append("")
        
        for module in sorted(all_modules):
            lines.append(f"- [{module}]({module}.md)")
        
        return "\n".join(lines)


def main() -> int:
    """Main entry point."""
    project_root = Path(__file__).parent.parent
    bpui_dir = project_root / "bpui"
    output_dir = project_root / "docs" / "api"
    
    generator = DocGenerator(output_dir)
    
    # Find all Python modules
    modules = []
    for py_file in sorted(bpui_dir.glob("*.py")):
        if py_file.stem != "__init__":
            try:
                docs = generator.generate_module_docs(py_file)
                markdown = generator.generate_markdown(docs, py_file.stem)
                
                output_file = output_dir / f"{py_file.stem}.md"
                output_file.write_text(markdown)
                modules.append(py_file.stem)
                print(f"✓ Generated docs for {py_file.stem}")
            except Exception as e:
                print(f"✗ Error processing {py_file.stem}: {e}")
    
    # Generate submodules
    for submodule_dir in bpui_dir.iterdir():
        if submodule_dir.is_dir() and not submodule_dir.name.startswith("_"):
            submodules = []
            for py_file in sorted(submodule_dir.glob("*.py")):
                if py_file.stem != "__init__":
                    try:
                        docs = generator.generate_module_docs(py_file)
                        markdown = generator.generate_markdown(docs, f"{submodule_dir.name}.{py_file.stem}")
                        
                        output_file = output_dir / submodule_dir.name / f"{py_file.stem}.md"
                        output_file.parent.mkdir(parents=True, exist_ok=True)
                        output_file.write_text(markdown)
                        submodules.append(f"{submodule_dir.name}.{py_file.stem}")
                        modules.append(f"{submodule_dir.name}.{py_file.stem}")
                        print(f"✓ Generated docs for {submodule_dir.name}.{py_file.stem}")
                    except Exception as e:
                        print(f"✗ Error processing {submodule_dir.name}.{py_file.stem}: {e}")
    
    # Generate index
    index = generator.generate_index(modules)
    (output_dir / "index.md").write_text(index)
    print(f"\n✓ Generated index with {len(modules)} modules")
    
    print(f"\n✓ Documentation generated in: {output_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())