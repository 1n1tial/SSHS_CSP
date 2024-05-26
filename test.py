import numpy as np
import cv2

img = cv2.imread('3208_윤영우.jpg')
cv2.imshow('Window name', img)

key =cv2.waitKey(0)
print(key)

if key== ord('q'):
   print("pressed q")

cv2.destroyAllWindows()