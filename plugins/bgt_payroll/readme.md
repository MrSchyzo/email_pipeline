# BGT Payroll plugin

Crawls the BGT website and looks for the last payroll. It uses `USERNAME` and `PASSWORD` to log into.
It stores the pdf into `<DST_ROOT>/{YYYYMM}_BustaH.pdf`, where the date is extracted as mentioned above.
`DST_ROOT` can be specified in the `.env` file.

Since it uses selenium with chrome, it requires the chromedriver to be present in the path.

So, either make sure to run `brew install chromedriver` or `apt install -y chromium-chromedriver`.

## Crawl instructions

1. Land on `https://portale.bgt-grantthornton.it/HRLeoniWeb/jsp/login.jsp`
1. enter username in `//input[@name="m_cUserName"]`
1. enter password in `//input[@name="m_cPassword"]`
1. click on `//input[@type="submit",@value="login"]`
1. click on the span containing `MySpace` with class `tab_text`
1. find a table contained in a `div` with class `column_shell`
1. mouse over the first `tr`
1. click on it
1. it opens up a new form with the PDF (use window handles)
1. download that PDF