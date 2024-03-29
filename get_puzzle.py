import puz
import requests
import json
import argparse
import re
import html
from datetime import date, timedelta
from os.path import isfile


num_re = re.compile(r'^(\d{1,3})\. ')
months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
days = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']

def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", action="store")
    return parser.parse_args()

def get_date(date_str: str):
    date_str = date_str or ""
    date_str = date_str.lower()
    today = date.today()
    date_obj = None
    match date_str.split('/'):
        case [""] | ["today"]:
            date_obj = today
        case [x] if x[:3] in days or x.startswith('sha'):
            x = x[:3]
            if x == "sha":
                x = "sat"
            today_ind = today.weekday()
            date_ind = days.index(x)
            delta = (today_ind - date_ind) % 7
            date_obj = today - timedelta(delta)
        case [month, day] if is_date_number(month, day):
            date_obj = date(today.year, int(month), int(day))
        case [month, day, year] if is_date_number(month, day, year):
            date_obj = date(2000 + int(year), int(month), int(day))
        case [month, day, year] if is_date_number(month, day) and re.fullmatch(r'\d{4}', year):
            date_obj = date(int(year), int(month), int(day))

    return date_obj and date_obj.strftime("%m/%d/%Y")

def is_date_number(*num_str):
    return all(re.fullmatch(r'\d{1,2}', day_str) for day_str in num_str)

def get_puzzle_json(date):
    req = requests.get("https://www.xwordinfo.com/JSON/Data.ashx", params={'date': date, "format": "text"},
        headers={'Referer': 'https://www.xwordinfo.com/JSON/'})

    data = json.loads(req.text)
    return data

def get_filename(date):
    month, day, year = date.split('/')
    return months[int(month) - 1] + day + year[2:] + ".puz"

def generate_puz(puz_json):
    p = puz.Puzzle()
    p.title = puz_json['title']
    p.author = f"{sanitize_bad_chars(puz_json['author'])} / {puz_json['editor']}"
    p.copyright = puz_json['copyright']
    p.width = int(puz_json['size']['cols'])
    p.height = int(puz_json['size']['rows'])
    p.fill = "".join(char if char == '.' else ('X' if len(char) > 1 else '-') for char in puz_json['grid'])
    p.solution = "".join(char if len(char) == 1 else 'X' for char in puz_json['grid'])
    p.notes = sanitize_bad_chars(get_notes(puz_json))
    p.clues = make_clue_list(puz_json)
    if puz_json['shadecircles'] or ("circles" in puz_json and puz_json["circles"]):
        p.markup().markup = fill_circles(puz_json)

    return p

def sanitize_bad_chars(string):
    return string.encode('latin-1', 'replace').decode('latin-1')

def get_notes(p):
    notes = p['notepad'] or ""

    if 'jnotes' in p and p['jnotes']:
        notes += "\n\nNotes from API author: " + p['jnotes']

    replaced_words = [word for word in p['grid'] if len(word) > 1]
    if len(replaced_words) > 1:
        notes += "\n\nNote from the coder: The following words were replaced with Xs from the puzzle's source JSON, in order: " + ", ".join(replaced_words)

    return notes

def fill_circles(p):
    return [puz.GridMarkup.Circled if c else 0 for c in p['circles']]

def get_numbering(b, cols):
    across = []
    down = []
    counter = 1
    inc = False
    for i, l in enumerate(b):
        if l == '.':
            continue

        # TODO: fix case of final space with black on left, and transpose
        if i % cols == 0 or (b[i - 1] == '.' and b[i + 1] != '.'):
            across += [counter]
            inc = True
        
        if i < cols or (b[i - cols] == '.' and b[i + cols] != '.'):
            down += [counter]
            inc = True
        
        if inc:
            counter += 1
            inc = False

    return across, down

def unescape(clue):
    clue = num_re.sub('', clue)
    clue = html.unescape(clue)
    clue = clue.replace('\u2026', '...')

    clue = "".join(c.encode('ISO-8859-1', 'namereplace').decode('ISO-8859-1', 'namereplace') for c in clue)

    return clue

def get_clue_map(p):
    across = {num_re.findall(clue)[0]: unescape(clue) for clue in p['clues']['across']}
    down = {num_re.findall(clue)[0]: unescape(clue) for clue in p['clues']['down']}

    return across, down

def prep_clues(p):
    across, down = get_clue_map(p)
    nums_across, nums_down = get_numbering(p['grid'], p['size']['cols'])

    across = [(across[str(i)] if str(i) in across else "NO CLUE FOUND", i) for i in nums_across]
    down = [(down[str(i)] if str(i) in down else "NO CLUE FOUND", i) for i in nums_down]

    return across, down

def make_clue_list(p):
    across, down = prep_clues(p)

    out = []

    i_a, i_d = (0, 0)
    while i_a < len(across) or i_d < len(down):
        if i_a < len(across) and (i_d >= len(down) or across[i_a][1] <= down[i_d][1]):
            out += [across[i_a][0]]
            i_a += 1
        elif i_d < len(down):
            out += [down[i_d][0]]
            i_d += 1

    return out

def main(args):
    date = get_date(args.date)
    filename = get_filename(date)

    if not isfile(filename):
        puz_file = generate_puz(get_puzzle_json(date))
        puz_file.save(filename)
    print(filename)

if __name__ == "__main__":
    main(get_args())
