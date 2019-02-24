import requests
from bs4 import BeautifulSoup
import chardet
from PIL import Image
import pytesseract
import re,os,time
from requests import exceptions
import threading
addr='http://jwdep.dhu.edu.cn/dhu/index/'
post_addr='http://jwdep.dhu.edu.cn/dhu/login_wz.jsp'
captcha_addr='http://jwdep.dhu.edu.cn/dhu/servlet/com.collegesoft.eduadmin.tables.captcha.CaptchaController'
selectCourseAddr='http://jwdep.dhu.edu.cn/dhu/servlet/com.collegesoft.eduadmin.tables.selectcourse.SelectCourseController'
selectInfo="http://jwdep.dhu.edu.cn/dhu/student/selectcourse/allCourseinf.jsp"
selectStateAddr="http://jwdep.dhu.edu.cn/dhu/student/selectcourse/seeselectedcourse.jsp"
isNetWorking=False
login_successfully=False


f=open('input.txt')
lines=f.readlines()

userId=lines[0].strip()
userPwd=lines[1].strip()
courseId=lines[2].strip()
courseNo=lines[3].strip()

while not isNetWorking:
    session=requests.session()
    try:
        response_test=session.get(addr,timeout=1.0)
        isNetWorking=True
    except Exception as e:
        #print('Connection to jwdep.dhu.edu.cn timed out. (connect timeout=1.0)')
        print(e)

while not login_successfully:
    session=requests.session()

    # write a binary content to a captcha image file
    captcha_code=session.get(captcha_addr)
    f = open('valcode.jpg', 'wb')
    f.write(captcha_code.content)
    f.close()

    #convert color images to string using tesseract-ocr
    image=Image.open('valcode.jpg')
    optCode = pytesseract.image_to_string(image)
    data={
    'userName':userId,
    'userPwd':userPwd,
    'code':optCode
    }

    resp=session.post(post_addr,data=data)
    print("Trying to decipher the captcha code!")
    if resp.url=='http://jwdep.dhu.edu.cn/dhu/student/':
        print('Successfully login!')
        login_successfully=True
    else:
        print("The captcha code is a little complex, let me try again! The process may take a little time")

#searching the course info using brute force

allCourse_html=session.get(selectInfo).text
soup=BeautifulSoup(allCourse_html,features='html.parser')

isAlreadyFound=False
courseName=''
print('Searching the course name...')
for x in soup.find_all('option'):
    tryConnect=True
    while tryConnect and not isAlreadyFound:
        try:
            traverse_html=session.post(selectInfo,data={'acadId':x['value']},timeout=2.0).text
            traverse_soup=BeautifulSoup(traverse_html,features='html.parser')
            tag_all=traverse_soup.find_all('td')
            for index in range(len(tag_all)):
                if tag_all[index].string==courseId:
                    print('The course you want to force is :'+tag_all[index-1].string)
                    #courseName=str(tag_all[index-1].string)
                    isAlreadyFound=True
                    break
            if isAlreadyFound:
                break
            tryConnect=False
        except Exception as e:
            print(e)

if not isAlreadyFound:
    print("Your course information is wrong, please check again!")
    os._exit(0)
sm={'doWhat':'selectcourse',
    'courseId':courseId,
    'courseNo':courseNo,
    'courseName':courseName.encode('gbk'),
    'studentId':userId,
    'selectCourseStatus':'2' }

isSelected=False
count=1
failedCount=0
def bruteForce():
    global isSelected,count,failedCount
    while not isSelected:
        try:
            select_response=session.post(selectCourseAddr,data=sm,timeout=1.0)
            if select_response.status_code>=400:
                failedCount+=1
            print('trying %d times...abandoned requests %d'%(count,failedCount))
            count+=1
            time.sleep(0.3)
        except Exception as e :
            #print('bruteForce Connection to jwdep.dhu.edu.cn timed out. (connect timeout=1.0)')
            print(e)

def checkSelectedState():
    global isSelected
    while not isSelected:
        try:
            check_response=session.get(selectStateAddr,timeout=1.0)
            check_soup=BeautifulSoup(check_response.text,features='html.parser')
            for x in check_soup.find_all("td"):
                if x.string==courseId:
                    isSelected=True
            time.sleep(10.0)
        except Exception as e:
            #print('Connection to jwdep.dhu.edu.cn timed out. (connect timeout=1.0)')
            print(e)

if __name__ == "__main__":
    for i in range(1):
        t1=threading.Thread(target=bruteForce)
        t1.start()
    t2=threading.Thread(target=checkSelectedState)
    t2.start()    
    t2.join()
    t1.join()
    if isSelected:
        print("Congratulations! You have selected the course successfully!")
    os.system('pause')
    