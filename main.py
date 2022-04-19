import webbrowser
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import requests
from bs4 import BeautifulSoup
from colorama import init
from colorama import Fore

FAKE_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}

VIDEO_PRIORITY_LIST = [
    "1080p",
    "720p",
]

MAP_SHOWS_WITH_DAY: dict[int, list[str]] = {
    0: ['WWE RAW'],
    2: ['AEW Dynamite'],
    4: ['WWE SmackDown', 'AEW Rampage']
}

PIRATE_BAY_SITES: [str] = [
    lambda x: f"https://www1.thepiratebay3.to/s/?q={x.replace(' ', '+')}",
    lambda x: f"http://thepiratebay.party/search/{x.replace(' ', '%20')}/1/99/0",
]

LATEST_SHOW_DATE = None


def get_latest_show(back_to: int = 0) -> tuple[list[str], datetime]:
    date = datetime.utcnow().replace(tzinfo=ZoneInfo("America/Los_Angeles")) - timedelta(days=back_to)
    try:
        shows = MAP_SHOWS_WITH_DAY[date.weekday()]
        return shows, date
    except KeyError:
        return get_latest_show(back_to + 1)


def has_date_in_title(title: str, date: datetime) -> bool:
    title = title.lower()
    """Check if show has date in title"""
    if date.strftime("%Y") in title and date.strftime("%m") in title and date.strftime("%d") in title:
        for video_resolution in VIDEO_PRIORITY_LIST:
            if video_resolution in title:
                return True


def get_shows_from_piratebay_html(html: str, current_date) -> [str]:
    """Parse piratebay html and return list of shows"""
    date = current_date
    shows = []
    bs4 = BeautifulSoup(html, 'html.parser')
    search_result = bs4.find("table", {"id": "searchResult"})
    if search_result is None:
        return []
    for row in search_result.find_all("tr"):
        tds = row.find_all("td")
        if tds is None:
            continue
        if len(tds) < 3:
            continue
        try:
            show_name = tds[1].find("a").text
        except AttributeError:
            continue
        show_url = tds[3].find("a")['href']
        seeders = int(tds[5].text)

        if has_date_in_title(show_name, date):
            shows.append({"name": show_name, "url": show_url, "seeders": seeders})

    return shows


def get_color_by_show_name(name) -> Fore:
    if "raw" in name.lower():
        return Fore.RED
    elif "rampage" in name.lower():
        return Fore.YELLOW
    elif "smackdown" in name.lower():
        return Fore.BLUE
    elif "dynamite" in name.lower():
        return Fore.YELLOW
    else:
        return Fore.WHITE


def find_data_from_piratebay() -> [str]:
    """Crawl piratebay website with search terms and return list of shows"""
    shows, date = get_latest_show()
    total_episodes = []
    for show in shows:
        show_name = show + f" {date.year} {date.strftime('%m')} {date.day}"
        for site in PIRATE_BAY_SITES:
            url = site(show_name)
            r = requests.get(url, headers=FAKE_HEADERS)
            if r.status_code != 200:
                return []
            episode_list = get_shows_from_piratebay_html(r.text, date)
            sorted_episode_by_seeds = sorted(episode_list, key=lambda k: k['seeders'], reverse=True)
            total_episodes.extend(sorted_episode_by_seeds[:3])

    sorted_episode_by_seeds = sorted(total_episodes, key=lambda k: k['seeders'], reverse=True)
    if len(sorted_episode_by_seeds) == 0:
        return "No episode found 😭"

    # Prompt user to select the best episode
    print("\n\n\n")
    for i, episode in enumerate(sorted_episode_by_seeds):
        color = get_color_by_show_name(episode['name'])
        print(color, f"{i + 1}. {episode['name']}\t\t\tSeeders: {episode['seeders']}")
    print("\n\n\n")

    try:
        print(Fore.CYAN, "Enter the number of the episode you want to download: ", end="")
        choice = int(input())
    except ValueError:
        return "Invalid input 😭"
    if choice > len(sorted_episode_by_seeds):
        return "Invalid choice 😭"

    magnet_url = sorted_episode_by_seeds[choice - 1]['url']
    # Prompt if user wants to download the episode
    print("\n\n\n")
    print(Fore.CYAN, f"Do you want to download {sorted_episode_by_seeds[choice - 1]['name']}? (y/n)")
    choice = input("Enter your choice: ")
    if choice.lower() == 'y':
        print("\n\n\n")
        print("Downloading...")
        print("\n\n\n")
        # Open magnet_url in web browser
        webbrowser.open(magnet_url)
    else:
        print("\n\n\n")
        print("Ok, no worries 😉")
        print("\n\n\n")


if __name__ == "__main__":
    find_data_from_piratebay()
