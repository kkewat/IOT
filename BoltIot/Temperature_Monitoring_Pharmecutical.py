import conf
from boltiot import Email, Bolt
import json, time
import numpy as np
from sklearn.preprocessing import PolynomialFeatures
from sklearn.linear_model import LinearRegression
import matplotlib.pyplot as plt

# Setting the temperature limits in degrees Celsius
minimum_limit = 25
maximum_limit = 30

mybolt = Bolt(conf.API_KEY, conf.DEVICE_ID)
mailer = Email(conf.MAILGUN_API_KEY, conf.SANDBOX_URL, conf.SENDER_EMAIL, conf.RECIPIENT_EMAIL)

# Initialize variables for polynomial regression and plotting
x_values = []
y_values = []

while True:
    print("Reading sensor value")
    response = mybolt.analogRead('A0')
    data = json.loads(response)
    
    sensor_value = (100*int(data['value']))/1024  # Convert analog value of LM35 to temperature in degrees Celsius
    print("Temperature is:", sensor_value)
    y_values.append(sensor_value)

    # Append data for polynomial regression
    x_values.append(len(x_values) + 1)
    

    print("Temperature is: " + str(sensor_value))

    try:
        if sensor_value > maximum_limit or sensor_value < minimum_limit:
            print("Making request to Mailgun to send an email")
            response = mailer.send_email("Alert", "The current temperature is " + str(sensor_value) + "°C")
            response_text = json.loads(response.text)
            print("Response received from Mailgun is: " + str(response_text['message']))

        # Check if enough data points are collected for polynomial regression
        if len(x_values) >= 5:
            # Perform polynomial regression
            x_poly = np.array(x_values).reshape(-1, 1)
            y_poly = np.array(y_values).reshape(-1, 1)

            poly_features = PolynomialFeatures(degree=2)
            x_poly = poly_features.fit_transform(x_poly)

            poly_model = LinearRegression()
            poly_model.fit(x_poly, y_poly)

            # Predict future values
            future_x = np.array(range(len(x_values) + 1, len(x_values) + 6)).reshape(-1, 1)
            future_x_poly = poly_features.transform(future_x)
            future_y_pred = poly_model.predict(future_x_poly)

            print("Predicted future values:", future_y_pred)

            # Plot and save the polynomial regression output
            plt.scatter(x_values, y_values, color='blue', label='Actual Data')
            plt.plot(future_x, future_y_pred, color='red', label='Polynomial Regression Prediction')
            plt.xlabel('Time')
            plt.ylabel('Temperature (°C)')
            plt.title('Temperature Prediction with Polynomial Regression')

            # Save the plot to an image file
            plt.savefig('temperature_prediction_plot1.png')
            print('Plot saved to temperature_prediction_plot.png')

            # Check if predicted values are within the specified range for 20 minutes
            if all(minimum_limit <= pred <= maximum_limit for pred in future_y_pred):
                print("Taking early action! Predicted temperature will be within the range for 20 minutes.")
                response = mailer.send_email("Alert", "Predicted that the temperature would be maintained within the -33 and -30 degrees Celsius range for longer than 20 minutes")
                response_text = json.loads(response.text)
                print("Response received from Mailgun is: " + str(response_text['message']))

    except Exception as e:
        # Handle exceptions
        print("Error occurred: Below are the details")
        print(e)

    # Wait for some time before the next iteration
    time.sleep(10)
