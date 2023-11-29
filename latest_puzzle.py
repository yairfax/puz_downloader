from glob import glob
from datetime import datetime

def main():
    puzzles = glob('*.puz')

    dates = [datetime.strptime(f.replace('.puz', ''), '%b%d%y') for f in puzzles]

    max_date = max(dates)

    return f'The last puzzle you did was on {max_date.strftime("%B %d")}, which was a {max_date.strftime("%A")}'

if __name__ == "__main__":
    print(main())