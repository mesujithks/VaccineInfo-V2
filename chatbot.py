from datetime import date
from db import DBHelper
import json
import requests
import time
import threading
import urllib
import logging

TOKEN = "<your telegaram bot token>"
URL = "https://api.telegram.org/bot{}/".format(TOKEN)

header = {'Accept': 'application/json',
          'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0'}

states = [{"state_id": 17, "state_name": "Kerala"}]
districts = []
doseTypes = [{"dose_type": "DOSE 1"}, {
    "dose_type": "DOSE 2"}, {"dose_type": "BOTH DOSE"}]
vaccineTypes = [{"vaccine": "COVISHIELD"}, {"vaccine": "COVAXIN"}, {
    "vaccine": "SPUTNIK V"}, {"vaccine": "ANY VACCINE"}]
feeTypes = [{"fee_type": "FREE"}, {
    "fee_type": "PAID"}, {"fee_type": "ANY FEE"}]
ageLimit = [{"age_limit": "18 PLUS"}, {
    "age_limit": "40 PLUS"}, {"age_limit": "ANY AGE"}]

defaultOptions = {"vaccine": "ANY VACCINE", "fee_type": "ANY FEE",
                  "age_limit": "ANY AGE", "dose_type": "BOTH DOSE"}

log = logging.getLogger("vaccine-logger")
log.setLevel(logging.DEBUG)
logFormatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fileHandler = logging.FileHandler("app.log")
fileHandler.setFormatter(logFormatter)
log.addHandler(fileHandler)


def _url(path):
    return 'https://cdn-api.co-vin.in/api/v2' + path


def get_url(url):
    response = requests.get(url)
    content = response.content.decode("utf8")
    return content


def get_json_from_url(url):
    content = get_url(url)
    js = json.loads(content)
    return js


def get_updates(offset=None):
    url = URL + "getUpdates"
    if offset:
        url += "?offset={}".format(offset)
    js = get_json_from_url(url)
    return js


def get_last_update_id(updates):
    update_ids = []
    for update in updates["result"]:
        update_ids.append(int(update["update_id"]))
    return max(update_ids)


def build_keyboard(items, key):
    keyboard = [[item[key]] for item in items]
    reply_markup = {"keyboard": keyboard, "one_time_keyboard": True}
    return json.dumps(reply_markup)


def echo_all(updates, dataBase):
    log.info(updates)
    for update in updates["result"]:
        text = ""
        if( "text" in update["message"]):
        	text = update["message"]["text"]
        chat_id = update["message"]["chat"]["id"]
        username = update["message"]["chat"]["first_name"]
        if "username" in update["message"]["chat"]:
            tg_user_id = update["message"]["chat"]["username"]
        else:
            tg_user_id = ""
        if dataBase.check_user_by_chat_id(chat_id) == 0:
            myDistricts = []
            myPreference = defaultOptions
        else:
            myDistricts = dataBase.get_districts_by_chat_id(chat_id)
            myPreference = dataBase.get_preference_by_chat_id(chat_id)

        if text == "/start":
            if dataBase.check_user_by_chat_id(chat_id) == 0:
                dataBase.add_user(chat_id, username, tg_user_id,
                                  json.dumps(myPreference))
                msg = "You are subcribed to Vaccine Updates! Thank you {}.\n\n*Command List*\n\n/start - start the bot\n/addcity - add new city to watch list\n/setdosetype - select dose type\n/setvaccinetype - select vaccine type\n/setfeetype - select vaccine fee type\n/setagelimit - select age limit\n/subscriptions - view watch list\n/mypreference - view my preference".format(
                    username)
                send_message(msg, chat_id)
            else:
                msg = "You are alreay subcribed to Vaccine Updates! Thank you {}.\n\n*Command List*\n\n/start - start the bot\n/addcity - add new city to watch list\n/setdosetype - select dose type\n/setvaccinetype - select vaccine type\n/setfeetype - select vaccine fee type\n/setagelimit - select age limit\n/subscriptions - view watch list\n/mypreference - view my preference".format(
                    username)
                send_message(msg, chat_id)
        elif text == "/addcity":
            keyboard = build_keyboard(states, 'state_name')
            send_message("Select a state", chat_id, keyboard)

        elif getStateByText(text) != None:
            state = getStateByText(text)
            keyboard = build_keyboard(districts, 'district_name')
            send_message("Select a District", chat_id, keyboard)
            dataBase.set_state_by_chat_id(json.dumps(state), chat_id)

        elif getDistrictByText(text) != None:
            district = getDistrictByText(text)
            if len(list(filter(lambda dict1: dict1['district_id'] == district['district_id'], myDistricts))) == 0:
                myDistricts.append(district)
            dataBase.set_city_by_chat_id(json.dumps(myDistricts), chat_id)
            send_message(text + " added to My Watchlist", chat_id)

        elif text == "/setdosetype":
            keyboard = build_keyboard(doseTypes, 'dose_type')
            send_message("Select Dose Type", chat_id, keyboard)
        elif len(list(filter(lambda option: option['dose_type'] == text, doseTypes))) == 1:
            myPreference['dose_type'] = text
            dataBase.save_options_by_chat_id(json.dumps(myPreference), chat_id)

        elif text == "/setvaccinetype":
            keyboard = build_keyboard(vaccineTypes, 'vaccine')
            send_message("Select a vaccine", chat_id, keyboard)
        elif len(list(filter(lambda option: option['vaccine'] == text, vaccineTypes))) == 1:
            myPreference['vaccine'] = text
            dataBase.save_options_by_chat_id(json.dumps(myPreference), chat_id)

        elif text == "/setfeetype":
            keyboard = build_keyboard(feeTypes, 'fee_type')
            send_message("Select a fee type", chat_id, keyboard)
        elif len(list(filter(lambda option: option['fee_type'] == text, feeTypes))) == 1:
            myPreference['fee_type'] = text
            dataBase.save_options_by_chat_id(json.dumps(myPreference), chat_id)

        elif text == "/setagelimit":
            keyboard = build_keyboard(ageLimit, 'age_limit')
            send_message("Select age limit", chat_id, keyboard)
        elif len(list(filter(lambda option: option['age_limit'] == text, ageLimit))) == 1:
            myPreference['age_limit'] = text
            dataBase.save_options_by_chat_id(json.dumps(myPreference), chat_id)

        elif text == "/subscriptions":
            myMasg = "*COVID-19 Vaccine Alerts - Your subcribed Districts*\n"
            if(len(myDistricts) > 0):
                count = 1
                for i in myDistricts:
                    myMasg = myMasg + "\n" + \
                        str(count) + ". " + i['district_name']
                    count = count + 1
            else:
                myMasg = myMasg + "\nYour watch list is empty"
            send_message(myMasg, chat_id)

        elif text == "/mypreference":
            myMasg = "*COVID-19 Vaccine Alerts - Your Prefences*\n"
            myMasg = myMasg + "\n1. Vaccine: " + myPreference['vaccine']
            myMasg = myMasg + "\n2. Dose Type: " + myPreference['dose_type']
            myMasg = myMasg + "\n3. Age Limit: " + myPreference['age_limit']
            myMasg = myMasg + "\n4. Fee type: " + myPreference['fee_type']
            send_message(myMasg, chat_id)

        elif text == "/mesu" and chat_id == 236033319:
            log.info("Interrupt Message Recieved")
            send_message("Interrupt Message Recieved", chat_id)
            raise Exception("Interrupt Message Recieved")
        elif chat_id == 236033319:
            send_message("echo : " + text, chat_id)
        else:
            send_message("Invalid command", chat_id)


def get_last_chat_id_and_text(updates):
    num_updates = len(updates["result"])
    last_update = num_updates - 1
    text = updates["result"][last_update]["message"]["text"]
    chat_id = updates["result"][last_update]["message"]["chat"]["id"]
    return (text, chat_id)


def send_message(text, chat_id):
    text = urllib.parse.quote_plus(text)
    url = URL + \
        "sendMessage?text={}&chat_id={}&parse_mode=Markdown".format(
            text, chat_id)
    get_url(url)


def send_message(text, chat_id, reply_markup=None):
    text = urllib.parse.quote_plus(text)
    url = URL + \
        "sendMessage?text={}&chat_id={}&parse_mode=Markdown".format(
            text, chat_id)
    if reply_markup:
        url += "&reply_markup={}".format(reply_markup)
    get_url(url)


def main():
    getStates()
    getDistricts(states[0]['state_id'])
    dataBase = DBHelper()
    dataBase.setup()

    ekmListerner = threading.Thread(target=listerner, args=(307,))
    ekmListerner.daemon = True
    ekmListerner.start()

    alpListerner = threading.Thread(target=listerner, args=(301,))
    alpListerner.daemon = True
    alpListerner.start()

    ktmListerner = threading.Thread(target=listerner, args=(304,))
    ktmListerner.daemon = True
    ktmListerner.start()

    last_update_id = None
    while True:
        print(str(last_update_id) + " - Tealegram Listerner Running")
        updates = get_updates(last_update_id)
        if len(updates["result"]) > 0:
            last_update_id = get_last_update_id(updates) + 1
            echo_all(updates, dataBase)
        time.sleep(0.5)


def getStates():
    pass
    """ global states
    resp = requests.get(_url('/admin/location/states'), headers = header)

    if resp.status_code != 200:
        log.info(resp)
    else:
        states = resp.json()['states'] """


def getDistricts(state_id):
    global districts
    resp = requests.get(
        _url('/admin/location/districts/' + str(state_id)), headers=header)

    if resp.status_code != 200:
        log.info(resp)
    else:
        districts = resp.json()['districts']


def getStateByText(text):
    if len(list(filter(lambda state: state['state_name'] == text, states))) == 1:
        return list(filter(lambda state: state['state_name'] == text, states))[0]
    else:
        return None


def getDistrictByText(text):
    global districts
    if len(list(filter(lambda district: district['district_name'] == text, districts))) == 1:
        return list(filter(lambda district: district['district_name'] == text, districts))[0]
    else:
        return None


def getDistrictById(id):
    global districts
    if len(list(filter(lambda district: district['district_id'] == id, districts))) == 1:
        return list(filter(lambda district: district['district_id'] == id, districts))[0]
    else:
        return None


def listerner(district_id):
    dataBaseListener = DBHelper()
    centerDatas = []
    currentFound = []
    previousFound = {}
    availableCenters = []
    while True:
        print(str(district_id) + " - Thread is running")
        log.info(str(district_id) + " - Thread is running")
        availabilityFound = False
        today = date.today()
        d1 = today.strftime("%d/%m/%Y")
        #previousFound = currentFound
        currentFound = []
        availableCenters = []
        resp = requests.get(_url('/appointment/sessions/public/calendarByDistrict'), params={
            "district_id": district_id,
            "date": d1
        }, headers=header)

        if resp.status_code != 200:
            log.info(resp)
        else:
            centerDatas = resp.json()['centers']

        for user in dataBaseListener.get_all_users():
            availabilityFound = False
            currentFound = []
            availableCenters = []
            myDistricts = []
            try:
                myDistricts = json.loads(user['districts'])
                myPreference = json.loads(user['options'])
            except Exception:
                myDistricts = []
                myPreference = defaultOptions

            if len(list(filter(lambda district: district['district_id'] == district_id, myDistricts))) == 1:

                for center in centerDatas:
                    for session in center['sessions']:
                        if (session['available_capacity'] > 0
                            and ((myPreference['dose_type'] == "DOSE 1" and session['available_capacity_dose1'] > 0)
                                 or (myPreference['dose_type'] == "DOSE 2" and session['available_capacity_dose2'] > 0)
                                 or (myPreference['dose_type'] == "BOTH DOSE" and True))
                            and ((myPreference['vaccine'] == "COVISHIELD" and session['vaccine'].upper() == "COVISHIELD")
                                 or (myPreference['vaccine'] == "COVAXIN" and session['vaccine'].upper() == "COVAXIN")
                                 or (myPreference['vaccine'] == "SPUTNIK V" and session['vaccine'].upper() == "SPUTNIK V")
                                 or (myPreference['vaccine'] == "ANY VACCINE" and True))
                            and ((myPreference['fee_type'] == "FREE" and center['fee_type'].upper() == "FREE")
                                 or (myPreference['fee_type'] == "PAID" and center['fee_type'].upper() == "PAID")
                                 or (myPreference['fee_type'] == "ANY FEE" and True))
                            and ((myPreference['age_limit'] == "18 PLUS" and session['min_age_limit'] >= 18 and session['min_age_limit'] < 40)
                                 or (myPreference['age_limit'] == "40 PLUS" and session['min_age_limit'] >= 40)
                                 or (myPreference['age_limit'] == "ANY AGE" and True))):
                            availabilityFound = True
                            if len(list(filter(lambda aCenter: aCenter['name'] == center['name'], availableCenters))) == 0:
                                availableCenters.append(center)
                                currentFound.append(center['name'])

                if (availabilityFound):
                    try:
                        if(previousFound[user['chat_id']] == None):
                            previousFound[user['chat_id']] = []
                    except KeyError:
                        previousFound[user['chat_id']] = []
                    currentFound.sort()
                    previousFound[user['chat_id']].sort()
                    if(district_id ==304):
                        print("previousFound ",previousFound[user['chat_id']],"\ncurrentFound ",currentFound)
                    if(currentFound != previousFound[user['chat_id']] and len(currentFound) > 0 ):
                        previousFound[user['chat_id']] = currentFound
                        log.info(str(len(availableCenters)) +
                                 " - Available Centers Found at -" + str(district_id))

                        msgString = "*COVID-19 Vaccine Alerts - " + \
                            getDistrictById(district_id)[
                                'district_name'] + "*\n"
                        index = 0
                        for center in availableCenters:
                            index = index + 1
                            msgString = msgString + "\n*" + \
                                str(index) + ". Center: " + \
                                center['name'] + "*\n"
                            msgString = msgString + \
                                "\nAddress: " + center['address']
                            msgString = msgString + "\nPincode: " + \
                                str(center['pincode'])
                            msgString = msgString + \
                                "\nVaccine Price: " + center['fee_type']

                            for session in center['sessions']:
                                if(session['available_capacity'] > 0):
                                    msgString = msgString + "\n\n_*Session Available on " + \
                                        session['date'] + "*_\n\n"
                                    msgString = msgString + "Total Availabity: " + \
                                        str(session['available_capacity'])
                                    msgString = msgString + \
                                        "\nDate: " + session['date']
                                    msgString = msgString + \
                                        "\nVaccine: " + session['vaccine']
                                    msgString = msgString + "\nAge Limit: " + \
                                        str(session['min_age_limit']) + "+"
                                    msgString = msgString + "\nDose 1 Availabity: " + \
                                        str(session['available_capacity_dose1'])
                                    msgString = msgString + "\nDose 2 Availabity: " + \
                                        str(session['available_capacity_dose2'])
                                    msgString = msgString + "\nSlots: " + \
                                        json.dumps(session['slots'])

                            msgString = msgString + "\n------------------------------------------------------"
                            if(len(msgString) > 3096):
                                send_message(msgString, user['chat_id'])
                                msgString = "*COVID-19 Vaccine Alerts - " + \
                                    getDistrictById(district_id)[
                                        'district_name'] + "*\n"
                        msgString = msgString + "\n\n\n*Register to get vaccinated now!*"
                        send_message(msgString, user['chat_id'])

        time.sleep(10)


if __name__ == '__main__':
    try:
        main()
    except (KeyboardInterrupt, Exception) as e:
        log.error(e)
        log.info("Interrupt")
        send_message("App Down", 236033319)
