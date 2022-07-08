from ast import Pass
import webbrowser
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.action_chains import ActionChains
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup
from time import sleep
import csv
import string
import random

print("- Finish importing package")

# Generate unique random ID for books, comments, replies.
# Type: book, comment, reply


class Utilities:
    @staticmethod
    def unique_id(size=10, type="book"):
        chars = list(set(string.ascii_uppercase + string.digits))
        if type == "book":
            return str("BOOK_") + str("".join(random.choices(chars, k=size)))
        elif type == "comment":
            return str("COMMENT_") + str("".join(random.choices(chars, k=size)))
        return "REPLY_" + "".join(random.choices(chars, k=size))


class Setup:
    def __init__(self, base_url="https://www.goodreads.com/"):
        self.base_url = base_url

    def create_driver(self):
        # Open Chrome and go to GoodReads's link
        options = Options()
        options.add_argument("start-maximized")
        options.add_argument("--incognito")
        self.driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()), options=options
        )
        self.driver.get(self.base_url)
        return self.base_url, self.driver

    @staticmethod
    def setup_writer(filename, headers):
        file = open(filename, "w", newline="", encoding="utf-8")
        writer = csv.DictWriter(
            file, delimiter=",", lineterminator="\n", fieldnames=headers
        )
        writer.writeheader()
        return writer


class DataScraping(Setup):
    def __init__(self, author_name="Higashino Keigo"):
        super(DataScraping, self).__init__()
        self.base_url, self.driver = Setup().create_driver()
        self.author_name = author_name
        self.all_item_urls = []
        self.book_headers = [
                "Book ID",
                "Title",
                "Authors",
                "Stars",
                "Ratings",
                "Reviews",
                "Description",
                "Cover",
            ]
        self.comment_headers = [
                "Book ID",
                "Comment ID",
                "Username",
                "Stars",
                "Content",
                "Likes"
            ]
        self.reply_headers = [
                "Comment ID",
                "Username",
                "Date",
                "Content"
            ]   
        

    def search_for_author(self):
        # Search for the author
        search_field = self.driver.find_element(By.ID, "sitesearch_field")
        search_query = self.author_name
        search_field.send_keys(search_query)
        search_field.send_keys(Keys.RETURN)
        # sleep(3)

    def find_next_page(self):
        try:
            next_page = self.driver.find_element(by=By.CLASS_NAME, value="next_page")
            if next_page.tag_name == "a":
                return next_page
            else:
                return False
        except:
            return False

    def find_books(self, drive):
        rows = self.driver.find_elements(by=By.TAG_NAME, value="tr")
        elements = [row.find_element(by=By.TAG_NAME, value="a") for row in rows]
        if elements:
            return elements
        else:
            return False

    def get_info_book(self):
        self.book_writer = Setup.setup_writer('collections/books.csv', self.book_headers)
        self.comment_writer = Setup.setup_writer('collections/comment.csv', self.comment_headers)
        self.reply_writer = Setup.setup_writer('collections/reply.csv', self.reply_headers)
        self.total_comment_links = []
        self.book_ids = []

        while True:
            books = WebDriverWait(self.driver, 20).until(self.find_books)
            book_index = 0
            while book_index < len(books):
                book = books[book_index]
                book_index += 1
                ActionChains(self.driver).move_to_element(book).move_by_offset(
                    -40, 0
                ).click().perform()
                book.click()
                sleep(2)

                page_source = BeautifulSoup(
                    self.driver.page_source, features="html.parser"
                )
                book_id = Utilities.unique_id(10, "book")
                self.book_ids.append(book_id)
                title = ""
                author_names = ""
                num_stars = ""
                num_ratings = ""
                num_reviews = ""
                description = ""
                content = ""
                title = (
                    page_source.find("h1", {"id": "bookTitle"}).get_text().strip()
                )
                author_tags = page_source.find_all("a", {"class": "authorName"})
                for author_tag in author_tags:
                    author_names += (
                        author_tag.find("span", {"itemprop": "name"})
                        .get_text()
                        .strip()
                        + ", "
                    )
                num_stars = (
                    page_source.find("span", {"itemprop": "ratingValue"})
                    .get_text()
                    .strip()
                )
                num_ratings = page_source.find(
                    "meta", {"itemprop": "ratingCount"}
                ).get("content")
                num_reviews = page_source.find(
                    "meta", {"itemprop": "reviewCount"}
                ).get("content")
                try:
                    description_meta = page_source.find_all(
                        "div", {"id": "description"}
                    )
                    for tag in description_meta:
                        description = (
                            tag.find("span", {"style": "display:none"})
                            .get_text()
                            .strip()
                        )
                except Exception:
                    description = "There is no description."
                try:
                    cover = (
                        page_source.find("img", {"id": "coverImage"})
                        .get("src")
                        .strip()
                    )
                except:
                    cover = ""
                self.book_writer.writerow(
                    {
                        self.book_headers[0]: book_id,
                        self.book_headers[1]: title,
                        self.book_headers[2]: author_names,
                        self.book_headers[3]: num_stars,
                        self.book_headers[4]: num_ratings,
                        self.book_headers[5]: num_reviews,
                        self.book_headers[6]: description,
                        self.book_headers[7]: cover,
                    }
                )
                comment_links = self.get_comments(page_source)
                self.total_comment_links.append(comment_links)
                
                for i in range(self.count - 1):
                    self.driver.back()
                    sleep(1)
                
                print("Title: ", title)
                print("Author name: ", author_names)
                print("Number of stars: ", num_stars)
                print("Number of ratings: ", num_ratings)
                print("Number of reviews: ", num_reviews)
                print("Descriptions: ", description)
                print("Cover image: ", cover)
                print("Content: ", content)
                print("\n")
                
                self.driver.back()
                sleep(1)
                books = WebDriverWait(self.driver, 20).until(self.find_books)
                sleep(1)

            next_page = self.find_next_page()
            if next_page:
                try:
                    next_page.click()
                except:
                    print(next_page.location)
                    ActionChains(self.driver).move_to_element(
                        next_page
                    ).move_by_offset(-40, 0).click().perform()
                    next_page.click()
                    sleep(2)
            else:
                break

        for comment_links, book_id in zip(self.total_comment_links, self.book_ids):
            if len(comment_links) > 0:
                for comment_link in comment_links:
                    comment = self.get_comment_content(comment_link)
                    self.comment_writer.writerow(
                    {
                        self.comment_headers[0]: book_id,
                        self.comment_headers[1]: comment['comment_id'],
                        self.comment_headers[2]: comment['user_name'],
                        self.comment_headers[3]: comment['num_stars'],
                        self.comment_headers[4]: comment['content'],
                        self.comment_headers[5]: comment['num_likes']
                    })
                    if len(comment['replies']) > 0:
                        for reply in comment['replies']:
                            self.reply_writer.writerow(
                            {
                                self.reply_headers[0]: reply['comment_id'],
                                self.reply_headers[1]: reply['comment_author'],
                                self.reply_headers[2]: reply['date_reply'],
                                self.reply_headers[3]: reply['content']
                            })

    def get_comments(self, page_source):
        comment_links = []
        self.count = 0
        while True:
            next_page = self.find_next_page()
            if next_page and len(comment_links) < 30:
                try:
                    self.count += 1
                    next_page.click()
                    page_source = BeautifulSoup(
                        self.driver.page_source, features="html.parser"
                    )
                    comment_tags = page_source.find_all("a", {"class": "reviewDate"})
                    for comment_tag in comment_tags:
                        comment_links.append(
                            self.base_url + comment_tag.get("href").strip()
                        )
                except:
                    print(next_page.location)
                    ActionChains(self.driver).move_to_element(next_page).move_by_offset(-40, 0).click().perform()
                    next_page.click()
                    page_source = BeautifulSoup(self.driver.page_source, features="html.parser")
                    comment_tags = page_source.find_all("a", {"class": "reviewDate"})
                    for comment_tag in comment_tags:
                        comment_links.append(
                            self.base_url + comment_tag.get("href").strip()
                        )
                    sleep(2)
            else:
                break

        print("Length comment links: ", len(comment_links))
        return comment_links

    def get_comment_content(self, comment_link):
        self.driver.get(comment_link)
        page_source = BeautifulSoup(self.driver.page_source, features="html.parser")
        comment = {}
        comment_id = Utilities.unique_id(10, 'comment')
        comment["comment_id"] = comment_id
        comment["user_name"] = (page_source.find("a", {"class": "userReview"}).get_text().strip())
        comment["date_cmt"] = (page_source.find("span", {"itemprop": "datePublished"}).get_text().strip())
        try:
            comment["num_stars"] = (page_source.find("meta", {"itemprop": "ratingValue"}).get("content").strip())
        except:
            comment["num_stars"] = 0
        try:
            comment["content"] = (page_source.find("div", {"itemprop": "reviewBody"}).get_text().strip())
        except:
            comment["content"] = 0
        try:
            comment["num_likes"] = (page_source.find("span", {"class": "likesCount"}).get_text()[:-5].strip())
        except:
            comment["num_likes"] = 0
        try:
            replies = page_source.find_all("div", {"class": "comment"})
        except:
            replies = ""
        if replies:
            comment["replies"] = self.get_replies(comment_id, replies)
        else:
            comment["replies"] = []
        return comment

    def get_replies(self, comment_id, replies):
        reply_list = []
        for reply in replies:
            reply_item = {}
            reply_item['comment_id'] = comment_id
            reply_item['comment_author'] = reply.find("span", {"class": "commentAuthor"}).text.strip()
            reply_item['date_reply'] = reply.find("div", {"class": "right"}).text.strip()
            reply_item['content'] = reply.find("div", {"class": "reviewText"}).text.strip()
            print(reply_item['comment_author'], reply_item['date_reply'], reply_item['content'])
            reply_list.append(reply_item)
        return reply_list


data_scraper = DataScraping()
data_scraper.search_for_author()
data_scraper.get_info_book()
