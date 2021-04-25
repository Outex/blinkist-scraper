import nltk
from nltk import tokenize
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize

from operator import itemgetter
import math

class KeywordExtractor:
    def __init__(self, lang='english'):
        self.set_lang(lang)

    def set_lang(self, lang):
        if lang in ['EN', 'english']:
            lang = 'english'
        elif lang in ['DE', 'german']:
            lang = 'german'
        self.lang = lang
        self.stop_words = stopwords.words(lang)

    def predict(self, text, n=5):
        #https://www.analyticsvidhya.com/blog/2020/11/words-that-matter-a-simple-guide-to-keyword-extraction-in-python/
        total_words = text.split()
        total_sentences = tokenize.sent_tokenize(text)
        print(f'The text has {len(total_words)} words and {len(total_sentences)} sentences.')

        tf_score = self.get_tf_score(total_words)
        idf_score = self.get_idf_score(total_words, total_sentences)

        tf_idf_score = {key: tf_score[key] * idf_score.get(key, 0) for key in tf_score.keys()}

        result = dict(sorted(tf_idf_score.items(), key = itemgetter(1), reverse = True)[:n])
        return result

    def get_tf_score(self, words):
        tf_score = {}
        for word in words:
            word = word.replace('.','')
            if word not in self.stop_words:
                if word in tf_score:
                    tf_score[word] += 1
                else:
                    tf_score[word] = 1

        tf_score.update((x, y/len(words)) for x, y in tf_score.items())
        return tf_score

    def get_idf_score(self, words, sentences):
        def check_sentences(word, sentences):
            final = [all([w in x for w in word]) for x in sentences]
            sentence_len = [sentences[i] for i in range(0, len(final)) if final[i]]
            return len(sentence_len)

        idf_score = {}
        for word in words:
            word = word.replace('.','')
            if word not in self.stop_words:
                if word in idf_score:
                    idf_score[word] = check_sentences(word, sentences)
                else:
                    idf_score[word] = 1

        # Performing a log and divide
        idf_score.update((x, math.log(len(sentences)/y)) for x, y in idf_score.items())
        return idf_score
