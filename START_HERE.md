# Riparti da qui

Agentic Forge trasforma configurazioni YAML in oggetti Python pronti da usare.
Per usarlo serve soprattutto `from agentic_forge import forge`: le classi
Material / Forge / Forged servono quando vuoi estendere il framework.

Questo e il repository del framework. `../coito/` e un'applicazione separata
con una copia del framework e componenti specifici; non e il punto di partenza
per sviluppare Agentic Forge.

## Scegli cosa vuoi fare

| Obiettivo | Punto di partenza |
| --- | --- |
| Creare e formattare un prompt, anche con immagini | [Chat prompt](examples/chat_prompt/quickstart.ipynb) |
| Scegliere un modello o consultare i provider | [LLM](examples/llm/quickstart.ipynb) |
| Combinare prompt, modello e risposta strutturata | [Structured output](examples/structured_output/quickstart.ipynb) |
| Definire soltanto lo schema della risposta | [Response schema](examples/response_schema/quickstart.ipynb) |
| Esporre funzioni Python come strumenti | [Tools](examples/tools/quickstart.ipynb) |
| Caricare e preparare dati | [Dataset](examples/dataset/quickstart.ipynb) |
| Elaborare dati e salvare risultati | [Data runner](examples/data_runner/quickstart.ipynb) |
| Aggiungere un componente personalizzato | [Core](examples/core/quickstart.ipynb) |

Ogni cartella contiene un README, la specifica dei campi YAML e configurazioni
concrete in `materials/`. [Indice completo](examples/README.md).

## Verifica rapida senza servizi esterni

Dalla radice del repository, con l'ambiente Python attivo:

```powershell
python -m pip install -e .
python -m unittest discover -s tests -v
```

I test non fanno chiamate API e non richiedono Ollama acceso o chiavi reali.
I notebook che interrogano un modello richiedono invece il relativo provider.

## Riprendere con Codex

[AGENTS.md](AGENTS.md) contiene le indicazioni per gli agenti.
[docs/HANDOFF.md](docs/HANDOFF.md) contiene stato, verifiche e prossimi passi.

Per aprire una sessione interattiva nella cartella corretta:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/start-codex.ps1
```

Il primo messaggio chiede a Codex di leggere il passaggio di consegne,
riassumere lo stato e attendere il prossimo obiettivo.
