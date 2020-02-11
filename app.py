
import os
from flask import Flask, make_response, request
from datetime import datetime
import json
import os.path
import random
import string
import psycopg2


app = Flask(__name__)

#Slack variables
client_id = os.environ["SLACK_CLIENT_ID"]
client_secret = os.environ["SLACK_CLIENT_SECRET"]
slack_verification_token=os.environ["SLACK_VERIFICATION_TOKEN"]


#client = WebClient(token=os.environ["SLACK_VERIFICATION_TOKEN"])

#Postgresql database used for storing orders
#Getting Database URL from environment variable
DB_URL = os.environ['DATABASE_URL']
#db = SQLAlchemy(app)
#

#Assiging uppercase characters from string module (will be used to generate random string for orderid).
chars = string.ascii_uppercase

#Assiging digits from string module (will be used to generate random string for orderid).
digits= string.digits

# Webhook url to send response to the user
wekbook_url = 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxx'

print()
print()


@app.route('/', methods=["GET", "POST"])

def webhook():
    #print("Inside WebHook")
    if request.method == 'GET':
        print('Get request found')

    # To check POST request sent by Dialogflow        
    if request.method == 'POST':
        print('Post request found')
        print(request.ur)

        # Getting the information from the 'Post' request, whatever it may be
        post_request = request.get_json(silent=True, force=True)

        #print(type(post_request))
        print(post_request)
        #print(post_request['responseId'])

        # Condtion to check whether the post request is for Placing new Pizza order
        if post_request['queryResult']['intent']['displayName'] == 'NewOrder_ContactNumber':

            # Generating a random string of total size 10 characters to use as OrderId.
            OrderId = random_OrderId_generator(4, chars)+random_OrderId_generator(6, digits)

            # Extracing data from request sent by Dialogflow integrated with Slack.
            PizzaType = post_request['queryResult']['outputContexts'][0]['parameters']['PizzaType']
            Topping = post_request['queryResult']['outputContexts'][0]['parameters']['Topping']
            CustName = post_request['queryResult']['outputContexts'][0]['parameters']['Name'] 
            PhoneNumber = post_request['queryResult']['outputContexts'][0]['parameters']['ContactNumber']

            # Finding current date and time 
            now = datetime.now()
            DateTime = now.strftime("%d/%m/%Y %H:%M:%S")


            #printing to check in console/log
            print("____Hi followings are the order details__________________")

            print("Order Id : ", OrderId )
            print("datetime", DateTime) 
            print("Pizza Type : ", PizzaType )
            print("Topping : ", Topping )
            print("Customer name : ",CustName )
            print("Phone number : ", PhoneNumber )


            # connecting with postgresql database on heroku cloud platform.
            conn = psycopg2.connect(DB_URL, sslmode='require')

            # create a cursor
            cur = conn.cursor()

            # sql commant to insert record in database
            sql = """INSERT INTO PizzaOrders (order_id, pizza_type, topping, cust_name, phone, dateandtime) values(%s,%s,%s,%s,%s,%s);"""
            
            # execute the INSERT statement
            cur.execute(sql, (OrderId, PizzaType, Topping, CustName, PhoneNumber,DateTime))

            # commit the changes to the database
            conn.commit()

            # close communication with the database
            cur.close()

            # close the database connection
            conn.close()

            # Generating response to sent to user ( provide order id )
            ResponseMessage = "Your Order Id is : "+ OrderId

            slack_data = {'text': ResponseMessage }

            # sending response to user
            response = requests.post(wekbook_url, data=json.dumps(slack_data), headers={'Content-Type': 'application/json'})

            #print('Response: ' + str(response.text))
            #print('Response code: ' + str(response.status_code))

        # Else the POST request is for Checking order status
        else:
            # extracting the order id from request 
            _orderId = post_request['queryResult']['outputContexts'][0]['parameters']['OrderId']
            #print(_orderId)
            # connecting with postgresql database on heroku cloud platform.
            conn = psycopg2.connect(DB_URL, sslmode='require')

            # create a cursor
            cur = conn.cursor()
            
            # sql commant to fetch order status for the given id
            sql = """SELECT orderstatus FROM PizzaOrders WHERE order_id = %s;"""
            
            # execute the INSERT statement
            cur.execute(sql, (_orderId,) )
            

            ResultStatus = cur.fetchone()
            
            #print(ResultStatus)

            # commit the changes to the database
            conn.commit()

            # close communication with the database
            cur.close()

            # close the database connection
            conn.close()

            # Generating response to sent to user ( provide order status  )
            if ResultStatus:
                ResponseMessage = "Your Order status : "+ ResultStatus[0] 
            else:
                # No record found
                ResponseMessage = "Please enter correct Order Id ! "

            slack_data = {'text': ResponseMessage }

            # sending response to user
            response = requests.post(wekbook_url, data=json.dumps(slack_data), headers={'Content-Type': 'application/json'})
            


# method to create a random string of str_size using allowed_chars
def random_OrderId_generator(str_size, allowed_chars):
    return ''.join(random.choice(allowed_chars) for x in range(str_size))


# Process to activate app
if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))

    print("Starting app on port %d" % port)

    app.run(debug=False, port=port, host='0.0.0.0')

