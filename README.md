# DayZ Dossier

Double-click **start.bat**. The Python backend opens the dashboard at **http://127.0.0.1:8765**. Keep the console open while using it; Ctrl+C stops the server. Alternatively run `python server.py` with Python 3.10 or newer. No packages, installation, account or internet connection are needed.

Personal killfeed exports and profile-ID portrait assignments are not included in this public project. On first launch the dashboard is empty; choose **Import summary** to load your own Discord HTML TXT exports. Imports are processed in memory and apply only to the current browser view. To load exports automatically on later launches, keep your files named `killfeedpart*.txt` in this folder; those files are ignored by Git. No source files are overwritten.

Search names, observed aliases or CFTools profile IDs. Choose a player to see kills, deaths, observed K/D, top three weapons and paginated encounters. Click an opponent to open their dossier. Events are ordered newest first and timestamps use the browser’s timezone. Players are grouped by exact CFTools profile ID; their most recently observed name is displayed. K/D is shown as a dash when no deaths were observed.

All statistics cover only successfully parsed imported events. The parser supports profile-linked `victim got killed by killer (weapon, distance m)` messages. Other messages remain visible in the summary and do not contribute to statistics. Discord message IDs deduplicate across files. No live status, equipment, location or name-similarity merging is provided. Combat-pattern associations are inferred and explicitly unconfirmed. There is no Discord scraping or external profile lookup.

The backend binds only to this computer (127.0.0.1). It serves the UI and data API, and parses replacement uploads in memory. Keep exports and `portrait-assignments.json` private; both are excluded from Git.

Run checks: `python -m unittest -v test_import.py`. Parser implementation: `import_data.py`; backend: `server.py`; browser UI: `app.js`, `style.css`, `index.html`.

The revised Clean Analyst view places eight recent encounters on the left, survivor/profile statistics and weapon cards on the right, and observed aliases and the association evidence panel below the activity. Search in the header or choose Players to select a dossier.

There are 21 fictional survivor portraits. A SHA-256 hash of the stable CFTools ID initially selects an image; the local, Git-ignored `portrait-assignments.json` then preserves that assignment. Keep this file in private backups if you want assignments to persist. Display name changes and later additions to the portrait manifest do not reassign existing profiles. Repeats across players are expected. Missing portraits fall back to the original illustration, with a final unavailable state if that too is absent.

Actual DayZ weapon cutouts are matched by exact imported weapon names. See `assets/CREDITS.md` and `assets/weapon-sources.json` for coverage and sources. Missing verified modded weapon images show text only. No generated or schematic weapon stand-ins are displayed.

Additional checks: `python -m unittest -v test_portraits.py`; with the server running, `node test_ui.cjs` exercises application rendering, filters, pagination, fallback handling and the API.

Association method and limitations: `ASSOCIATION_PROPOSAL.md`. The first-pass model includes all event roles, keeps uncertain candidates separate from globally consistent inferred duos/trios, and never exceeds two inferred teammates plus the selected player. Run `python -m unittest -v test_associations.py` for invariant checks.

Associations are model-only and explicitly unconfirmed; weapon similarity is entirely excluded. See `ASSOCIATION_PROPOSAL.md` and the How it works dialog. A capped score of 100 is explicitly marked saturated, not 100% probability.
