# books_to_scrape_com_scrapper

This is a web scraper that collects product information 
from [books.toscrape.com](https://books.toscrape.com/)

## How to run?
```
docker build -t scraper .
docker run -it --rm --name running-scraper scraper
```


## 🏗️ How to run (on Windows)?
```
python -m venv venv
source venv/Scripts/activate
pip install -r requirements.txt
```

## 🏗️ How to run (on Mac/Ubuntu)?
```
python -m venv venv
source venv\bin\activate
pip install -r requirements.txt
```

# Task 1

### Technical Considerations

One could use Selenium to collect data from this website.  
Advantage of Selenium would be that it would allow us to 
traverse the page in a more human-like manner.In other words, 
when running the scrapper we would have more control over the 
browser UI. This in turn would allow us to execute more 
intricate steps such as perform user authentication by typing 
user credentials, scroll to "Submit" button and then hover
over it for some random amount of time. These extra steps
could be needed if the page does the lazy loading of its file
contents (e.g., using AJAX). Even though I used Selenium
multiple times before, I believe that for this website
Selenium would be an overkill, because:

- I've tried loading the page without JavaScript enabled and 
the page still seems to work. Hence, there is no need to use 
browser to bypass some JavaScript pecularities
- Selenium might have some problems running on headless 
servers. I encountered a situation at work when migrating
a prototype Python script that was perfectly running on 
Desktop but not on a screen-less server.

Finally, I also investigated `Network` tab to check if the
data is not already passed from the API in some convenient
format. Unfortunatelly, this was not the case. But it
turned out that `curl` managed to download the page 
contents. Hence, the current strategy would be to use
`requests` and `BeutifulSoap` libraries to extract data.

### Rate limiting considerations

The page does not have `robots.txt` page (i.e., 
`http://books.toscrape.com/robots.txt`). Hence, one can't
deduce safe rate limits for the e-shop.

### Page structure traverse strategy

**Initial/naive implementation**: find book links by iterating
over `https://books.toscrape.com/catalogue/page-X.html` and 
then incorporate investigate further links that have the 
following format: `https://books.toscrape.com/catalogue/BOOKNAME_BOOKNUMBER/index.html`.

**More robust strategy** start in 
`https://books.toscrape.com/index.html` and then perform
Breadth-first-search (BFS) by ascending via `<a>` tags.
This might show us more available books otherwise not visible
from the main catalogue. Moreover, such method would be more
resilient to page structure change (e.g., the shop owners could
accidentaly change the page structure, say by introducing
discount code `div`). Page structure change could prevent us 
from finding the total number of pages in the catalogue (e.g., 
50 in `Page 3 of 50`). For BFS to work we would need to 
remember already discovered links. Drawback of BFS could be
that we might end up in the rabbit hole searching for 
recursively infinite number of pages (e.g., one url could be 
pointing to itself with some extra url arguments).