from bs4 import BeautifulSoup as bs
import os
import pyperclip
from datetime import datetime
import json

from blinkdb import BlinkDB

BASE_LINK = 'https://www.blinkist.com'
#DAILY_LINK_DE = 'https://www.blinkist.com/de/nc/daily'
#DAILY_LINK_EN = 'https://www.blinkist.com/en/nc/daily'
FEEDBACK_PHRASE = 'remember@blinkist.com'
BASE_PATH = './BlinkHTML/'

class BlinkistScraper:

    def __init__(self):
        self.current_main_html = None
        self.current_blink_html = None
        self.blink_data = {}
        self.db = BlinkDB()

    def get_daily_blink(self, platform, fresh = True):
        self.blink_data = {}
        self.blink_data['lang'] = platform

        main_link = BASE_PATH + 'PRE_{}.html'.format(platform)
        blink_link = BASE_PATH + 'MAIN_{}.html'.format(platform)

        with open(main_link, 'r', encoding='utf8') as file:
            content = file.read()

        if fresh or self.current_main_html == None:
            main_html = content
            self.current_main_html = content
        else:
            main_html = self.current_main_html


        main_soup = bs(main_html, 'html.parser')
        full_title = main_soup.find(class_ = 'daily-book__headline').getText()
        title_list = full_title.split(' ')
        for i in range(len(title_list)):
            title_list[i] = title_list[i].strip(' \n \" \'!?*')
        self.blink_data['title'] = ' '.join(title_list).strip(' ')
        self.blink_data['author'] = main_soup.find(class_ = 'daily-book__author').getText().strip(' \n von by')
        self.blink_data['time'] = main_soup.find(class_ = 'book-stats__label').getText().strip(' \n Lesedauer : Min -minute read')
        self.blink_data['blink_link'] = BASE_LINK + main_soup.find(class_ = 'daily-book__cta')['href']

        #check if we already scraped that blink (if yes just load it)
        file_name = self.get_file_name()
        if self.db.blink_exists(file_name):
            self.load_blink(file_name)
            return


        with open(blink_link, 'r', encoding='utf8') as file:
            content = file.read()
        if fresh or self.current_blink_html == None:
            blink_html = content
            self.current_blink_html = content
        else:
            blink_html = self.current_blink_html


        blink_soup = bs(blink_html, 'html.parser')
        content_container = blink_soup.find(class_ = 'reader__container__content').select('article > div')
        blink_headers, blink_contents, blink_supplements = [], [], []
        for chapter in content_container:
            if 'reader__container__buttons' in chapter['class']:
                continue
            if 'supplement' in chapter['class']:
                sup = chapter.div.get_text()
                blink_supplements.append(sup)
                continue
            h1 = chapter.h1.get_text()
            ps = chapter.div.get_text()
            if FEEDBACK_PHRASE in ps:
                pos = ps.find(FEEDBACK_PHRASE)
                pos2 = ps[:pos-1].rfind('\n')
                ps = ps[:pos2]
                pos2 = ps[:pos-1].rfind('\n')
                ps = ps[:pos2]
                pos3 = ps.find('\n')
                ps = ps[pos3+1:]
            blink_headers.append(h1)
            blink_contents.append(ps)

        self.blink_data['headers'] = blink_headers
        self.blink_data['contents'] = blink_contents
        self.blink_data['supplements'] = blink_supplements
        self.blink_data['category'] = []
        self.blink_data['favorite'] = 0

        self.add_to_db()

    def add_to_db(self):
        self.db.add_blink(self.blink_data, self.get_file_name())
        self.save_blink()

    def remove_from_db(self):
        self.db.remove_blink(self.get_file_name())

    def set_favorite(self, fav=0):
        self.blink_data['favorite'] = fav
        self.db.set_favorite(self.get_file_name(), fav)
        self.save_blink()

    def add_category(self, category_str):
        categories = category_str.split(' ')
        successful = 0
        for category in categories:
            if category not in self.blink_data['category']:
                self.blink_data['category'].append(category)
                self.db.add_category(category, self.blink_data, self.get_file_name())
                self.save_blink()
                print(f'The category {category} was added.')
                successful += 1
            else:
                print(f'The category {category} already exists.')
        return successful


    def remove_category(self, category_str):
        categories = category_str.split(' ')
        successful = 0
        for category in categories:
            try:
                self.blink_data['category'].remove(category)
                self.db.remove_category(self.get_file_name(), category)
                self.save_blink()
                successful += 1
            except:
                print('Category not found.')
        return successful


    def get_category_str(self):
        return ', '.join(sorted(self.blink_data['category']))

    def get_file_name(self, title=None, author=None, lang=None):
        if title == None:
            title = '_'.join(self.blink_data['title'].split()).lower()
        else:
            title = '_'.join(title.split()).lower()
        if author == None:
            author = '_'.join(self.blink_data['author'].split()).lower()
        else:
            author = '_'.join(author.split()).lower()
        if lang == None:
            lang = self.blink_data['lang']
        return f'{author}_{title}_{lang}'

    def get_excel_string(self):
        if len(self.blink_data) == 0:
            print('Please load the Blinks first..')
            return None
        else:
            title = self.blink_data['title']
            author = self.blink_data['author']
            lang = self.blink_data['lang']
            date = datetime.now().strftime('%d.%m.%Y')
            category = 'KATEGORIE' if len(self.blink_data['category']) == 0 else self.get_category_str()
            wrap = self.blink_data['contents'][-1].replace('\n', '   ')
            heads = '   '.join(self.blink_data['headers'][1:-1])
            return '{}\t{}\t{}\t{}\t\t{}\t{}\t{}'.format(title, author, lang, date, category, wrap, heads) #date neets two tabs.. whyever...

    def excel_string_to_clipboard(self):
        ex_str = self.get_excel_string()
        if ex_str != None:
            pyperclip.copy(ex_str)
            print('COPIED DATA TO CLIPBOARD!')
        else:
            raise ValueError('Something went wrong when trying to copy the data for excel to the clipboard..')

    def save_blink(self, format = 'json'):
        if len(self.blink_data) == 0:
            print('Cannot save empty Blink Dict.. Please load the Blink first!')
            return
        if format == 'json':
            file_name = './json/{}.json'.format(self.get_file_name())
            with open(file_name, 'w') as json_file:
                json.dump(self.blink_data, json_file)
        else:
            raise NotImplementedError(f'Blink saving for the {format} format is not implemented yet.')
        print('DONE SAVING!')

    def load_blink(self, name, format = 'json'):
        if format == 'json':
            file_name = f'./json/{name}'
            file_name = file_name+'.json' if not file_name.endswith('.json') else file_name
            with open(file_name, 'r') as json_file:
                self.blink_data = json.load(json_file)
        else:
            raise NotImplementedError(f'Blink loading for the {format} format is not implemented yet.')
        print('Loaded Blinks for {}'.format(self.blink_data['title']))
