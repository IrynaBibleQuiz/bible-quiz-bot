import json
import logging
import os
from pathlib import Path
from threading import Thread

from flask import Flask
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes

logging.basicConfig(level=logging.INFO)
QUESTIONS = json.loads(Path(__file__).with_name('questions.json').read_text(encoding='utf-8'))
assert len(QUESTIONS) == 100
TOKEN = os.environ['BOT_TOKEN']
web = Flask(__name__)

@web.get('/')
def health():
    return 'Bible quiz bot is running', 200

def run_web():
    web.run(host='0.0.0.0', port=int(os.environ.get('PORT', '10000')))

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['index'] = 0
    context.user_data['score'] = 0
    await update.effective_message.reply_text('📖 Біблійна вікторина: Матвій та Марко!\n100 запитань, 4 варіанти відповіді. Результат побачиш лише наприкінці.\n\nНатисни /quiz, щоб почати.')

async def quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['index'] = 0
    context.user_data['score'] = 0
    await show_question(update, context)

async def show_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    index = context.user_data['index']
    if index >= len(QUESTIONS):
        score = context.user_data['score']
        text = f'🎉 Вікторину завершено!\n\n✅ Правильних: {score}\n❌ Неправильних: {100-score}\n🏆 Результат: {score}/100 ({score}%)\n\nЩоб пройти ще раз: /quiz'
        await update.effective_message.reply_text(text)
        return
    q = QUESTIONS[index]
    buttons = [[InlineKeyboardButton(f'{chr(65+i)}. {option}', callback_data=f'a:{index}:{i}')] for i, option in enumerate(q['options'])]
    text = f'📖 Запитання {index+1}/100 ({q["book"]})\n\n{q["question"]}'
    await update.effective_message.reply_text(text, reply_markup=InlineKeyboardMarkup(buttons))

async def answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    try:
        _, idx, choice = query.data.split(':')
        idx, choice = int(idx), int(choice)
    except (ValueError, AttributeError):
        return
    if context.user_data.get('index') != idx:
        await query.answer('Це запитання вже пройдено.', show_alert=True)
        return
    if choice == QUESTIONS[idx]['answer']:
        context.user_data['score'] += 1
    context.user_data['index'] = idx + 1
    await query.edit_message_reply_markup(reply_markup=None)
    if idx + 1 < 100:
        await show_question(update, context)
    else:
        score = context.user_data['score']
        await query.message.reply_text(f'🎉 Вікторину завершено!\n\n✅ Правильних: {score}\n❌ Неправильних: {100-score}\n🏆 Результат: {score}/100 ({score}%)\n\nПовторити: /quiz')

def main():
    Thread(target=run_web, daemon=True).start()
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler('quiz', quiz))
    app.add_handler(CallbackQueryHandler(answer, pattern=r'^a:\d+:\d+$'))
    app.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
