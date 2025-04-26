import telebot
import requests
import logging
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# === Настройки ===
TELEGRAM_TOKEN = "7778726649:AAFy7Rl7d3_2L-SJNXx3bnWCm1U7faZgTO0"
AUDD_API_TOKEN = "0a1ca1b1ebbca8118dac37831eefdc7a"

bot = telebot.TeleBot(TELEGRAM_TOKEN)

# === Логирование в консоль и файл ===
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logfile = open("logs.txt", "a", encoding="utf-8")

# === Команда /start ===
@bot.message_handler(commands=['start'])
def start_message(message):
    bot.send_message(message.chat.id,
        "Привет! Я музыкальный бот. Отправь мне фрагмент песни — я найду название и исполнителя.")

# === Команда /help ===
@bot.message_handler(commands=['help'])
def help_message(message):
    bot.send_message(message.chat.id,
        "Отправь мне голосовое, аудио, видео или файл с песней — я попробую её распознать.")

# === Ответ на текст ===
@bot.message_handler(content_types=['text'])
def text_message(message):
    bot.send_message(message.chat.id,
        "Чтобы распознать трек, отправь мне аудио, голосовое или видео.")

# === Обработка медиа ===
@bot.message_handler(content_types=['audio', 'voice', 'video', 'video_note', 'document'])
def handle_media(message):
    try:
        file_id = getattr(message, message.content_type).file_id
        file_info = bot.get_file(file_id)
        file_path = file_info.file_path
        file_url = f"https://api.telegram.org/file/bot{TELEGRAM_TOKEN}/{file_path}"

        logging.info(f"Файл от {message.chat.username or message.chat.id} ({message.content_type}): {file_path}")
        logfile.write(f"{message.chat.username or message.chat.id} | {file_path}\n")

        bot.send_message(message.chat.id, "Распознаю трек, подожди немного...")

        # Запрос в Audd API
        response = requests.post(
            'https://api.audd.io/',
            data={
                'api_token': AUDD_API_TOKEN,
                'url': file_url,
                'return': 'apple_music,spotify,youtube,soundcloud,deezer',
            }
        )

        result = response.json()
        if result['status'] == 'success' and result.get('result'):
            track = result['result']
            title = track.get('title', 'Без названия')
            artist = track.get('artist', 'Неизвестен')
            album = track.get('album', '')
            cover = track.get('spotify', {}).get('album', {}).get('images', [{}])[0].get('url', '')

            # Текст ответа
            msg = f"Название: {title}\nИсполнитель: {artist}"
            if album:
                msg += f"\nАльбом: {album}"

            # Кнопки
            markup = InlineKeyboardMarkup()

            # Добавляем кнопки для платформ, если они доступны
            if track.get('song_link'):
                markup.add(InlineKeyboardButton("Слушать на платформе", url=track['song_link']))

            if track.get('spotify'):
                spotify_link = track['spotify'].get('url', '')
                if spotify_link:
                    markup.add(InlineKeyboardButton("Слушать в Spotify", url=spotify_link))

            if track.get('apple_music'):
                apple_music_link = track['apple_music'].get('url', '')
                if apple_music_link:
                    markup.add(InlineKeyboardButton("Слушать в Apple Music", url=apple_music_link))

            if track.get('youtube'):
                youtube_link = track['youtube'].get('url', '')
                if youtube_link:
                    markup.add(InlineKeyboardButton("Слушать на YouTube", url=youtube_link))

            if track.get('soundcloud'):
                soundcloud_link = track['soundcloud'].get('url', '')
                if soundcloud_link:
                    markup.add(InlineKeyboardButton("Слушать на SoundCloud", url=soundcloud_link))

            if track.get('deezer'):
                deezer_link = track['deezer'].get('url', '')
                if deezer_link:
                    markup.add(InlineKeyboardButton("Слушать на Deezer", url=deezer_link))

            # Кнопка для повторного поиска
            markup.add(InlineKeyboardButton("Повторить поиск", callback_data="retry"))

            bot.send_message(message.chat.id, msg, parse_mode="Markdown", reply_markup=markup)
            if cover:
                bot.send_photo(message.chat.id, cover)
        else:
            bot.send_message(message.chat.id, "Не удалось распознать трек. Попробуй отправить другой файл.")

    except Exception as e:
        logging.exception("Ошибка при обработке")
        bot.send_message(message.chat.id, f"Произошла ошибка: {e}")

# === Обработка нажатий кнопок ===
@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    if call.data == "retry":
        bot.answer_callback_query(call.id, "Отправь новый фрагмент аудио или видео.")
        bot.send_message(call.message.chat.id, "Жду новый файл!")

# === Запуск бота ===
print("Бот запущен. Ждёт сообщений...")
bot.polling(none_stop=True)