from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

# from rasa.core.actions.action import Action
from rasa_sdk import Action
from rasa_sdk.events import SlotSet
# from rasa.core.events import SlotSet
import zomatopy
import json
import requests
import ast


result_of_last_query = ""

class restaurant_search(Action):
    def name(self):
        return 'action_restaurant_search'

    def run(self, dispatcher, tracker, domain):
        config={"user_key":"7f90aaa7bde29e0522cb3c9762c564c4"}
        zomato = zomatopy.initialize_app(config)
        location = tracker.get_slot('location')
        cuisine = tracker.get_slot('cuisine')
        average_cost_for_two = tracker.get_slot('budget')

        print('location selected - '+location)
        print('cuisine selected - '+cuisine)
        print('budget selected - '+average_cost_for_two)
        
        response = ""
        global result_of_last_query
        result_of_last_query = ""
        restaurantList=[]
        location_detail=zomato.get_location(location, 1)
        location_detail_json = json.loads(location_detail)

        latitude=location_detail_json["location_suggestions"][0]["latitude"]
        longitude=location_detail_json["location_suggestions"][0]["longitude"]
        cuisines_dict={
        'american':1,
        'mexican':73,
        'italian':55,
        'thai':95,
        'chinese':25,
        'north indian':50,
        'cafe':30,
        'bakery':5,
        'biryani':7,
        'south indian':85
        }
        
        
        results=zomato.restaurant_search("", latitude, longitude, str(cuisines_dict.get(cuisine)),20)
        d = json.loads(results)
        
        if d['results_found'] == 0:
            response= "no results"
        else:
     	    for restaurant in d['restaurants']:
                restaurant_json =  '{ "name":"'+restaurant['restaurant']['name']+'", "address":"'+restaurant['restaurant']['location']['address']+'", "user_rating":"'+restaurant['restaurant']['user_rating']['aggregate_rating']+'", "user_rating":"'+restaurant['restaurant']['user_rating']['aggregate_rating']+'", "average_cost_for_two":"'+str(restaurant['restaurant']['average_cost_for_two'])+'"}'
                restaurantList.append(json.loads(restaurant_json))
        
        filteredList = list(map(lambda x:x if int(x['average_cost_for_two']) <= int(average_cost_for_two) else '',restaurantList))
        while("" in filteredList) : 
            filteredList.remove("") 
    
        index=len(filteredList)
        #response=response+str(len(filteredList))+" Restaurants Found(s)\n"
        for count,restaurant in enumerate(filteredList):
            if( count < 10):
                response=response+"\n "+str(count+1)+". "+restaurant['name'] +" in " +restaurant['address']+" has been rated "+restaurant['user_rating']+" and average price is Rs "+restaurant['average_cost_for_two']+" for two people. \n"


        # modifying the search results
        # if the no. of result fall short, appending the results of other price range
        if index == 0:
            response = "Oops! no restaurant found for this query. "
        elif index < 5:
            # we can add restaurants from the higher range but for now i am appending an extra message 
            response = response + "\n \nFor more results please search in higher budget range...\n \n"
        elif index < 10:
            result_of_last_query = result_of_last_query + "\n \nFor more results please search in higher budget range...\n \n"

        result_of_last_query=response
        dispatcher.utter_message(response)
        return [AllSlotsReset()]

t1_t2_cities = ["Ahmedabad","Bangalore","Chennai","Delhi","Hyderabad","Kolkata","Mumbai","Pune",
"Agra","Ajmer","Aligarh","Allahabad","Amravati","Amritsar","Asansol","Aurangabad",
"Bareilly","Belgaum","Bhavnagar","Bhiwandi","Bhopal","Bhubaneswar",
"Bikaner","Bokaro Steel City","Chandigarh","Coimbatore","Cuttack","Dehradun",
"Dhanbad","Durg-Bhilai Nagar","Durgapur","Erode","Faridabad","Firozabad","Ghaziabad",
"Gorakhpur","Gulbarga","Guntur","Gurgaon","Guwahati",
"Gwalior","Hubli-Dharwad","Indore","Jabalpur","Jaipur","Jalandhar","Jammu","Jamnagar","Jamshedpur","Jhansi","Jodhpur",
"Kannur","Kanpur","Kakinada","Kochi","Kottayam","Kolhapur","Kollam","Kota","Kozhikode","Kurnool","Lucknow","Ludhiana",
"Madurai","Malappuram","Mathura","Goa","Mangalore","Meerut",
"Moradabad","Mysore","Nagpur","Nanded","Nashik","Nellore","Noida","Palakkad","Patna","Pondicherry","Raipur","Rajkot",
"Rajahmundry","Ranchi","Rourkela","Salem","Sangli","Siliguri",
"Solapur","Srinagar","Sultanpur","Surat","Thiruvananthapuram","Thrissur","Tiruchirappalli","Tirunelveli","Tiruppur",
"Ujjain","Vijayapura","Vadodara","Varanasi",
"Vasai-Virar City","Vijayawada","Visakhapatnam","Warangal"]

t1_t2_cities_list = [x.lower() for x in t1_t2_cities]

# Check if the location exists. using zomato api.if found then save it, else utter not found.
class ActionValidateLocation(Action):
    def name(self):
        return 'action_check_location'

    def run(self, dispatcher, tracker, domain):
        loc = tracker.get_slot('location')
        zomato_config={"user_key":"7f90aaa7bde29e0522cb3c9762c564c4"}
        city = str(loc)
        # dispatcher.utter_message(city)

        if city.lower() in t1_t2_cities_list:
            return [SlotSet('location_match',"one")]
        else:
            zomato = zomatopy.initialize_app(zomato_config)

            try:
                results = zomato.get_city_ID(city)
                return [SlotSet('location_match',"one")]
            except:
                # results = "Sorry, didn’t find any such location. Can you please tell again?" + "-----" + city
                # dispatcher.utter_message(city)
                return [SlotSet('location_match',"zero")]


# Send email the list of 10 restaurants
class ActionSendEmail(Action):
    def name(self):
        return 'action_send_email'

    def run(self, dispatcher, tracker, domain):
        email = tracker.get_slot('email')
        global result_of_last_query
        #email='jr.gauravsingh@gmail.com'
        import smtplib 
        from email.mime.text import MIMEText
        s = smtplib.SMTP('smtp.gmail.com', 587) 
        s.starttls() 
        s.login("shikhacomputergeek@gmail.com", "testingchatbot@1234")

        message=MIMEText("The details of all the restaurants you inquried \n \n" + result_of_last_query+"\n\n Bon Appetite.")
        message['From']="shikhacomputergeek@gmail.com"
        message['To']=str(email)
        message['Subject']='Foodie Restaurant Bot'
        try:
            s.sendmail("shikhacomputergeek@gmail.com", str(email), message.as_string())
            s.quit()
        except Exception as e:
            print(e)
            #dispatcher.utter_message(email)

        result_of_last_query = ''
        return [AllSlotsReset()]

from rasa_sdk.events import AllSlotsReset
from rasa_sdk.events import Restarted

class ActionRestarted(Action):     
    def name(self):
        return 'action_restart'
    def run(self, dispatcher, tracker, domain):
        return[Restarted()] 

class ActionSlotReset(Action): 
    def name(self): 
        return 'action_slot_reset' 
    def run(self, dispatcher, tracker, domain): 
        return[AllSlotsReset()]