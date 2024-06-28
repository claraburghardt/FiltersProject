import cv2 as cv
import numpy as np

def apply_filter(image, filter_type):
    if filter_type == 'gray':
        return cv.cvtColor(image, cv.COLOR_BGR2GRAY)
    elif filter_type == 'blur':
        return cv.GaussianBlur(image, (15, 15), 0)
    elif filter_type == 'canny':
        return cv.Canny(image, 100, 200)
    elif filter_type == 'invert':
        return cv.bitwise_not(image)
    elif filter_type == 'sepia':
        sepia_filter = np.array([[0.272, 0.534, 0.131],
                                 [0.349, 0.686, 0.168],
                                 [0.393, 0.769, 0.189]]).astype(np.float32)
        return cv.transform(image, sepia_filter)
    elif filter_type == 'emboss':
        kernel = np.array([[0,-1,-1],[1,0,-1],[1,1,0]])
        return cv.filter2D(image, -1, kernel)
    elif filter_type == 'sharpen':
        kernel = np.array([[0,-1,0],[-1,5,-1],[0,-1,0]])
        return cv.filter2D(image, -1, kernel)
    elif filter_type == 'threshold':
        _, thresholded = cv.threshold(cv.cvtColor(image, cv.COLOR_BGR2GRAY), 127, 255, cv.THRESH_BINARY)
        return thresholded
    elif filter_type == 'sobel_x':
        gray = cv.cvtColor(image, cv.COLOR_BGR2GRAY)
        sobel_x = cv.Sobel(gray, cv.CV_64F, 1, 0, ksize=5)
        sobel_x = cv.convertScaleAbs(sobel_x)
        return sobel_x
    elif filter_type == 'edges':
        return cv.Canny(image, 50, 150)
    else:
        return image
