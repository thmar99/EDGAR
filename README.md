# EDGAR
Project to webscrape SEC EDGAR database
Credits: areeed1192 EDGAR queries available at: https://github.com/areed1192/sigma_coding_youtube/blob/master/python/python-finance/sec-web-scraping/Web%20Scraping%20SEC%20-%20EDGAR%20Queries.ipynb

All relevant functions are contained within the EDGARFetcher() function

User must have the following information to process a request
* email address
* institution of employment (any institution will satisfy the parameter)
* request date in MMDDYYY format
* form type (currently supports 10-Q and 10-K)
* company stock ticker

The program will fetch the most **recent** filing that satisfy the above parameters, i.e. if user punched in 04152024. and the relevant company's most recent filing was 04012024, it will fetch & parse those filings.

Upon successful fetch request, program will parse all relevant sub-sections of the report. The user will then select the sub-sections that contain **tabular data only**, namely the consolodated financial statements. User will have to exercise his/her/they discretion in determining which subsection contains datatables.

When users see "EDGAR requests done", it indicates the fetch & parse steps were successfully executed
