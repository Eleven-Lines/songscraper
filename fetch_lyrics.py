import sys
from searcher import (
    LyricsNotFoundError,
    MutipleLyricsSearcher,
    JLyricSearcher,
    UtanetSearcher,
    PetitLyricsSearcher,
    JLyricTitleSearcher
)

filename = sys.argv[1]

with open(filename) as f:
    for line in f:
        title, artist = line.rstrip("\n").split("\t")
        searcher = MutipleLyricsSearcher([
            JLyricSearcher,
            UtanetSearcher,
            PetitLyricsSearcher,
            JLyricTitleSearcher
        ], False)
        try:
            lyrics = searcher.fuzzy_title_search(artist, title)
        except LyricsNotFoundError:
            print(f"Lyrics not found: {title} - {artist}")
            continue
        print(f"Lyrics found: {title}_{artist}.txt")
        with open("lyrics/" + f"{artist}-{title}".replace("/", "_"), "w") as of:
            of.write(lyrics)
