import conf
from boltiot import Email, Bolt
import json, time
import math, statistics
import numpy as np
from sklearn.preprocessing import PolynomialFeatures
from sklearn.linear_model import LinearRegression
import matplotlib.pyplot as plt

# Setting the temperature limits in degrees Celsius
minimum_limit = 12
maximum_limit = 15

mybolt = Bolt(conf.API_KEY, conf.DEVICE_ID)
mailer = Email(conf.MAILGUN_API_KEY, conf.SANDBOX_URL, conf.SENDER_EMAIL, conf.RECIPIENT_EMAIL)
history_data=[]

def compute_bounds(history_data,frame_size,factor):
    if len(history_data)<frame_size :
        return None

    if len(history_data)>frame_size :
        del history_data[0:len(history_data)-frame_size]
    Mn=statistics.mean(history_data)
    Variance=0
    for data in history_data :
        Variance += math.pow((data-Mn),2)
    Zn = factor * math.sqrt(Variance / frame_size)
    High_bound = history_data[frame_size-1]+Zn
    Low_bound = history_data[frame_size-1]-Zn
    return [High_bound,Low_bound]

while True:
    print("Reading sensor value")
    response = mybolt.analogRead('A0')
    data = json.loads(response)
    sensor_value = (100*int(data['value']))/1024  # Convert analog value of LM35 to temperature in degrees Celsius
    print("Temperature is:", sensor_value)

    try:
        if sensor_value > maximum_limit or sensor_value < minimum_limit:
            print("Making request to Mailgun to send an email")
            response = mailer.send_email("Alert", "The current temperature is " + str(sensor_value) + "°C")
            response_text = json.loads(response.text)
            print("Response received from Mailgun is: " + str(response_text['message']))
    except e:
        print("There was an error while parsing the response: ",e)
        continue

    bound = compute_bounds(history_data,conf.FRAME_SIZE,conf.MUL_FACTOR)
    if not bound:
        required_data_count=conf.FRAME_SIZE-len(history_data)
        print("Not enough data to compute Z-score. Need ",required_data_count," more data points")
        history_data.append(int(data['value']))
        time.sleep(5)
        continue

    try:
        if sensor_value > bound[0] :
            print ("The Refrigerator is been CLosed")
            print("Making request to Mailgun to send an email")
            response = mailer.send_email("Alert", "The Refrigerator is been Closed")
            response_text = json.loads(response.text)
            print("Response received from Mailgun is: " + str(response_text['message']))
        elif sensor_value < bound[1]:
            print ("The Refrigerator is Opened")
            print("Making request to Mailgun to send an email")
            response = mailer.send_email("Alert", "The Refrigerator is been Opened")
            response_text = json.loads(response.text)
            print("Response received from Mailgun is: " + str(response_text['message']))
        history_data.append(sensor_value);
    except Exception as e:
        print ("Error",e)
    time.sleep(10) 
