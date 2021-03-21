from os import walk
import cv2
from lib.filters import get_grayscale, thresholding, pytesseract
from lib.format_output import format_output


def apply_filter(plate):
    gray = get_grayscale(plate)
    thresh = thresholding(gray)
    return thresh


def scan_plate(image):
    custom_config = r'-c tessedit_char_blacklist=abcdefghijklmnopqrstuvwxyz/ --psm 6'
    plate_number = (pytesseract.image_to_string(image, config=custom_config))
    return plate_number[:-2]


def validate_plate(plate_number, authorized_plate):
    if plate_number in authorized_plate:
        return 'AUTHORIZED'
    else:
        return 'NOT AUTHORIZED'


def main():
    authorized_plate = ['FUN-0972', 'BRA2E19']

    images = [
        '../images/placa1.jpg',
        '../images/placa2.jpg',
        '../images/placa3.jpg',
        '../images/placa4.jpg'
    ]

    plates = []
    plates_filter_applied = []
    plates_numbers = []
    data = []
    _, _, filenames = next(walk('../images/'))

    # Append the files name to list data
    for i in range(len(filenames)):
        data.append([])
        data[i].append(filenames[i])

    # Make an append to list plates
    for i in images:
        plates.append(cv2.imread(i))

    # Calls the function apply_filter() passing the plate image
    for i in range(len(plates)):
        plates_filter_applied.append(apply_filter(plates[i]))

    # Calls the function scan_plate() passing the plate image with filter applied
    for i in range(len(plates_filter_applied)):
        plates_numbers.append(scan_plate(plates_filter_applied[i]))
        data[i].append(plates_numbers[i])

    # Calls the function validate_plate() passing the plate number
    for i in range(len(plates_numbers)):
        data[i].append(validate_plate(plates_numbers[i], authorized_plate))

    format_output(data)


main()
