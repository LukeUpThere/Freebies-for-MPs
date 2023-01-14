import os
from bs4 import BeautifulSoup
from selenium import webdriver
import pickle

# URL of the webpage containing the links to the individual pages
url = 'https://publications.parliament.uk/pa/cm/cmregmem/220503/contents.htm'
base_url = 'https://publications.parliament.uk/pa/cm/cmregmem/220503/'

# Correctly set up the Chrome Driver Exe path.
os.environ["PATH"] += os.pathsep + 'D:\Code\chromedriver_win32'
# Use a chrome webdriver to get the HTML from the URL and make some Soup.
driver = webdriver.Chrome()
driver.get(url)
driver.implicitly_wait(10)
soup = BeautifulSoup(driver.page_source, 'html.parser')

# Initialise variables to store the names and links of the individuals
names = []
links = []

# Find the links to the individual pages and iterate over them
link_tags = soup.find_all('a')
for link_tag in link_tags:
    # Filter then extract the name of the individual from the tag
    if len(link_tag.text) > 0 and link_tag.text[-1] == ' ':
        names.append(link_tag.text)
    # Filter out unnecessary link_tags and extract links
    if link_tag.has_attr('href'):
        if '.htm' in link_tag['href']  and '/' not in link_tag['href']:
            links.append(base_url + link_tag['href'])

# Add the names and links of the individuals to a dictionary
mp_finances_link_dic = {}
for i in range(len(names)):
    mp_finances_link_dic[names[i]] = links[i]

# Pickle the dictionary
file_object = open('mp_finances_link_dic.pydata', 'wb')
pickle.dump(mp_finances_link_dic, file_object)
file_object.close()
