import math

PROGRESS_CHARACTERS = " ▏▎▍▌▋▊▉█"
CHARACTER_COUNT = len(PROGRESS_CHARACTERS)


def progress(percentage, length):
    bar = ""
    for charIndex in range(length):
        charProgress = percentage * length - charIndex
        charProgress = max(0, min(charProgress, 1))
        charToUse = round(charProgress * (CHARACTER_COUNT - 1))
        # print(charToUse)
        bar += PROGRESS_CHARACTERS[charToUse]
    return bar
