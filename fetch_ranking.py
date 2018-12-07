import sys
import re
import itertools
import requests
from mojimoji import zen_to_han
from bs4 import BeautifulSoup

match_paren = re.compile(r"(\(.+\)|\(.+\)\[.+\])$")

def fetch_from_ranking(year):
    assert(len(year) == 6)
    r = requests.get(f"https://www.karatetsu.com/ranking/index.php?top_ym={year}")
    soup = BeautifulSoup(r.content, "html5lib")
    return [(match_paren.sub("", zen_to_han(s.select("td:nth-of-type(3)")[0].text, kana=False)),
             zen_to_han(s.select("td:nth-of-type(4)")[0].text, kana=False))
            for s in soup.select("#ranking tr")[2:]]


for i in itertools.product((str(x) for x in range(2008, 2019)[::-1]),
                           ("01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "12")):
    top_ym = "".join(i)
    try:
        result = fetch_from_ranking(top_ym)
    except:
        sys.stderr.write(f"{top_ym}: failed\n")
    if len(result) > 1:
        print("\n".join([f"{t}\t{a}" for t, a in result]))
    sys.stderr.write(f"{top_ym}: {len(result)}\n")
