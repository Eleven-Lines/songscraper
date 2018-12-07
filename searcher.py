import re
import requests
from abc import ABCMeta, abstractmethod
from bs4 import BeautifulSoup


class LyricsNotFoundError(RuntimeError):
    pass


class LyricsSearcher(metaclass=ABCMeta):
    """
    Abstract base class for lyrics searcher classes.
    Inherit this class to implement searcher.

    Attributes
    ----------
    artist : str
        Artist to search.
    title : str
        Title to search.
    strict : bool, optional
        Check artist name strictly or not.
    """
    def __init__(self, artist, title, strict=True):
        self.artist = artist
        self.title = self.preprocess_title(title)
        self.strict = strict

    @property
    @abstractmethod
    def search_result_css_selector(self):
        """str: Selector query for search result container in search page. """
        pass

    @property
    @abstractmethod
    def search_result_artist_css_selector(self):
        """str: Selector query for artist name in search result container. """
        pass

    @property
    @abstractmethod
    def search_result_lyrics_link_css_selector(self):
        """str: Selector query for link to lyrics page in search result container. """
        pass

    @property
    @abstractmethod
    def lyrics_base_url(self):
        """str: Base url for lyrics page."""
        pass

    @property
    @abstractmethod
    def lyrics_css_selector(self):
        """str: Selector query for lyrics container in lyrics page."""
        pass

    @property
    @abstractmethod
    def search_url(self):
        """str: Url for search."""
        pass

    def preprocess_title(self, title):
        """
        Preprocessor for title. Override this to preprocess user's input.

        Parameters
        ----------
        title: str
            Title to preprocess.

        Returns
        ----------
        title: str
            Preprocessed title.
        """
        return title

    def preprocess_artist(self, artist):
        """
        Preprocessor for artist name. Override this to preprocess user's input.

        Parameters
        ----------
        artist: str
            Artist to preprocess.

        Returns
        ----------
        artist: str
            Preprocessed artist name.
        """
        return artist

    def postprocess(self, target):
        """
        Postprocessor for lyrics. Override this to postprocess the result lyrics.

        Parameters
        ----------
        target: str
            Lyrics to postprocess.

        Returns
        ----------
        target: str
            Postprocessed lyrics.
        """
        return target

    def find_lyrics_link(self, candidates):
        """
        Find lyrics link from list of search result container.

        Parameters
        ----------
        candidates: bs4.element.Tag[]
            List of tag instance of search result container.

        Returns
        ----------
        suggested_url: str
            suggested url of lyrics.
        """
        for candidate in candidates:
            link_selector = self.search_result_lyrics_link_css_selector
            artist_selector = self.search_result_artist_css_selector

            if not candidate.select_one(artist_selector):
                continue

            suggested_artist = candidate.select_one(artist_selector).text
            suggested_url = (self.lyrics_base_url
                             + candidate.select_one(link_selector).get("href"))

            # if candidates contains exactly one result,
            # just check match for 1st character
            if (len(candidates) == 1
                    and suggested_artist[0].lower() == self.artist[0].lower()):
                return suggested_url
            # validate artist
            elif suggested_artist == self.artist:
                return suggested_url
            # non-strict mode
            elif (not self.strict
                  and suggested_artist[0].lower() == self.artist[0].lower()):
                return suggested_url
        raise LyricsNotFoundError

    def get_lyrics_url(self):
        """
        Fetches lyrics url and return it.

        Returns
        ----------
        lyrics_url: str
            Url of lyrics page.
        """
        r = requests.get(self.search_url)
        soup = BeautifulSoup(r.content, "lxml")
        # filter result page
        candidates = soup.select(self.search_result_css_selector)
        return self.find_lyrics_link(candidates)

    def get_lyrics(self):
        """
        Fetches lyrics and return it.

        Returns
        ----------
        lyrics: str
            Lyrics for the song specified in constructor.
        """
        r = requests.get(self.get_lyrics_url())
        soup = BeautifulSoup(r.content, "lxml")
        # extract lyrics
        extracted = soup.select_one(self.lyrics_css_selector)
        # postprocess extracted lyrics block
        return self.postprocess(str(extracted))

    # Utils
    def remove_surrounding(self, tag, target):
        """
        Remove surrounding tag from target string.

        Parameters
        -----------
        tag: str
            A tag to remote.
        target: str
            A target HTML element.

        Returns
        ----------
        processed: str
            An unwrapped target.
        """
        return re.sub(f'(<{tag}.*?>|</{tag}>)', '', target)

    def remove_p(self, target):
        return self.remove_surrounding("p", target)

    def remove_div(self, target):
        return self.remove_surrounding("div", target)

    def replace_br(self, target):
        close_removed = re.sub('</br>', '', target)
        return re.sub('(<br>|<br/>)', '\n', close_removed)


class UtanetSearcher(LyricsSearcher):
    # Full match of title
    @property
    def search_url(self):
        return (f"https://www.uta-net.com/search/"
                f"?Aselect=2&Keyword={self.title}&Bselect=4&x=0&y=0")

    @property
    def search_result_css_selector(self):
        return '#ichiran .result_table table tbody tr'

    @property
    def lyrics_css_selector(self):
        return '#kashi_area'

    @property
    def search_result_artist_css_selector(self):
        return ".td2 a"

    @property
    def search_result_lyrics_link_css_selector(self):
        return ".td1 a"

    @property
    def lyrics_base_url(self):
        return "https://www.uta-net.com"

    def postprocess(self, target):
        target = self.remove_div(target)
        target = self.replace_br(target)
        return target


class JLyricSearcher(LyricsSearcher):
    # Forward match of title, artist
    @property
    def search_url(self):
        return (f"http://search.j-lyric.net/index.php"
                f"?kt={self.title}&ct=2&ka={self.artist}&ca=2")

    @property
    def search_result_css_selector(self):
        return '#bas #cnt #mnb .bdy'

    @property
    def lyrics_css_selector(self):
        return '#Lyric'

    @property
    def search_result_artist_css_selector(self):
        return ".sml a"

    @property
    def search_result_lyrics_link_css_selector(self):
        return ".mid a"

    @property
    def lyrics_base_url(self):
        return ""

    def postprocess(self, target):
        target = self.remove_p(target)
        target = self.replace_br(target)
        return target


class JLyricTitleSearcher(JLyricSearcher):
    # Forward match of title
    @property
    def search_url(self):
        return (f"http://search.j-lyric.net/index.php"
                f"?kt={self.title}&ct=2&ka=&ca=2")


class PetitLyricsSearcher(LyricsSearcher):
    # Full match of title
    @property
    def search_url(self):
        return (f"https://petitlyrics.com/search_lyrics?title={self.title}")

    @property
    def search_result_css_selector(self):
        return '#lyrics_list tr'

    @property
    def lyrics_css_selector(self):
        return '#lyrics'

    @property
    def search_result_artist_css_selector(self):
        return "td:nth-of-type(2) a:nth-of-type(2)"

    @property
    def search_result_lyrics_link_css_selector(self):
        return "td:nth-of-type(2) a:nth-of-type(1)"

    @property
    def lyrics_base_url(self):
        return "https://petitlyrics.com/"

    def postprocess(self, target):
        target = self.remove_div(target)
        target = self.replace_br(target)
        target = self.remove_surrounding("canvas", target)
        return target


class MutipleLyricsSearcher:
    def __init__(self, searcher_classes, strict=True):
        self.searcher_classes = searcher_classes
        self.strict = strict

    def search(self, artist, title):
        for searcher in self.searcher_classes:
            try:
                return searcher(artist, title, strict=self.strict).get_lyrics()
            except LyricsNotFoundError:
                pass
        raise LyricsNotFoundError

    def fuzzy_title_search(self, artist, title):
        fuzzy_titles = [title]

        if "？"in title or "！" in title:
            halfwidth_title = title.replace("？", "?").replace("！", "!")
            fuzzy_titles.append(halfwidth_title)

        if "?"in title or "!" in title:
            fullwidth_title = title.replace("?", "？").replace("!", "！")
            fuzzy_titles.append(fullwidth_title)

        for title in fuzzy_titles:
            try:
                return self.search(artist, title)
            except LyricsNotFoundError:
                pass
        raise LyricsNotFoundError
