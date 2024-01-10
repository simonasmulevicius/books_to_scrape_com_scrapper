import json
import requests
from bs4 import BeautifulSoup
import time
from urllib.parse import urljoin


def wait(sleeping_time_quantum_in_seconds=1):
    time.sleep(sleeping_time_quantum_in_seconds)


def get_page_contents(url: str) -> BeautifulSoup:
    wait()  # implicitly wait to prevent DDoS or violating Terms of Service of the page under test
    response = requests.get(url)

    if response.status_code != 200:
        # TODO consider what should we do
        raise Exception("Future TODO")

    return BeautifulSoup(response.content, "html.parser")


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


def get_product_links(page_number: int):
    products_group_url = (
        f"https://books.toscrape.com/catalogue/category/books_1/page-{page_number}.html"
    )
    products_group_soup = get_page_contents(products_group_url)
    product_urls = extract_product_links_from_soap(
        products_group_soup, products_group_url
    )
    return product_urls


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


def get_products_with_details(product_details_url):
    product_soup = get_page_contents(product_details_url)

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
        "price_excluding_tax": product_information_dict["Price (excl. tax)"],
        "tax": product_information_dict["Tax"],
        "availability": product_information_dict[
            "Availability"
        ],  # TODO In stock/not in stock + x available
    }


def save_products(products_with_details):
    with open("db.json", "w") as file:
        json.dump(products_with_details, file)


def main():
    product_urls = []
    for page_number in range(
        1, 51
    ):  # TODO instead of having hardcoded threshold create a way to extract dynamic threshold
        product_urls += get_product_links(page_number)

    products_with_details = [
        get_products_with_details(product_url) for product_url in product_urls
    ]

    save_products(products_with_details)


if __name__ == "__main__":
    main()
