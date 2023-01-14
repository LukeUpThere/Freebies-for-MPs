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
    def __init__(self, name, constituency = 'Unknown', party = 'Unknown'):
        self.name = name
        self.constituency = constituency
        self.party = party
        self.donations = []

    def add_donation(self, amount, interest_type, date):
        self.donations.append({"amount": amount,
                               "interest type": interest_type, 
                               "date": date})

    def total_donations(self):
        total = 0
        for donation in self.donations:
            total += donation["amount"]
        return total

### FUNCTIONS ###

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

def get_total_from_monthly(text):
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
        date_received = end_date_match
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
    total_income = round(income * ((end_date - start_date).days / 30), 2)
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
    driver.implicitly_wait(10)
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    
    # Setup a running tally and a list of elements to search.
    grand_total = 0.0
    donations = []
    infos = soup.find_all(get_header_and_info)
    
    print('\n' + name)
    interest_type = ''
    for info in infos:
        print(info)
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
        elif 'total' in text and text[text.find("total"):].find('£') != -1:
            tot_indx = text.find("total")
            find_p = text[tot_indx:].find('£')
            end_indx = re.search(r"[^1234567890,.£]",
                                            text[tot_indx + find_p:]).start()
            tot = text[tot_indx + find_p + 1:tot_indx + find_p + end_indx]
            total = ''.join([c for c in tot if c in '1234567890.']).strip('.')
            print(f"£_{total_value} (Suspected total)") # Printing
            date_received = re.search(r"(\d{1,2} [A-Za-z]{3,9} \d{4})", text)
            amount = total_value
        # Locate date ranges with monthly pay and calculate an annual total.
        elif all(x in tl for x in ['from','until','£']) and not any(x in tl for x in ['annual', 'yearly', 'a year']):
            total_value, date_received = get_total_from_monthly(text)
            print(f"£_{total_value} (Calculated total)") # Printing
            amount = total_value
        # Locate all other monetary sums and print them.
        else:
            date_received = re.search(r"(\d{1,2} [A-Za-z]{3,9} \d{4})", text)
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
                              'date': date_received.group(1)})
    return donations

### MAIN CODE ###

# Pickle load links
mp_finances_link_dic = {}
with open('mp_finances_link_dic.pydata', 'rb') as f:
    mp_finances_link_dic = pickle.load(f)

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


# Create a dictionary of MP objects, match the names to the CSV data and apply
#   that data to each object (add each MPs Party and Constituency).
mps = {}
for name, link in mp_finances_link_dic.items():
    if name[0] == 'A':
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
        print(mps[name].party)

# Pickle the dictionary
# ~ file_object = open('mp_finances_dic.pydata', 'wb')
# ~ pickle.dump(mp_finances_dic, file_object)
# ~ file_object.close()


## To-Do (Ideas and Planing) ##

# <strong></strong> contains numbered headers needed to sort types of info.
# Headers represent 10 types of financial interests that need to be declared.
# More info on these 10 types can be found here:
#   https://publications.parliament.uk/pa/cm201719/cmcode/1882/188204.htm



# Print the parsed HTML content
#print(soup.prettify())
