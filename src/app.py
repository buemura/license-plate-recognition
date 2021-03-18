from lib.filters import *
# from lib.processing import *

authorized_plate = ['FUN-0972', 'BRA2E19']

def apply_filter(plate):
    gray = get_grayscale(plate)
    thresh = thresholding(gray)
    # print("Altura (height): %d pixels" % (plate.shape[0]))
    # print("Largura (width): %d pixels" % (plate.shape[1]))
    # print("Canais (channels): %d" % (plate.shape[2]))
    return thresh


def scan_plate(image):
    custom_config = r'-c tessedit_char_blacklist=abcdefghijklmnopqrstuvwxyz/ --psm 6'
    value = (pytesseract.image_to_string(image, config=custom_config))
    return value[:-2]


def validate_plate(value):
    if value == 'FUN-0972' or value == 'BRA2E19':
        print('Liberado')
    else:
        print('Não liberado')


# Reading the images
plate1 = cv2.imread('../images/placa1.jpg')
plate2 = cv2.imread('../images/placa2.jpg')
plate3 = cv2.imread('../images/placa3.jpg')
plate4 = cv2.imread('../images/placa4.jpg')

plate1_filter_applied = apply_filter(plate1)
plate2_filter_applied = apply_filter(plate2)
plate3_filter_applied = apply_filter(plate3)
plate4_filter_applied = apply_filter(plate4)

# cv2.imshow('Thresh', plate1_filter_applied)
# cv2.imshow('Thresh', plate2_filter_applied)
# cv2.imshow('Thresh', plate3_filter_applied)
# cv2.imshow('Thresh', plate4_filter_applied)

plate1_value = scan_plate(plate1_filter_applied)
plate2_value = scan_plate(plate2_filter_applied)
plate3_value = scan_plate(plate3_filter_applied)
plate4_value = scan_plate(plate4_filter_applied)

validate_plate(plate1_value)
validate_plate(plate2_value)
validate_plate(plate3_value)
validate_plate(plate4_value)

cv2.waitKey(0)