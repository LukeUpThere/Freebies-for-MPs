# Gets financial data on each MP
import os
import time
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
    def __init__(self, name, constituency = 'Unknown', party = 'Unknown', url = ''):
        self.name = name
        self.constituency = constituency
        self.party = party
        self.url = url
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
    time_unit = r"(hr|hrs|hour|hours|min|mins|minute|minutes)"
    frequency = r"(a|per|each|every)"
    period = r"(day|week|month|quarter|year)"
    t_regex = re.compile(r"\d* " + time_unit + " " + frequency + " " + period)
    is_hrs_per_time_unit = re.search(t_regex, string)
    
    # Find hours worked
    # This section may not work correctly when hours are written as
    #   "2 hours 30 mins". Updated RegEx will be needed.
    new_hours_regex = r"([\d\.]+)\s*" + time_unit

    
    hours_regex = re.compile(r"Hours:\s*([\d\.]+)\s*" + time_unit)
    match = hours_regex.search(string)
    
    # Convert hrs and mins to a floating point decimal (ie. 75min = 1.25)
    if match:
        hours = match.group(1)
        unit = match.group(2)
        if unit in ['hr', 'hrs', 'hour', 'hours']:
            hours = float(hours)
        elif unit in ['min', 'mins', 'minute', 'minutes']:
            hours = float(hours) / 60
    else:
        return None

    # Calculate the hours per year, based on the stated period of hours worked.
    if is_hrs_per_time_unit:
        hours_period = is_hrs_per_time_unit.group(3)
        hours_period_multipliers = {'year':1,
                                    'quarter':4,
                                    'month':12,
                                    'week':52,
                                    'day':365}
        return hours * hours_period_multipliers[hours_period]
    elif hours:
        return hours
    else:
        return "is_hrs_per_time_unit fail"
    

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
    ### (when sd is written without date eg. January 2020) fixed?
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
    income_match = re.search(r"£(\d{1,}(?:,\d{3})*(?:\.\d{2})?)", text)
    if income_match:
        income = float(income_match.group(1).replace(',', ''))
        #print(f"income: {income}") # Debugging
    else:
        # handle the case where no match was found
        return ('error with income_match', date_received)

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
    
    print('webscrape_freebies: ________________\n' + name)
    interest_type = ''
    for info in infos:
        # ~ print(info) # Debugging
        amount = 0
        text = info.text
        tl = text.lower()
        yr_syn = ['annual', 'yearly', 'a year', 'per annum', 'per year']
        has_year = any(x in tl for x in yr_syn)
        
        # Print numbered headers.
        if re.match(r"\d{1,2}\..*", text):
            interest_type = text[:text.find(':')] if ':' in text else text
            # ~ print(f"Interest type has been set to '{interest_type}'")
            continue

        # Locate and print stated totals.
        # if 'total' is in the text and '£' is not present after 'total'
        elif 'total' in tl and tl[tl.find("total"):].find('£') != -1:
            total_match = re.search(r"total.*£(\d{1,3}(?:,\d{3})*)", tl)
            amount = float(total_match.group(1).replace(',',''))

            # ~ print(f"£{amount} (Stated Total)") # Printing

            date_received = re.search(r"(\d{1,2} [a-z]{3,9} \d{4})", tl)
            date_received = date_received.group(1)

        # Locate date ranges with monthly pay and calculate an annual total.
        elif all(x in tl for x in ['from','until','£']) and not has_year:
            year_regex = r"(a year|per year|yearly|per annum|annually)"
            has_hr_per_yr = re.search(r"\d{1,3} hours " + year_regex, tl)
            if has_hr_per_yr:
                amount, date_received = get_annual_total(text)
                
                # ~ print(f"£{amount} (Calculated Total)") # Printing

        # Locate all other monetary sums and print them.
        else:
            date_received = re.search(r"(\d{1,2} [a-z]{3,9} \d{4})", tl)
            if date_received:
                date_received = date_received.group(1)
            words_in_info = info.text.split(' ')
            #print(info.text) # Debugging
            for word in words_in_info:
                if '£' in word:
                    val_string = [c for c in word if c in '1234567890.']
                    total_value = float(''.join(val_string).strip('.'))
                    # ~ print(f"£_{total_value}") # Printing
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

def textscrape_freebies(name):
    """
    Scrapes a webpage for financial interests of a member of parliament and 
    returns details about each donation in the form of a list of dictionaries.
    :param name: name of the member of parliament
    :return: list of donations received
    """
    donations = []
    interest_type = ''
    for donation in mps[name].donations:
        amount = 0
        text = donation['text']
        tl = text.lower()
        yr_syn = ['annual', 'yearly', 'a year', 'per annum', 'per year']
        has_year = any(x in tl for x in yr_syn)
        
        # Print numbered headers.
        if re.match(r"\d{1,2}\..*", text):
            interest_type = text[:text.find(':')] if ':' in text else text
            #print(f"Interest type has been set to '{interest_type}'")
            continue

        # Locate and print stated totals.
        elif 'total' in tl and tl[tl.find("total"):].find('£') != -1:
            ## Optimised code: 2 line regex
            total_match = re.search(r"total.*£(\d{1,3}(?:,\d{3})*)", tl)
            amount = float(total_match.group(1).replace(',',''))

            #print(f"£{amount} (Stated Total)") # Printing

            date_received = re.search(r"(\d{1,2} [a-z]{3,9} \d{4})", tl)
            date_received = date_received.group(1)

        # Locate date ranges with monthly pay and calculate an annual total.
        elif all(x in tl for x in ['from','until','£']) and not has_year:
            year_regex = r"(a year|per year|yearly|per annum|annually)"
            has_hr_per_yr = re.search(r"\d{1,3} hours " + year_regex, tl)
            if has_hr_per_yr:
                amount, date_received = get_annual_total(text)
                
                #print(f"£{amount} (Calculated Total)") # Printing

        # Locate all other monetary sums and print them.
        else:
            date_received = re.search(r"(\d{1,2} [a-z]{3,9} \d{4})", tl)
            if date_received:
                date_received = date_received.group(1)
            words_in_text = text.split(' ')
            value_match = re.search(r"£(\d{1,}(?:,\d{3})*(?:\.\d{2})?)", tl)
            amount = float(value_match.group(1).replace(',',''))
                    #print(f"£_{total_value}") # Printing
        
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

def mp_generator(theyworkforyou_csv):
    # Load CSV and get party and constituency data
    unmatched_mps = []
    mps = {}

    with open(theyworkforyou_csv, 'r', encoding = 'utf-8') as csvfile:
        csv_reader = csv.reader(csvfile)
        next(csv_reader)
        rows = list(csv_reader)

    for row in rows:
        mp_full_name = (row[1], row[2])
        mp_party = row[3]
        mp_constituency = row[4]
        mps[mp_full_name] = MP(name=mp_full_name, party=mp_party, constituency=mp_constituency)

    matched_mp_files = []  # Separate list to store matched file names

    for file_name in os.listdir('HTML_Files'):
        matched = False  # Flag to track whether the current file is matched
        for mp_full_name, mp in mps.items():
            if all(x in file_name for x in mp_full_name) and file_name not in matched_mp_files:
                mp_url = os.path.join('HTML_Files', file_name)
                mp.url = mp_url
                matched = True
                matched_mp_files.append(file_name)
                break  # Exit the loop once a match is found
        if not matched:
            unmatched_mps.append(file_name)

    print(f'\n{len(unmatched_mps)} unmatched MPs:')
    for mp_name in unmatched_mps:
        print(mp_name)

    return mps


### MAIN CODE ###
mps = mp_generator('mps_2024.csv')
# for mp in mps.values():
#     print(mp.name)
quit()


# Load MP Object dictionary from file
mps = pickle_io('New_MP_Object_Dict', load = True)


## Find and print average MP interest amount.
donations = []
for mp in mps.values():
    donations.append(mp.total_donations())
print(f"MP Average: {sum(donations)/len(donations)}")
print(f"MP Total: {sum(donations)}\n")
# Set up a list of parties
for mp in mps.values():
    if mp.party == 'Labour/Co-operative':
        mp.party = 'Labour'
parties = list({mps[mp].party for mp in mps})
# Find average Party MP interest amount.
party_averages = {}
for party in parties:
    donations = []
    for mp in mps.values():
        if mp.party == party:
            donations.append(mp.total_donations())
    party_averages[party] = [round(sum(donations)/len(donations)), round(sum(donations))]
# Print values
for party, amount in sorted(party_averages.items(), key=lambda item: item[1]):
    print(f"{party} Average: {amount[0]}\n{party} Total: {amount[1]}\n")

## Display donation totals for each MP
mp_totals = {}
for mp in mps.values():
    mp_totals[mp.name] = (mp.total_donations(), mp.party)
for mp, amount in sorted(mp_totals.items(), key=lambda item: item[1]):
    print(f"{mp}, {amount[1]}: {amount[0]}")
        
# Update donations.
# ~ for name in mps:
    # ~ #print(name)
    # ~ donations = textscrape_freebies(name)
    # ~ mps[name].donations = []
    # ~ for donation in donations:
        # ~ mps[name].add_donation(donation['amount'], 
                               # ~ donation['interest type'],
                               # ~ donation['date'],
                               # ~ donation['hours'],
                               # ~ donation['text'])
    # ~ print(f"Saving new donation data for {name}...")
    # ~ pickle_io('New_MP_Object_Dict', data = mps, save = True)
