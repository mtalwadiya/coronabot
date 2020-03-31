
import os
from flask import Flask, request, render_template, jsonify
import pandas as pd
import requests  
import json

app = Flask(__name__, static_folder='static', static_url_path='')


@app.route('/')
def root():
    #default html file for root path
    return app.send_static_file('index.html')
  
  
@app.route('/webhook', methods=['POST'])
def df_webhook():
    data = request.get_json(silent=True)
    intent = data["queryResult"]["intent"]["displayName"]
    url = 'https://api.rootnet.in/covid19-in/unofficial/covid19india.org/statewise'
    
    if intent == "state_status": 
        response = requests.get(url)

        payload = response.json()

        statewise = payload["data"]["statewise"]
        df = pd.read_json(json.dumps(statewise))
        state_name = data["queryResult"]["parameters"]["state"]
        df_filtered = df[df['state'] == state_name]
        
        status = data["queryResult"]["parameters"]["casestatus"]
        
        if df_filtered.shape[0] > 0:
            state_obj = df_filtered.iloc[0].to_dict()
            if status in ["recovered", "deaths", "active"]: 
                resp = {"fulfillmentText": "Number of {} cases in {}: {}".format(status, state_name, state_obj[status]), "fulfillmentMessages": []}
                return jsonify(resp)
            else:
                #return jsonify(state_obj)
                resp = {"fulfillmentText": "Total confirmed cases in {}: {}".format(state_name, state_obj["confirmed"]), "fulfillmentMessages": [create_card(state_obj)]}
                return jsonify(resp)
        else:
            return jsonify({"fulfillmentText" : "Please provide a valid state name",  "fulfillmentMessages": []})
      
    elif intent == "country_status": 
        response = requests.get(url)

        payload = response.json()
        
        status = data["queryResult"]["parameters"]["casestatus"]

        total = payload["data"]["total"]
        
        if status in ["recovered", "deaths", "active"]: 
            resp = {"fulfillmentText": "Number of {} cases in India: {}".format(status, total[status]), "fulfillmentMessages": []}
            return jsonify(resp)
        else: 
            #return jsonify(total)    
            resp = {"fulfillmentText": "Total confirmed cases in India: {}".format(total["confirmed"]), "fulfillmentMessages": [create_card(total)]}
            return jsonify(resp)
    
    elif intent == "state_district": 
        response = requests.get("https://api.covid19india.org/state_district_wise.json")

        payload = response.json()
        state_name = data["queryResult"]["parameters"]["state"]
        
        if state_name in payload: 
            dist_data = payload[state_name]["districtData"]
            text = "Confirmed cases in districts of {}:\n".format(state_name)
            
            for dist in dist_data: 
                text += dist + " - " + str(dist_data[dist]["confirmed"]) + "\n"
            
            resp = {"fulfillmentText": text, "fulfillmentMessages": []}
            return jsonify(resp)
        else: 
            return jsonify({"fulfillmentText" : "Please provide a valid state name",  "fulfillmentMessages": []})
    
    else: 
        return jsonify({"error" : "invalid intent"})
      
      
def create_card(obj):
    r = {"card": {}}
    r["card"]["title"] = "Confirmed cases: {}".format(obj["confirmed"])
   
    if "state" not in obj: 
        r["card"]["subtitle"] = "in India"
    else: 
        r["card"]["subtitle"] = "in {}".format(obj["state"])
        
    imageData = str(obj["active"]) + "," + str(obj["recovered"]) + "," + str(obj["deaths"])
    #r["card"]["imageUri"] = "https://quickchart.io/chart?c={type:'pie',data:{labels:['active', 'recovered','deaths'], datasets:[{data:[" + imageData + "]}]}}"
    
    r["card"]["imageUri"] = "https://chart.googleapis.com/chart?cht=p&chs=350x200&chd=t:" + imageData + "&chl=" + imageData.replace(",", "|") + "&chdl=active|recovered|deaths&chds=a&chco=1eaeef,1fef66,e46334"
        
    r["card"]["buttons"] = [{"postback": "https://www.covid19india.org/", "text": "More Info"}]

    return r
    

if __name__ == '__main__':
    app.run()