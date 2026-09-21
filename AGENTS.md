# Working on Agentic Forge

- This checkout is the reusable framework. The sibling `../coito/` is an
  application with a vendored copy; do not treat it as the canonical framework.
- Read `START_HERE.md` and `docs/HANDOFF.md` before continuing this work.
- Preserve the public `forge(path)` entrypoint and the Material -> Forge ->
  Forged extension pattern. Document user-visible changes in `examples/`.
- Keep COITO-specific profiles, mood/personality logic, UI and persistence out
  of the generic framework unless a separate generalization is requested.
- Run `python -m unittest discover -s tests -v` for the recovered functionality.
  These are offline tests. Do not use real API keys or paid model calls for them.
- Do not read or print `api_keys.yaml` or credentials as part of exploration.
- Keep existing local changes. The recovery work may still be uncommitted.
- Communicate with this user in Italian and focus on simple usage by objective.
