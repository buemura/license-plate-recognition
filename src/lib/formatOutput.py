import os

header = ['Image', 'Plate', 'Status']


def fixed_length(text, length):
    if len(text) > length:
        text = text[:length]
    elif len(text) < length:
        text = (text + " " * length)[:length]
    return text


def format_output(data):
    os.system('clear')
    print("━" * 70)
    print("┃", end=" ")
    for column in header:
        print(fixed_length(column, 20), end=" ┃ ")
    print()
    print("━" * 70)

    for row in data:
        print("┃", end=" ")
        for column in row:
            print(fixed_length(column, 20), end=" ┃ ")
        print()
    print("━" * 70)
