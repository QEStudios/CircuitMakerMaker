import re
import random

FACE_CHANCE = 0.25
FACE = [" (・`ω´・) ", " ;;w;; ", " owo ", " UwU ", " >w< ", " ^w^ "]


def uwuify(string):
    if len(string) > 0:
        uwu = string
        fr = "rlRL"
        to = "wwWW"
        for i, _ in enumerate(fr):
            uwu = uwu.replace(fr[i], to[i])
            print(fr[i], to[i], uwu)
        uwu = re.sub(r"(n)([aeiou])", r"\1y\2", uwu, flags=re.IGNORECASE)
        uwu.replace("ove", "uv")

        def replace_periods(match):
            if random.random() < FACE_CHANCE:
                return random.choice(FACE)
            else:
                return match.group(1)

        uwu = re.sub(r"(\.+)", replace_periods, uwu)
        return uwu
