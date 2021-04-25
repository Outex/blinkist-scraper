"""
from blinkistscraper import BlinkistScraper
import os

t = ('tit', 'auth', 'lang',)
bs.get_file_name()

bs = BlinkistScraper()
bs.db.remove_blink('heino_falcke_&_jã¶rg_rã¶mer_licht_im_dunkeln_DE')
print(bs.db)


bs.load_blink(files[0])

bs.get_daily_blink('DE')

bs.add_category('Klimaerwärmung')
bs.excel_string_to_clipboard()

print(bs.db)
files = os.listdir('./json')



s = '\'ok\"'
s
s.strip('\" \'')
"""


import sys
sys.path.insert(0, '../blinkistscraper')
from main import _main as scrape
import random



class Arguments:
    pass

args = Arguments()

args.email = 'Magana1111@web.de'
args.password = 'Magana1111'
args.language = 'en'
args.verbose = False
args.create_html = True
args.create_epub = True
args.create_pdf = True
args.audio = True
args.concat_audio = True
args.embed_cover_art = True
args.keep_noncat = False
args.save_cover = True
args.no_scrape = True
args.match_language = False
args.headless = False
args.chromedriver = None
args.book = False
args.daily_book = True
args.book_category = 'Uncategorized'
args.books = False
args.cooldown = random.randint(5,15)
args.categories = ''
args.ignore_categories = ''

pb = scrape(args)
print(pb)



sys.path
