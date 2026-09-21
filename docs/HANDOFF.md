# Passaggio di consegne - 2026-09-22

## Contesto e obiettivo dell'utente

L'utente vuole riprendere Agentic Forge dopo una pausa, capire come usarlo
senza ricordare ogni componente, e individuare bug e miglioramenti.
La sessione iniziale era aperta per errore nella copia `coito/agentic_forge`.
Il repository corretto e `Desktop/progetti/agentic_forge`, branch `main`,
remote `https://github.com/alessandropec/agentic_forge.git`.

Documentazione ed esempi esistevano gia: README, 8 quickstart notebook,
specifiche dei materiali e YAML in `examples/`. Ora `START_HERE.md` li
indicizza per obiettivo. La documentazione non andava ricostruita da zero.

## Recupero completato

Confrontati tutti i file Python fra il main originale e la copia COITO:
9 file differivano, nessun nuovo modulo generico. Recuperati:

- `core/refiner.py`: lettura UTF-8 di YAML e riferimenti.
- `core/codex.py`: messaggio di errore del registro in inglese.
- `data_runner/forge.py`, `llm/forge.py`,
  `structured_output/forge/structured_model.py`: propagazione di base_dir.
- `chat_prompt/forged.py`: immagini locali convertite anche da format_messages.
- `llm/materials.py`: supports_vision ed extra_options.
- `llm/forged/manager.py`: get_model_info e metadati vision nel catalogo.
- `llm/forged/provider.py`: caricamento differito delle chiavi e parametri chat.

Correzioni aggiuntive necessarie nel recupero:

- Un unico dizionario di opzioni elimina gli argomenti duplicati nei costruttori:
  campi statici < extra_options < kwargs espliciti. In COITO l'override di
  temperature su Ollama produceva TypeError; il test ora copre tutti i provider.
- Propagato base_dir anche al manager inline in structured_model.
- max_tokens viene tradotto in num_predict per Ollama; base_url viene rispettato
  anche per OpenAI e keep_alive viene passato al costruttore Ollama.
- Campi opzionali di sampling assenti non vengono forzati a None.

Origine storica: tag archive/coito-split nel repository originale,
commit 7e682b7 e 40d6b61. UTF-8 e lazy credentials sono modifiche successive
della copia COITO. OpenRouter e il manager multi-provider esistevano gia in main.
Nessuna modifica effettuata al codice di COITO. Nessun commit/push automatico.

## Verifiche

`python -m unittest discover -s tests -v`: 9 test offline, superati usando
inizialmente l'interprete `../coito/.venv/Scripts/python.exe`, con import del
framework da QUESTO repository. I test coprono percorsi inline e referenziati,
immagini, UTF-8, catalogo senza credenziali, merge delle opzioni e un vero
costruttore ChatOllama senza invocazione di rete. Nessuna chiamata LLM eseguita.

Verifica finale ripetuta con `.venv/Scripts/python.exe` di questo repository:
tutti i 9 test passano anche nell'ambiente locale originale. `git diff --check`
non segnala errori di whitespace. Codex CLI risulta autenticato via ChatGPT.

## Problemi segnalati al termine del recupero iniziale (risolti sotto)

Osservati/riprodotti nella precedente analisi della copia COITO; verificare
anche qui prima di modificarli:

- Dataset.save in formato list puo omettere gli ID sintetici e produrre un file
  che non si ricarica; skip_keys stringhe non salta ID numerici.
- Fallback senza tqdm: il runner usa progress.n che lo stub non implementa.
- ResponseSchemaForge perde le descrizioni dei campi nel modello Pydantic.
- Riferimenti YAML ciclici provocano RecursionError, senza diagnosi del ciclo.
- Immagini in singoli messaggi caricati via ref non usano il base_dir del
  messaggio; invoke diretto del prompt non converte come format_messages.
- Chiavi API e keep_alive usano ancora variabili d'ambiente globali: valutare
  isolamento per provider. extra_options riguarda attualmente solo i chat model.
- Verificare compatibilita notebook con la conversione immagini in
  format_messages; compact_for_display evita stampe base64 enormi.

## Correzioni successive - 2026-09-22

Su richiesta dell'utente sono stati corretti tutti i problemi sopra elencati:

- Salvataggio list con ID sintetici/custom e round-trip dopo preprocessing.
- skip_keys confrontati come stringhe, ID tensor convertiti in scalari Python.
- Runner indipendente da progress.n; batch_size=0 rifiutato correttamente.
- Descrizioni mantenute nello schema Pydantic, anche nei campi annidati e nelle liste.
- Cicli ref diagnosticati con ValueError e catena dei file; ref condivisi ammessi.
- Immagini relative alla directory del messaggio referenziato, anche con variabili
  e partial; conversione coerente in format_messages, invoke, ainvoke e pipeline.
- Credenziali locali all'istanza e keep_alive passato al costruttore, senza
  modificare l'ambiente. Anche gli embedding rispettano extra_options e base_url.
- Override esplicito del nome modello senza collisioni con i parametri interni.
- Notebook aggiornati per stampare immagini con compact_for_display.

Verifica con `.venv/Scripts/python.exe -m unittest discover -s tests -v`:
18 test offline superati. Usate solo credenziali fittizie temporanee,
nessuna chiave reale letta e nessuna chiamata LLM eseguita.
Note d'uso in `examples/recovery_fixes.md`.

L'utente ha richiesto un commit locale comprendente il recupero e le correzioni.
Non e stato richiesto un push. Non sono stati modificati file di COITO.

## Prossimo lavoro suggerito

Ripartire dall'obiettivo concreto dell'utente. Eventuali ricette end-to-end
aggiuntive e strumenti di ispezione/validazione YAML sono miglioramenti futuri,
non necessari per queste correzioni. Conservare forge(path) e il pattern
Material -> Forge -> Forged.
