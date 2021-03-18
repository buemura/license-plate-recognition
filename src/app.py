import cv2
from lib.filters import get_grayscale, thresholding, pytesseract

authorized_plate = ['FUN-0972', 'BRA2E19']

images = [
    '../images/placa1.jpg',
    '../images/placa2.jpg',
    '../images/placa3.jpg',
    '../images/placa4.jpg'
]


def apply_filter(plate):
    gray = get_grayscale(plate)
    thresh = thresholding(gray)
    print("Height: %d pixels" % (plate.shape[0]))
    print("Width: %d pixels" % (plate.shape[1]))
    print("Channels: %d" % (plate.shape[2]))
    return thresh


def scan_plate(image):
    custom_config = r'-c tessedit_char_blacklist=abcdefghijklmnopqrstuvwxyz/ --psm 6'
    plate_number = (pytesseract.image_to_string(image, config=custom_config))
    return plate_number[:-2]


def validate_plate(plate_number):
    if plate_number in authorized_plate:
        print(f'{plate_number} - AUTHORIZED')
    else:
        print(f'{plate_number} - NOT AUTHORIZED')


plates = []
plates_filter_applied = []
plates_numbers = []

# Make an append to list plates
for i in images:
    plates.append(cv2.imread(i))

# Calls the function apply_filter() passing the plate image
for i, value in enumerate(plates):
    print(f'\n========== Image {i + 1} details ==========')
    plates_filter_applied.append(apply_filter(plates[i]))

# Calls the function scan_plate() passing the plate image with filter applied
for i, value in enumerate(plates_filter_applied):
    plates_numbers.append(scan_plate(plates_filter_applied[i]))

# Calls the function validate_plate() passing the plate number
print('\n========== Validating Plates ========== ')
for i, value in enumerate(plates_numbers):
    validate_plate(plates_numbers[i])
