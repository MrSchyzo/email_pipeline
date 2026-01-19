# TIM plugin

Just copies any attached PDF at `<DST_ROOT>/Tim{YYYYMMDD}.pdf` if the email is a Tim internet bill.
`DST_ROOT` can be specified in the `.env` file, while `YYYYMMDD` is extracted from the PDF, assuming the bill structure as of Jan 2026.