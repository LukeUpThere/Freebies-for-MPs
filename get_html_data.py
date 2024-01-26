import os
from bs4 import BeautifulSoup
from selenium import webdriver
import pickle

# URL of the webpage containing the links to the individual pages
url =      'https://publications.parliament.uk/pa/cm/cmregmem/231030/contents.htm'
base_url = 'https://publications.parliament.uk/pa/cm/cmregmem/231030/'

# Correctly set up the Chrome Driver Exe path.
os.environ["PATH"] += os.pathsep + 'D:\Code\chromedriver-win32'
# Use a chrome webdriver to get the HTML from the URL and make some Soup.

driver = webdriver.Chrome()
driver.get(url)
driver.implicitly_wait(10)
soup = BeautifulSoup(driver.page_source, 'html.parser')
driver.quit()

# Create dictionary to store the names and links of the individuals
mp_finances_link_dic = {}

# Find the links to the individual pages and iterate over them
link_tags = soup.find_all('a')
for link_tag in link_tags:
    name = ''
    link = ''
    # Filter then extract the name of the individual from the tag
    if len(link_tag.text) > 0 and link_tag.text[-1] == ' ':
        name = link_tag.text
    # Filter out unnecessary link_tags and extract links
    if link_tag.has_attr('href'):
        if '.htm' in link_tag['href']  and '/' not in link_tag['href']:
            link = base_url + link_tag['href']
    if name and link:
        mp_finances_link_dic[name] = link

# Pull HTML data from each link
for mp, link in mp_finances_link_dic.items():
    print(link)
    driver = webdriver.Chrome()
    driver.get(link)
    driver.implicitly_wait(10)
    
    # Save the page source to a file
    with open(f'HTML Files/{mp}.html', 'w', encoding='utf-8') as file:
        file.write(driver.page_source)

    driver.quit()