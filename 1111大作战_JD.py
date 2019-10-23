import os
import time
import cv2
import numpy as np
import re


scale = 0.25
threshold = 100

JD_X_limit=[int(800*scale),int(1050*scale)]
JD_Y_limit=[int(850*scale),int(2100*scale)]

acknowledge_btn=(550*scale,1550*scale)

def pull_screenshot():
    os.system('adb shell screencap -p /sdcard/autoclick.png')
    os.system('adb pull /sdcard/autoclick.png ./autoclick.png')

def update_data():

    img = cv2.imread('./autoclick.png')
    img = cv2.resize(img, (0, 0), fx=scale, fy=scale)
    #img, src_x, src_y = search(img)
    return img


def convert_btn_list(img):
    img_r=img[:,:,0]
    img_r=img_r[JD_Y_limit[0]:JD_Y_limit[1],JD_X_limit[0]:JD_X_limit[1]]
    ret,img_t=cv2.threshold(img_r,threshold,255,cv2.THRESH_BINARY)
    for i in range(img_t.shape[0]):
        for j in range(img_t.shape[1]):
            if img_t[i,j]>threshold:
                if i>1 and j>1 and img_t[i-1,j]<=threshold and img_t[i,j-1]<=threshold:
                    img_t[i,j]=0
    cv2.imwrite('jd_grey.jpg',img_t)
    x_mid=int(img_t.shape[1]/2)
    p_list=[]
    for y in range(img_t.shape[0]):
        if y>=1 and img_t[y-1,x_mid]!=img_t[y,x_mid]:
            p_list.append(y)
    assert len(p_list)%2==0 and len(p_list)>0
    y_target=[]
    for i in range(0,len(p_list)-1,2):
        y_target.append(JD_Y_limit[0]+(p_list[i]+p_list[i+1])/2)
    return (x_mid,y_target)

def get_current_activity():
    cmd = ' adb shell dumpsys activity activities | findstr "Run"'
    pattern = 'com.jingdong.app.mall/(.*) t\d+}\n '
    ans=os.popen(cmd)
    strans=''.join(ans.readlines())
    reans = re.findall(pattern,strans)
    assert len(reans)>0
    return reans[0]

def press(x,y):
    cmd = "adb shell input swipe %d %d %d %d  500" % (x/scale,y/scale,x/scale,y/scale) 
    print(cmd)
    os.system(cmd)

def back():
    cmd = "adb shell input keyevent 4"
    os.system(cmd)
    time.sleep(1)

if get_current_activity()=='.WebActivity':
    pull_screenshot()
    img=update_data()
    x_mid,y_target=convert_btn_list(img)
    i=0
    while i < len(y_target):
        press(x_mid,y_target[i])
        time.sleep(2)
        if get_current_activity() == '.basic.ShareActivity':
            i+=1
            back()
            continue
        back()
        press(acknowledge_btn[0],acknowledge_btn[1])
        time.sleep(1)
        pull_screenshot()   #拉取新的截图
        img_t = update_data() 
        try:
            x_mid_t,y_target_t=convert_btn_list(img_t)
        except AssertionError:
            print("检测出错")
        finally:
            if y_target[i] in y_target_t:
                pass
            else:
                i+=1
    
