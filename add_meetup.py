import re
import argh
import requests
import colorsys

from io import BytesIO

from PIL import Image
from bs4 import BeautifulSoup
from redbaron import RedBaron
from colorific.palette import extract_colors

template = """
@event_source(background_color="%(background_color)s", text_color="%(text_color)s", url="%(url)s", predefined_tags=[%(tags)s])
def %(function_name)s():
    \"\"\"%(description)s\"\"\"
    return generic_meetup("%(meetup_name)s")
""".strip()


def color_distance(rgb1, rgb2):
    '''d = {} distance between two colors(3)'''
    rm = 0.5 * (rgb1[0] + rgb2[0])
    d = sum((2 + rm, 4, 3 - rm) * (rgb1 - rgb2) ** 2) ** 0.5
    return d


def rgb_to_hex(rgb):
    return "#" + "".join(map(lambda x: hex(x)[2:], rgb))


def rgb_to_hsv(rgb):
    return colorsys.rgb_to_hsv(*map(lambda x: x/255., rgb))


def hsv_to_rgb(h, s, v):
    return map(lambda x: int(x * 255), colorsys.hsv_to_rgb(h, s, v))


def main(meetup):
    target_url = meetup

    soup = BeautifulSoup(requests.get(target_url).content)

    description = soup.find("div", id="groupDesc")
    description = (" " * 4).join(map(lambda x: str(x), description.contents)) + (" " * 4)
    description = "\n".join(map(lambda x: x.rstrip(), description.split("\n")))

    target_meetup_name = target_url.split("/")[-2]
    target = target_url.split("/")[-2].lower().replace("-", "_")

    if re.match("^\d", target):
        target = "_" + target

    logo_url = soup.find("img", "photo")["src"] if soup.find("img", "photo") else None
    palette = extract_colors(Image.open(BytesIO(requests.get(logo_url).content)))
    colors = palette.colors

    background_color = colors[0].value

    h, s, v = rgb_to_hsv(background_color)
    # text_color = hsv_to_rgb((h + 0.5555555555555) % 1, s, (v * 0.6) if (v * 0.6) < 1 else 1)
    text_color = (255, 255, 255)

    # background_color = map(lambda x: (x + 255)/2, background_color)

    red = RedBaron(open("agendas/be.py", "r").read())

    for i in red("def", recursive=False):
        if target < i.name:
            break

    i.insert_before(template % {
        "background_color": rgb_to_hex(background_color),
        "text_color": rgb_to_hex(text_color),
        "url": target_url,
        "tags": "",
        "function_name": target,
        "description": description,
        "meetup_name": target_meetup_name,
    })

    red.dumps()

    open("agendas/be.py", "w").write(red.dumps())


if __name__ == '__main__':
    argh.dispatch_command(main)