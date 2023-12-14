import requests,pprint,json

url = "https://coinranking1.p.rapidapi.com/coins"

querystring = {"referenceCurrencyUuid":"yhjMzLPhuIDl","timePeriod":"24h","tiers[0]":"1","orderBy":"marketCap","orderDirection":"desc","limit":"500","offset":"0"}

headers = {
	"X-RapidAPI-Key": "cd8cd7d41emsh4ba0432bad96d8dp186666jsn22cf5af893bf",
	"X-RapidAPI-Host": "coinranking1.p.rapidapi.com"
}

response = requests.get(url, headers=headers, params=querystring)

with open("/Users/sarthakgarg/Desktop/Airflow_projects/raw_data/test.json",'w') as json_file:
    json.dump(response.json()["data"]["coins"],json_file)








    # url= "https://api-generator.retool.com/MaUeBz/data"
    # response=requests.get(url)
    # json_file_path="/opt/airflow/files/test.json"

    # if response.status_code==200:
    #     data=response.json()

    #     with open(json_file_path,'w+') as datafile:
    #         json.dump(data, datafile)
    #     print("json file created")

    # else:
    #     print(f"API request failed with status code: {response.status_code}")
