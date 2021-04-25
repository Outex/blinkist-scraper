import dash
import os
import shutil
import webbrowser
import dash_core_components as dcc
import dash_bootstrap_components as dbc
import dash_html_components as html
from dash.dependencies import Input, Output, State
from subprocess import Popen
from bs4 import BeautifulSoup


CENTER_STYLE = {'textAlign':'center', 'margin':'auto'}
STYLESHEETS = [dbc.themes.BOOTSTRAP] #['https://codepen.io/chriddyp/pen/bWLwgP.css']
BLINK_PATH = 'D:/blinkist_scraper/books/'


class Interface:
    def __init__(self):
        self.app = self.create_app()

    def run(self):
        self.app.run_server(debug=True)  # use_reloader = False)


    def get_blink_list(self, cats = None):
        categories = os.listdir(BLINK_PATH)
        blinks = []
        for category in categories:
            if cats == None or category in cats:
                blinks += os.listdir(os.path.join(BLINK_PATH, category))
        return categories, blinks

    def get_cat_blink_dict(self):
        cat_dict = {}
        categories = os.listdir(BLINK_PATH)
        for category in categories:
            cat_dict[category] = os.listdir(os.path.join(BLINK_PATH, category))
        return cat_dict

    def get_cat_for_blink(self, blink):
        cat_dict = self.get_cat_blink_dict()
        for cat, blinks in cat_dict.items():
            if blink in blinks:
                return cat
        print('Something went really wrong here... You should not be here...')

    def get_blink_options(self, cats = None):
        categories, blinks = self.get_blink_list(cats)
        blink_opts = sorted([{'label':blink, 'value':blink} for blink in blinks], key= lambda x:x['label'])
        cat_opts = sorted([{'label':cat, 'value':cat} for cat in categories], key= lambda x:x['label'])
        return cat_opts, blink_opts

    def create_app(self):
        app = dash.Dash(__name__, external_stylesheets=STYLESHEETS, suppress_callback_exceptions=True)

        app.layout = html.Div([
            dcc.Location(id='url', refresh=False),
            html.Div(id='main_content'),
            html.Div(id='placeholder', children='')
        ])
        categories, blinks = self.get_blink_options()

        scaper_layout = html.Div([
        dbc.Row(dbc.Col(html.H1('Blinkist Scraper', style = CENTER_STYLE))),
        # FILTERS
        dbc.Row(html.H1('FILTER', style = CENTER_STYLE)),
        #TITLE SELECTION
        dbc.Row([
        dbc.Col(dcc.Dropdown(id='title_dropdown', options=blinks, placeholder='Select a title.'), width={'offset':1, 'size':8}, align='center'),
        dbc.Col(dbc.Button('Read', id='read_button', color='success'), width={'offset':0, 'size':1}, align='left'),
        dbc.Col(dbc.Button('Open Folder', id='folder_button', color='success'), width={'offset':0, 'size':1}, align='left'),
        dbc.Col(dbc.Button('Play', id='play_button', color='success'), width={'offset':0, 'size':1}, align='left')
        ]),
        #CATEGORY SELECTION
        dbc.Row([
        dbc.Col(dcc.Dropdown(id='category_dropdown', options=categories, placeholder='Select category.'), width={'offset':1, 'size':8}, align='center'),
        dbc.Col(dbc.Button('Refresh', id='refresh_button', color='success'), width={'offset':0, 'size':1}, align='left')
        ]),
        #ADD CATEGORIES
        dbc.Row([
        dbc.Col(dbc.Input(id='category_input', type='text', placeholder='Change category here.'), width={'offset':1, 'size':5}, align='center'),
        dbc.Col(dbc.Button('Change', id='change_category_button', color='success'), width={'offset':0, 'size':1}, align='center')
        ]),
        dbc.Row(dbc.Col(id='title_status_container', children='', width={'offset':1, 'size':8}, align = 'center')),
        #DAILY SCRAPER
        dbc.Row([
        dbc.Col(dbc.Button('Scrape daily Blinks', id='scrape_button', color='success'), width={'offset':1, 'size':2}, align='center'),
        dbc.Col([
        dbc.Col(id='scrape_status_container', children=''),
        dbc.Col(id='change_category_container', children=''),
        dbc.Col(id='dummy_container1', children=''),
        dbc.Col(id='dummy_container2', children='')
        ], width={'offset':0, 'size':6}, align = 'center')
        ])
        ])


        #SWITCH PAGE
        @app.callback(
        Output('main_content', 'children'),
        [Input('url', 'pathname')])
        def display_content(path):
            #print('Path', path)
            if path == '/' or path == None:
                content = scaper_layout
            elif path == '/blink':
                blink_contents, supplements = [], []
                for header, text in zip(self.bs.blink_data['headers'], self.bs.blink_data['contents']):
                    blink_contents.append(dbc.Row(dbc.Col(html.H4(header), width={'offset':1, 'size':8}, align = 'left')))
                    blink_contents.append(dbc.Row(dbc.Col(html.P(text, style={'text-align':'justify'}), width={'offset':1, 'size':10}, align = 'left')))
                    blink_contents.append(html.Br())

                if len(self.bs.blink_data['supplements']) > 0:
                    supplements.append(dbc.Row(dbc.Col(html.H4('Supplements'), width={'offset':1, 'size':8}, align = 'left')))
                    for supplement in self.bs.blink_data['supplements']:
                        supplements.append(dbc.Row(dbc.Col(html.P(supplement), width={'offset':1, 'size':10}, align = 'left')))

                blink_layout = html.Div([
                dbc.Row(html.H1(self.bs.blink_data['title'], style=CENTER_STYLE)),
                dbc.Row(html.H3('von {} ({} Minuten Lesedauer)'.format(self.bs.blink_data['author'], self.bs.blink_data['time']), style=CENTER_STYLE)),
                html.Br()
                ]+blink_contents+supplements)

                content = blink_layout

            else:
                raise ValueError('You´re on the wrong path... Get back on your track!')
            return content

        #REFRESH TITLE SELECTION
        @app.callback(
        [Output('title_dropdown', 'options'),
         Output('category_dropdown', 'options')],
        [Input('refresh_button', 'n_clicks')],
        [State('category_dropdown', 'value')])
        def refresh(click, categories):
            if categories == []:
                categories = None
            cat_options, blink_options = self.get_blink_options(categories)
            return blink_options, cat_options

        #SCRAPE DAILY BLINK
        @app.callback(
        Output('scrape_status_container', 'children'),
        [Input('scrape_button', 'n_clicks')])
        def scrape(click):
            if click != None:
                p = Popen("run.bat", cwd="../")
                stdout, stderr = p.communicate()
                notification = dbc.Alert(f'Successfully scraped the Blinks', color = 'success', style=CENTER_STYLE)
            else:
                notification = html.Div()
            return notification

        #READ SELECTED BLINK
        @app.callback(
        Output('title_status_container', 'children'),
        [Input('read_button', 'n_clicks')],
        [State('title_dropdown', 'value')]
        )
        def read(click, title):
            if click != None and title != None:
                blink_html = os.path.join(BLINK_PATH, self.get_cat_for_blink(title), title, title+'.html')
                cover = os.path.join(BLINK_PATH, self.get_cat_for_blink(title), title, 'cover.jpg')
                cover = os.path.realpath(cover)
                with open(blink_html, 'r', encoding='utf8') as file:
                    contents = file.read()
                    soup = BeautifulSoup(contents, 'lxml')
                soup.find('img')['src'] = cover
                with open(blink_html, 'w', encoding='utf8') as file:
                    file.write(str(soup))
                webbrowser.get('C:/Program Files (x86)/Google/Chrome/Application/chrome.exe %s').open(blink_html)
            return html.Div()


        #Change CATEGORY
        @app.callback(
        Output('change_category_container', 'children'),
        [Input('change_category_button', 'n_clicks')],
        [State('title_dropdown', 'value'),
         State('category_input', 'value')]
        )
        def change_cat(click, title, category):
            if click != None and title != None and category != None:
                cat = self.get_cat_for_blink(title)
                new_path = os.path.join(BLINK_PATH, category, title)
                old_path = os.path.join(BLINK_PATH, cat, title)
                if cat == category:
                    notification = dbc.Alert(f'{title} already is in the category {cat}.', color = 'warning', style=CENTER_STYLE)
                else:
                    if not os.path.isdir(os.path.join(BLINK_PATH, category)):
                        os.mkdir(os.path.join(BLINK_PATH, category))
                    shutil.move(old_path, new_path)
                    notification = dbc.Alert(f'Successfully changed category of {title} to {category}.', color = 'success', style=CENTER_STYLE)
                return notification
            return html.Div()

        #OPEN FOLDER OF BLINK
        @app.callback(
        Output('dummy_container1', 'children'),
        [Input('folder_button', 'n_clicks')],
        [State('title_dropdown', 'value')]
        )
        def open_folder(click, title):
            if click != None and title != None:
                blinkpath = os.path.join(BLINK_PATH, self.get_cat_for_blink(title), title)
                path = os.path.realpath(blinkpath)
                os.startfile(path)
            return html.Div()

        #OPEN FOLDER OF BLINK
        @app.callback(
        Output('dummy_container2', 'children'),
        [Input('play_button', 'n_clicks')],
        [State('title_dropdown', 'value')]
        )
        def open_folder(click, title):
            if click != None and title != None:
                blinkpath = os.path.join(BLINK_PATH, self.get_cat_for_blink(title), title, title+'.m4a')
                path = os.path.realpath(blinkpath)
                os.startfile(path)
            return html.Div()

        return app




def main():
    try:
        webbrowser.get('C:/Program Files (x86)/Google/Chrome/Application/chrome.exe %s').open('http://127.0.0.1:8050/')
    except Exception as e:
        print(e)
    interface = Interface()
    interface.run()



if __name__ == '__main__':
    main()
