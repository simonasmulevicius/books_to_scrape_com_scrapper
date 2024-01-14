import json
from aiohttp import ClientSession, ClientConnectorError
import asyncio
from bs4 import BeautifulSoup
import time
from urllib.parse import urljoin
import concurrent.futures
import logging

logging.basicConfig(format="%(asctime)s - %(message)s", level=logging.INFO)

from constants import CATALOGUE_URL, HOME_URL


async def get_page_contents(url: str, max_retries=5) -> str:
    async with ClientSession() as session:
        for attempt in range(1, max_retries + 1):
            try:
                async with session.get(url) as response:
                    if response.status == 200:
                        return await response.text()

                    logging.error(
                        f"Attempt {attempt}: Failed to get page contents of '{url}' "
                        f"(received status code {response.status})"
                    )
            except ClientConnectorError as e:
                logging.error(f"Attempt {attempt}: Connection error for '{url}': {e}")
            except Exception as e:
                logging.error(f"Attempt {attempt}: Unexpected error for '{url}': {e}")

            if attempt < max_retries:
                # Adding exponential back-off
                await asyncio.sleep(2**attempt)
            else:
                raise Exception(
                    f"Failed to fetch page '{url}' after {max_retries} attempts"
                )


def extract_product_links_from_soap(products_group_soup: BeautifulSoup, base_url):
    products = products_group_soup.find_all("article", class_="product_pod")
    product_urls = []

    for product in products:
        product_image_container = product.find("div", class_="image_container")
        if product_image_container is None:
            continue

        a_tag = product_image_container.find("a")
        relative_product_link = (
            a_tag["href"] if a_tag and "href" in a_tag.attrs else None
        )
        absolute_product_link = (
            urljoin(base_url, relative_product_link) if relative_product_link else None
        )

        if relative_product_link is None:
            continue

        product_urls.append(absolute_product_link)

    return product_urls


async def get_product_links(page_number: int):
    products_group_url = f"{CATALOGUE_URL}/page-{page_number}.html"
    logging.info(f"extracting product links from '{products_group_url}'")
    products_group_page_content = await get_page_contents(products_group_url)
    products_group_soup = BeautifulSoup(products_group_page_content, "html.parser")

    product_urls = extract_product_links_from_soap(
        products_group_soup, products_group_url
    )
    return product_urls


async def get_total_number_of_catalogue_pages():
    """
    Instead of having hardcoded pages threshold (50),
    we extract number of pages dynamically
    """

    home_page = await get_page_contents(HOME_URL)
    home_page_soup = BeautifulSoup(home_page, "html.parser")
    page_count_wrapper_element = home_page_soup.find("ul", class_="pager")
    if page_count_wrapper_element is None:
        raise Exception("Could not find catalogue page count")

    page_count_element = page_count_wrapper_element.find("li", class_="current")
    if page_count_element is None:
        raise Exception("Could not find catalogue page count")

    page_count_raw = page_count_element.get_text(strip=True)
    if "Page " not in page_count_raw or " of " not in page_count_raw:
        raise Exception("Catalogue page count format has changed")

    page_count_str = page_count_raw.split(" of ")[1]
    if not page_count_str.isnumeric():
        raise Exception("Total catalogue page count is not an integer")

    return int(page_count_str)


def flatten_list_of_lists(list_of_lists: list) -> list:
    return [item for sublist in list_of_lists for item in sublist]


async def get_all_product_urls():
    number_of_catalogue_pages = await get_total_number_of_catalogue_pages()

    tasks_to_get_product_links = [
        asyncio.create_task(get_product_links(page_number))
        for page_number in range(1, number_of_catalogue_pages + 1)
    ]

    pages_product_urls = await asyncio.gather(*tasks_to_get_product_links)
    product_urls = flatten_list_of_lists(pages_product_urls)
    return product_urls


async def get_all_products_with_raw_details(product_urls, batch_size=50):
    """
    Sending 1000 requests resulted in expired connection timeouts.
    Hence, to prevent us from overflowing the server on the receiving
    end, we introduce rate limiting in a form of batching - at most
    "batch_size" number of requests.
    """

    products_with_raw_details = []

    for product_index in range(0, len(product_urls), batch_size):
        batch = product_urls[product_index : product_index + batch_size]
        tasks_to_get_product_details = [
            asyncio.create_task(get_page_contents_for_products_with_raw_details(url))
            for url in batch
        ]
        results = await asyncio.gather(*tasks_to_get_product_details)
        products_with_raw_details.extend(results)

    return products_with_raw_details


def convert_product_information_table_to_dict(product_information_table):
    product_information_pairs = product_information_table.find_all("tr")
    product_information_dict = {}

    for information_pair in product_information_pairs:
        information_key = (
            information_pair.find("th").text if information_pair.find("th") else None
        )
        information_value = (
            information_pair.find("td").text if information_pair.find("td") else None
        )

        if information_key and information_value:
            product_information_dict[information_key] = information_value

    return product_information_dict


async def get_page_contents_for_products_with_raw_details(product_details_url):
    logging.info(f"collecting product data from '{product_details_url}'")
    product_details_page_content = await get_page_contents(product_details_url)
    return product_details_page_content


def _convert_string_to_float(number_str: str) -> float or None:
    try:
        return float(number_str)
    except ValueError:
        logging.warning(f"failed to convert '{number_str}' to float")
        return None


def _extract_price_in_pounds(price_in_pounds_str: str) -> float or None:
    return _convert_string_to_float(price_in_pounds_str.replace("£", ""))


def _extract_product_availability(product_availability_str: str) -> int:
    if "In stock" not in product_availability_str:
        return 0

    return int(
        product_availability_str.replace("In stock (", "").replace(" available)", "")
    )


def parse_product_details(product_details_page_content):
    product_soup = BeautifulSoup(product_details_page_content, "html.parser")

    product_page_article = product_soup.find("article", class_="product_page")
    product_main_container = (
        product_page_article.find("div", class_="product_main")
        if product_page_article
        else None
    )
    product_name = (
        product_main_container.find("h1").text if product_main_container else None
    )

    product_information_table = product_page_article.find("table", class_="table")
    product_information_dict = convert_product_information_table_to_dict(
        product_information_table
    )
    return {
        "product_name": product_name,
        "upc": product_information_dict["UPC"],
        "price_excluding_tax": _extract_price_in_pounds(
            product_information_dict["Price (excl. tax)"]
        ),
        "tax": _extract_price_in_pounds(product_information_dict["Tax"]),
        "availability": _extract_product_availability(
            product_information_dict["Availability"]
        ),
    }


def parse_all_product_details(products_with_raw_details: list) -> list:
    """
    As this is a CPU-bound task (as compared to network-IO bound previous tasks),
    hence ThreadPoolExecutor is used.
    """

    with concurrent.futures.ThreadPoolExecutor() as executor:
        products_with_details = list(
            executor.map(parse_product_details, products_with_raw_details)
        )
        return products_with_details


def deduplicate_products(products_with_details):
    product_codes = [product["upc"] for product in products_with_details]
    # dict structure ensures that the set would have just unique key values (hence, duplicates will be overwritten)
    return dict(zip(product_codes, products_with_details))


def store_extracted_products(products_with_details):
    db_file_path = "./data/db.json"
    os.makedirs(os.path.dirname(db_file_path), exist_ok=True)

    with open(db_file_path, "w") as file:
        json.dump(products_with_details, file)

    logging.info(f"Finished scraping - found {len(products_with_details)} products")


async def main():
    product_urls = await get_all_product_urls()
    products_with_raw_details = await get_all_products_with_raw_details(product_urls)
    products_with_details = parse_all_product_details(products_with_raw_details)
    unique_products_with_details = deduplicate_products(products_with_details)
    store_extracted_products(unique_products_with_details)


if __name__ == "__main__":
    asyncio.run(main())
