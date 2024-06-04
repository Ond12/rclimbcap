import cv2
import numpy as np
import matplotlib.pyplot as plt
import os
  
def find_pattern(signal):
        match_red = False
        match_green = False
        indices = []

        for i in range(len(signal)):

            if signal[i-1] == 0 and signal[i] == 2 and not match_red:
                match_red = True
                start_time_red = i
            elif signal[i-1] == 2 and signal[i] == 0 and match_red:
                end_time_red = i - 1
                indices.append(('r',start_time_red, end_time_red))
        
            if signal[i-1] == 0 and signal[i] == 1 and match_red:
                start_time_green = i
                match_green = True

            elif signal[i-1] == 1 and signal[i] == 0 and match_red and match_green:
                end_time_green = i - 1
                match_green = False
                indices.append(('g',start_time_green, end_time_green))
                
        return indices

def find_last_green_frame_idx(pattern):
    if len(pattern) >= 5:
        return pattern[-1][1]
    else:
        return 0

def post_pro_rawvideo(input_video_path):

    directory = os.path.dirname(input_video_path)
    input_file_name = os.path.basename(input_video_path)

    name, ext = os.path.splitext(input_file_name)
    new_file_name = name + '_post.avi'

    output_video_path = os.path.join(directory, new_file_name)

    cap = cv2.VideoCapture(input_video_path)
    if not cap.isOpened():
        print("Error: Could not open video.")
        exit()
        
    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    width, height = 310, 640  # Desired width and height of the corrected image
    fourcc = cv2.VideoWriter_fourcc(*'XVID')  
    out = cv2.VideoWriter(output_video_path, fourcc, fps, (width, height))

    x, y, w, h = 230, 1340, 100, 100  

    startX, startY = 200, 100
    endX, endY = 800, 1800

    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.5
    font_color = (255, 255, 255)  
    thickness = 1
    position = (20, 20)  

    lower_lighter_green = np.array([35, 50, 50])
    upper_lighter_green = np.array([85, 255, 255])
                                                
    lower_red_hsv = np.array([170, 70, 50])
    upper_red_hsv = np.array([180, 255, 255])

    detected_frames = []
    min_green_pixels = 200 
    min_red_pixels = 200   

    def on_mouse_click(event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            param['clicked'] = True
            print((x,y))

    # cv2.namedWindow('Frame')
    # mouse_param = {'clicked': False}
    # cv2.setMouseCallback('Frame', on_mouse_click, mouse_param)

    frame_index = 0

    pts_src = np.array([[181, 225], [822, 240], [790, 1780], [198, 1813]])

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        frame = cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)

        roi = frame[y:y+h, x:x+w]
        #frame = frame[startY:endY, startX:endX]

        text = f'Frame: {frame_index} / {total_frames}, t: {round(frame_index/60, 2)}'

        # for point in pts_src:
        #     cv2.circle(frame, tuple(point), 5, (0, 255, 0), -1) 
        #     cv2.putText(frame, f"({point[0]}, {point[1]})", 
        #             (point[0] + 5, point[1] - 5), 
        #             cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA) 
            
        hsv_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)

        mask = cv2.inRange(hsv_roi, lower_lighter_green, upper_lighter_green)
        maskred = cv2.inRange(hsv_roi, lower_red_hsv, upper_red_hsv)

        red_pixel_count = np.sum(maskred > 0)
        green_pixel_count = np.sum(mask > 0)

        if green_pixel_count > min_green_pixels:
            detected_frames.append(1)
            font_color = (0,255,0)
        elif red_pixel_count > min_red_pixels:
            detected_frames.append(2)
            font_color = (0,0,255)
        else:
            detected_frames.append(0)
            font_color = (255,255,255)
            
        #cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 0, 0), 2)  
        #cv2.rectangle(frame, (startX, startY), (endX, endY), (0, 255, 0), 2) 
        #resized_frame = cv2.resize(frame, (540, 960))
        
        pts_src = np.array(pts_src, dtype='float32')

        width, height = 310, 640  # Desired width and height of the corrected image
        pts_dst = np.array([[0, 0], [width, 0], [width, height], [0, height]], dtype='float32')

        # Calculate the perspective transform matrix
        M = cv2.getPerspectiveTransform(pts_src, pts_dst)

        # Apply the perspective transformation
        corrected_image = cv2.warpPerspective(frame, M, (width, height))

        cv2.putText(corrected_image, text, position, font, font_scale, font_color, thickness)
            
        # cv2.imshow('Frame', corrected_image)
        out.write(corrected_image)
        # cv2.imshow('ROI', roi)
        # cv2.imshow('Mask', maskred)
        
        #mouse_param['clicked'] = False
        
        # while not mouse_param['clicked']:
        #     if cv2.waitKey(1) & 0xFF == ord('q'):
        #         break

        # if cv2.waitKey(25) & 0xFF == ord('q'):
        #     break
        if frame_index == 450:
            break
        frame_index += 1

    result = find_pattern(detected_frames)
    offsettime = int((find_last_green_frame_idx(result) / 60 ) *1000)
    
    out.release()
    cap.release()
    cv2.destroyAllWindows()

    return output_video_path, offsettime

# plt.figure(figsize=(12, 6))
# plt.plot(detected_frames, marker='o', linestyle='-', color='b')
# plt.title('Frame-by-Frame Color Detection')
# plt.xlabel('Frame Number')
# plt.ylabel('Detection (1: Green, 2: Red, 0: None)')
# plt.grid(True)
# plt.show()



#post_pro_rawvideo('C:/Users/thepaula/Downloads/run_jerome_video/run4/ESC_2024-05-22_15-32-01.mp4')