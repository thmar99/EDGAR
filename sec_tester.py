import json
import requests
import pandas as pd
from cik_searcher import getCIK
from bs4 import BeautifulSoup
import re
import xml.etree.ElementTree as ET

"""-------------------------------------------STEP 1 (fetch xml file)-----------------------------------------------------------------"""
def FetchXml(cik,dateb,frm_type,headers):
    '''get the xml entries corresponding to the company id, daterange, and form type'''
    assert(isinstance(cik,str)) and isinstance(frm_type,str)
    ## base URL for the SEC EDGAR browser
    endpoint = r"https://www.sec.gov/cgi-bin/browse-edgar"

    # define our parameters dictionary
    param_dict = {'action':'getcompany','CIK':cik,'type':frm_type,'dateb':dateb,'owner':'exclude','start':'','output':'atom','count':'100'}

    # request the url, and then parse the response.
    response = requests.get(url = endpoint, params = param_dict, headers=headers)

    soup = BeautifulSoup(response.content, 'lxml')
    entries = soup.find_all('entry') 

    # Let the user know it was successful. See xml_file.txt for response text. Will show content for step 2
    print('Fetched xml file: '+str(response.url))

    # find & return all the entry tags, see entry.txt for file
    entries = soup.find_all('entry')
    return entries
#'0001265107','20190101','10-k'

"""-------------------------------------------STEP 2 (GRAB ENTRY TAGS FROM XML)----------------------------------------------------"""
def FetchReqFilings(xml_entries):
    '''store each xml entry in a dictionary with the accession number as a key'''
    # initalize our list for storage
    master_list_xml = []

    # loop through each found xml, remember this is only the first two
    for entry in xml_entries:
    
        # grab the accession number so we can create a key value dictionary
        accession_num = entry.find('accession-number').text
        
        # create a new dictionary
        entry_dict = {}
        entry_dict[accession_num] = {}
        
        # store the category info into each entry
        category_info = entry.find('category')    
        entry_dict[accession_num]['category'] = {}
        entry_dict[accession_num]['category']['label'] = category_info['label']
        entry_dict[accession_num]['category']['scheme'] = category_info['scheme']
        entry_dict[accession_num]['category']['term'] =  category_info['term']

        # store the file info
        entry_dict[accession_num]['file_info'] = {}
        #entry_dict[accession_num]['file_info']['act'] = entry.find('act').text
        entry_dict[accession_num]['file_info']['file_number'] = entry.find('file-number').text
        entry_dict[accession_num]['file_info']['file_number_href'] = entry.find('file-number-href').text
        entry_dict[accession_num]['file_info']['filing_date'] =  entry.find('filing-date').text
        entry_dict[accession_num]['file_info']['filing_href'] = entry.find('filing-href').text
        entry_dict[accession_num]['file_info']['filing_type'] =  entry.find('filing-type').text
        entry_dict[accession_num]['file_info']['form_number'] =  entry.find('film-number').text
        entry_dict[accession_num]['file_info']['form_name'] =  entry.find('form-name').text
        entry_dict[accession_num]['file_info']['file_size'] =  entry.find('size').text
        
        # store extra info
        entry_dict[accession_num]['request_info'] = {}
        entry_dict[accession_num]['request_info']['link'] =  entry.find('link')['href']
        entry_dict[accession_num]['request_info']['title'] =  entry.find('title').text
        entry_dict[accession_num]['request_info']['last_updated'] =  entry.find('updated').text
        
        # store in the master list. see master_list.txt for content
        master_list_xml.append(entry_dict)

        #print(master_list_xml)
    '''with open(f'correct_master_list_xml.json','w')as f:
        f.write(json.dumps(master_list_xml,indent=4))'''
    return master_list_xml

"""-------------------------------------------STEP 3 (fetch relevant links & convert to json)-----------------------------------------------------------------"""



def GetKeys(master_list_xml):
    '''get list of accession numbers from each xml entry'''
    list_of_keys = []
    for i in range(len(master_list_xml)):

        #loop through nested dictionary
        for k, v in master_list_xml[i].items():
        
            #fetch accession & submission dates from xml file
            list_of_keys.append(k)

    return list_of_keys

def GetDates(master_list_xml,keys):
    '''get filing dates from each xml entry'''
    list_of_dates= []
    for i in range(len(master_list_xml)):

        #loop through nested dictionary
        for k, v in master_list_xml[i].items():
        
            #fetch accession & submission dates from xml file
            keys.append(k)
            d8 = master_list_xml[i][k]['file_info']['filing_date']
            list_of_dates.append(d8)
            
    return list_of_dates

def ConvertFiling(master_list_xml):
    '''convert htm entries to json for future scraping'''
    json_list = []
    list_of_keys = []
    list_of_dates= []
    for i in range(len(master_list_xml)):

        #loop through nested dictionary
        for k, v in master_list_xml[i].items():
        
            #fetch accession & submission dates from xml file
            list_of_keys.append(k)
            d8 = master_list_xml[i][k]['file_info']['filing_date']
            list_of_dates.append(d8)

            #add dict(accession num: url) to a new list
            url_entries = {k:{d8:v['file_info']['filing_href']}}
            url_entries[k][d8] = url_entries[k][d8].replace(str(k)+'-index.htm','index.json')

            json_list.append(url_entries)
    '''with open(f'correct_json_list.json','w')as f:
        f.write(json.dumps(json_list,indent=4))'''
    return json_list


"""-------------------------------------------STEP 4 (fetch FilingSummary.xml file from json & break down)-----------------------------------------------------------------"""

def ReportPieces(json_list,keys,dates,headers):
    '''Iterate through All JSON Links to retrieve Data, Data is retrieved with a request to the report html link and parsed with bS4'''
    count = 0 
    while count != 1:
        stop_gap  = len(json_list) 
        #Iterate through each json_list entry
        document_url = json_list[count][keys[count]][dates[count]]
        content = requests.get(document_url,headers=headers).json()

        #fetch & save Filingsummary.xml file
        #Contains all sections of SEC report
        base_url = r"https://www.sec.gov"
        for file in content['directory']['item']:
            if file['name'] == 'FilingSummary.xml':
                xml_summary = base_url + content['directory']['name'] + "/" + file['name']
               #print('xml_summary: {}'.format(xml_summary))
               # print('-' * 100)
               # print('File Name: ' + file['name'])
               # print('File Path: ' + xml_summary)       

        base_url = xml_summary.replace('FilingSummary.xml', '')
        #print(f'base url: {base_url}')

        # request and parse the content
        content = requests.get(xml_summary, headers=headers).content
        soup = BeautifulSoup(content, 'lxml')

        reports = soup.find('myreports')

        # I want a list to store all the individual components of the report, so create the master list.
        master_reports = []

        # loop through each report in the 'myreports' tag but avoid the last one as this will cause an error.
        for report in reports.find_all('report')[:-1]:

            # let's create a dictionary to store all the different parts we need.
            report_dict = {}
            report_dict['name_short'] = report.shortname.text
            report_dict['name_long'] = report.longname.text
            '''report_dict['position'] = report.position.text
            report_dict['category'] = report.menucategory.text'''
            if report.htmlfilename is not None: report_dict['url'] = base_url + report.htmlfilename.text
            elif report.xmlfilename is not None: report_dict['url'] = base_url + report.xmlfilename.text
            else: continue
            #report.xmlfilename is not None: report_dict['url'] = base_url + report.xmlfilename.text
            # append the dictionary to the master list.
            master_reports.append(report_dict)

        count+=1
    return master_reports

def xmlfindr(soup):
# Parse the XML file
    root = ET.fromstring(soup)

    # Extract headers from <Label> elements, handling None values
    headers = [label.get("label") for label in root.findall(".//label")]
    headers = [col for col in headers if col is not None and 'Ended' not in col]
    print(f'headers: {headers}')

    # Extract data and fields from <Rows> elements
    rows_element = root.findall(".//rows")
    fields = [row.text for row in rows_element[0].findall(".//elementname")]
    rmvCHar = lambda text: text.replace('us-gaap_',"")
    fields = [rmvCHar(field) for field in fields]
    print(f'fields: {fields}')
    data = [value.text for value in rows_element[0].findall('.//roundednumericamount')]

    # Reshape the data for the DataFrame
    reshaped_data = [data[i:i + len(headers)] for i in range(0, len(data), len(headers))]

    # Create DataFrame
    df = pd.DataFrame(reshaped_data, columns=headers, index=fields)
    return df

def StructFinancials(report,headers):
    print(f'scraping: {report[0]}')
    '''constructs relevant data files from Consolidated financial statements (balance sheet, cash flows, operations and comprehensive income)'''
    statements_data = []
    # loop through each statement url
    count = 0
    #print(f'scraped: {scraped[statement]}')
    #print(f'statement: {statement}')
    count += 1
    # define a dictionary that will store the different parts of the statement.
    statement_data = {}
    statement_data['headers'] = []
    statement_data['sections'] = []
    statement_data['data'] = []
    statement_data['url'] = report[1]

    #print(f'scraped: {scraped[statement][1]}')
    content = requests.get(report[1],headers=headers).content
    report_soup = BeautifulSoup(content,'lxml')

    if report_soup.find('document') is None:
        return xmlfindr(str(report_soup))

    # find all the rows, figure out what type of row it is, parse the elements, and store in the statement file list.
    for index, row in enumerate(report_soup.table.find_all('tr')):
        #print(f'line 280 index: {index}, row{row}')
        
        # first let's get all the elements.
        cols = row.find_all('td')
        
        # if it's a regular row and not a section or a table header
        if (len(row.find_all('th')) == 0 and len(row.find_all('strong')) == 0): 
            reg_row = [ele.text.strip() for ele in cols]
            statement_data['data'].append(reg_row)
            
        # if it's a regular row and a section but not a table header
        elif (len(row.find_all('th')) == 0 and len(row.find_all('strong')) != 0):
            sec_row = cols[0].text.strip()
            statement_data['sections'].append(sec_row)
            
        # finally if it's not any of those it must be a header
        elif (len(row.find_all('th')) != 0):            
            hed_row = [ele.text.strip() for ele in row.find_all('th')]
            statement_data['headers'].append(hed_row)
            #print(statement_data['headers'])
            #print(f"url: {statement_data['url']} for header: {statement_data['headers']}")
        else:            
            print('We encountered an error.')
            return None

        #Ensure the headers in each financial report are a nested list of length 1
        if len(statement_data['headers']) > 1:
            thisStament = list((statement for statement in statement_data['headers'][-1]))
            for statement in thisStament:
                statement_data['headers'][0].append(statement)
            statement_data['headers'].pop(-1)
        if '12 Months Ended' in statement_data['headers'][0]:
            statement_data['headers'][0].remove('12 Months Ended')
        elif '3 Months Ended' in statement_data['headers'][0]:
            statement_data['headers'][0].remove('3 Months Ended')
        else:
            pass
    statements_data.append(statement_data)
    print(f'scraping complete: To verify accuracy of data please visit \n\t{report[1]}')

    return statements_data    

"""-------------------------------------------STEP 5 (fetch $ structure financial data)-----------------------------------------------------------------"""

def remChar(value):
    '''remove specific strings mixed in with cells, and all subsequent characters''' 
    '''if cell[0]=='-':
        return '-' + re.sub(r'[^0-9.]', '', cell)  # Remove non-numeric characters but keep th negative sign
    elif isinstance(cell, str):
        return re.sub(r'[^0-9.]', '', cell) #Remove non-numeric characters
    return cell'''
    '''if value and isinstance(value, str):
        numeric_value = re.sub(r'[^-0-9.]', '', value)  # Keep '-' and digits
        if numeric_value and numeric_value[0] == '-':  # If '-' is at the start
            return '-' + re.sub(r'[^0-9.]', '', numeric_value[1:])  # Keep digits after '-'
        return numeric_value
    return value'''
    '''if value and isinstance(value, str):
        # Remove characters like '$', ',', and other non-numeric symbols
        numeric_value = re.sub(r'[^-0-9.]', '', value.replace(',', '').replace('$', ''))  
        if numeric_value and numeric_value[0] == '-':  # If '-' is at the start
            return '-' + re.sub(r'[^0-9.]', '', numeric_value[1:])  # Keep digits after '-'
        return numeric_value
    return value'''
    '''if value and isinstance(value, str):
        # Find the pattern for retaining the leading '-' before numeric values
        numeric_value = re.sub(r'^(-?)(?=\d)', r'\1', value)
        # Remove all non-numeric characters except the leading '-'
        numeric_value = re.sub(r'[^\d.-]', '', numeric_value)
        return numeric_value
    return value'''
    match = re.search(r'[-+]?\d*\.?\d+', value)
    if match:
        return value[:match.end()]
    return ""


def CleanSheet(DataFrame):   
    #Remove footer notes
    null_val = lambda row : True if str(row[0])=="" or str(row[0])=='nan' else False
    for index,row in DataFrame.iterrows():
        if "[" in str(row[0]) or null_val(row): DataFrame.drop(index,inplace=True)

    #drop empty columns
    DataFrame.dropna(how='all',axis=1,inplace=True)
    #DataFrame.to_csv('after_empty_cols.csv')

    #drop columns that contain square brackets and integers between
    pattern = r'\[\d+\]'
    # Identify columns containing the specified pattern
    columns_to_drop = [col for col in DataFrame.columns if any(DataFrame[col].apply(lambda x: re.search(pattern, str(x))))]
    # strip non-numerical characters in the columns
    df_cleaned = DataFrame.drop(columns=columns_to_drop)
    #print(type(df_cleaned.iloc[1,1]))
    #df_cleaned.to_csv('filtered.csv')
    #df_cleaned.iloc[:,1:].to_csv('ctu_filtered.csv',index=False)
    #df_cleaned.iloc[:,1:] = df_cleaned.iloc[:,1:].applymap(remChar)
    #df_cleaned.to_csv('mapped_filtered.csv')
    #df_clean = df_cleaned.applymap(remChar)

    return df_cleaned

def CreateDataframe(financials,name):
    '''Structures report sections into DatFrames and saves to csv files'''
    #Add url to headers
    income_data = financials[0]['data']
    income_header =  financials[0]['headers'][0]
    
    income_df = pd.DataFrame(income_data)
    if len(income_df.columns) != len(income_header):
        print('Incorrect DataFrame alignment. Attempting to fix')
        income_df = CleanSheet(income_df)

    # Get rid of the '$', '(', ')', and convert the '' to NaNs.
    income_df = income_df.replace('[\$,)]','', regex=True )\
                        .replace( '[(]','-', regex=True)\
                        .replace( '', 'NaN', regex=True)
    #income_df.to_csv('filtered'+name+'.csv')

    filtered_list = [s for s in income_header if all(word not in s for word in ["Ended", "Months", "Years"])]
    income_df.columns= filtered_list
    indeces = income_df.iloc[:,0].to_list()
    #print(f'indeces: \n{indeces}')
    clean_ind = lambda text: re.sub(r'[=-]','',text)
    indexes = pd.Series([clean_ind(index) for index in indeces])
    #print(f'indexes: \n{indexes.to_list()}')
    income_df.set_index(indexes,inplace=True)
    print(income_df)
    '''income_df.set_index(income_df.iloc[:,0],inplace=True)
    income_df.iloc[:,0] = indexes'''
    income_df.iloc[:,1:] = income_df.iloc[:,1:].applymap(remChar)
    print(income_df)
    #income_df.to_csv('raw_csv.csv',index=False)
    #inc_df  = income_df.applymap(remChar)
    return income_df

def EdgarFetcher(dates,tickr,frm):
    #headers are prerequisite for SEC EDGAR requests
    headers = {'User-Agent':'Cornell University thm55@cornell.edu',"Accept-Encoding": "gzip, deflate"}
    print('running sec EDGAR requests')

    #User input
    dateRange = dates
    ticker = tickr
    cik = getCIK(ticker)
    formType = frm
    #Function Stack to arrive at desired filings. See function headers for description of what each achieves
    #print('fetching entries')
    entries = FetchXml(cik,dateRange,formType,headers=headers)
    #print('fetching master_list_xml') 
    master_list_xml = FetchReqFilings(entries)
    #print('fetching list_of_keys') 
    list_of_keys = GetKeys(master_list_xml)
    #print('fetching list_of_dates') 
    list_of_dates = GetDates(master_list_xml,keys=list_of_keys)
    #print('fetching json_list') 
    json_list = ConvertFiling(master_list_xml)
    #print('fetching master_reports') 
    master_reports = ReportPieces(json_list,keys=list_of_keys,dates=list_of_dates,headers=headers)

    #Main event loop. This will display each section of the report and parse 
    wanted = {} 
    for report in range(len(master_reports)):
        print('_'*100)
        lst = [f'{report}: ', master_reports[report]['name_short']];print(lst[0],lst[1])
        master_reports[report]['id']=report
        wanted[f'{report}']=[master_reports[report]['name_short'],master_reports[report]['url']]

    #User inputs
    inp = input('Enter the desired reports section to fetch\n Use a comma to separate each row (e.g. n1,n2. no spaces): ')
    inp.split(',');print(inp)

    #Iterate over selected items
    for k,v in wanted.items():
        #retain url for each tabular report 
        #print(f'val type: {type(v)}\n\tval:{v}')
        if k in inp:
            csv_name = f'{ticker}_{v[0]}_{dateRange}'
            financials = StructFinancials(v,headers=headers)
            if isinstance(financials, list):
                print('ITS A LIST')
                Fin_Frame = CreateDataframe(financials,csv_name)
                url_column = ['NaN']*(len(Fin_Frame)-1)+[v[1]]
                Fin_Frame['url']=url_column
                Fin_Frame.to_csv(f'{csv_name}.csv',index=False)
            else:
                print('NOT A LIST')   
                Fin_Frame = financials
                url_column = ['NaN']*(len(Fin_Frame)-1)+[v[1]]
                Fin_Frame['url']=url_column
                Fin_Frame.to_csv(f'{csv_name}.csv',index=True)
        else: pass
    print('EDGAR requests done')