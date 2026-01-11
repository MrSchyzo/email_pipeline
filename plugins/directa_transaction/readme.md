# Directa transaction plugin

Just copies any attached PDF at `<DST_ROOT>/{YYMMDD}_{ISIN}.pdf` if the email is a Directa transaction receipt.
`DST_ROOT` can be specified in the `.env` file, while `ISIN` is extracted from the PDF, assuming the receipt structure as of Jan 2026.