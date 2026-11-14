# Magis plugin

Handles invoice emails from `paperless@gruppomagis.it` whose subject looks like `Fattura nr. ... del dd/mm/yyyy`.

Each attached PDF is copied as `{yyyymmdd}_{original_name}.pdf`, where the date comes from the subject.
The destination folder is chosen by the `Codice offerta: <code>` found in the PDF, looked up in `config.json`'s `paths`
(see `config.example.json`). Unknown or missing codes go to `paths.otherwise`, or `DST_ROOT` from `.env` if `otherwise` is not set.
