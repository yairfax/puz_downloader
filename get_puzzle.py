import puz
import requests
import json
import argparse
import re
import html

num_re = re.compile(r'^(\d{1,3})\. ')
months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", required=True, action="store")
    return parser.parse_args()

def get_puzzle_json(date):
    req = requests.get("https://www.xwordinfo.com/JSON/Data.aspx", params={'date': date, "format": "text"},
        headers={'Referer': 'https://www.xwordinfo.com/JSON/'})

    data = json.loads(req.text)
    return data

def get_filename(date):
    month, day, year = date.split('/')
    return months[int(month) - 1] + day + year[2:] + ".puz"

def generate_puz(puz_json):
    p = puz.Puzzle()
    p.title = puz_json['title']
    p.author = f"{puz_json['author']} / {puz_json['editor']}"
    p.copyright = puz_json['copyright']
    p.notes = puz_json['notepad']
    p.width = int(puz_json['size']['cols'])
    p.height = int(puz_json['size']['rows'])
    p.fill = "".join(char if char == '.' else '-' for char in puz_json['grid'])
    p.solution = "".join(puz_json['grid'])
    p.clues = make_clue_list(puz_json['clues']['across'], puz_json['clues']['down'])

    return p

def make_clue_list(across, down):
    across = [(html.unescape(num_re.sub('', clue)), int(num_re.findall(clue)[0])) for clue in across]
    down = [(html.unescape(num_re.sub('', clue)), int(num_re.findall(clue)[0])) for clue in down]

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
    puz_file = generate_puz(get_puzzle_json(args.date))

    puz_file.save(get_filename(args.date))

if __name__ == "__main__":
    main(get_args())