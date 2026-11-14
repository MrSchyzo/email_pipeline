# NeN plugin

Handles emails from `nen.it` whose subject looks like `La fattura <gas|luce> di <mese> è disponibile`.

Logs into the NeN personal area (AWS Cognito, credentials in `.env`), then, for every home context listed in `/profile`,
downloads each bill emitted within 5 days before or after the email date (asking for both calendar years when that window crosses New Year) as `{yyyymmdd}_{Gas|Luce}_dettaglio.pdf` and `{yyyymmdd}_{Gas|Luce}_sintetica.pdf`.
The destination folder is chosen by the bill's `subscriptionId` (one per supply, so gas and luce route separately),
looked up in `config.json`'s `paths` (see `config.example.json`). Unknown ids go to `paths.otherwise`.
Relative paths are resolved against `DST_ROOT` from `.env` (default: the plugin folder).

Cognito pool/client ids and the API base URL are read at runtime from the `nen.it` page config, not hardcoded.
