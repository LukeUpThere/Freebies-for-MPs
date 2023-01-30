# Gets financial data on each MP
import os
import pickle
import csv
from bs4 import BeautifulSoup
from selenium import webdriver
import re
from dateutil.parser import parse
### CLASSES ###

class MP:
    """
    Represent a Member of Parliament with name, constituency, party and 
    donations attributes. Provide methods to add a donation and calculate
    total donations received.
    """
    def __init__(self, name, constituency = 'Unknown', party = 'Unknown'):
        self.name = name
        self.constituency = constituency
        self.party = party
        self.url = ''
        self.donations = []

    def add_donation(self, amount, interest_type, date, hours, text_):
        self.donations.append({"amount": amount,
                               "interest type": interest_type, 
                               "date": date,
                               "hours": hours,
                               "text": text_})

    def total_donations(self):
        total = 0
        for donation in self.donations:
            total += float(donation["amount"])
        return total
    
    def total_hours(self):
        total = 0
        for donation in self.donations:
            if isinstance(donation['hours'], float):
                total += donation['hours']
        return total

### FUNCTIONS ###

def pickle_io(file_name, data = None, save = False, load = False):
    if save and load:
        raise ValueError("Cannot both save and load")
    elif save:
        if data != None:
            with open(f'{file_name}.pydata', 'wb') as f:
                pickle.dump(data, f)
        else:
            raise ValueError("Data cannot be None")
    elif load:
        with open(f'{file_name}.pydata', 'rb') as f:
            return pickle.load(f)
    else:
        raise ValueError("Must set save or load to true")

def get_header_and_info(tag):
    """
    This function returns true for indented elements and for the numbered 
    headers without returning duplicate items when tagged as 'strong'.
    """
    classes = ['indent', 'indent2']
    if tag is None:
        return False
    elif tag.name == 'p' and any(c in classes for c in tag.get('class', [])):
        return True
    elif tag.name != 'strong':
        header_pattern = '^\d{1,2}\. '
        if re.search(header_pattern, tag.get_text()):
            return True
    else:
        return False

def find_hours(string):
    # Determine if the string contains a unit of time appended by a frequency
    #   and a time period. 
    time_unit = r"(hr|hrs|hour|hours|min|mins|minute|minutes):*"
    frequency = r"(a|per|each|every)"
    period = r"(day|week|month|quarter|year)"
    money = r"(\£\d{1,3}(?:,\d{3})*)"
    t_regex = re.compile(r"\d* " + time_unit + " " + frequency + " " + period)
    m_regex = re.compile(money + " " + frequency + " " + period) 
    is_hrs_per_time_unit = re.search(t_regex, string)
    is_money_per_time_unit = re.search(m_regex, string)
    
    # Find hours worked
    hours_regex = re.compile(r"Hours:\s*([\d\.]+)\s*(hr|hrs|mins|min)")
    match = hours_regex.search(string)
    
    # If the frequency of the payment doesn't match the frequency of the hours
    #   worked, return an error message.
    if is_hrs_per_time_unit and is_money_per_time_unit:
        if is_hrs_per_time_unit.group(3) != is_money_per_time_unit.group(3):
            return "Error: Frequency of payments and hours don't match."
            
    
    # Calculate and return the hours worked.
    if match:
        hours = match.group(1)
        unit = match.group(2)
        if unit == "hrs" or unit == "hr":
            return float(hours)
        elif unit == "mins" or unit == "min":
            return float(hours) / 60
    else:
        return None

def get_annual_total(text):
    """
    This function takes in a string containing a date range and a monthly 
    income, extracts the start and end dates, and calculates the total income 
    for the given date range.
    """
    
    # Find the start and end dates in the date range string
    date_regex = r"(\d{0,2} *[A-Za-z]{3,9} \d{4})"
    s_d_regex = re.compile(r"[fF]rom:* " + date_regex) 
    s_d_match = re.search(s_d_regex, text)
    ### Need to edit to fix issue where there is no s_d_match.
    ### (when sd is written without date eg. January 2020)
    e_d_match = re.search(date_regex, text[s_d_match.end():text.find('£')])
    if e_d_match:
        end_date = parse(e_d_match.group(1))
        date_received = e_d_match.group(1)
        # ~ print('end date matched.') # Debugging
    else:
        end_date = parse("01 May 2022")
        date_received = "01 May 2022"
        
    written_sd = parse(s_d_match.group(1))
    session_sd = parse("01 May 2021")
    start_date = session_sd if session_sd >= written_sd else written_sd
    # ~ print(f"Start date: {start_date}") # Debugging
    # ~ print(f"End date: {end_date}") # Debugging
    
    # Catch edge cases where dates are out of range of the financial year
    if start_date > end_date:
        return (0, None)
    
    # Find the monthly income
    income_match = re.search(r"(\£\d{1,3}(?:,\d{3})*)", text)
    if income_match:
        income = float(income_match.group(1).replace(',', '')[1:])
        print(f"income: {income}") # Debugging
    else:
        # handle the case where no match was found
        return ('error with income_match', date_received)

    income = float(income_match.group(1).replace(',', '')[1:])

    # Calculate the total income
    quarter_synonyms = ['a quarter', 'quarterly', 'every three months']
    if any(phrase in text.lower() for phrase in quarter_synonyms):
        total_income = round(income * ((end_date - start_date).days / 91.3), 2)
    else:
        total_income = round(income * ((end_date - start_date).days / 30.4), 2)
    return (total_income, date_received)

def webscrape_freebies(name, url):
    """
    Scrapes a webpage for financial interests of a member of parliament and 
    returns details about each donation in the form of a list of dictionaries.
    :param name: name of the member of parliament
    :param url: url of the webpage to scrape
    :return: list of donations received
    """
    # Correctly set up the Chrome Driver Exe path.
    os.environ["PATH"] += os.pathsep + 'D:\Code\chromedriver_win32'
    # Use a chrome webdriver to get the HTML from the URL and make some Soup.
    driver = webdriver.Chrome()
    driver.get(url)
    driver.implicitly_wait(5)
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    driver.quit()

    # Setup a running tally and a list of elements to search.
    grand_total = 0.0
    donations = []
    infos = soup.find_all(get_header_and_info)
    
    print('\n' + name)
    interest_type = ''
    for info in infos:
        # ~ print(info) # Debugging
        amount = 0
        text = info.text
        tl = text.lower()
        
        # Print numbered headers.
        if re.match(r"\d{1,2}\..*", text):
            if ':' in text:
                print(text[:text.find(':')])
                interest_type = text[:text.find(':')]
            else:
                print(text)
                interest_type = text
            continue

        # Locate and print stated totals.
        elif 'total' in tl and tl[tl.find("total"):].find('£') != -1:
            ## Optimised code: 2 line regex
            total_match = re.search(r"total.*£(\d{1,3}(?:,\d{3})*)", tl)
            amount = float(total_match.group(1).replace(',',''))

            ## Silly old code: 6 line '.find()' madness.
            # ~ tot_indx = tl.find("total")
            # ~ find_p = text[tot_indx:].find('£')
            # ~ not_money = r"[^1234567890,.£]"
            # ~ end_indx = re.search(not_money, text[tot_indx + find_p:]).start()
            # ~ tot = text[tot_indx + find_p + 1:tot_indx + find_p + end_indx]
            # ~ amount = float(''.join([c for c in tot if c in '1234567890.']).strip('.'))

            print(f"£{amount} (Stated Total)") # Printing

            date_received = re.search(r"(\d{1,2} [a-z]{3,9} \d{4})", tl)
            date_received = date_received.group(1)

        # Locate date ranges with monthly pay and calculate an annual total.
        elif all(x in tl for x in ['from','until','£']):
            yr_syn = ['annual', 'yearly', 'a year', 'per annum', 'per year']
            has_year = any(x in tl for x in yr_syn)
            year_regex = r"(a year|per year|yearly|per annum|annually)"
            has_hr_per_yr = re.search(r"\d{1,3} hours " + year_regex, tl)
            if not has_year or has_hr_per_yr:
                amount, date_received = get_annual_total(text)
                
                print(f"£{amount} (Calculated Total)") # Printing

        # Locate all other monetary sums and print them.
        else:
            date_received = re.search(r"(\d{1,2} [A-Za-z]{3,9} \d{4})", text)
            if date_received:
                date_received = date_received.group(1)
            words_in_info = info.text.split(' ')
            #print(info.text) # Debugging
            for word in words_in_info:
                if '£' in word:
                    val_string = [c for c in word if c in '1234567890.']
                    total_value = float(''.join(val_string).strip('.'))
                    print(f"£_{total_value}") # Printing
                    amount += total_value
        if amount:
            hours = find_hours(text)
            donations.append({'amount': amount,
                              'interest type': interest_type,
                              'date': date_received,
                              'hours': hours,
                              'text': text})
    # There are 10 types of financial interests that need to be declared.
    # https://publications.parliament.uk/pa/cm201719/cmcode/1882/188204.htm
    return donations

def match_mps_data():
    """
    Create a dictionary of MP objects and match the names to the CSV data.
    Apply the CSV data to each object by adding the MP's Party and Constituency.
    Also, Scrape the donations information and add it to each MP object and
    save the updated object to the pickle file
    """
    for name, link in mp_finances_link_dic.items():
        if name not in mps:
            for names, detail in mp_party_constit.items():
                if all(x in name for x in names):
                    mps[name] = MP(name, detail['Constituency'], detail['Party'])
                    print(f'{name} vs {names}: csv match')
                    break
                else:
                    mps[name] = MP(name)
                    print(f'{name} vs {names}: no csv match')
            # Add donations to each MP
            donations = webscrape_freebies(name, link)
            for donation in donations:
                mps[name].add_donation(donation['amount'], 
                                       donation['interest type'],
                                       donation['date'])
        print('\n--Saving data--\n')
        pickle_io('MP_Object_Dict', data = mps, save=True)

### MAIN CODE ###

# Pickle load links
mp_finances_link_dic = pickle_io(load=True, file_name = 'mp_finances_link_dic')

# Load CSV and get party and constituency data
mp_party_constit = {}
with open('mps.csv', 'r') as csvfile:
    csv_reader = csv.reader(csvfile)
    rows = [row for row in csv_reader]
for row in rows:
    mp_fl_names = (row[2], row[1])
    mp_party_constit[mp_fl_names] = {'Party': row[3], 'Constituency': row[4]}


mps = pickle_io('MP_Object_Dict', load = True)
# ~ match_mps_data()

#### WIP

# Finding hours errors
error_mps = {}
error_count = 0
for mp in mps:
    has_error = False
    mp_errors = 0
    for donation in mps[mp].donations:
        if isinstance(donation['hours'], str):
            has_error = True
            mp_errors += 1
            # ~ print(mp)
            # ~ print(donation['amount'])
    if has_error:
        error_count += 1
        error_mps[mp] = mp_errors

print(f"Of {len(mps)} MPs, {error_count} contain missmatched hours.\n")
print("The MPs with errors are listed below.")
for name, errors in dict(sorted(error_mps.items(),key= lambda x:x[1])).items():
    print(f"\n\n{name.strip()}: {errors}")
    for donation in mps[name].donations:
        if isinstance(donation['hours'], str):
            print(donation['text'])
            print()

# Update donations.
for name in mps:
    if name == 'Beresford, Sir Paul ':
        #print(name)
        mps[name].donations = []
        donations = webscrape_freebies(name, mps[name].url)
        # ~ for donation in donations:
            # ~ mps[name].add_donation(donation['amount'], 
                                   # ~ donation['interest type'],
                                   # ~ donation['date'],
                                   # ~ donation['hours'],
                                   # ~ donation['text'])
        # ~ for donation in mps[name].donations:
            # ~ if isinstance(donation['hours'], str):
                # ~ print(donation['amount'])
                # ~ print(donation['hours'])
                # ~ print()
                # ~ print(donation['text'])
            
        # ~ print(f"Saving new donation data for {name}...")
        # ~ pickle_io('MP_Object_Dict', data = mps, save = True)

