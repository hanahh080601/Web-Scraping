from ast import Pass
import webbrowser
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.action_chains import ActionChains
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup
from time import sleep
import csv
import string
import random
print('- Finish importing package')

# Generate unique random ID for books, comments, replies.
# Type: book, comment, reply

class Utilities:
    @staticmethod
    def unique_id(size=10, type='book'):
        chars = list(set(string.ascii_uppercase + string.digits))
        if type == 'book':
            return str('BOOK_') + str(''.join(random.choices(chars, k=size)))
        elif type == 'comment':
            return str('COMMENT_') + str(''.join(random.choices(chars, k=size)))
        return 'REPLY_' + ''.join(random.choices(chars, k=size))

class Setup:
    def __init__(self, base_url="https://www.goodreads.com/"):
        self.base_url = base_url    

    def create_driver(self):
        #Open Chrome and go to GoodReads's link
        options = Options()
        options.add_argument("start-maximized")
        options.add_argument("--incognito")
        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options) 
        self.driver.get(self.base_url)
        return self.base_url, self.driver

class DataScraping(Setup):
    def __init__(self, author_name='Higashino Keigo'):
        super(DataScraping, self).__init__()
        self.base_url, self.driver = Setup().create_driver()
        self.author_name = author_name
        self.all_item_urls = []
        self.books = []

    def search_for_author(self):
        #Search for the author
        search_field = self.driver.find_element(By.ID, 'sitesearch_field')
        search_query = self.author_name
        search_field.send_keys(search_query)
        search_field.send_keys(Keys.RETURN)
        #sleep(3)

    
    def find_next_page(self):
        next_page = self.driver.find_element(by=By.CLASS_NAME, value="next_page")
        if next_page.tag_name == "a":
            return next_page
        else:
            return False

    #Scrape links to items in 1 page
    def get_book_urls_one_page(self):
        page_source = BeautifulSoup(self.driver.page_source, features="html.parser")
        items = page_source.find_all('a', attrs={'class': 'bookTitle'})
        
        for item in items:
            link_item = self.base_url + item.get('href')
            if link_item not in self.all_item_urls:
                self.all_item_urls.append(link_item)

    #Scrape links to items in all pages
    def get_book_urls_multipages(self):
        self.get_book_urls_one_page()
        while True:
            next_page = self.find_next_page()
            if next_page:
                try:
                    next_page.click()
                    sleep(1)
                    self.get_book_urls_one_page()
                    sleep(1)
                except:
                    print(next_page.location)
                    ActionChains(self.driver).move_to_element(next_page).move_by_offset(-40, 0).click().perform()
                    next_page.click()
                    self.get_book_urls_one_page()
                    sleep(2)
            else:
                break

    def check_default(self):
        self.check = False
        self.driver.get(self.all_item_urls[0])
        page_source = BeautifulSoup(self.driver.page_source, features="html.parser")
        try:
            title = page_source.find('h1', {'id': 'bookTitle'}).get_text().strip()
            self.check  = True
        except:
            title = page_source.find('h1', {'data-testid': 'bookTitle'}).get_text().strip()
        return self.check 

    def get_info_book(self):
        with open('book.csv', 'w', newline='', encoding="utf-8") as file_output:
            headers = ['Book ID', 'Title', 'Authors', 'Stars', 'Ratings', 'Reviews', 'Description', 'Cover']
            writer = csv.DictWriter(file_output, delimiter=',',lineterminator='\n', fieldnames=headers)
            writer.writeheader()

            self.check = self.check_default()
            for item in self.all_item_urls[:5]:
                book = {}
                self.driver.get(item)
                page_source = BeautifulSoup(self.driver.page_source, features="html.parser")
                book_id = Utilities.unique_id(10, 'book')
                title = ''
                author_names = ''
                num_stars = ''
                num_ratings = ''
                num_reviews = ''
                description = ''

                if self.check :
                    title = page_source.find('h1', {'id': 'bookTitle'}).get_text().strip()
                    author_tags = page_source.find_all('a', {'class': 'authorName'})
                    for author_tag in author_tags:
                        author_names += author_tag.find('span', {'itemprop': 'name'}).get_text().strip() + ', '
                    num_stars = page_source.find('span', {'itemprop': 'ratingValue'}).get_text().strip()
                    num_ratings = page_source.find('meta', {'itemprop': 'ratingCount'}).get('content')
                    num_reviews = page_source.find('meta', {'itemprop': 'reviewCount'}).get('content')
                    try:
                        description_meta = page_source.find_all('div', {'id': 'description'})
                        for tag in description_meta:
                            description = tag.find('span', {'style': 'display:none'}).get_text().strip()
                    except Exception:
                        description = 'There is no description.'
                    cover = page_source.find('img', {'id': 'coverImage'}).get('src').strip()                    
                else:
                    '''
                    title = page_source.find('h1', {'data-testid': 'bookTitle'}).get_text().strip()
                    author_tags = page_source.find_all('a', {'class': 'ContributorLink'})
                    for author_tag in author_tags:
                        author_names += author_tag.find('span', {'data-testid': 'name'}).get_text().strip() + ', '
                    num_stars = page_source.find('div', {'class': 'RatingStatistics__rating'}).get_text().strip()
                    num_ratings = page_source.find('span', {'data-testid': 'ratingsCount'}).get_text().strip()
                    num_reviews = page_source.find('span', {'data-testid': 'reviewsCount'}).get_text().strip()
                    try:
                        description_meta = page_source.find_all('div', {'data-testid': 'contentContainer'})
                        for tag in description_meta:
                            description = tag.find('span', {'class': 'Formatted'}).get_text().strip()
                    except Exception:
                        description = 'There is no description.'
                    cover = page_source.find('img', {'class': 'ResponsiveImage'}).get('src').strip()
                    '''
                comment_links = self.get_comments(page_source, default=self.check)
                content = self.get_comment_content(comment_links[0])
                writer.writerow({ headers[0]: str(book_id), headers[1]: title, headers[2]: author_names, headers[3]: num_stars, 
                                headers[4]: num_ratings, headers[5]: num_reviews, headers[6]: description, headers[7]: cover
                            })
                
                book['book_id'] = str(book_id)
                book['title'] = title
                book['author_names'] = author_names
                book['num_stars'] = num_stars
                book['num_ratings'] = num_ratings
                book['num_reviews'] = num_reviews
                book['description'] = description
                book['cover'] = cover
                book['comments'] = {'book_id': str(book_id),
                                    'comment_links': comment_links
                                }

                print('Title: ', title)
                print('Author name: ', author_names)
                print('Number of stars: ', num_stars)
                print('Number of ratings: ', num_ratings)
                print('Number of reviews: ', num_reviews)
                print('Descriptions: ', description)
                print('Cover image: ', cover)
                #print('Comment links: ', comment_links)
                print('Content: ', content)
                print("\n")


    def get_comments(self, page_source, default=True):
        comment_links = []
        while True:
            next_page = self.find_next_page()
            if next_page and len(comment_links) < 40:
                next_page.click()
                page_source = BeautifulSoup(self.driver.page_source, features="html.parser")
                if default:
                    comment_tags = page_source.find_all('a', {'class': 'reviewDate'})
                    for comment_tag in comment_tags:
                        comment_links.append(self.base_url + comment_tag.get('href').strip())
                else:
                    self.driver.get(self.base_url + page_source.find_all('a', {'class': 'DiscussionCard'}).get('href'))
                    comment_links.append()
            else:
                break
        print("Length comment links: ", len(comment_links))
        return comment_links

    def get_comment_content(self, comment_link):
        self.driver.get(comment_link)
        page_source = BeautifulSoup(self.driver.page_source, features="html.parser")
        comment = {}
        comment['user_name'] = page_source.find('a', {'class': 'userReview'}).get_text().strip()
        comment['date_cmt'] = page_source.find('span', {'itemprop': 'datePublished'}).get_text().strip()
        comment['num_stars'] = page_source.find('meta', {'itemprop': 'ratingValue'}).get('content').strip()
        comment['content'] = page_source.find('div', {'itemprop': 'reviewBody'}).get_text().strip()
        comment['num_likes'] = page_source.find('span', {'class': 'likesCount'}).get_text()[:-5].strip()
        replies = page_source.find_all('div', {'class': 'comment u-anchorTarget'})
        comment['replies'] = self.get_reply_content(replies)
        
        return comment

    def get_reply_content(self, replies):
        replies_list = []
        for reply_item in replies:
            print(reply_item)
            reply = {}
            reply['user_name'] = reply_item.find('span', {'class': 'commentAuthor'}).find('a').get_text().strip()        
            reply['date_reply'] = reply_item.find('div', {'class': 'brownBox '}).find('div', {'class': 'right'}).get('title')
            reply['content'] = reply_item.find('div', {'class': 'mediumText reviewText'}).get_text().strip()

            replies_list.append(reply)
        return replies_list


data_scraper = DataScraping()
data_scraper.search_for_author()
data_scraper.get_book_urls_multipages()
data_scraper.get_info_book()

