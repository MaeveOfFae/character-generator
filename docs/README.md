# Character Generator - Documentation

This directory contains comprehensive documentation for the character-generator project.

## Documentation Files

### Feature Documentation
- **[FEATURE_AUDIT.md](FEATURE_AUDIT.md)** - Complete feature audit report covering all project features, modules, and capabilities
- **[SIMILARITY_ENHANCEMENTS.md](SIMILARITY_ENHANCEMENTS.md)** - Detailed documentation of the character similarity analyzer, including LLM-powered analysis and redundancy detection

### API Documentation
- **[api/](api/)** - Generated API documentation
  - Run `make docs` to generate
  - View at `docs/api/bpui/`
  - See [api/README.md](api/README.md) for details

### Project Documentation (Root)
- **[../README.md](../README.md)** - Main project README with quickstart guide
- **[../QUICKSTART.md](../QUICKSTART.md)** - Quick reference guide
- **[../bpui/README.md](../bpui/README.md)** - TUI documentation and keyboard shortcuts
- **[../IMPLEMENTATION_ROADMAP.md](../IMPLEMENTATION_ROADMAP.md)** - Development roadmap
- **[../bpui/docs/INSTALL.md](../bpui/docs/INSTALL.md)** - Installation guide
- **[../bpui/docs/IMPLEMENTATION.md](../bpui/docs/IMPLEMENTATION.md)** - Implementation details
- **[../bpui/docs/PYTHON_3.13_NOTES.md](../bpui/docs/PYTHON_3.13_NOTES.md)** - Python 3.13 compatibility notes

## Key Features

### Similarity Analyzer

The similarity analyzer allows you to:
- Compare two characters to find commonalities and differences
- Get LLM-powered narrative insights, story opportunities, and relationship arcs
- Detect character redundancy at four levels (low/medium/high/extreme)
- Generate actionable rework suggestions to differentiate similar characters
- Get merge recommendations for extreme duplicates (>95% similar)
- Compare all character pairs in batch mode
- Cluster similar characters for group analysis

**Usage:**
```bash
# Basic comparison
bpui similarity "character1" "character2"

# With LLM analysis
bpui similarity "character1" "character2" --use-llm

# Compare all pairs
bpui similarity drafts --all --use-llm

# Cluster characters
bpui similarity drafts --cluster --threshold 0.75
```

See [SIMILARITY_ENHANCEMENTS.md](SIMILARITY_ENHANCEMENTS.md) for complete details.

## Documentation Organization

```
docs/
├── README.md                     # This file
├── FEATURE_AUDIT.md              # Complete feature audit
├── SIMILARITY_ENHANCEMENTS.md     # Similarity analyzer docs
├── draft-index.md                 # Draft index docs
├── PHASE_3.4_SURPRISE_ME.md    # Feature documentation
└── api/                         # Generated API docs
    ├── README.md
    └── bpui/                    # Module documentation
```

## Generating API Documentation

To generate API documentation:

```bash
make docs
```

This will generate documentation in `docs/api/bpui/` using the script in `tools/generate_api_docs.py`.

## Contributing to Documentation

When adding new features:
1. Update [FEATURE_AUDIT.md](FEATURE_AUDIT.md) with the new feature
2. Add detailed documentation in this directory
3. Update [../README.md](../README.md) with a summary
4. Update [../QUICKSTART.md](../QUICKSTART.md) with usage examples
5. Update [../bpui/README.md](../bpui/README.md) if it affects TUI
6. Run `make docs` to regenerate API documentation

## Getting Help

- **Quick Start**: See [../README.md](../README.md)
- **TUI Guide**: See [../bpui/README.md](../bpui/README.md)
- **Installation**: See [../bpui/docs/INSTALL.md](../bpui/docs/INSTALL.md)
- **API Reference**: See [api/](api/)
- **Feature Details**: See specific documentation files above
- **Contributing**: See [../CONTRIBUTING.md](../CONTRIBUTING.md)