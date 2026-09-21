# Correzioni e utilizzo dopo il recupero

L'API rimane `from agentic_forge import forge`.

## Salvare e ricaricare un dataset

Il salvataggio in formato `list` include anche gli ID sintetici e rispetta
`key_field`, senza modificare gli elementi originali. Funziona anche dopo
`preprocess(..., keep_original=False)`.

```python
from agentic_forge import forge
from agentic_forge.dataset.forged import ForgedItemDataset

dataset = ForgedItemDataset([{"text": "ciao"}], keys=["primo"])
dataset.save("items.json", key_field="record_id")
reloaded = forge("items.yaml")
assert reloaded.get_key(0) == "primo"
```

Nel data runner, `skip_keys=["17"]` salta anche un ID numerico `17`.
Gli ID numerici collazionati da PyTorch vengono riportati a scalari Python
prima di passare l'elemento a `process_item`, per poterli salvare in JSON.
Il runner funziona anche senza `tqdm` e rifiuta `batch_size=0`.

## Usare immagini nei prompt

Le immagini locali dei messaggi caricati con `ref` vengono cercate rispetto
al file YAML del messaggio. I messaggi inline ereditano la directory del prompt.
La risoluzione funziona anche con variabili come `images: ['{image_path}']`
e con `partial()`. URL HTTP e data URL rimangono validi.

`format_messages()`, `invoke()`, `ainvoke()` e le pipeline convertono le immagini
locali in data URL. `invoke()` conserva il risultato LangChain con `to_messages()`.
Per ispezionare un prompt senza stampare enormi stringhe base64:

```python
messages = prompt.format_messages(image_path="image.png")
for message in prompt.compact_for_display(messages):
    print(message)
```

## Diagnosticare YAML e schemi

Un ciclo nei `ref` produce un `ValueError` con la catena dei file coinvolti.
Lo stesso file puo essere riutilizzato in rami indipendenti senza errori.
Le descrizioni dei campi, inclusi oggetti annidati ed elementi di liste,
compaiono nello schema Pydantic passato al modello; i campi opzionali
rimangono opzionali.

## Configurare piu provider

Le credenziali lette da file rimangono nell'istanza del provider, senza
sovrascrivere quelle degli altri provider o le variabili d'ambiente.
`keep_alive` viene passato direttamente ai modelli Ollama.
Anche gli embedding rispettano `base_url` e `extra_options`.
La precedenza e: configurazione di base, `extra_options`, argomenti espliciti
di `get_model()`. I parametri specifici del backend devono essere supportati
dal relativo costruttore LangChain.

La verifica automatica usa solo fixture locali e costruttori simulati,
oltre al costruttore Ollama senza chiamate di rete:

```powershell
python -m unittest discover -s tests -v
```
