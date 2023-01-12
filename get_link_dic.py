import os
from bs4 import BeautifulSoup
from selenium import webdriver
import pickle
os.system('clear')

# URL of the webpage containing the links to the individual pages
url = 'https://publications.parliament.uk/pa/cm/cmregmem/220503/contents.htm'
base_url = 'https://publications.parliament.uk/pa/cm/cmregmem/220503/'

# Create a Safari webdriver, Navigate to the webpage
driver = webdriver.Safari()
driver.get(url)
driver.implicitly_wait(10)

# Extract the HTML content of the webpage and make soup
html_content = driver.page_source
soup = BeautifulSoup(html_content, 'html.parser')

# Initialise variables to store the names and links of the individuals
names = []
links = []

# Find the links to the individual pages
link_tags = soup.find_all('a')
# Iterate over the link tags
for link_tag in link_tags:
    # Filter then extract the name of the individual from the tag
    if len(link_tag.text) > 0 and link_tag.text[-1] == ' ':
        names.append(link_tag.text)
    # Filter out unnecessary link_tags and extract links
    if link_tag.has_attr('href'):
        if '.htm' in link_tag['href']  and '/' not in link_tag['href']:
            links.append(base_url + link_tag['href'])

mp_finances_link_dic = {}
# Add the names and links of the individuals to a dictionary
for i in range(len(names)):
    mp_finances_link_dic[names[i]] = links[i]
    # ~ print(f'{names[i]}: {links[i]}') # Debugging

# Pickle the dictionary
file_object = open('mp_finances_link_dic_v2.pydata', 'wb')
pickle.dump(mp_finances_link_dic, file_object)
file_object.close()


# Print the parsed HTML content
#print(soup.prettify())
