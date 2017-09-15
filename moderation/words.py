__author__ = 'Daniel Nikulin'


def read_words(words_file):
    return [word for line in open(words_file, 'r', encoding='utf-8') for word in line.split()]


forbidden_words = read_words("moderation/swear_words.txt")
forbidden_words_full = read_words("moderation/forbidden_roots.txt")
