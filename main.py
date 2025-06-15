import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto
import random
import time
import json
import os
from crypto_api import CryptoPayAPI
from config import BOT_TOKEN, CRYPTO_TOKEN, ADMIN_ID

bot = telebot.TeleBot(BOT_TOKEN)
crypto = CryptoPayAPI(CRYPTO_TOKEN)

SYMBOLS = ['🍒', '🍋', '🔔', '💎', '🍇', '7️⃣']

# Загрузка данных
def load_data():
    global users, leaders, invoices, promocodes, transactions
    try:
        with open('users.json', 'r') as f:
            users = json.load(f)
    except:
        users = {}
    
    try:
        with open('leaders.json', 'r') as f:
            leaders = json.load(f)
    except:
        leaders = {}
    
    try:
        with open('invoices.json', 'r') as f:
            invoices = json.load(f)
    except:
        invoices = {}
    
    try:
        with open('promocodes.json', 'r') as f:
            promocodes = json.load(f)
    except:
        promocodes = {}
    
    try:
        with open('transactions.json', 'r') as f:
            transactions = json.load(f)
    except:
        transactions = {}

def save_data():
    with open('users.json', 'w') as f:
        json.dump(users, f)
    with open('leaders.json', 'w') as f:
        json.dump(leaders, f)
    with open('invoices.json', 'w') as f:
        json.dump(invoices, f)
    with open('promocodes.json', 'w') as f:
        json.dump(promocodes, f)
    with open('transactions.json', 'w') as f:
        json.dump(transactions, f)

load_data()

# ========== Helpers ==========
def get_balance(uid): return users.get(str(uid), 1000)

def set_balance(uid, val): 
    users[str(uid)] = val
    save_data()

def add_balance(uid, val):
    uid = str(uid)
    users[uid] = get_balance(uid) + val
    save_data()

def add_win(uid, val):
    uid = str(uid)
    leaders[uid] = leaders.get(uid, 0) + val
    save_data()

def is_admin(uid):
    return str(uid) == str(ADMIN_ID)

def main_menu_kb():
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("🎰Деп", callback_data="play"))
    kb.add(InlineKeyboardButton("💰Кэш", callback_data="balance"))
    kb.add(InlineKeyboardButton("🛒Магаз", callback_data="shop"))
    kb.add(InlineKeyboardButton("🏆Лидеры", callback_data="leaders"))
    kb.add(InlineKeyboardButton("💸Перевод", callback_data="transfer"))  # Новая кнопка перевода
    return kb

def back_kb():
    return InlineKeyboardMarkup().add(InlineKeyboardButton("🔙", callback_data="menu"))

def admin_kb():
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("📢 Рассылка", callback_data="admin_mailing"))
    kb.add(InlineKeyboardButton("🎁 Промокод", callback_data="admin_create_promo"))
    return kb

# ========== Start Command ==========
@bot.message_handler(commands=['start'])
def start_handler(message):
    uid = message.from_user.id
    users.setdefault(str(uid), 1000)
    save_data()
    
    if is_admin(uid) and message.text == '/start admin':
        bot.send_message(uid, "Админ панель:", reply_markup=admin_kb())
        return
    
    bot.send_sticker(uid, 'CAACAgQAAxkBAAEOs2FoTkndPmDU0GNif_ppju_cs1VbdgACvBgAAp7ecVL-Xlydi3VS6zYE')
    with open("menu.jpg", "rb") as photo:
        bot.send_photo(uid, photo, reply_markup=main_menu_kb())

# ========== Callback Handling ==========
@bot.callback_query_handler(func=lambda c: True)
def callback_handler(call):
    uid = call.from_user.id
    msg_id = call.message.message_id

    if call.data == 'menu':
        with open("menu.jpg", "rb") as photo:
            bot.edit_message_media(
                media=InputMediaPhoto(photo),
                chat_id=uid,
                message_id=msg_id,
                reply_markup=main_menu_kb()
            )

    elif call.data == 'balance':
        kb = back_kb()
        text = f"```\n💵 Ваш баланс: {get_balance(uid)}$\n```"
        bot.edit_message_caption(
            chat_id=uid,
            message_id=msg_id,
            caption=text,
            parse_mode="Markdown",
            reply_markup=kb
        )

    elif call.data == 'play':
        if get_balance(uid) < 100:
            bot.answer_callback_query(call.id, "Недостаточно монет!", show_alert=True)
            return
        add_balance(uid, -100)
        symbols, result_text, chance_bar = roll_with_animation(uid, call.message)
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("🔄", callback_data='play'))
        kb.add(InlineKeyboardButton("🔙", callback_data='menu'))
        bot.edit_message_caption(
            chat_id=uid,
            message_id=call.message.message_id,
            caption=f"🎰 {symbols}\n{result_text}\n🎯 Шанс: {chance_bar}",
            reply_markup=kb
        )

    elif call.data == 'shop':
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("100 монет — $0.1", callback_data="buy_100"))
        kb.add(InlineKeyboardButton("300 монет — $0.2", callback_data="buy_300"))
        kb.add(InlineKeyboardButton("500 монет — $0.5", callback_data="buy_500"))
        kb.add(InlineKeyboardButton("🔙", callback_data='menu'))
        bot.edit_message_caption(
            chat_id=uid,
            message_id=msg_id,
            caption="\u200b",
            reply_markup=kb
        )

    elif call.data.startswith("buy_"):
        amount_map = {'buy_100': (0.1, 100), 'buy_300': (0.2, 300), 'buy_500': (0.5, 500)}
        price, coins = amount_map[call.data]
        invoice = crypto.create_invoice(price, payload=f"{uid}|{coins}")
        if invoice:
            invoices[str(uid)] = invoice["invoice_id"]
            save_data()
            kb = InlineKeyboardMarkup()
            kb.add(InlineKeyboardButton("💳Оплатить деп", url=invoice["pay_url"]))
            kb.add(InlineKeyboardButton("✅Проверка", callback_data="check_payment"))
            kb.add(InlineKeyboardButton("🔙", callback_data='menu'))
            bot.edit_message_caption(
                chat_id=uid,
                message_id=msg_id,
                caption="\u200b",
                reply_markup=kb
            )

    elif call.data == 'check_payment':
        invoice_id = invoices.get(str(uid))
        if invoice_id:
            invoice = crypto.check_invoice(invoice_id)
            if invoice and invoice.get("status") == "paid":
                _, coins = invoice.get("payload", "0|0").split("|")
                add_balance(uid, int(coins))
                bot.answer_callback_query(call.id, "Оплата прошла. Баланс пополнен.")
            else:
                bot.answer_callback_query(call.id, "Оплата не найдена.")
        else:
            bot.answer_callback_query(call.id, "Инвойс не найден")

    elif call.data == 'leaders':
        board = sorted(leaders.items(), key=lambda x: -x[1])[:5]
        lines = [f"{i+1}. @{bot.get_chat(int(u)).username or u} | {w}$ | {get_balance(u)}$" 
                for i, (u, w) in enumerate(board)]
        text = "\n".join(lines)
        kb = back_kb()
        bot.edit_message_caption(
            chat_id=uid,
            message_id=msg_id,
            caption=f"```\n🏆 Лидеры:\nЮзер | Вины | Баланс\n{text}\n```",
            parse_mode="Markdown",
            reply_markup=kb
        )

    elif call.data == 'transfer':  # Новый обработчик перевода
        msg = bot.send_message(uid, "Введите ID пользователя и сумму перевода через пробел (пример: 7893893 100)")
        bot.register_next_step_handler(msg, process_transfer)

    elif call.data == 'admin_mailing' and is_admin(uid):
        msg = bot.send_message(uid, "Введите текст рассылки:")
        bot.register_next_step_handler(msg, process_mailing)

    elif call.data == 'admin_create_promo' and is_admin(uid):
        msg = bot.send_message(uid, "Введите промокод и сумму через пробел:")
        bot.register_next_step_handler(msg, process_create_promo)

# ========== Transfer Function ==========
def process_transfer(message):
    uid = str(message.from_user.id)
    try:
        parts = message.text.split()
        if len(parts) != 2:
            raise ValueError
        
        recipient_id, amount = parts[0], int(parts[1])
        
        if uid == recipient_id:
            bot.send_message(uid, " Нельзя переводить себе!", reply_markup=main_menu_kb())
            return
            
        if amount <= 0:
            bot.send_message(uid, " Сумма должна быть больше 0", reply_markup=main_menu_kb())
            return
            
        if get_balance(uid) < amount:
            bot.send_message(uid, f"Недостаточно средств Ваш баланс: {get_balance(uid)}$", 
                            reply_markup=main_menu_kb())
            return
            
        # Проверяем существует ли получатель
        try:
            bot.get_chat(recipient_id)
        except:
            bot.send_message(uid, "не найден", reply_markup=main_menu_kb())
            return
            
        # Выполняем перевод
        add_balance(uid, -amount)
        add_balance(recipient_id, amount)
        
        # Записываем транзакцию
        transaction = {
            'from': uid,
            'to': recipient_id,
            'amount': amount,
            'time': int(time.time())
        }
        transactions[str(int(time.time()))] = transaction
        save_data()
        
        bot.send_message(uid, f"Перевод {amount}$ пользователю ID:{recipient_id} выполнен!", 
                        reply_markup=main_menu_kb())
        
        # Уведомляем получателя
        try:
            bot.send_message(recipient_id, f"💸 Вам перевели {amount}$ от пользователя ID:{uid}")
        except:
            pass
            
    except ValueError:
        bot.send_message(message.chat.id, "Ошибка формата вот так надо блять 7383838 100", reply_markup=main_menu_kb())
    except Exception as e:
        print(f"Transfer error: {e}")
        bot.send_message(message.chat.id, "ошибка при переводе", reply_markup=main_menu_kb())

# ========== Game Logic ==========
def roll_with_animation(uid, msg):
    slots = ['❓', '❓', '❓']
    for i in range(3):
        for _ in range(3):
            slots[i] = random.choice(SYMBOLS)
            try:
                bot.edit_message_caption(
                    chat_id=msg.chat.id,
                    message_id=msg.message_id,
                    caption=f"🎰 {' | '.join(slots)}"
                )
            except:
                pass
            time.sleep(0.3)

    if slots[0] == slots[1] == slots[2]:
        win = 500
        add_balance(uid, win)
        add_win(uid, win)
        result = "😛 Джекпот! +500$"
    elif len(set(slots)) == 2:
        win = 150
        add_balance(uid, win)
        add_win(uid, win)
        result = "😁 Почти +150$"
    else:
        result = "😭 Не повезло."

    chance = random.randint(30, 95)
    bar = f"[{('🟩' * (chance // 10)).ljust(10)}] {chance}%"
    return " | ".join(slots), result, bar

# ========== Admin Functions ==========
def process_mailing(message):
    if not is_admin(message.from_user.id):
        return
    
    text = message.text
    success = 0
    for user_id in users:
        try:
            bot.send_message(user_id, text)
            success += 1
        except:
            continue
    bot.send_message(message.from_user.id, f"Рассылка завершена\nУспешно: {success}")

def process_create_promo(message):
    if not is_admin(message.from_user.id):
        return
    
    try:
        promo, amount = message.text.split()
        promocodes[promo.upper()] = int(amount)
        save_data()
        bot.send_message(message.from_user.id, f"Промокод {promo} на {amount}$ создан!")
    except:
        bot.send_message(message.from_user.id, "Ошибка формата")

# ========== Run Bot ==========
if __name__ == '__main__':
    print("Бот запущен!")
    bot.infinity_polling()
