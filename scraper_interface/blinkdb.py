import sqlite3
from operator import itemgetter

CREATE_BLINKS = 'CREATE TABLE IF NOT EXISTS blinks (id integer PRIMARY KEY, title text NOT NULL, author text NOT NULL, lang text NOT NULL, category text NOT NULL, filename text NOT NULL, favorite integer NOT NULL);'
DATABASE = 'blinks.db'

class BlinkDB:
    def __init__(self):
        self.create_db()

    def __str__(self):
        db_str = 'DATABASE CONTENT:\n'
        template = '|{0:30}|{1:20}|{2:4}|{3:20}|{4:40}|{5:3}|\n'
        db_str += template.format('TITLE', 'AUTHOR', 'LANG', 'CATEGORY', 'FILE', 'FAV')
        with sqlite3.connect(DATABASE) as conn:
            c = conn.cursor()
            c.execute('SELECT * FROM blinks')
            rows = c.fetchall()
            for r in rows:
                db_str += template.format(*(r[1:]))
        return db_str

    def create_db(self):
        with sqlite3.connect(DATABASE) as conn:
            c = conn.cursor()
            c.execute(CREATE_BLINKS)
            conn.commit()

    def add_blink(self, blink_data, file_name):
        if self.blink_exists(file_name):
            print('That Blink was already added to the database!')
            return
        with sqlite3.connect(DATABASE) as conn:
            c = conn.cursor()
            if len(blink_data['category']) > 0:
                for category in blink_data['category']:
                    c.execute('INSERT INTO blinks (title, author, lang, category, filename, favorite) VALUES (?,?,?,?,?,?)', (blink_data['title'], blink_data['author'], blink_data['lang'], category, file_name, blink_data['favorite']))
            else:
                c.execute('INSERT INTO blinks (title, author, lang, category, filename, favorite) VALUES (?,?,?,?,?,?)', (blink_data['title'], blink_data['author'], blink_data['lang'], '', file_name, blink_data['favorite']))
            conn.commit()

    def blink_exists(self, file_name):
        with sqlite3.connect(DATABASE) as conn:
            c = conn.cursor()
            c.execute('SELECT filename FROM blinks WHERE filename=?', (file_name,))
            rows = c.fetchall()
            conn.commit()
            return len(rows) > 0

    def remove_blink(self, file_name):
        with sqlite3.connect(DATABASE) as conn:
            c = conn.cursor()
            c.execute('SELECT * FROM blinks WHERE filename=?', (file_name,))
            rows = c.fetchall()
            if len(rows) == 0:
                notification = 'Already removed {}.'.format(file_name)
            else:
                c.execute('DELETE FROM blinks WHERE filename=?', (file_name,))
                notification = 'Successfully removed {} from the database.'.format(file_name)
            print(notification)
            conn.commit()


    def set_favorite(self, file_name, fav):
        with sqlite3.connect(DATABASE) as conn:
            c = conn.cursor()
            c.execute('UPDATE blinks SET favorite = ? WHERE filename=?', (fav, file_name))
            conn.commit()


    def add_category(self, category, blink_data, file_name):
        with sqlite3.connect(DATABASE) as conn:
            c = conn.cursor()
            c.execute('SELECT category FROM blinks WHERE filename=?', (file_name,))
            rows = c.fetchall()
            if ('',) in rows:
                c.execute('UPDATE blinks SET category = ? WHERE filename=? AND category=?', (category, file_name, ''))
                notification = 'Successfully added category {} to {}.'.format(category, file_name)
            elif category in rows:
                notification = 'Category {} was already added to {}.'.format(category, file_name)
            else:
                c.execute('INSERT INTO blinks (title, author, lang, category, filename, favorite) VALUES (?,?,?,?,?,?)', (blink_data['title'], blink_data['author'], blink_data['lang'], category, file_name, blink_data['favorite']))
                notification = 'Successfully added category {} to {}.'.format(category, file_name)
            print(notification)
            conn.commit()


    def remove_category(self, file_name, category):
        with sqlite3.connect(DATABASE) as conn:
            c = conn.cursor()
            c.execute('SELECT category FROM blinks WHERE filename=?', (file_name,))
            rows = c.fetchall()
            if not (category,) in rows:
                notification = 'Already removed {}.'.format(file_name)
            elif len(rows) < 2:
                c.execute('UPDATE blinks SET category = ? WHERE filename=? AND category=?', ('', file_name, category))
                notification = 'Successfully removed category {} from {}.'.format(category, file_name)
            else:
                c.execute('DELETE FROM blinks WHERE filename=? AND category=?', (file_name, category))
                notification = 'Successfully removed category {} from {}.'.format(category, file_name)
            print(notification)
            conn.commit()

    def get_filtered(self, categories=None, favorite=None, langs=None):
        title_dropdown_data = []
        with sqlite3.connect(DATABASE) as conn:
            c = conn.cursor()
            if categories == None and favorite == None and langs == None: #Just get all blinks
                c.execute('SELECT title, author, lang FROM blinks')
            else: #use filters
                if langs == None:
                    langs = ['DE', 'EN']
                if categories == None:
                    categories = self.get_categories()
                cat = ','.join('?'*len(categories))
                lan = ','.join('?'*len(langs))
                if favorite:
                    c.execute('SELECT title, author, lang FROM blinks WHERE category IN ({}) AND lang IN ({}) AND favorite=?'.format(cat, lan), tuple(categories+langs+[1]))
                else:
                    c.execute('SELECT title, author, lang FROM blinks WHERE category IN ({}) AND lang IN ({})'.format(cat, lan), tuple(categories+langs))
            rows = list(set(c.fetchall())) #remove duplicates
            for title, author, lang in rows:
                title_dropdown_data.append({'label': f'{title} ({author}) {lang}', 'value':self.get_file_name(title, author, lang)})
            conn.commit()
        return sorted(title_dropdown_data, key=lambda x:x['label'])

    def get_categories(self):
        categories = set()
        with sqlite3.connect(DATABASE) as conn:
            c = conn.cursor()
            c.execute('SELECT category FROM blinks')
            rows = c.fetchall()
            for r in rows:
                categories.add(r[0])
            conn.commit()
        try:
            categories.remove('')
        except:
            pass
        categories = sorted(list(categories))
        return [{'label':cat, 'value':cat} for cat in categories] # categories


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
