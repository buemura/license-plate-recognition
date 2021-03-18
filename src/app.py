from lib.filters import *


def apply_filter(plate):
    gray = get_grayscale(plate)
    thresh = thresholding(gray)
    print("Altura (height): %d pixels" % (plate.shape[0]))
    print("Largura (width): %d pixels" % (plate.shape[1]))
    print("Canais (channels): %d" % (plate.shape[2]))
    return thresh


def scan_plate(image):
    custom_config = r'-c tessedit_char_blacklist=abcdefghijklmnopqrstuvwxyz/ --psm 6'
    value = (pytesseract.image_to_string(image, config=custom_config))
    return value[:-2]


def validate_plate(plate_number):
    if plate_number == 'FUN-0972' or plate_number == 'BRA2E19':
        print(f'{plate_number} - AUTHORIZED')
    else:
        print(f'{plate_number} - NOT AUTHORIZED')


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

# Make an append to list plates
for i in images:
    plates.append(cv2.imread(i))

# Calls the function apply_filter() passing the plate image
for i, value in enumerate(plates):
    plates_filter_applied.append(apply_filter(plates[i]))
    cv2.imshow('Thresh', plates_filter_applied[i])

for i, value in enumerate(plates_filter_applied):
    plates_numbers.append(scan_plate(plates_filter_applied[i]))

for i, value in enumerate(plates_numbers):
    validate_plate(plates_numbers[i])

cv2.waitKey(0)
