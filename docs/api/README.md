# API Documentation

The authoritative live API reference is the FastAPI OpenAPI UI served by the backend.

## Live Docs

Start the backend:

```bash
python -m uvicorn bpui.api.main:app --reload
```

Then open:

- `http://localhost:8000/docs`
- `http://localhost:8000/redoc`

## Static Files in This Folder

The Markdown files in `docs/api/` are supplementary notes about provider integrations and related API behavior. They are not a replacement for the live OpenAPI schema.

## Main Route Groups

- `/api/config`
- `/api/models`
- `/api/templates`
- `/api/blueprints`
- `/api/drafts`
- `/api/generate`
- `/api/seedgen`
- `/api/similarity`
- `/api/offspring`
- `/api/lineage`
- `/api/export`
- `/api/chat`
- `/api/validate`
