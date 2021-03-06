from cv2 import cv2
from pyclick import HumanClicker
from captchaSolver import start
from src.date import dateFormatted
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext

import numpy as np
import mss
import pyautogui
import yaml
import time
import random
import telegram
import sys

try:
    stream = open("./config/config.yaml", 'r')
    streamConfig = yaml.safe_load(stream)
    configThreshold = streamConfig['threshold']
    configTimeIntervals = streamConfig['time_intervals']
    metamaskData = streamConfig['metamask']
    chestData = streamConfig['value_chests']
    offsets = streamConfig['offsets']
    stream.close()
except FileNotFoundError:
    print('Error: Config file not found, rename EXAMPLE-config.yaml to config.yaml inside /config folder')
    print('Erro: Arquivo config não encontrado, renomear EXAMPLE-config.yaml para config.yaml dentro da pasta /config')
    exit()

telegramIntegration = False
try:
    stream = open("./config/telegram.yaml", 'r')
    streamConfigTelegram = yaml.safe_load(stream)
    telegramIntegration = streamConfigTelegram['telegram_enable']
    telegramChatId = streamConfigTelegram['telegram_chat_id']
    telegramBotToken = streamConfigTelegram['telegram_bot_token']
    telegramFormatImage = streamConfigTelegram['format_of_images']
    TelegramEmergencyCall = streamConfigTelegram['enable_emergency_call']
    stream.close()
except FileNotFoundError:
    print('Info: Telegram not configure, rename EXAMPLE-telegram.yaml to telegram.yaml')

login_attempts = 0

hc = HumanClicker()
pyautogui.PAUSE = streamConfig['time_intervals']['interval_between_movements']
pyautogui.FAILSAFE = False
arrow_img = cv2.imread('./images/targets/go-back-arrow.png')
jaula_img = cv2.imread('./images/targets/jaula.png')
metamask_icon_img = cv2.imread('./images/targets/metamask_icon.png')
smart_chain_img = cv2.imread('./images/targets/smart_chain.png')
options_img = cv2.imread('./images/targets/options.png')
criar_conta_img = cv2.imread('./images/targets/criar_conta.png')
btn_criar_img = cv2.imread('./images/targets/btn_criar.png')
nao_conectado_img = cv2.imread('./images/targets/nao_conectado.png')
conectar_img = cv2.imread('./images/targets/conectar.png')
teasureHunt_icon_img = cv2.imread('./images/targets/treasure-hunt-icon.png')
ok_btn_img = cv2.imread('./images/targets/ok.png')
connect_wallet_btn_img = cv2.imread('./images/targets/connect-wallet.png')
sign_btn_img = cv2.imread('./images/targets/metamask_sign.png')
robot = cv2.imread('./images/targets/robot.png')
slider = cv2.imread('./images/targets/slider.png')
metamask_unlock_img = cv2.imread('./images/targets/unlock_metamask.png')
metamask_cancel_button = cv2.imread('./images/targets/metamask_cancel_button.png')
error_img = cv2.imread('./images/targets/error.png')

def logger(message, telegram=False, emoji=None):
    formatted_datetime = dateFormatted()
    console_message = "{} - {}".format(formatted_datetime, message)
    service_message = "⏰{}\n{} {}".format(formatted_datetime, emoji, message)
    if emoji is not None and streamConfig['emoji'] is True:
        console_message = "{} - {} {}".format(formatted_datetime, emoji, message)

    print(console_message)
    
    if telegram == True:
        sendTelegramMessage(service_message)

    if (streamConfig['save_log_to_file'] == True):
        logger_file = open("./logs/logger.log", "a", encoding='utf-8')
        logger_file.write(console_message + '\n')
        logger_file.close()
    return True

# Initialize telegram
updater = None
if telegramIntegration == True:
    logger('Initializing Telegram...', emoji='📱')
    updater = Updater(telegramBotToken)

    try:
        TBot = telegram.Bot(token=telegramBotToken)

        def send_print(update: Update, context: CallbackContext) -> None:
            update.message.reply_text('🔃 Proccessing...')
            screenshot = printScreen()
            cv2.imwrite('./logs/print-report.%s' % telegramFormatImage, screenshot)
            update.message.reply_photo(photo=open('./logs/print-report.%s' % telegramFormatImage, 'rb'))

        def send_id(update: Update, context: CallbackContext) -> None:
            update.message.reply_text(f'🆔 Your id is: {update.effective_user.id}')

        def send_map(update: Update, context: CallbackContext) -> None:
            update.message.reply_text('🔃 Proccessing...')
            if sendMapReport() is None:
                update.message.reply_text('😿 An error has occurred')

        def send_bcoin(update: Update, context: CallbackContext) -> None:
            update.message.reply_text('🔃 Proccessing...')
            if sendBCoinReport() is None:
                update.message.reply_text('😿 An error has occurred')

        commands = [
            ['print', send_print],
            ['id', send_id],
            ['map', send_map],
            ['bcoin', send_bcoin]
        ]

        for command in commands:
            updater.dispatcher.add_handler(CommandHandler(command[0], command[1]))

        updater.start_polling()
        # updater.idle()
    except:
        logger('Bot not initialized, see configuration file', emoji='🤖')

def sendTelegramMessage(message):
    if telegramIntegration == False:
        return
    try:
        if(len(telegramChatId) > 0):
            for chat_id in telegramChatId:
                TBot.send_message(text=message, chat_id=chat_id)
    except:
        #logger('Error to send telegram message. See configuration file', emoji='📄')
        return

def sendTelegramPrint(name):
    if telegramIntegration == False:
        return
    try:
        if(len(telegramChatId) > 0):
            screenshot = printScreen()
            cv2.imwrite('./logs/%s.%s' % (name, telegramFormatImage), screenshot)
            for chat_id in telegramChatId:
                TBot.send_photo(chat_id=chat_id, photo=open('./logs/%s.%s' % (name, telegramFormatImage), 'rb'))
    except:
        # logger('Error to send telegram message. See configuration file', emoji='📄')
        return

def clickButton(img,name=None, timeout=3, threshold = configThreshold['default']):
    if not name is None:
        pass
    start = time.time()
    clicked = False
    while(not clicked):
        matches = positions(img, threshold=threshold)
        if(matches is False):
            hast_timed_out = time.time()-start > timeout
            if(hast_timed_out):
                break
                if not name is None:
                    pass
                    # print('timed out')
                return False
            # print('button not found yet')
            continue

        x,y,w,h = matches[0]
        hc.move((int(x + (w / 2)), int(y + (h / 2))),1)
        pyautogui.click()
        return True

def printScreen():
    with mss.mss() as sct:
        # The screen part to capture
        # Grab the data
        sct_img = np.array(sct.grab(sct.monitors[streamConfig['monitor_to_use']]))
        return sct_img[:,:,:3]

def positions(target, threshold=configThreshold['default'], base_img=None, return_0=False):
    if base_img is None:
        img = printScreen()
    else:
        img = base_img

    w = target.shape[1]
    h = target.shape[0]

    result = cv2.matchTemplate(img, target, cv2.TM_CCOEFF_NORMED)

    yloc, xloc = np.where(result >= threshold)


    rectangles = []
    for (x, y) in zip(xloc, yloc):
        rectangles.append([int(x), int(y), int(w), int(h)])
        rectangles.append([int(x), int(y), int(w), int(h)])

    rectangles, weights = cv2.groupRectangles(rectangles, 1, 0.2)
    if return_0 is False:
        if len(rectangles) > 0:
            # sys.stdout.write("\nGet_coords. " + str(rectangles) + " " + str(weights) + " " + str(w) + " " + str(h) + " ")
            return rectangles
        else:
            return False
    else:
        return rectangles

def waitForImage(imgs, timeout=30, threshold=0.5, multiple=False):
    start = time.time()
    while True:
        if multiple is not False:
            for img in imgs:
                matches = positions(img, threshold=threshold)
                if matches is False:
                    hast_timed_out = time.time()-start > timeout
                    if hast_timed_out is not False:
                        return False
                    continue
                return True
        else:
            matches = positions(imgs, threshold=threshold)
            if matches is False:
                hast_timed_out = time.time()-start > timeout
                if hast_timed_out is not False:
                    return False
                continue
            return True

def handleError():
    if positions(error_img, configThreshold['error']) is not False:
        sendTelegramPrint("error")
        logger('Error detected, trying to resolve', telegram=True, emoji='💥')
        clickButton(ok_btn_img)
        logger('Refreshing page', telegram=True, emoji='🔃')
        # pyautogui.hotkey('ctrl', 'f5')
        pyautogui.hotkey('ctrl', 'shift', 'r')
        waitForImage(connect_wallet_btn_img)
        login()
    else:
        return False

def login():
    global login_attempts

    if clickButton(connect_wallet_btn_img):
        logger('Connect wallet button detected, logging in!', emoji='🎉')
        time.sleep(10)
        # checkCaptcha()
        waitForImage((sign_btn_img, metamask_unlock_img), multiple=True)
        
    metamask_unlock_coord = positions(metamask_unlock_img)
    if metamask_unlock_coord is not False:
        sleep(1, 3)
        if(metamaskData["enable_login_metamask"] is False):
            logger('Metamask locked! But login with password is disabled, exiting', emoji='🔒')
            exit()
        logger('Found unlock button. Waiting for password', emoji='🔓')
        password = metamaskData["password"]
        pyautogui.typewrite(password, interval=0.1)
        sleep(1, 3)
        if clickButton(metamask_unlock_img):
            logger('Unlock button clicked', emoji='🔓')
            waitForImage(sign_btn_img, timeout=30)

    if clickButton(sign_btn_img):
        logger('Found sign button. Waiting to check if logged in', emoji='✔️')
        time.sleep(5)
        if clickButton(sign_btn_img): ## twice because metamask glitch
            logger('Found glitched sign button. Waiting to check if logged in', emoji='✔️')
        # time.sleep(25)
        waitForImage(teasureHunt_icon_img, timeout=30)
        handleError()

    if currentScreen() == "main":
        logger('Logged in', telegram=False, emoji='🎉')
        return True
    else:
        logger('Login failed, trying again', emoji='😿')
        login_attempts += 1

        if (login_attempts > 3):
            # sendTelegramPrint()
            logger('+3 login attempts, retrying', telegram=False, emoji='🔃')
            # pyautogui.hotkey('ctrl', 'f5')
            pyautogui.hotkey('ctrl', 'shift', 'r')
            login_attempts = 0

            if clickButton(metamask_cancel_button):
                logger('Metamask is glitched, fixing', emoji='🙀')
            
            waitForImage(connect_wallet_btn_img)

        # checkCaptcha()
        login()

    handleError()
   
def currentScreen():
    if positions(arrow_img) is not False:
        # sys.stdout.write("\nThunt. ")
        return "thunt"
    elif positions(teasureHunt_icon_img) is not False:
        # sys.stdout.write("\nmain. ")
        return "main"
    elif positions(connect_wallet_btn_img) is not False:
        # sys.stdout.write("\nlogin. ")
        return "login"
    else:
        # sys.stdout.write("\nUnknown. ")
        return "unknown"
      
def checkCaptcha():
    robot_pos = positions(robot)
    if robot_pos is not False:
        logger('Captcha detected.', telegram=False, emoji='🧩')
        start()
    else:
        return True
        
def createNewAccount():
    if clickButton(metamask_icon_img):
        waitForImage(options_img, threshold=0.8)
        smartChain = positions(options_img)
        if smartChain is not False:
            x,y,w,h = smartChain[0]
            # pyautogui.moveTo(x+(w/2),y+(h/2),1)
            # pyautogui.moveTo(int(random.uniform(x, x+w)),int(random.uniform(y, y+h)),1)
            hc.move((int(x + (w / 2) + w), int(y + (h / 2))),1)
            pyautogui.click()
            waitForImage(criar_conta_img)
            
            if clickButton(criar_conta_img):
                waitForImage(btn_criar_img)
                
            if clickButton(btn_criar_img):
                waitForImage(nao_conectado_img, timeout=300)
                
            if clickButton(nao_conectado_img):
                waitForImage(conectar_img)
                
            if clickButton(conectar_img):
                waitForImage(connect_wallet_btn_img, timeout=60)

def main():
    while True:
        if currentScreen() == "login":
            login()
            
        handleError()
        
        # checkCaptcha()
        
        if currentScreen() == "main":
            if clickButton(teasureHunt_icon_img):
                logger('Entering treasure hunt', emoji='▶️')
    
        if currentScreen() == "thunt":
            waitForImage(jaula_img)
            jaula_coord = positions(jaula_img)
            if jaula_coord is not False:
                logger('Jaula detectada.', telegram=True, emoji='⛓️')
                sendTelegramMessage("Mapa com a jaula:")
                sendTelegramPrint("jaula")
                time.sleep(2)
                clickButton(metamask_icon_img)
                waitForImage(options_img)
                sendTelegramMessage("Conta:")
                sendTelegramPrint("account")
                sys.exit()
            else:
                logger('Jaula indisponivel.', telegram=False, emoji='⛓️')
                createNewAccount()
        
if __name__ == '__main__':
    main()