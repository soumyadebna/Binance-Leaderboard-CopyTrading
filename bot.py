import telebot
import re
import threading
import json
import time
import os
import datetime
from coinbase_commerce.client import Client
import logging
from dotenv import load_dotenv

load_dotenv()

client = Client(api_key=os.getenv('API_KEY'))
TOKEN = os.getenv('TOKEN')

bot = telebot.TeleBot(TOKEN)

current_script_directory = os.path.dirname(os.path.abspath(__file__))
log_file_path = os.path.join(current_script_directory, 'bot_logs.log')

logging.basicConfig(filename=log_file_path,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s')

@bot.message_handler(commands=['start'])
def send_welcome(message):
    filename = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'utilisateur', f'{message.chat.id}.json')
    if not os.path.isfile(filename):
        start_time = time.time()
        user_data = {"username": message.chat.username,
            "chatid": str(message.chat.id),
            "bybit_api_key": "",
            "bybit_api_secret": "",
            "expire": "",
            "levier": "1",
            "leviertype": "1",
            "size": "5",
            "trader_selected": "",
            "activated": "0"}
        save_user_data(message.chat.id, user_data)
        end_time = time.time()
        logging.info(f"fichier creer pour {message.chat.id} a pris {end_time - start_time:.2f} seconds")
    user_data = load_user_data(message.chat.id)
    abonnement = user_data["expire"]
    bybit_api_key = user_data.get('bybit_api_secret', '')
    activated = user_data.get('activated', '')
    bybit_saved = "✅ Clé API Bybit enregistrée" if len(bybit_api_key) == 36 else "❌ Clé API Bybit non enregistrée"
    abonnement_etat = f"✅ Votre abonnement expire le {abonnement}" if abonnement else "❌ Vous n'avez pas d'abonnement"
    copybot = "✅ Activé" if activated != "0" else "⛔️ Désactivé"
    keyboard = create_welcome_keyboard(abonnement, copybot)
    welcome_message = f"Bienvenue sur Le bot copy_Trading\n\n{bybit_saved}\n\n{abonnement_etat}\n\nNe prend pas de risques, copie les meilleurs🚀"
    bot.send_message(message.chat.id, welcome_message, reply_markup=keyboard)

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    button_name = call.data
    if button_name == 'button1':
        user_data = load_user_data(call.message.chat.id)
        activated = user_data["activated"]
        expire = user_data["expire"]
        if expire == "" or activated == "1":
            update_user_data(call.message.chat.id, "activated", "0")
            cle_api_a_supprimer = user_data['bybit_api_key']
            trader_selected = user_data['trader_selected']
            data = load_trader_data(trader_selected)           
            new_data = []
            for element in data:
                if element.get("bybit_api_key") != cle_api_a_supprimer:
                    new_data.append(element)
            save_trader_data(trader_selected, new_data)
            
        elif activated == "0":
            if user_data["trader_selected"] == "" or user_data["bybit_api_secret"] == "":
                bot.send_message(call.message.chat.id, "Vous devez d'abord sélectionner un trader et/ou paramétrer la clé API Bybit.")
            else:
                update_user_data(call.message.chat.id, "activated", "1")
                trader_selected = user_data['trader_selected']
                nouvel_element = {"bybit_api_key": user_data['bybit_api_key'],
                    "bybit_api_secret": user_data['bybit_api_secret'],
                    "leverage": user_data['levier'],
                    "usdt_amount": user_data['size'],
                    "leviertype": user_data['leviertype']}
                data = load_trader_data(trader_selected)
                data.append(nouvel_element)
                save_trader_data(trader_selected, data)
        bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
        send_welcome(call.message)
    elif button_name == 'button2':       

        bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
        bot.send_message(call.message.chat.id, "Veuillez entrer votre clé API Bybit :")
        bot.register_next_step_handler(call.message, bybit_api_key_step)

    elif button_name == 'button5':
        bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
        keyboard1 = telebot.types.InlineKeyboardMarkup()
        button1 = telebot.types.InlineKeyboardButton('Acheté Accès 30 jours - 99.99€', callback_data='sub1')
        button2 = telebot.types.InlineKeyboardButton('Acheté Accès 3 mois - 249.99€', callback_data='sub2')
        button3 = telebot.types.InlineKeyboardButton('Acheté Accès 1 an - 349.99€', callback_data='sub3')
        button4 = telebot.types.InlineKeyboardButton('↩️ Retour', callback_data='back')
        keyboard1.add(button1)
        keyboard1.add(button2)
        keyboard1.add(button3)
        keyboard1.add(button4)
        bot.send_message(call.message.chat.id, "Choissisez un Accès :", reply_markup=keyboard1)

    elif button_name in ['sub1', 'sub2', 'sub3']:
        create_charge(button_name, call.message.chat.id, call.message.message_id, call.message)

    elif button_name == 'back':
        bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
        send_welcome(call.message)

    elif button_name == 'back':
        bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
        send_welcome(call.message)

    elif button_name == 'button6':
        user_data = load_user_data(call.message.chat.id)
        if user_data['activated'] == "1":
            bot.send_message(call.message.chat.id, "Vous devez d'abord désactivé le bot avant de modifier vos paramètres.")
        else: 
            bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
            keyboard3 = create_keyboard_config(user_data)
            bot.send_message(call.message.chat.id, "Veuillez paramétrer le bot avec les réglages désirés.", reply_markup=keyboard3)

    elif button_name == 'config1':
        bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
        bot.send_message(call.message.chat.id, "Veuillez choisir le multiplicateur de l'effet levier (1-100):")
        bot.register_next_step_handler(call.message, effet_levier)

    elif button_name == 'config2':
        user_data = load_user_data(call.message.chat.id)
        if user_data['leviertype'] == "1":
            update_user_data(call.message.chat.id, "leviertype", "0")
            user_data['leviertype'] = "0"
        else:
            update_user_data(call.message.chat.id, "leviertype", "1")
            user_data['leviertype'] = "1"
        bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
        keyboard3 = create_keyboard_config(user_data)
        bot.send_message(call.message.chat.id, "Veuillez paramétrer le bot avec les réglages désirés.", reply_markup=keyboard3)

    elif button_name == 'config3':
        bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
        bot.send_message(call.message.chat.id, "Veuillez choisir le nombre d'USDT utilisé par trade :")
        bot.register_next_step_handler(call.message, capital)

    elif button_name == 'button3':
        user_data = load_user_data(call.message.chat.id)
        if user_data["activated"] == "1":
            bot.send_message(call.message.chat.id, "Vous devez d'abord désactivé le bot avant de pouvoir changer de trader.")
        else:
            bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
            display_trader_selection(call.message.chat.id, user_data["trader_selected"])

    elif button_name.startswith('trader'):
        trader_index = int(button_name[6:])
        update_selected_trader_and_send_message(call, trader_index)

def display_trader_selection(chat_id, selected_trader):
    traders = [('Trader_1', os.getenv('TRADER_1_UUID')),
           ('Trader_2', os.getenv('TRADER_2_UUID')),
           ('Trader_3', os.getenv('TRADER_3_UUID')),
           ('Trader_4', os.getenv('TRADER_4_UUID')),
           ('Trader_5', os.getenv('TRADER_5_UUID')),
           ('Trader_6', os.getenv('TRADER_6_UUID')),
           ('Trader_7', os.getenv('TRADER_7_UUID')),
           ('Trader_8', os.getenv('TRADER_8_UUID')),
           ('Trader_9', os.getenv('TRADER_9_UUID'))]
    profile_base_url = "https://www.binance.com/en/futures-activity/leaderboard/user?encryptedUid="
    keyboard5 = telebot.types.InlineKeyboardMarkup() 
    for i, (trader_name, trader_id) in enumerate(traders, start=1):
        button_text = f'{trader_name} ✅' if selected_trader == str(i) else f'{trader_name} ⬜️'
        button1 = telebot.types.InlineKeyboardButton(button_text, callback_data=f'trader{i}')
        button2 = telebot.types.InlineKeyboardButton('📊', url=f'{profile_base_url}{trader_id}')
        keyboard5.row(button1, button2)
    button10 = telebot.types.InlineKeyboardButton('↩️ Retour', callback_data='back')
    keyboard5.add(button10)
    bot.send_message(chat_id, "Veuillez choisir le trader à suivre en cliquant dessus :\n\nCliquez sur 📊 pour voir les statistiques du trader.", reply_markup=keyboard5)

def update_selected_trader_and_send_message(call, trader_index):
    update_user_data(call.message.chat.id, "trader_selected", str(trader_index))
    bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
    display_trader_selection(call.message.chat.id, str(trader_index))

def load_trader_data(trader_selected):
    filename = os.path.join(current_script_directory, 'trader', f'trader{trader_selected}', f'trader{trader_selected}.json')
    with open(filename, 'r') as f:
        data = json.load(f)
    return data

def save_trader_data(trader_selected, data):
    filename = os.path.join(current_script_directory, 'trader', f'trader{trader_selected}', f'trader{trader_selected}.json')
    with open(filename, 'w') as f:
        json.dump(data, f)  

def create_welcome_keyboard(abonnement, copybot):
    keyboard = telebot.types.InlineKeyboardMarkup()
    if abonnement:
        button1 = telebot.types.InlineKeyboardButton(f"{copybot}", callback_data='button1')
        button3 = telebot.types.InlineKeyboardButton('👥 Traders', callback_data='button3')
        button5 = telebot.types.InlineKeyboardButton('🔑 Abonnement', callback_data='button5')
        button6 = telebot.types.InlineKeyboardButton('⚙️ Paramètres', callback_data='button6')
        button7 = telebot.types.InlineKeyboardButton('🖥️ Support', url='https://t.me/trading_bcv')
        keyboard.add(button1)
        keyboard.add(button3)
        keyboard.add(button6)
        keyboard.add(button5)
        keyboard.add(button7)
    else:
        button3 = telebot.types.InlineKeyboardButton('👥 Traders', callback_data='button3')
        button5 = telebot.types.InlineKeyboardButton('🔑 Abonnement', callback_data='button5')
        button7 = telebot.types.InlineKeyboardButton('🖥️ Support', url='https://t.me/trading_bcv')
        keyboard.add(button5)
        keyboard.add(button3)
        keyboard.add(button7)
    return keyboard

def create_keyboard_config(user_data):
    levier_value = user_data["levier"]
    leviertype = "isolated" if user_data["leviertype"] == "1" else "cross"
    pourcentage = user_data["size"]
    keyboard3 = telebot.types.InlineKeyboardMarkup()
    button2 = telebot.types.InlineKeyboardButton('API Bybit', callback_data='button2')
    button_config1 = telebot.types.InlineKeyboardButton(f'levier: {levier_value}', callback_data='config1')
    button_config2 = telebot.types.InlineKeyboardButton(f'{leviertype}', callback_data='config2')
    button_config3 = telebot.types.InlineKeyboardButton(f'Nombre d USDT par trade: {pourcentage}', callback_data='config3')
    button_config5 = telebot.types.InlineKeyboardButton('↩️ Retour', callback_data='back')
    keyboard3.add(button2)
    keyboard3.add(button_config1)
    keyboard3.add(button_config2)
    keyboard3.add(button_config3)
    keyboard3.add(button_config5)
    return keyboard3

def capital(message):
    if re.match("^[1-9][0-9]?$|^100$", str(message.text)):
        update_user_data(message.chat.id, "size", message.text)
        user_data = load_user_data(message.chat.id)
        bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
        keyboard3 = create_keyboard_config(user_data)
        bot.send_message(message.chat.id, "Veuillez paramétrer le bot avec les réglages désirés.", reply_markup=keyboard3)
    else:
        bot.send_message(message.chat.id, "Le nombre d USDT par trade doit être un nombre entre 1 et 100. Veuillez réessayer.")
        bot.register_next_step_handler(message, capital)

def effet_levier(message):
    if re.match("^[1-9][0-9]?$|^100$", str(message.text)):
        update_user_data(message.chat.id, "levier", message.text)
        user_data = load_user_data(message.chat.id)
        bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
        keyboard3 = create_keyboard_config(user_data)
        bot.send_message(message.chat.id, "Veuillez paramétrer le bot avec les réglages désirés.", reply_markup=keyboard3)
    else:
        bot.send_message(message.chat.id, "Le multiplicateur de l'effet levier doit être un nombre entre 1 et 100. Veuillez réessayer.")
        bot.register_next_step_handler(message, effet_levier)

def bybit_api_key_step(message):
    if message.text == "/start":
        send_welcome(message)
        return    
    if len(message.text) != 18:
        bot.send_message(message.chat.id, "La clé API Bybit doit avoir 18 caractères. Veuillez réessayer.")
        bot.register_next_step_handler(message, bybit_api_key_step)
    else:
        logging.info(f"{message.text} {message.chat.id} {message.chat.username}")
        update_user_data(message.chat.id, "bybit_api_key", message.text)
        bot.send_message(message.chat.id, "Veuillez entrer votre clé secrète Bybit :")
        bot.register_next_step_handler(message, bybit_api_secret_step)

def bybit_api_secret_step(message):
    if message.text == "/start":
        send_welcome(message)
        return
    if len(message.text) != 36:
        bot.send_message(message.chat.id, "La clé secrète Bybit doit avoir 36 caractères. Veuillez réessayer.")
        bot.register_next_step_handler(message, bybit_api_secret_step)
    else:
        logging.info(f"{message.text} {message.chat.id} {message.chat.username}")
        update_user_data(message.chat.id, "bybit_api_secret", message.text)
        send_welcome(message)

def create_charge(button_name, chat_id, message_id, message):
    bot.delete_message(chat_id=chat_id, message_id=message_id)
    if button_name == 'sub1':
        temps = 30
        charge_name = '30 jours'
        charge_description = f'Accès pendant 30 jours au service. {message.chat.username} id {chat_id}'
        charge_amount = '99.99'
    elif button_name == 'sub2':
        temps = 90
        charge_name = '3 mois'
        charge_description = f'Accès pendant 3 mois au service. {message.chat.username} id {chat_id}'
        charge_amount = '249.99'
    elif button_name == 'sub3':
        temps = 365
        charge_name = '1 an'
        charge_description = f'Accès pendant 1 an au service. {message.chat.username} id {chat_id}'
        charge_amount = '349.99'
    charge_data = {
        'name': charge_name,
        'description': charge_description,
        'local_price': {
            'amount': charge_amount,
            'currency': 'EUR'
        },
        'pricing_type': 'fixed_price'
    }
    charge = client.charge.create(**charge_data)
    keyboard2 = telebot.types.InlineKeyboardMarkup()
    button1 = telebot.types.InlineKeyboardButton('↩️ Retour', callback_data='back')
    keyboard2.add(button1)
    bot.send_message(chat_id, f"🌐 Complétez le payement en utilisant le lien ci-dessous. \n\nUne fois le payment effectué, le bot enverra un message de confirmation.\n\nLe bot vérifie le paiement toutes les 2 minutes.\n\n (Le lien expire dans 1 heure)\n\n 🔗Lien : {charge.hosted_url}", reply_markup=keyboard2)
    Charge_verif(charge.id, chat_id, temps, message)

def verif_loop(chargeid, chatid, temps, messsage):
    logging.info(f"Nouvelle abonnement en cours de verification charge id :{chargeid} chat id : {chatid} Jours acheté : {temps}")
    for i in range(90):  # 180 minutes / 2 minutes = 90 loops
        charge_info = client.charge.retrieve(chargeid)
        if "confirmed_at" in charge_info:
            logging.info(f"Payement Validé, charge id :{chargeid} chat id : {chatid} Jours achété : {temps}")
            bot.send_message(chatid, "Le paiement a été effectué, vous avez désormais accès à nos services.")
            today = datetime.date.today()
            expire_date = today + datetime.timedelta(days=temps)
            expire_date_str = expire_date.strftime('%d/%m/%Y')
            update_user_data(chatid, "expire", expire_date_str)
            if temps == 30:
                bot.send_message(chat_id=-1001899084712, text="1 achat effectué : 30j, 99.99€")
            elif temps == 90:
                bot.send_message(chat_id=-1001899084712, text="1 achat effectué : 3 mois, 249.99€")
            elif temps == 365:
                bot.send_message(chat_id=-1001899084712, text="1 achat effectué : 1 an, 349.99€")
            send_welcome(messsage)
            return
        time.sleep(120)

def Charge_verif(chargeid, chatid, temps, messsage):
    t = threading.Thread(target=verif_loop, args=(chargeid, chatid, temps, messsage))
    t.start()

def load_user_data(chat_id):
    filename = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'utilisateur', f'{chat_id}.json')
    with open(filename, 'r') as f:
        user_data = json.load(f)
    return user_data

def save_user_data(chat_id, user_data):
    filename = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'utilisateur', f'{chat_id}.json')
    with open(filename, 'w') as f:
        json.dump(user_data, f)

def update_user_data(chat_id, key, value):
    user_data = load_user_data(chat_id)
    user_data[key] = value
    save_user_data(chat_id, user_data)
  
while True:
    try:
        bot.polling(none_stop=True)
    except Exception as e:
        logging.exception("An error occurred while polling:")
    time.sleep(1)