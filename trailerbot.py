# coding:utf8
# Importations
from binance_client import Client
import binance_enums, binance_exceptions, binance_helpers
from threading import Thread
from time import sleep
import requests
from itsdangerous import URLSafeSerializer
import ast
from utility import *

# variables
admin_bots = []
launched_bots = []
bots = []
tokens = []
token_database = []
token_db_dic = {}
current_users = []

trail_bot_tk, log_bot_tk, lch_bot_tk, tk_manager_tk = '', '', '', ''
client0 = Client('sjbdv', 'ksjbvdzvb')

# Fonctions
def starter():
    try :
        mdp = input('Hey Master ! Hope you have a nice day. Please input your password :')
        tokens = decrypter(mdp, '.eJwtzs2OgjAUQOFnUdcmvXBpb51VERSHVlHjD26MYJzM0AEcYtC3l4muzupLTh-AcSERCUZKhfnPCT5LvfMvVzFWVKXWiCTyEWfZYRHXeW_wMeiB40gH0AXWken6vvVYMOOJPmduajFcFWcrg9yY-E9a3bwIAxDkAHkdmWRFUfnH8VRBvBDB9xI1PsLmWhpMuTlONi8CQkqXONH_mK2TtqSa3-ZRU9z95bDSt9W8UfvW-41y-fUmSEx6XfpPBf07bg.qCeJwuIef3w2cvy2OM14ruebscM','list')
        client0apis = decrypter(mdp, 'IlhkVU5BaWp3dWRVeXNud05jbEo4NUl4ekpJaGZZY0ZpaURHektUVE9NUzk5S2hHUVFHNTV2UTZHSDdtQXlWVU4gISM7IyFURkJHYVllT0RBOGlnSlFzdFUxYUVHOENXTjRDTkhmWjVCUExpYXE0NzROcjVWbkRGRGRmUndKWGFBZGh6enJYIg.c21AIGR8G18-BmMrMlkdnYw66Q8','list')
        pack = [tokens, client0apis]
        return pack
    except Exception as e:
        print('Oh, looks like there is a problem in the password you put... Please try again.')
        print('Error in [starter] function, known as : {}'.format(e))
        starter()


def crypter(mdp, uncrypted, typed="(optionnal) None or list"):
    if typed == 'list':
        uncrypted = '!#;#!'.join(uncrypted)
    passwd = URLSafeSerializer(mdp)
    crypted = passwd.dumps(str(uncrypted))
    del passwd
    del mdp
    return crypted

def decrypter(mdp, crypted, typed="(optionnal) None, list or dict"): #Can be list or dict
    mdp = str(mdp)
    passwd = URLSafeSerializer(mdp)
    decrypted = passwd.loads(str(crypted))
    del mdp
    del passwd
    if typed=='list':
        decrypted = list(decrypted.split('!#;#!'))        
    elif typed=='dict':
        decrypted = ast.literal_eval(decrypted)
    return decrypted

def stansendlog(bot_message):
    global log_bot_tk, stan_id
    send_text ='https://api.telegram.org/bot' + str(log_bot_tk) + '/sendMessage?chat_id=' + str(stan_id) + '&parse_mode=Markdown&text=' + bot_message
    response = requests.get(send_text)
    return response.json()

def log_func(msg):
    with open('log.txt','a') as f:
        f.write('{}\n'.format(msg))
    stansendlog(msg)
  
def read_log():
    with open('log.txt','r') as f:
        txt=f.read()
    return txt

def is_correct_paire(client, paire, tradetype='spot'):
    try :
        infos = client.get_exchange_info()
        if tradetype == 'margin' :
            for i in range(len(infos['symbols'])):
                if infos['symbols'][i]['symbol'] == paire and infos['symbols'][i]['isMarginTradingAllowed'] :
                    return True
        else :
            for i in range(len(infos['symbols'])):
                if infos['symbols'][i]['symbol'] == paire :
                    return True
        return False
    except Exception as e:
        log_func('Error in [is_correct_paire] function ({}) gonna try again every 5 seconds'.format(e))
        sleep(2)
        is_correct_paire(client, paire, tradetype)

def round_x_to_y_decimal(x,y):
    return float(int(x*10**y)/10**y)

def telegram_bot_sendtext(bot_message, chat_id, bot_token=trail_bot_tk):
    send_text = 'https://api.telegram.org/bot' + str(bot_token) + '/sendMessage?chat_id=' + str(chat_id) + '&parse_mode=Markdown&text=' + str(bot_message)
    response = requests.get(send_text)
    return response.json()


def get_precision(paire, client):
    success, precision = False, 8
    try :
        infos = client.get_exchange_info()['symbols']
    except Exception as e:
            log_func('Error in getting prices from [get_precision()] line 38, known as : {} ; will try again every 5 seconds'.format(e))
            sleep(5)
            get_precision()
    for i in range(len(infos)):
        if infos[i]['symbol'] == paire:
            precision = int(infos[i]['baseAssetPrecision'])
            success = True
    if success == False :
        precision = 8
    return int(precision)

def get_spot_lastorder(client, paire):
    try :
        lastorder = client.get_all_orders(symbol=paire)[-1]
        executedQty = lastorder['executedQty']
        quoteQty = lastorder['cummulativeQuoteQty']
        return  executedQty, quoteQty
    except Exception as e:
        log_func('Error in [get_spot_lastorder], as : {} ; gonna try again in 5 seconds'.format(e))
        sleep(5)
        get_spot_lastorder(client, paire)
    
def get_margin_lastorder(client, paire):
    try :
        lastorder = client.get_margin_order(symbol=paire)[-1]
        executedQty = lastorder['executedQty']
        quoteQty = lastorder['cummulativeQuoteQty']
        return executedQty, quoteQty
    except Exception as e:
        log_func('Error in [get_margin_lastorder], as : {} ; gonna try again in 5 seconds'.format(e))
        sleep(5)
        get_margin_lastorder(client, paire)


def sell_x_pourcent(client, x, paire, asset_qty, trade_type='spot or margin'):
    precision = get_precision(paire, client)
    executedQty, quoteQty = 0, 0
    if trade_type == 'spot':
        try :
            client.order_market(paire, 'SELL', round_x_to_y_decimal(((float(x)*asset_qty)/100), precision))
            sleep(2)
            executedQty, quoteQty = get_spot_lastorder(client, paire)
        except Exception as e:
            log_func('Error in sell_x_pourcent, on paire : {} ; gonna try every 5 seconds'.format(e))
            sleep(5)
            sell_x_pourcent(client, x, paire, asset_qty, trade_type)
    elif trade_type == 'margin':
        try :
            client.create_margin_order(paire, 'SELL', 'MARKET', round_x_to_y_decimal(((float(x)*asset_qty)/100), precision))
            sleep(2)
            executedQty, quoteQty = get_margin_lastorder(client, paire)
        except Exception as e:
            log_func('Error in sell_x_pourcent, on paire : {} ; gonna try every 5 seconds'.format(e))
            sleep(5)
            sell_x_pourcent(client, x, paire, asset_qty, trade_type)
    sold = (float(x)*asset_qty)/100
    return executedQty, quoteQty


# Classes
class TrailerBot(Thread):
    """Bot de trailing"""
    def __init__(self, owner, client, paire, asset_qty, price, chat_id, sltp, trade_type='spot ou margin'):
        self.client, self.owner, self.paire, self.asset_qty, self.price,  self.chat_id, self.sltp, self.trade_type = client, owner, paire, float(asset_qty), float(price), str(chat_id), sltp, trade_type
        self.lp_s = self.price
        self.sl1, self.sl2, self.tp = (1-(float(self.sltp[0])/100)), (1-(float(self.sltp[1])/100)), (1-(float(self.sltp[2])/100))
        self.f_qty = self.asset_qty
        Thread.__init__(self)
        self.w_f_value = round_x_to_y_decimal(self.asset_qty*self.price, 5)
        self.continuer = True
        self.pauser = False
        self.last_telegram_id = '0'

    def wallet(self):
        wallet = round_x_to_y_decimal((self.asset_qty/self.f_qty)*100, 2)
        lastprice = float(self.get_prices())
        roi = round_x_to_y_decimal(((lastprice/self.price)-1)*100, 2)
        return wallet, roi, lastprice

    def telegram_answer(self):
        global trail_bot_tk
        self.answer = "I'm ready"
        self.id={}
        self.get = 'https://api.telegram.org/bot' + trail_bot_tk + '/getUpdates?limit=100'
        self.response = requests.get(self.get)
        if not isinstance(self.response.json()['result'], list):
            return
        try :
            self.max=int(len(self.response.json()['result']))
            if self.max>2:
                if self.max > 10:
                    self.offset = int(self.response.json()['result'][0]['update_id'])+1
                for i in range(1,self.max):
                    self.id = self.response.json()['result'][-i]['message']
                    if str(self.id['date']) > str(self.last_telegram_id) and str(self.id['chat']['id']) == str(self.chat_id):
                        self.wallet, self.roi, lastprice = self.wallet()
                        if str(self.id['text']) == '/roi' :
                            if self.roi != '0':
                                self.answer  = 'On {} : you made {} pourcent of profit'.format(self.paire,round_x_to_y_decimal(self.roi, 2))
                            else :
                                self.answer = 'On {} : your wallet is empty'.format(self.paire)
                        elif str(self.id['text']) == '/wallet' :
                            self.answer = 'On {} : your wallet is worth {} quote : you have {} asset'.format(self.paire, round_x_to_y_decimal(lastprice*self.asset_qty, 5), round_x_to_y_decimal(self.asset_qty, 4))
                        elif str(self.id['text']) == '/credits':
                            self.answer = """Credits to Stanislas du Rivau. Please consider tipping me for my work :
                
                                            BTC

                                            1F7b9ocDCqLtoDX9kbCQJo1T9q5ZMZjezm

                                            ETH 

                                            0x565c5E1d3484dE8b144dD00753f0CcDd518c24C6

                                            Xrp

                                            rMdG3ju8pgyVh29ELPWaDuA74CpWW6Fxns

                                            Tag :

                                            3061811188

                                            Any help appreciated. Thank you !"""
                        elif str(self.id['text']) == '/commands' :
                            self.answer = """Commands :
                                /wallet : get your current wallet value, minus what you borrowed
                                /roi : get your current Return On Investment
                                /credits"""
                        else :
                            self.answer = 'Unknown command, type /commands to get commands'
                        self.telegram_bot_sendtext(self.answer, self.chat_id, trail_bot_tk)
                        self.last_telegram_id = str(self.id['date'])
                        if self.max > 60 :
                            requests.get('https://api.telegram.org/bot' + trail_bot_tk + '/getUpdates?limit=100' + '&offset=' + str(self.offset))
                        break
        except Exception as e:
            log_func('Error in telegram answer, {}'.format(e))
        
    def get_prices(self):
        try :
            last_price = float(self.client.get_klines(symbol=self.paire, interval='1m')[1])
            return(last_price)
        except Exception as e:
            log_func('Error in getting prices from [get_prices()] line 77, known as : {} ; will try again every 5 seconds'.format(e))
            sleep(5)
            self.get_prices()

    def first_loop(self):
        lp = self.get_prices()
        while (lp>self.sl1*self.price and lp<1.01*self.price):
            sleep(5)
            lp = self.get_prices()
        if lp >= 1.01*self.price:
            self.lp_s = lp
            return 'goodloop'
        elif lp <= self.sl1*self.price :
            return 'oupsloop'

    def oups_loop(self):
        lp = self.get_prices()
        while (lp>self.sl2*self.price and lp<1.01*self.price) :
            sleep(5)
            lp = self.get_prices()
        if lp >= 1.01*self.price:
            self.lp_s = lp
            return 'goodloop'
        elif lp <= self.sl2*self.price :
            return 'sell_all'

    def good_loop(self):
        end = False
        while not end:
            lp = self.get_prices()
            if lp >= 1.01*self.lp_s :
                self.lp_s = lp
                end = False
            elif lp <= self.tp*self.lp_s :
                end = True
        # Now, bot will be killed
        executedQty, quoteQty = sell_x_pourcent(self.client, 100, self.paire, self.asset_qty, self.trade_type)
        log_func('{} sold 100 pourcent on {} because of goodloop, which is {} asset, winning {} quote'.format(self.owner, self.paire, executedQty, quoteQty))
        log_func('Now, {} bot on {} is gonna be killed.'.format(self.owner, self.paire))
        self.telegram_bot_sendtext('{} sold 100 pourcent on {} because target profit is reached, which is {} asset, winning {} quote'.format(self.owner, self.paire, executedQty, quoteQty), self.chat_id, trail_bot_tk)
        self.telegram_bot_sendtext("Now, {} bot on {} is gonna be killed. It's mission is achieved.".format(self.owner, self.paire), self.chat_id, trail_bot_tk)
        self.continuer = False

    def run(self):
        executedQty, quoteQty = 0,0
        while self.continuer:
            sleep(3)
            while self.pauser :
                sleep(10)
            attempt = self.first_loop()
            if attempt == 'oupsloop':
                executedQty, quoteQty = sell_x_pourcent(self.client, 50, self.paire, self.asset_qty, self.trade_type)
                log_func('{} sold 50 pourcent on {} because of oupsloop, which is {} asset, winning {} quote'.format(self.owner, self.paire, executedQty, quoteQty))
                self.telegram_bot_sendtext('{} sold 50 pourcent on {} because first stop loss is reached, which is {} asset, winning {} quote'.format(self.owner, self.paire, executedQty, quoteQty), self.chat_id, trail_bot_tk)
                executedQty, quoteQty = 0,0
                n_attempt = self.oups_loop()
                if n_attempt == 'sell_all':
                    executedQty, quoteQty = sell_x_pourcent(self.client, 100, self.paire, self.asset_qty, self.trade_type)
                    log_func('{} sold 100 pourcent on {} because of oupsloop, which is {} asset, winning {} quote'.format(self.owner, self.paire, executedQty, quoteQty))
                    log_func('Now, {} bot on {} is gonna be killed.'.format(self.owner, self.paire))
                    self.telegram_bot_sendtext('{} sold 100 pourcent on {} because stop loss is reached, which is {} asset, winning {} quote'.format(self.owner, self.paire, executedQty, quoteQty), self.chat_id, trail_bot_tk)
                    self.telegram_bot_sendtext("Now, {} bot on {} is gonna be killed. It's mission is achieved.".format(self.owner, self.paire), self.chat_id, trail_bot_tk)
                    self.continuer = False
                    break
                elif n_attempt == 'goodloop':
                    self.good_loop()
                    break
            elif attempt == 'goodloop':
                self.good_loop()
                break


class DelBots(Thread):
    def __init__(self):
        Thread.__init__(self)
        global bots
        global launched_bots
        self.continuer = True
    
    def run(self):
        while self.continuer:
            global bots
            global launched_bots
            try :
                if bots != [] :
                    for b in bots:
                        if b.continuer == False :
                            del b
                if launched_bots != [] :
                    for b in launched_bots :
                        if b.continuer == False :
                            del b
            except Exception :
                pass
            sleep(1)
            
class TokenManagerBot(Thread):
    def __init__(self):
        self.init = True
        global token_database
        global token_db_dic
        global stan_id
        global tk_manager_tk
        self.continuer = True
        self.newtoken = 'abcTOKENcba'
        Thread.__init__(self)

    def send_offset(self, offset):
        global tk_manager_tk
        done = False
        try :   
            requests.get('https://api.telegram.org/bot' + tk_manager_tk + '/getUpdates?limit=100' + '&offset=' + str(offset))
            done = True
            return done
        except Exception as e:
            log_func('Error occured in LaunchBots class, [offset] method : {} ; gonna try again every 5 seconds'.format(e))
            sleep(5)
            self.send_offset(offset)

    def init_session(self) :
        global token_database
        global token_db_dic
        global stan_id
        self.offset = 0
        self.offset_id = '0'
        global bots
        answer = 'Waiting for database...'
        try :
            response = requests.get('https://api.telegram.org/bot' + tk_manager_tk + '/getUpdates?limit=100')
            if not isinstance(response.json()['result'], list):
                sleep(5)
                log_func('Error in TokenManagerBot class, [init_session] method : error : {} ; gonna try every 5 seconds'.format(e))
                self.init_session()
        except Exception as e :
            sleep(5)
            log_func('Error in TokenManagerBot class, [init_session] method : error : {} ; gonna try every 5 seconds'.format(e))
            self.init_session()
        try :
            results = response.json()['result']
            leng = int(len(results))
            if leng > 2:
                if leng > 10 :
                    self.offset = int(results[0]['update_id'])+1
                for i in range(1,leng):
                    msg = response.json()['result'][-i]['message']
                    if str(msg['date']) > str(self.offset_id) and str(msg['chat']['id']) == stan_id :
                        self.offset_id = str(msg['date'])
                self.init = False
        except Exception as e :
            sleep(5)
            log_func('Error in TokenManagerBot class, [init_session] method : error : {} ; gonna try every 5 seconds'.format(e))
            self.init_session()
        

    def handle_msg(self):
        global token_database
        global token_db_dic
        global stan_id
        self.offset = '0'
        global bots
        answer = 'Waiting for database...'
        try :
            response = requests.get('https://api.telegram.org/bot' + tk_manager_tk + '/getUpdates?limit=100')
            if not isinstance(response.json()['result'], list):
                sleep(5)
                log_func('Error in TokenManagerBot class, [handle_msg] method : error : {} ; gonna try every 5 seconds'.format(e))
                self.handle_msg()
        except Exception as e :
            sleep(5)
            log_func('Error in TokenManagerBot class, [handle_msg] method : error : {} ; gonna try every 5 seconds'.format(e))
            self.handle_msg()
        try :
            results = response.json()['result']
            leng = int(len(results))
            if leng > 2:
                if leng > 10 :
                    self.offset = int(results[0]['update_id'])+1
                for i in range(1,leng):

                    msg = response.json()['result'][-i]['message']
                    msg['chat']['id'] = str(msg['chat']['id'])

                    answer = 'Waiting for database...'

                    if msg['text'].startswith('newtoken') and (msg['chat']['id'] == stan_id) and str(self.offset_id) < str(msg['date']) :
                        self.offset_id = str(msg['date'])
                        self.newtoken = str(msg['text'].split(' ')[1])
                        answer = 'Is the newtoken : {} ? (/oui or /n )'.format(self.newtoken)

                    elif msg['text'].startswith('/oui') and (msg['chat']['id'] == stan_id) and str(self.offset_id) < str(msg['date']) :
                        self.offset_id = str(msg['date'])
                        if str(self.newtoken) not in token_database :
                            log_func('New token added.')
                            telegram_bot_sendtext('Ok, token well added to token_database', stan_id, tk_manager_tk)
                            token_database.append(self.newtoken)
                        else :
                            self.newtoken = 'abcTOKENcba'
                            answer = 'Token already in database'
                        self.newtoken = 'abcTOKENcba'

                    elif msg['text'].startswith('removetoken') and (msg['chat']['id'] == stan_id) and str(self.offset_id) < str(msg['date']) :
                        self.offset_id = str(msg['date'])
                        if msg['text'].split(' ')[1] in token_database :
                            token_database.remove(msg['text'].split(' ')[1])
                            answer = 'Token {} removed from database.'.format(msg['text'].split(' ')[1])
                            log_func('Token {} removed from database.'.format(msg['text'].split(' ')[1]))
                        else :
                            answer = 'Token {} not in database.'.format(msg['text'].split(' ')[1])

                    elif msg['text'] == '/n' and (msg['chat']['id'] == stan_id) and str(self.offset_id) < str(msg['date']) :
                        self.offset_id = str(msg['date'])
                        self.newtoken = 'abcTOKENcba'
                        answer = 'Ok, please type newtoken [token_id] to add it to database'

                    elif msg['text'] == '/gettokens' and (msg['chat']['id'] == stan_id) and str(self.offset_id) < str(msg['date']) :
                        self.offset_id = str(msg['date'])
                        answer = 'Tokens : ' + str(token_database) + '// Dic database : ' +  str(token_db_dic)

                    elif msg['text'].startswith('pause') and (msg['chat']['id'] == stan_id) and str(self.offset_id) < str(msg['date']) :
                        self.offset_id = str(msg['date'])
                        comm = msg['text']
                        if comm == 'pause all' :
                            for b in bots :
                                telegram_bot_sendtext('Your bot, trading on {}, has been paused'.format(b.paire), b.chat_id, trail_bot_tk)
                                b.pauser = True
                            answer = 'All bot paused'
                        else : 
                            for b in bots :
                                if id(b) == comm.split(' ')[1]:
                                    telegram_bot_sendtext('Your bot, trading on {}, has been paused'.format(b.paire), b.chat_id, trail_bot_tk)
                                    b.pauser = True
                                    answer = 'Bot paused'
                                            
                                    

                    elif msg['text'].startswith('resume') and (msg['chat']['id'] == stan_id) and str(self.offset_id) < str(msg['date']) :
                        self.offset_id = str(msg['date'])
                        comm = msg['text']
                        if comm == 'resume all' :
                            for b in bots :
                                telegram_bot_sendtext('Your bot, trading on {}, has been rsumed'.format(b.paire), b.chat_id, trail_bot_tk)
                                b.pauser = False
                            answer = 'All bot resumed'
                        else : 
                            for b in bots :
                                if id(b) == comm.split(' ')[1]:
                                    telegram_bot_sendtext('Your bot, trading on {}, has been resumed'.format(b.paire), b.chat_id, trail_bot_tk)
                                    b.pauser = False
                                    answer = 'Bot resumed'

                    elif msg['text'] == '/list' and (msg['chat']['id'] == stan_id) and str(self.offset_id) < str(msg['date']) :
                        self.offset_id = str(msg['date'])
                        for b in bots :
                            answer = ('Bot {}, owner : {}, paire : {} , asset qty : {}, status : {}'.format(id(b), b.owner, b.paire, b.asset_qty, ['ENABLED', 'PAUSED'][b.pauser]))
                            telegram_bot_sendtext(answer, stan_id, tk_manager_tk)
                        answer = 'End of list'

                    elif msg['text'] == '/commands' and (msg['chat']['id'] == stan_id) and str(self.offset_id) < str(msg['date']) :
                        self.offset_id = str(msg['date'])
                        answer = """Commands :
                        newtoken [token_id]
                        removetoken [token_id]
                        /gettokens
                        /list
                        pause all
                        pause [id]
                        resume all
                        resume [id]                        """

                    elif str(self.offset_id) < str(msg['date']) and (msg['chat']['id'] == stan_id) :
                        self.offset_id = str(msg['date'])
                        answer = 'Unknown command.  Type /commands'

                    if str(self.offset_id) == str(msg['date']) and answer != 'Waiting for database...' :
                        telegram_bot_sendtext(answer, msg['chat']['id'], tk_manager_tk)
                        self.offset_id = str(int(self.offset_id))
                        if leng > 60 :
                            self.send_offset(self.offset)
                            

        except Exception as e:
            log_func('Error in TokenManagerBot, [handle_msg] class ({}) gonna try  again every 5 seconds'.format(e))
            sleep(5)
            self.handle_msg()

    def run(self):
        while self.continuer :
            if self.init :
                self.init_session()
            sleep(0.5)
            self.handle_msg()

class NotifBot(Thread):
    def __init__(self):
        Thread.__init__(self)
        self.continuer=True
                    
    def run(self):
        global bots
        while self.continuer == True:
            if bots != []:
                try:
                    for b in bots:
                        b.telegram_answer()      
                except Exception as e:
                    log_func('Error occured in NotifBot, : {}'.format(e))
            sleep(0.5)



class InterfaceBot(Thread) :
    """bot that redirects user to in order to launch a new bot"""
    def __init__(self) :
        self.continuer = True
        Thread.__init__(self)
        global lch_bot_tk
        self.lch_bot_tk = lch_bot_tk
        self.offset_id = {}

    def send_offset(self, offset):
        done = False
        try :   
            requests.get('https://api.telegram.org/bot' + self.lch_bot_tk + '/getUpdates?limit=100' + '&offset=' + offset)
            done = True
            return done
        except Exception as e:
            log_func('Error occured in InterfaceBot class, [offset] method : {} ; gonna try again every 5 seconds'.format(e))
            sleep(5)
            self.send_offset(offset)

    def handle_user(self) :
        global current_users
        global token_database
        global launched_bots
        answer = 'Waiting for database...'
        try :
            response = requests.get('https://api.telegram.org/bot' + self.lch_bot_tk + '/getUpdates?limit=100')
            if not isinstance(response.json()['result'], list):
                sleep(5)
                log_func('Error in InterfaceBot class, [handle_user] method : error : response is not a list, described : {} ; gonna try every 5 seconds'.format(e))
                self.handle_user()
        except Exception as e :
            sleep(5)
            log_func('Error in InterfaceBot class, [handle_user] method : error : {} ; gonna try every 5 seconds'.format(e))
            self.handle_user()
        try :
            results = response.json()['result']
            leng = int(len(results))
            if leng > 2:
                if leng > 10 : 
                    self.offset = int(results[0]['update_id'])+1
                for i in range(1,leng):
                    answer = 'Waiting for database...'
                    redir = ''
                    msg = response.json()['result'][-i]['message']

                    msg['chat']['id'] = str(msg['chat']['id'])

                    if 'text' not in list(msg):
                        continue

                    if msg['text'] == '/startbot' and msg['chat']['id'] not in current_users and (msg['chat']['id'] not in list(self.offset_id) or int(msg['date']) > int(self.offset_id[msg['chat']['id']])) :
                        self.offset_id[msg['chat']['id']] =  msg['date']
                        answer = """Bonjour ! Si vous avez un token, merci de l'envoyer. Sinon, rendez-vous sur : https://surferbot.xyz/trailer-bot """

                    elif str(msg['text']) in token_database and msg['chat']['id'] not in current_users and (msg['chat']['id'] not in list(self.offset_id) or int(msg['date']) > int(self.offset_id[msg['chat']['id']])):
                        self.offset_id[msg['chat']['id']] =  msg['date']
                        launch_bot = LaunchBots(msg['chat']['id'], self.offset_id[msg['chat']['id']])
                        launch_bot.start()
                        launched_bots.append(launch_bot)
                        current_users.append(msg['chat']['id'])
                        answer = 'Vous allez pouvoir lancer votre bot de trailing. Quel est votre nom ?'

                    elif (msg['chat']['id'] not in current_users) and (msg['chat']['id'] not in list(self.offset_id) or int(msg['date']) > int(self.offset_id[msg['chat']['id']])) :
                        self.offset_id[msg['chat']['id']] = msg['date']
                        answer = 'Commande inconnue. La commande pour lancer un bot est : /startbot '

                    if answer != 'Waiting for database...':
                        telegram_bot_sendtext(answer, msg['chat']['id'], self.lch_bot_tk)
                        if leng > 60 :
                            self.send_offset(self.offset)

        except Exception as e :
            log_func('Error in InterfaceBot class, [handle_user] method ; gonna try again in 5 seconds...')
            sleep(5)
            self.handle_user()

    def run(self) :
        while self.continuer :
            try :
                self.handle_user()
            except Exception as e :
                log_func("""Error in InterfaceBot class, [handle_user] method, = '{}' ; gonna try again in 5 seconds""".format(e))
                sleep(5)
            sleep(0.3)                

class LaunchBots(Thread):
    """bot that helps user to launch a new bot"""
    def __init__(self, chat_id, last_offset_id):
        self.continuer = True
        self.lch_bot_tk = lch_bot_tk
        self.chat_id = str(chat_id)
        self.last_offset_id = last_offset_id
        Thread.__init__(self)

    def send_offset(self, offset):
        done = False
        try :   
            requests.get('https://api.telegram.org/bot' + self.lch_bot_tk + '/getUpdates?limit=100' + '&offset=' + offset)
            done = True
            return done
        except Exception as e:
            log_func('Error occured in LaunchBots class, [offset] method : {} ; gonna try again every 5 seconds'.format(e))
            sleep(5)
            self.send_offset(offset)

    def step_choice(self, package) :
        if 'step' in package :
            return int(package['step'])
        else :
            return 1

    def redirect_loop(self):
        answer = 'Waiting for database...'
        package = {}
        package['ok'] = False
        package['chat_id'] = self.chat_id
        step = 1
        step_retro = ['/name', '/tradetype']
        while not package['ok'] :
            try :
                response = requests.get('https://api.telegram.org/bot' + self.lch_bot_tk + '/getUpdates?limit=100')
                if not isinstance(response.json()['result'], list):
                    sleep(5)
                    log_func('Error in LaunchBots class, [redirect_loop] method : error : response is not a list ({}) ; gonna try every 5 seconds'.format(e))
                    self.redirect_loop()
            except Exception as e :
                sleep(5)
                log_func('Error in LaunchBots class, [redirect_loop] method : error : {} ; gonna try every 5 seconds'.format(e))
                self.redirect_loop()
            try :
                results = response.json()['result']
                leng = int(len(results))
                if leng > 2:
                    if leng > 10 : 
                        self.offset = int(results[0]['update_id'])+1
                    next_step = 1
                    for i in range(1,leng):
                        answer = 'Waiting for database...'
                        msg = response.json()['result'][-i]['message']
                        msg['chat']['id'] = str(msg['chat']['id'])
                        step = next_step
                        if 'text' not in list(msg):
                            continue

                        if msg['chat']['id'] != self.chat_id :
                            continue

                        # if msg['text'] in step_retro and int(msg['date']) > int(self.last_offset_id) and msg['chat']['id'] == self.chat_id:
                        #     self.last_offset_id = msg['date']
                        #     if msg['text'] == '/change_name' :
                        #         if 'owner' in list(package):
                        #             del package['owner']
                        #         step = self.step_choice(package)
                        #     elif msg['text'] == '/change_tradetype': 
                        #         if 'tradetype' in list(package):
                        #             del package['tradetype']
                        #         step = self.step_choice(package)
                        #     pass #TODO


                        if step  == 1 and int(msg['date']) > int(self.last_offset_id) and msg['chat']['id'] == self.chat_id :
                            self.last_offset_id = msg['date']
                            package['owner'] = msg['text']
                            answer = 'Super, {} ! Souhaitez vous trader sur le /spot ou le /margin ? (Si vous souhaitez changer de nom, envoyez /change_name) (Si vous ne savez pas ce que sont le spot et le margin, consultez les tutoriels sur https://surferbot.xyz)'.format(package['owner'])
                            package['step'] = 1
                            next_step = self.step_choice(package)

                        elif step == 2  and (msg['text'] == '/spot' or msg['text'] == '/margin' or ('spot' in msg['text'] and 'margin' not in msg['text']) or ('spot' not in msg['text'] and 'margin' in msg['text'])) and int(msg['date']) > int(self.last_offset_id) and msg['chat']['id'] == self.chat_id :
                            self.last_offset_id = msg['date']
                            if msg['text'] == '/spot' or ('spot' in msg['text'] and 'margin' not in msg['text']) :
                                package['trade_type'] = 'spot'
                            elif msg['text'] == '/margin' or ('spot' not in msg['text'] and 'margin' in msg['text']) :
                                package['trade_type'] = 'margin'        
                            answer = "Bien retenu, vous voulez tradez sur le {}. Pour changer ce choix, tapez /change_tradetype. Sinon, veuillez envoyer creer une clef API Binance, accorder l'acces au trading et au margin trading, et refuser le droit au withdraw. Puis, répondez par la clé publique. Ex de réponse : iuzb8393ibvsbi " #TODO : Marque-page
                            package['step'] = 2
                            next_step = self.step_choice(package)

                        if step  == 3  and int(msg['date']) > int(self.last_offset_id) and msg['chat']['id'] == self.chat_id :
                            self.last_offset_id = msg['date']
                            package['api1'] = msg['text']
                            answer = 'Bien ! Envoyez maintenant la clef privee. Sinon, envoyez /change_api'
                            package['step'] = 3
                            next_step = self.step_choice(package)

                        if step  == 4  and int(msg['date']) > int(self.last_offset_id) and msg['chat']['id'] == self.chat_id :
                            self.last_offset_id = msg['date']
                            package['api2'] = msg['text']
                            if 'api1' in list(package) and 'api2' in list(package) :
                                try :
                                    client_test = Client(package['api1'],package['api2'])
                                    client_ok = is_client(client_test)
                                    if client_ok : 
                                        package['client'] = client_test
                                        package['step'] = 4
                                        answer = 'Parfait ! Envoyez maintenant la paire tradee. Par exemple : BTCUSDT ou LINKBTC'
                                    else : 
                                        answer = 'Vos clef API semblent incorrectes. Merci de renvoyer votre clef publique.'
                                except Exception :
                                    answer = 'Vos clef API semblent incorrectes. Merci de renvoyer votre clef publique.'
                            next_step = self.step_choice(package)


                        if step  == 5  and int(msg['date']) > int(self.last_offset_id) and msg['chat']['id'] == self.chat_id :
                            self.last_offset_id = msg['date']
                            if is_correct_paire(package['client'], msg['text'], package['trade_type']) :
                                package['paire'] = msg['text']
                                answer = "Merci. Quel etait le prix d'achat ? Vous pouvez le recuperer dans l'historique des ordres sur Binance. Exemple : 123.456"
                                package['step'] = 5
                            else :
                                answer = "Cette paire n'est pas reconnue par Binance. Merci de renvoyer une paire du format : BTCUSDT ou ADABTC ou XRPETH"
                            next_step = self.step_choice(package)

                        if step  == 6 and int(msg['date']) > int(self.last_offset_id) and msg['chat']['id'] == self.chat_id :
                            self.last_offset_id = msg['date']
                            if "," in msg['text'] :
                                msg['text'].replace(',', '.')
                            try :
                                price = float(msg['text'])
                            except Exception as e :
                                answer = "Le prix entre est du mauvais format. Merci d'envoyer un prix correct, par exemple : 12345.6789"
                            if isinstance(price, float) :
                                lp = client0.get_klines_data(symbol=package['paire'], interval='1m')[1]
                                ecart = round_x_to_y_number((1- abs(price/lp))*100, 2)
                                package['step'] = 6
                                answer = "L'ecart est de {} pourcent entre le prix actuel et le prix d'achat ; etes vous sur du prix ? Si oui, envoyez '/confirm_price' ; sinon, /change_price".format(ecart)
                            next_step = self.step_choice(package)

                        if step  == 7 and msg['text'] == '/confirm_price' and int(msg['date']) > int(self.last_offset_id) and msg['chat']['id'] == self.chat_id :
                            self.last_offset_id = msg['date']
                            package['price_ok'] = True
                            answer = "Quel est la quantité de coin à trailer que vous avez ? Exemple : 123.45 ou 0.0243"
                            package['step'] = 7
                            next_step = self.step_choice(package)

                        if step  == 8 and int(msg['date']) > int(self.last_offset_id) and msg['chat']['id'] == self.chat_id :
                            self.last_offset_id = msg['date']
                            if "," in msg['text'] :
                                msg['text'].replace(',', '.')
                            try :
                                quantity = float(msg['text'])
                            except Exception as e :
                                answer = "La quantite entree est du mauvais format. Merci d'envoyer une quantite correct, par exemple : 12345.6789"
                            if isinstance(quantity, float) :
                                package['asset_qty'] = quantity
                                package['step'] = 8
                            answer = "Par defaut, les trailing stop-losses sont 4 pourcents (vente de la moitie) et 7 pourcent (vente du total) et le trailing take profit est de 2.5 pourcents en dessous du prix atteint le plus haut. Si cela ne vous convient pas, merci de repondre avec les 2 stop loss et le take profit. Merci de n'entrer que des nombres entiers. Respectez ce format : [1, 2, 3] signifie : 1er sl 1 pourcent, 2e 2 pourcent, take profit trail 3 pourcent. Envoyez votre reponse sous la forme de liste entre crochets avec les virgules comme separateurs : par exemple, [1, 2, 3]. Sinon, envoyez /continuer"
                            next_step = self.step_choice(package)

                        if step  == 9 and msg['text'] != '/continuer' and int(msg['date']) > int(self.last_offset_id) and msg['chat']['id'] == self.chat_id :
                            self.last_offset_id = msg['date']
                            try : 
                                list_sltp = list(msg['text'])
                                sltp = []
                                for i in list_sltp :
                                    if i in [range(1,10)] :
                                        sltp.append(i)
                                        if len(sltp) > 2 :
                                            break
                                if len(sltp) != 3 :
                                    answer = 'Liste du mauvais format. Merci de renvoyer une liste separee par des virgules, ne contenant que des nombres entiers, par exemple : [1,2,3]'
                                else :
                                    package['sltp'] = sltp
                                    answer = "Ok, votre liste des stop losses est : {}. Merci d'envoyer /continuer pour verifier les informations.".format(sltp)
                                    package['step'] = 9
                            except Exception :
                                answer = 'Liste du mauvais format. Merci de renvoyer une liste separee par des virgules, ne contenant que des nombres entiers, par exemple : [1,2,3]'


                        if step  == 10 and msg['text'] == '/continuer' and int(msg['date']) > int(self.last_offset_id) and msg['chat']['id'] == self.chat_id :
                            self.last_offset_id = msg['date']
                            package['step'] = 10
                            answer = """Super ! Merci de confirmer que ces informations sont correctes.
Votre nom : {}
La paire tradee : {}
La quantitee tradee : {}
Le prix d'achat : {}
Votre type de trading : {}
Est-ce correct ?

/confirm_final 

/incorrect

                                """.format(package['owner'], package['paire'], package['asset_qty'], package['price'], package['trade_type'])
                            next_step = self.step_choice(package)



                        if step  == 11 and (msg['text'] == '/confirm_final' or msg['text'] == '/incorrect') and int(msg['date']) > int(self.last_offset_id) and msg['chat']['id'] == self.chat_id :
                            self.last_offset_id = msg['date']
                            package['step'] = 11
                            if msg['text'] == '/confirm_final' :
                                self.launch_bot(package)
                                answer = 'Votre bot est en cours de lancement...'
                            elif msg['text'] == '/incorrect' :
                                answer = 'Quel est votre nom ?'
                                step = 1

                        if answer != 'Waiting for database...':
                            telegram_bot_sendtext(answer, msg['chat']['id'], self.lch_bot_tk)
                            if leng > 60 :
                                self.send_offset(self.offset)

            except Exception as e :
                log_func('Error in LaunchBots class, [redirect_loop] method : error : {} ; gonna try every 5 seconds'.format(e))
                sleep(5)
                self.redirect_loop()

    def launch_bot(self, package):
        global bots
        client = Client(package['api1'], package['api2'])
        owner = package['owner']
        chat_id = package['chat_id']
        paire = package['paire']
        price = package['price']
        asset_qty = package['asset_qty']
        trade_type = package['trade_type']
        if 'sltp' in list(package) :
            sltp = package['sltp']
        else :
            sltp = [4, 7, 2.5]
        try :
            t_bot = TrailerBot(owner, client, paire, asset_qty, price, chat_id, sltp, trade_type)
            t_bot.start()
            bots.append(t_bot)
            log_func('New bot launched.'+str(package))
            self.continuer = False
        except Exception as e:
            log_func('Error in DelBots class, [launch_bots] method, known as : {} ; gonna try again every 5 seconds')
            sleep(5)
            self.launch_bot(package)

    def run(self):
        while self.continuer :
            self.redirect_loop()
            sleep(3)



# Interpreteur
SupprBot = DelBots()
pack = starter()
tokens, client0apis = pack[0], pack[1]
trail_bot_tk, log_bot_tk, lch_bot_tk, tk_manager_tk = tokens[0], tokens[1], tokens[2], tokens[3]
client0 = Client(client0apis[0], client0apis[1])
stan_id = tokens[4]


chat_id_database = []

notif_bot = NotifBot()
notif_bot.start()
admin_bots.append(notif_bot)
del_bots = DelBots()
del_bots.start()
admin_bots.append(del_bots)
interface_bot = InterfaceBot()
interface_bot.start()
admin_bots.append(interface_bot)
tk_manager_bot = TokenManagerBot()
tk_manager_bot.start()
admin_bots.append(tk_manager_bot)

log_func('Connecte')
print('Hey ! This bot  works on Telegram. Please go talking at @trailer_tradingbot there if you want to launch a bot !')
while True :
    check = 'n'
    comm = input('@ :')
    if comm == 'help' :
        print("""Commands :
        list : list bots
        kill [id] : kill a bot
        kill all : kill all bots 
        pause [id] : pause a bot
        pause all : pause all bots
        resume [id] : resume a bot
        resume all : resume all bots
        log : read log.txt""")
    elif comm == 'list':
        for b in bots :
            print('Bot {}, owner : {}, paire : {} , asset qty : {}, status : {}'.format(id(b), b.owner, b.paire, b.asset_qty, ['ENABLED', 'PAUSED'][b.pauser]))
    elif comm.startswith('kill') :
        if comm == 'kill all' :
            check = input('Are you sure ? (y/n)')
            if check == 'y' :
                for b in bots :
                    telegram_bot_sendtext('Your bot, trading on {}, has been stopped'.format(b.paire), b.chat_id)
                    b.continuer = False
            else :
                continue
        else : 
            check = input('Are you sure ? (y/n)')
            if check == 'y' :
                for b in bots :
                    if id(b) == comm.split(' ')[1]:
                        telegram_bot_sendtext('Your bot, trading on {}, has been stopped'.format(b.paire), b.chat_id)
                        b.continuer = False
                        break  

    elif comm.startswith('pause') :
        if comm == 'pause all' :
            check = input('Are you sure ? (y/n)')
            if check == 'y' :
                for b in bots :
                    telegram_bot_sendtext('Your bot, trading on {}, has been paused'.format(b.paire), b.chat_id)
                    b.pauser = True
            else :
                continue
        else : 
            check = input('Are you sure ? (y/n)')
            if check == 'y' :
                for b in bots :
                    if id(b) == comm.split(' ')[1]:
                        telegram_bot_sendtext('Your bot, trading on {}, has been paused'.format(b.paire), b.chat_id)
                        b.pauser = True
                        break   

    elif comm.startswith('resume') :
        if comm == 'resume all' :
            check = input('Are you sure ? (y/n)')
            if check == 'y' :
                for b in bots :
                    telegram_bot_sendtext('Your bot, trading on {}, has been paused'.format(b.paire), b.chat_id)
                    b.pauser = False
            else :
                continue
        else : 
            check = input('Are you sure ? (y/n)')
            if check == 'y' :
                for b in bots :
                    if id(b) == comm.split(' ')[1]:
                        telegram_bot_sendtext('Your bot, trading on {}, has been paused'.format(b.paire), b.chat_id)
                        b.pauser = False
                        break    
                                   
    elif comm=='log':
        with open('log.txt','r') as f:
            print(f.read())
    
    else :
        print("Unknow command, type 'help' for commands")


