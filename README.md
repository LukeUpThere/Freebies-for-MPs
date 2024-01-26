# Freebies-for-MPs
A project that web-scrapes publicly available 'Financial Interest' information about UK MPs and provides some insights into that data.

- The project initialy scrapes all the necisarry links from the [contents page](https://publications.parliament.uk/pa/cm/cmregmem/220503/contents.htm).
- Each MP page is then webscraped using Selenium and BeautifulSoup. Data is then applied to MP objects held in a dictionary.
- MatPlotLib and general data analysis can then be used to see broader trends across this dataset.
---
In the 2021 to 2022 tax year, almost 10 million pounds were accepted across the UK House of Commons in MP financial interests. Of this, nearly three quarters (75%) went to Conservative MP's, despite them only holding  just over half (54%) of the House of Commons seats.

On average, an MP in this tax year received £15,400 in financial interests. However, the average MP for both the Conservative and Liberal Democrat parties recived over 30% more than that (£20,887 and £20,302 respectively).

The four MP's with the highest financial interests were all members of the conservative party. Combined, these MPs recieved over three million pounds. Among them are former PM **Theresa May** who had stepped down shortly before the tax year began, and **Sir Geoffrey Cox**.

![DataVis](https://user-images.githubusercontent.com/19293025/227812415-ac38b463-284b-4e8f-a3b2-54d807cbc2e8.jpg)
