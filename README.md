# books_to_scrape_com_scrapper

This is a web scraper that collects product information 
from [books.toscrape.com](https://books.toscrape.com/)

## How to run?
```
docker build -t scraper-image:latest .
docker run -it --rm --name running-scraper scraper-image:latest
```


## Fallback run options:

### Windows
```
python -m venv venv
source venv/Scripts/activate
pip install -r requirements.txt
```

### Mac/Ubuntu
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


# Task 2

Check `Dockerfile`.


# Task 3

After running the pod, the end user/tester might want to
investigate the database. Hence, `pvc.yaml` was added to 
store the final database output in a persistent volume.

## Built docker image with:
```
docker build -t scraper-image:latest .
```

## Pushed docker image to Docker Hub:
```
docker tag scraper-image:latest simonasmulevicius/scraper-image:latest
docker push simonasmulevicius/scraper-image:latest
```

Assuming that there is a local cluster (e.g., started with `minikube start`)
the following commands need to be executed:

```
kubectl apply -f pvc.yaml
kubectl apply -f deployment.yaml
```

To check that everything is working, I used:

```
kubectl get deployments
kubectl get pods
```

Then, I used `kubectl logs scraper-deployment-5884c8f74c-b9t8w` to see
logs for specific pod.

And it seemed to work :D
```
...
2024-01-14 20:41:53,861 - collecting product data from 'https://books.toscrape.com/catalogue/a-spys-devotion-the-regency-spies-of-london-1_3/index.html'     
2024-01-14 20:41:53,861 - collecting product data from 'https://books.toscrape.com/catalogue/1st-to-die-womens-murder-club-1_2/index.html'
2024-01-14 20:41:53,861 - collecting product data from 'https://books.toscrape.com/catalogue/1000-places-to-see-before-you-die_1/index.html'
2024-01-14 20:42:52,522 - Finished scraping - found 1000 products
```

# Task 4

The final output is `db.json` which looks as follows:
```
{
  "a897fe39b1053632": {
    "product_name": "A Light in the Attic",
    "upc": "a897fe39b1053632",
    "price_excluding_tax": 51.77,
    "tax": 0.0,
    "availability": 22
  },
  "90fa61229261140a": {
    "product_name": "Tipping the Velvet",
    "upc": "90fa61229261140a",
    "price_excluding_tax": 53.74,
    "tax": 0.0,
    "availability": 20
  },
 
 ...

 "228ba5e7577e1d49": {
    "product_name": "1,000 Places to See Before You Die",
    "upc": "228ba5e7577e1d49",
    "price_excluding_tax": 26.08,
    "tax": 0.0,
    "availability": 1
  }
}
```

The _database_ copy is not included in this repo as it is
a standard practise to keep large files outside 
repository.

I noticed problem with the data was that all books seemed
to be sold tax-free. Moreover, all of the books were in
stock. Hence, to test this application more thoroughly
it would be benefial to see more products with different
parameters.