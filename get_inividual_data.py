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

    def add_donation(self, amount, interest_type, date):
        self.donations.append({"amount": amount,
                               "interest type": interest_type, 
                               "date": date})

    def total_donations(self):
        total = 0
        for donation in self.donations:
            total += float(donation["amount"])
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
    if tag is None:
        return False
    elif tag.name == 'p' and any(cls in ['indent', 'indent2'] for cls in tag.get('class', [])):
        return True
    elif tag.name != 'strong':
        header_pattern = '^\d{1,2}\. '
        if re.search(header_pattern, tag.get_text()):
            return True
    else:
        return False

def get_total_from_monthly_or_quarterly(text):
    """
    This function takes in a string containing a date range and a monthly 
    income, extracts the start and end dates, and calculates the total income 
    for the given date range.
    """
    # Find the start and end dates in the date range string
    start_date_match = re.search(r"(\d{1,2} [A-Za-z]{3,9} \d{4})", text)
    end_date_match = re.search(r"(\d{1,2} [A-Za-z]{3,9} \d{4})", 
                                text[start_date_match.end():text.find('£')])
    if end_date_match:
        end_date = parse(end_date_match.group(1))
        date_received = end_date_match.group(1)
        #print('end date matched.') # Debugging
    else:
        end_date = parse("01 May 2022")
        date_received = "01 May 2022"
        
    written_sd = parse(start_date_match.group(1))
    session_sd = parse("01 May 2021")
    start_date = session_sd if session_sd >= written_sd else written_sd
    #print(start_date) # Debugging
    
    # Find the monthly income
    income_match = re.search(r"(\£\d{1,3}(?:,\d{3})*)", text)
    if income_match:
        income = float(income_match.group(1).replace(',', '')[1:])
        #print(f"income: {income}") # Debugging
    else:
        # handle the case where no match was found
        return ('error with income_match', date_received)

    income = float(income_match.group(1).replace(',', '')[1:])

    # Calculate the total income
    if any(x in text.lower() for x in ['a quarter', 'quarterly', 'every three months']):
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
        if text[0].isalnum() and text[1] == '.':
            if ':' in text:
                print(text[:text.find(':')])
                interest_type = text[:text.find(':')]
            else:
                print(text)
                interest_type = text
            continue
        # Locate and print stated totals.
        elif 'total' in tl and tl[tl.find("total"):].find('£') != -1:
            tot_indx = tl.find("total")
            find_p = text[tot_indx:].find('£')
            end_indx = re.search(r"[^1234567890,.£]",
                                            text[tot_indx + find_p:]).start()
            tot = text[tot_indx + find_p + 1:tot_indx + find_p + end_indx]
            amount = ''.join([c for c in tot if c in '1234567890.']).strip('.')
            print(f"£_{amount} (Suspected total)") # Printing
            date_received = re.search(r"(\d{1,2} [A-Za-z]{3,9} \d{4})", text)
            date_received = date_received.group(1)
        # Locate date ranges with monthly pay and calculate an annual total.
        elif all(x in tl for x in ['from','until','£']) and not any(x in tl for x in ['annual', 'yearly', 'a year', 'per annum']):
            total_value, date_received = get_total_from_monthly_or_quarterly(text)
            print(f"£_{total_value} (Calculated total)") # Printing
            amount = total_value
        # Locate all other monetary sums and print them.
        else:
            date_received = re.search(r"(\d{1,2} [A-Za-z]{3,9} \d{4})", text)
            if date_received:
                date_received = date_received.group(1)
            words_in_info = info.text.split(' ')
            #print(info.text) # Debugging
            for word in words_in_info:
                if '£' in word:
                    total_value = ''.join([c for c in word if c in 
                                                    '1234567890.']).strip('.')
                    print(f"£_{total_value}") # Printing
                    amount += float(total_value)
        
        if amount:
            donations.append({'amount': amount,
                              'interest type': interest_type,
                              'date': date_received})
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
fields = []
mp_party_constit = {}
with open('mps.csv', 'r') as csvfile:
    csv_reader = csv.reader(csvfile)
    feilds = next(csv_reader)
    rows = [row for row in csv_reader]
for row in rows:
    mp_fl_names = (row[2], row[1])
    mp_party_constit[mp_fl_names] = {'Party': row[3], 'Constituency': row[4]}


mps = pickle_io('MP_Object_Dict', load = True)
# ~ match_mps_data()

#### WIP

# ~ mps['Brady, Sir Graham '].donations = []
# ~ link = 'https://publications.parliament.uk/pa/cm/cmregmem/220503/brady_graham.htm'
# ~ donations = webscrape_freebies('Brady, Sir Graham ', link)
# ~ for donation in donations:
    # ~ mps['Brady, Sir Graham '].add_donation(donation['amount'], 
                           # ~ donation['interest type'],
                           # ~ donation['date'])

for mp, mpclass in mps.items():
    if mpclass.total_donations() >= 100000:
        print(mp)
        print(mpclass.party)
        print(mpclass.constituency)
        for donation in mpclass.donations:
            print(donation['amount'])
        print(f'Total: £{mpclass.total_donations()}\n')



#pickle_io('MP_Object_Dict', data = mps, save = True)

