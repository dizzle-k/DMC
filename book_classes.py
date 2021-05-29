import json
import pickle
import re
from types import SimpleNamespace

from fuzzywuzzy import fuzz


class DMCGenre:
    def __init__(self, dmc_books, dumpfile):
        self.dmc_books = dmc_books
        self.relevant_authors = self._retrieve_relevant_authors()
        self.dumpfile = dumpfile

        self.goodreads_books = None

    def _retrieve_relevant_authors(self):
        return set([b.author_lastname for b in self.dmc_books])

    def read_in_dump(self, authors):
        self.goodreads_books = parse_books_to_obj(
            self.dumpfile, authors, self.relevant_authors
        )

    def find_matches(self):
        c = 0
        t = len(self.dmc_books)
        for b in self.dmc_books:
            if b.author_lastname in self.goodreads_books.keys():
                find_match(b, self.goodreads_books[b.author_lastname])
                c += 1
                print(f"checked {c} of {t}", end="\r")

    def pickle(self, filename):
        with open(filename, "wb") as f:
            pickle.dump(self.dmc_books, f)


class DMCBook:
    def __init__(self, title, author, itemID, main_topic):
        self.title = title
        self.author = author
        self.author_lastname = self.get_author_lastname()
        self.itemID = itemID
        self.main_topic = main_topic

        self.goodreads_match = None

    def get_author_lastname(self):
        a = self.author.lower()
        a = re.sub("[()*]", " ", a)
        parts = a.split()
        return parts[0] if len(parts) > 0 else ""


class GoodreadsBook:
    def __init__(self, title, author, authors, isbn, book_id, lg, similar_books):
        self.title = title
        self.author = author
        self.all_authors = authors
        self.isbn = isbn
        self.book_id = book_id
        self.lg = lg
        self.similar_books = similar_books

    def __str__(self):
        return f"Title: {self.title}\nAuthors: {self.authors}\nISBN: {self.isbn}\nBook-ID: {self.book_id}\nLG: {self.lg}\nsimilar books: {self.similar_books}"


class GoodreadsAuthor:
    def __init__(self, name, author_id, books):
        self.name = name
        self.lastname = self._get_lastname()
        self.author_id = author_id
        self.books = books

    def _get_lastname(self):
        a = self.name.lower()
        a = re.sub("[()*]", " ", a)
        parts = a.split()
        return parts[0] if len(parts) > 0 else ""

    def __str__(self):
        return f"Name: {self.name}\nAuthor_ID: {self.author_id}"


def find_match(dmcb, goodreads_books):
    higher_match = False
    if dmcb.author_lastname == "":
        higher_match = True
    for grb in goodreads_books:
        ratio = fuzz.ratio(dmcb.title.lower(), grb.title.lower())
        if ratio < 95:
            partial_ratio = fuzz.partial_ratio(dmcb.title.lower(), grb.title.lower())
            if partial_ratio < 85:
                continue
            else:
                if higher_match:
                    if partial_ratio < 95:
                        continue
        dmcb.goodreads_match = grb


def parse_books_to_obj(filename, all_authors, relevant_authors):
    """Read in goodreads genre dump"""
    books_by_author = {}
    with open(filename, "r") as f:
        c = 0
        for jsonObj in f:
            b = json.loads(jsonObj, object_hook=lambda d: SimpleNamespace(**d))

            # match authorID with name
            a_obj = None
            try:
                main_authorID = b.authors[0].author_id
                if all_authors[main_authorID]:
                    a_obj = all_authors[main_authorID]
                    lastname = a_obj.lastname

                    # discard books with irrelevant authors
                    if lastname in relevant_authors:
                        grb = GoodreadsBook(
                            b.title,
                            a_obj,
                            b.authors,
                            b.isbn,
                            b.book_id,
                            b.language_code,
                            b.similar_books,
                        )
                        if lastname in books_by_author:
                            books_by_author[lastname].append(grb)
                        else:
                            books_by_author[lastname] = [grb]
            except IndexError:
                # print("book without author")
                pass
            c += 1
            if c % 100 == 0:
                print(f"read {c} books", end="\r")

    return books_by_author
