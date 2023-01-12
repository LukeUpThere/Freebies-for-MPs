# Gets financial data on each MP
import os
import pickle
from bs4 import BeautifulSoup
from selenium import webdriver
import re
from dateutil.parser import parse

### FUNCTIONS ###
# ~ def old_get_header_and_info(tag):
    # ~ return tag.name == 'p' and ('indent' in tag.get('class', [])or'indent2' in
    # ~ tag.get('class', [])) or (tag.name == 'strong' and tag.child.name != 'em')

def get_header_and_info(tag):
    if tag is None:
        return False
    if tag.name == 'p' and ('indent' in tag.get('class', []) or 'indent2' in tag.get('class', [])):
        return True
    if tag.name == 'strong':
        if tag.child is None:
            return True
        elif tag.child.name == 'em':
            return True
    return False

def get_total_from_monthly(text):
    # Find the start and end dates in the date range string
    start_date_match = re.search(r"(\d{1,2} [A-Za-z]{3,9} \d{4})", text)
    end_date_match = re.search(r"(\d{1,2} [A-Za-z]{3,9} \d{4})", 
                                text[start_date_match.end():text.find('£')])
    if end_date_match:
        end_date = parse(end_date_match.group(1))
        #print('end date matched.') # Debugging
    else:
        end_date = parse("01 May 2022")
        
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
        return 'error with income_match'

    income = float(income_match.group(1).replace(',', '')[1:])

    # Calculate the total income
    total_income = round(income * ((end_date - start_date).days / 30), 2)
    return total_income


def get_freebies(name, url):
    # Correctly set up the Chrome Driver Exe path.
    os.environ["PATH"] += os.pathsep + 'D:\Code\chromedriver_win32'
    # Use a chrome webdriver to get the HTML from the URL and make some Soup.
    driver = webdriver.Chrome()
    driver.get(url)
    driver.implicitly_wait(10)
    soup = BeautifulSoup(driver.page_source, 'html.parser')

    grand_total = 0.0
    infos = soup.find_all(get_header_and_info)
    print('\n' + name)
    for info in infos:
        text = info.text
        tl = text.lower()

        # Trying to catch the duplicates but failing
        used_text = []
        if tl in used_text:
            continue
        else:
            used_text.append(tl)
        
        if text[0].isalnum() and text[1] == '.':
            if ':' in text:
                print(text[:text.find(':')])
            else:
                print(text)
        elif 'total' in text and text[text.find("total"):].find('£') != -1:
            tot_indx = text.find("total")
            find_p = text[tot_indx:].find('£')
            end_indx = re.search(r"[^1234567890,.£]",
                                            text[tot_indx + find_p:]).start()
            total_value = text[tot_indx + find_p + 1:tot_indx + find_p +
                                                                    end_indx]
            total_value = ''.join([c for c in total_value if c in 
                                                    '1234567890.']).strip('.')
            print(f"£_{total_value} (Suspected total)") # Printing
            grand_total += float(total_value)
        elif 'from' in tl and 'until' in tl and '£' in tl and not ('annual' in 
                                    tl or 'yearly' in tl or 'a year' in tl):
            total_value = get_total_from_monthly(text)
            print(f"£_{total_value} (Calculated total)") # Printing
            grand_total += float(total_value)
        else:
            words_in_info = info.text.split(' ')
            #print(info.text) # Debugging
            for word in words_in_info:
                if '£' in word:
                    total_value = ''.join([c for c in word if c in 
                                                    '1234567890.']).strip('.')
                    print(f"£_{total_value}") # Printing
                    grand_total += float(total_value)
    print(f'Grand Total: {round(grand_total, 2)}')
    return round(grand_total, 2)

### MAIN CODE ###
# Pickle load links
mp_finances_link_dic = {}
with open('mp_finances_link_dic_v2.pydata', 'rb') as f:
    mp_finances_link_dic = pickle.load(f)

mp_finances_dic = {}
# View items in dictionary
for name, link in mp_finances_link_dic.items():
    if name == 'Aiken, Nickie ' or name == 'Abbott, Ms Diane ':
        mp_finances_dic[name] = get_freebies(name, link)

# Pickle the dictionary
# ~ file_object = open('mp_finances_dic.pydata', 'wb')
# ~ pickle.dump(mp_finances_dic, file_object)
# ~ file_object.close()


## To-Do (Ideas and Planing) ##
# class="indent" and class="indent2" contain main information.
# having issue where text with both strong and indent is being passed to
#   get_freebies() twice. Probably coming from issue with get_head... func

# The text can be searched, every word containing '£' could be returned.
# I need to come up with a way of filtering out (or otherwise accounting for)
# 'total values' of financial interests. perhaps looking for the word 'total'?
# In addition, many MPs log income as a monthly sum and give start/end dates;
# I'll need to figure out how to account for that.

# <strong></strong> contains numbered headers needed to sort types of info.
# Headers represent 10 types of financial interests that need to be declared.
# More info on these 10 types can be found here:
#   https://publications.parliament.uk/pa/cm201719/cmcode/1882/188204.htm



# Print the parsed HTML content
#print(soup.prettify())
