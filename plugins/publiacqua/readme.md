# Publiacqua plugin

Considers mails coming from `no-reply@publiacqua.it` containing `MyPubliacqua: nuova bolletta web documento` in the subject.
Crawls the HTML contained in the email in search of a link akin to `https://bollettainterattiva.publiacqua.it/mi/...`, then, by using the chromedriver from selenium, it looks for the PDF link and the end date of the receipt.
After that, it stores the pdf into `<DST_ROOT>/{YYYYMMDD}_Acqua.pdf`, where the date is extracted as mentioned above.
`DST_ROOT` can be specified in the `.env` file.

Since it uses selenium with chrome, it requires the chromedriver to be present in the path.

So, either make sure to run `brew install chromedriver` or `apt install -y chromium-chromedriver`.