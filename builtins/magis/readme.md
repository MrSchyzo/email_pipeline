# Magis plugin

Handles invoice emails from `paperless@gruppomagis.it` whose subject looks like `Fattura nr. ... del dd/mm/yyyy`.

Each attached PDF is copied as `{yyyymmdd}_Bolletta.pdf`, where the date comes from the subject.
The destination folder is chosen by the `Codice offerta: <code>` found in the PDF, looked up in `config.json`'s `paths`
(see `config.example.json`). Unknown or missing codes go to `paths.otherwise`.
Relative paths are resolved against `DST_ROOT` from `.env` (default: the plugin folder), and `otherwise` defaults to `DST_ROOT` itself.
