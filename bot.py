import os
import telebot
import google.generativeai as genai
import ffmpeg

TELEGRAM_TOKEN = 'AAHvP6VkEs43oBI6qLAYRD47hkAFS3XKos0'

bot = telebot.TeleBot(TELEGRAM_TOKEN)

user_keys = {}
user_states = {}

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    welcome_text = (
        "🎬 *ZM Movie Recap Pro Bot* မှ ကြိုဆိုပါတယ်!\n\n"
        "ပထမဆုံးအနေဖြင့် သင်၏ **Google Gemini API Key** ကို Bot ထဲသို့ ထည့်သွင်းပေးရပါမည်။\n"
        "ကျေးဇူးပြု၍ သင့်ရဲ့ Gemini API Key ကို ပို့ပေးပါခင်ဗျာ!"
    )
    user_states[message.chat.id] = 'waiting_for_key'
    bot.reply_to(message, welcome_text, parse_mode='Markdown')

@bot.message_handler(content_types=['text', 'video'])
def handle_incoming(message):
    chat_id = message.chat.id
    
    if user_states.get(chat_id) == 'waiting_for_key' and message.text:
        user_key = message.text.strip()
        user_keys[chat_id] = user_key
        user_states[chat_id] = 'ready'
        bot.reply_to(message, "✅ API Key ကို အောင်မြင်စွာ မှတ်သားပြီးပါပြီ!\n\nအခု တရုတ်/အင်္ဂလိပ် ဇာတ်လမ်းစာသားများ (သို့မဟုတ်) ဗီဒီယိုဖိုင်များကို ပို့နိုင်ပါပြီ။")
        return

    if chat_id not in user_keys:
        user_states[chat_id] = 'waiting_for_key'
        bot.reply_to(message, "⚠️ ကျေးဇူးပြု၍ သင်၏ **Google Gemini API Key** ကို ဦးစွာ ပို့ပေးပါခင်ဗျာ။")
        return

    genai.configure(api_key=user_keys[chat_id])
    model = genai.GenerativeModel('gemini-1.5-flash')

    if message.content_type == 'text':
        user_input = message.text
        processing_msg = bot.reply_to(message, "⏳ ဇာတ်လမ်းအကျဉ်းကို အပိုင်းလိုက် (Parts) ခွဲ၍ ဆွဲဆောင်မှုရှိသော မြန်မာဇာတ်ကြောင်းအဖြစ် ပြောင်းလဲနေပါပြီ...")

        prompt = (
            "You are an expert professional movie recap scriptwriter for TikTok and Facebook Reels. "
            "The input text may be in Chinese or English. Understand the full plot deeply and rewrite it into an engaging, dramatic, "
            "and captivating Burmese (Myanmar) narration script split into clear parts (Part 1, Part 2, Part 3, etc.). "
            "Make the hooks strong, use a natural conversational storytelling tone, and add relevant popular hashtags at the end:\n\n"
            f"{user_input}"
        )

        try:
            response = model.generate_content(prompt)
            ai_output = response.text
            bot.edit_message_text(
                chat_id=chat_id,
                message_id=processing_msg.message_id,
                text=f"✨ *Generated Multi-Part Recap Scripts:*\n\n{ai_output}",
                parse_mode='Markdown'
            )
        except Exception as e:
            bot.edit_message_text(
                chat_id=chat_id,
                message_id=processing_msg.message_id,
                text=f"❌ အမှားအယွင်း ဖြစ်သွားပါသည် (API Key မှန်ရဲ့လား စစ်ဆေးပါ): {str(e)}"
            )

    elif message.content_type == 'video':
        processing_msg = bot.reply_to(message, "🎬 ဗီဒီယိုကို Copyright Safe ဖြစ်စေရန် အစအဆုံး ပြုပြင်နေပါပြီ (hflip & watermark)... ခဏစောင့်ပါ...")
        
        try:
            file_info = bot.get_file(message.video.file_id)
            downloaded_file = bot.download_file(file_info.file_path)

            input_filename = f"input_{chat_id}.mp4"
            output_filename = f"output_{chat_id}.mp4"

            with open(input_filename, 'wb') as new_file:
                new_file.write(downloaded_file)

            stream = ffmpeg.input(input_filename)
            video = stream.video.hflip().filter(
                'drawtext', 
                text="ZM Movie Recap", 
                x='w-tw-50', 
                y=50, 
                fontsize=28, 
                fontcolor='white', 
                box=1, 
                boxcolor='black@0.6'
            )
            audio = stream.audio.filter('atempo', 1.04)
            output = ffmpeg.output(video, audio, output_filename, vcodec='libx264', acodec='aac', video_bitrate='2.5M')
            ffmpeg.run(output, overwrite_output=True, quiet=True)

            with open(output_filename, 'rb') as video_result:
                bot.send_video(chat_id, video_result, caption="✅ Copyright Safe ဖြစ်အောင် အစအဆုံး ပြုပြင်ပြီးပါပြီ!")

            bot.delete_message(chat_id, processing_msg.message_id)

            if os.path.exists(input_filename): os.remove(input_filename)
            if os.path.exists(output_filename): os.remove(output_filename)

        except Exception as e:
            bot.edit_message_text(
                chat_id=chat_id,
                message_id=processing_msg.message_id,
                text=f"❌ ဗီဒီယိုပြုပြင်ရာတွင် အမှားအယွင်း ဖြစ်သွားပါသည်: {str(e)}"
            )

if __name__ == '__main__':
    print("🤖 ZM Movie Recap Pro Bot with Dynamic API Key is running smoothly...")
    bot.infinity_polling()
