# books_to_scrape_com_scrapper

This is a web scrapper that collects product information from [books.toscrape.com](https://books.toscrape.com/)

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
