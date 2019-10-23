
from PIL import Image
import os
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import cv2
import time
import numpy as np
import re
import codecs

scale = 0.25
threshold = 50


TB_X_limit=(int(190),int(250))
TB_Y_limit=(int(180),int(490))

CAT_ENTER_BTN=(222,29)
GET_CATCOIN_BTN=(237,423)

def convert_btn_list(img):
    #裁切截图，获取按钮列图片
    btn_list_img=img[TB_Y_limit[0]:TB_Y_limit[1],TB_X_limit[0]:TB_X_limit[1]]
    #灰度化
    gray_btn_list_img = btn_list_img[:,:,1]
    cv2.imwrite("gray_btn_list_img.jpg", gray_btn_list_img)
    #二值化
    ret,gray_btn_list_img_t=cv2.threshold(gray_btn_list_img,threshold,255,cv2.THRESH_BINARY)
    cv2.imwrite("gray_btn_list_img_t.jpg", gray_btn_list_img_t)
    #补全按钮中白色的字体部分
    btn_full=np.zeros((gray_btn_list_img_t.shape[0],gray_btn_list_img_t.shape[1]))
    for i in range(btn_full.shape[0]):
        for j in range(btn_full.shape[1]):
            if gray_btn_list_img_t[i,j]>threshold:  #白色
                if i>1 and j>1 and gray_btn_list_img_t[i-1,j]<=threshold and gray_btn_list_img_t[i,j-1]<=threshold: #左侧和上方都是黑的
                    gray_btn_list_img_t[i,j]=0  #则填充黑色
                else:
                    btn_full[i,j]=gray_btn_list_img_t[i,j]
            else:
                btn_full[i,j]=gray_btn_list_img_t[i,j]
    cv2.imwrite("btn_full.jpg", btn_full)
    #找到中线
    x_mid = int(btn_full.shape[1]/2)
    count=0
    p_list=[]
    for i in range(btn_full.shape[0]):
        if i>=1 and btn_full[i-1,x_mid]!=btn_full[i,x_mid]: #上面一个像素点和当前像素点颜色不一致
            p_list.append(i)
    print(p_list)
    assert len(p_list)%2==0 and len(p_list)>0
    y_target=[]

    for i in range(0,len(p_list)-1,2):
        y_target.append(TB_Y_limit[0]+(p_list[i]+p_list[i+1])/2)
    print(y_target)
    return (x_mid,y_target)

def pull_screenshot():
    os.system('adb shell screencap -p /sdcard/autoclick.png')
    os.system('adb pull /sdcard/autoclick.png ./autoclick.png')

def update_data():

    img = cv2.imread('./autoclick.png')
    img = cv2.resize(img, (0, 0), fx=scale, fy=scale)
    #img, src_x, src_y = search(img)
    return img

def updatefig(*args):
    global update

    if update:
        time.sleep(1)
        pull_screenshot()
        im.set_array(update_data())
        update = False
    return im,

def on_click(event):
    global update    
    #global src_x, src_y
    
    dst_x, dst_y = event.xdata, event.ydata
    print((dst_x,dst_y))
    press(dst_x,dst_y)
    #print('distance = ', distance)
    update = True

def press(x,y):
    cmd = "adb shell input swipe %d %d %d %d  500" % (x/scale,y/scale,x/scale,y/scale) 
    print(cmd)
    os.system(cmd)

def back():
    cmd = "adb shell input keyevent 4"
    os.system(cmd)
    time.sleep(1)

def is_share(img):
    X=img.shape[1]
    Y=img.shape[0]

    grey_target=img[:,:,1]
    ret,grey_target=cv2.threshold(grey_target,130,255,cv2.THRESH_BINARY)
    cv2.imwrite('grey_target.jpg',grey_target)
    count=0
    for x in range(X):
        for y in range(int(Y/2)):
            if grey_target[y,x]<130:
                count+=1
                
    
    if count/(X*Y/2)>=0.95:
        print("检测到当前页面是分享页面！")
        print("当前页面黑色占比：%f" %  (count/(X*Y/2),))
        return True
    return False
    
    
def get_content_xml():
    cmd='adb shell /system/bin/uiautomator dump /data/local/tmp/tmpUI.xml'
    os.system(cmd)
    time.sleep(2)
    cmd='adb pull /data/local/tmp/tmpUI.xml content.xml'
    os.system(cmd)
    time.sleep(1)
    f=codecs.open('content.xml','r','utf-8')
    strXml=''.join(f.readlines())
    return strXml

def isTaskList():
    strXml=get_content_xml()
    pattern='分享|完成|浏览'
    if re.search(pattern,strXml) is None:
        return False
    else:
        return True


def shopping(t):
    cmd = "adb shell input swipe 300 600 300 100 1000"
    for i in range(t):
        os.system(cmd)
        print(cmd)
        print("正在逛街%d/%d秒" % (i+1,t))
        time.sleep(1)

def get_current_activity():
    cmd = ' adb shell dumpsys activity activities | findstr "Run"'
    pattern = 'com.taobao.taobao/(.*) t\d+}\n '
    ans=os.popen(cmd)
    strans=''.join(ans.readlines())
    reans = re.findall(pattern,strans)
    assert len(reans)>0
    return reans[0]

def from_home_to_cat():
    press(CAT_ENTER_BTN[0],CAT_ENTER_BTN[1])

def from_cat_to_tasklist():
    press(GET_CATCOIN_BTN[0],GET_CATCOIN_BTN[1])

def ensure_is_in_tasklist():
    if get_current_activity()=='com.taobao.tao.TBMainActivity':
        print('在主页')
        from_home_to_cat()
        time.sleep(5)
        from_cat_to_tasklist()
        time.sleep(3)
    elif get_current_activity()=='com.taobao.browser.BrowserActivity':
        if isTaskList():
            pass
        else:
            print('不在猫币页面，尝试回到猫币页面……')
            from_cat_to_tasklist()

ensure_is_in_tasklist()

fig = plt.figure()
pull_screenshot()
img = update_data()
im = plt.imshow(img, animated=True)
update = True
fig.canvas.mpl_connect('button_press_event', on_click)
ani = animation.FuncAnimation(fig, updatefig, interval=5, blit=True)



x_mid,y_target=convert_btn_list(img)

i=0
#对于每一个按钮
while i<len(y_target):
    ensure_is_in_tasklist()
    #按下去
    press(x_mid+TB_X_limit[0],y_target[i])
    time.sleep(3)   #等三秒让页面加载
    pull_screenshot()   #拉取新的截图
    img = update_data() 
    if is_share(img):   #检测是否是分享页面（分享页面直接返回、返回键按两次）
        back()
        back()
        i+=1
        continue
    else:
        shopping(8)    #如果不是分享页面就逛街15秒（保险起见逛17s）
        back()
        pull_screenshot()   #拉取新的截图
        img_t = update_data() 
        try:
            x_mid_t,y_target_t=convert_btn_list(img_t)
        except AssertionError :
            from_cat_to_tasklist()
            x_mid_t,y_target_t=convert_btn_list(img_t)
        finally:
            if y_target[i] in  y_target_t:  #如果按钮还可以点击
                pass
            else:
                i+=1
    

cv2.waitKey(0)
plt.show()
