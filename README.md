# KICMPI
Project voor KICMPI group

De antwoorden worden gegenereerd door Ollama met `qwen2.5:3b`. Installeer Ollama
en laad het model lokaal:

```powershell
ollama pull qwen2.5:3b
```

Start daarna de app met Docker Compose. Vanuit de app-container wordt Ollama
bereikt via `http://host.docker.internal:11434`. Bij lokaal starten zonder
Docker gebruikt de app standaard `http://localhost:11434`.

De URL en het model kunnen worden aangepast met `OLLAMA_URL` en `OLLAMA_MODEL`.

## Documenten toevoegen

PDF's kunnen via de sectie **Documenten** in de webinterface worden toegevoegd of
verwijderd. Een geüploade PDF komt in de map `pdfs/` en wordt direct geïndexeerd
in Qdrant, dus de app hoeft niet opnieuw te worden opgestart. `python rag.py ingest`
bouwt de hele index opnieuw op vanuit `pdfs/`.
