import telebot
from telebot import types
import sqlite3
from datetime import datetime

# Инициализация бота
TOKEN = '5870874378:AAG5bQCHt_Zi6R7krBiQT0ZiUyE_9B9USlg'
bot = telebot.TeleBot(TOKEN)

# Создание базы данных SQLite
conn = sqlite3.connect('notes.db')
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS notes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        title TEXT,
        content TEXT,
        author TEXT,
        date_created DATETIME
    )
''')
conn.commit()

# Обработчик команды /post
@bot.message_handler(commands=['post'])
def post_handler(message):
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
    markup.add(types.KeyboardButton('Опубликовать'), types.KeyboardButton('Отмена'))
    bot.send_message(message.chat.id, 'Введите заголовок заметки:', reply_markup=markup)
    bot.register_next_step_handler(message, get_title)


def get_title(message):
    title = message.text
    bot.send_message(message.chat.id, 'Введите текст заметки:')
    bot.register_next_step_handler(message, get_content, title)


def get_content(message, title):
    content = message.text
    author = message.from_user.username
    date_created = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    conn = sqlite3.connect('notes.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO notes (user_id, title, content, author, date_created) VALUES (?, ?, ?, ?, ?)',
                   (message.from_user.id, title, content, author, date_created))
    conn.commit()

    markup = types.ReplyKeyboardRemove(selective=False)
    bot.send_message(message.chat.id, f'Заметка сохранена:\n\n<b>{title}</b>\n\n{content}\n\nАвтор: {author}\nДата создания: {date_created}',
                     parse_mode='html', reply_markup=markup)


# Обработчик команды /news
@bot.message_handler(commands=['news'])
def news_handler(message):
    conn = sqlite3.connect('notes.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id, title FROM notes')
    notes = cursor.fetchall()

    markup = types.InlineKeyboardMarkup(row_width=1)

    for note in notes:
        button = types.InlineKeyboardButton(note[1], callback_data=f'show_note_{note[0]}')
        markup.add(button)

    bot.send_message(message.chat.id, 'Выберите заметку:', reply_markup=markup)


# Обработчик нажатия на кнопку с заголовком заметки
@bot.callback_query_handler(func=lambda call: call.data.startswith('show_note_'))
def show_note_handler(call):
    note_id = int(call.data.split('_')[1])

    conn = sqlite3.connect('notes.db')
    cursor = conn.cursor()
    cursor.execute('SELECT title, content, author, date_created FROM notes WHERE id = ?', (note_id,))
    note_data = cursor.fetchone()

    note_text = f'<b>{note_data[0]}</b>\n\n{note_data[1]}\n\nАвтор: {note_data[2]}\nДата создания: {note_data[3]}'

    bot.send_message(call.message.chat.id, note_text, parse_mode='html')


if __name__ == "__main__":
    bot.polling(none_stop=True)
