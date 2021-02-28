import cv2
import numpy as np
from openni import openni2


video_path = r"C:\Users\UserPC\Desktop\testData\cap1.oni"
openni2.initialize()
dev = openni2.Device.open_file(video_path.encode('utf-8'))
print(dev.get_sensor_info(openni2.SENSOR_DEPTH))

depth_stream = dev.create_depth_stream()
depth_stream.start()
while True:
    frame_depth = depth_stream.read_frame()
    frame_depth_data = frame_depth.get_buffer_as_uint16()
    depth_array = np.ndarray((frame_depth.height, frame_depth.width),
                             dtype=np.uint16,
                             buffer=frame_depth_data) / 10000.  # 0-10000mm to 0.-1.
    cv2.imshow('Depth', depth_array)

    ch = 0xFF & cv2.waitKey(1)
    if ch == 27:
        break

depth_stream.stop()
openni2.unload()
cv2.destroyAllWindows()
