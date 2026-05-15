import telebot
from telebot import types
import subprocess
import os
import re
from fpdf import FPDF

# 🔧 إعدادات البوت الأساسية
API_TOKEN = '8884141366:AAE01llBmMCrh82S7cOPIxkFAkxrbokoIL4'
bot = telebot.TeleBot(API_TOKEN)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
user_sessions = {}

# ℹ️ معلومات الحقوق
MY_CHANNEL = "@altaee_z"
MY_WEBSITE = "www.ali-Altaee.free.nf"

# --- وظيفة إنشاء PDF المحدثة ---
def create_pdf(chat_id, code, inputs, result):
    pdf = FPDF()
    pdf.add_page()
    
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt="C++ Execution Report", ln=True, align='C')
    pdf.ln(5)
    
    pdf.set_font("Courier", 'B', 12)
    pdf.set_fill_color(230, 230, 230)
    pdf.cell(0, 10, txt=" Source Code:", ln=True, fill=True)
    pdf.set_font("Courier", '', 10)
    pdf.multi_cell(0, 5, txt=code)
    pdf.ln(5)
    
    if inputs:
        pdf.set_font("Courier", 'B', 12)
        pdf.set_fill_color(255, 243, 205)
        pdf.cell(0, 10, txt=" User Inputs (Input Data):", ln=True, fill=True)
        pdf.set_font("Courier", '', 11)
        pdf.multi_cell(0, 7, txt=inputs)
        pdf.ln(5)
    
    pdf.set_font("Courier", 'B', 12)
    pdf.set_fill_color(212, 237, 218)
    pdf.cell(0, 10, txt=" Execution Output:", ln=True, fill=True)
    pdf.set_font("Courier", 'B', 11)
    pdf.multi_cell(0, 7, txt=result)
    
    pdf.ln(15)
    pdf.set_font("Arial", 'I', 8)
    pdf.cell(0, 10, txt=f"Developer: {MY_CHANNEL} | Web: {MY_WEBSITE} || @Execut_C_Bot", align='C')
    
    pdf_path = os.path.join(BASE_DIR, f"Report_{chat_id}.pdf")
    pdf.output(pdf_path)
    return pdf_path

# --- الأزرار والقوائم ---
def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("🗑️ مسح الجلسة"))
    return markup

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(message.chat.id, f"👋 أهلاً بك يا علي.\nأرسل كود C++ وسأقوم بإنشاء تقرير PDF كامل.", reply_markup=main_menu())

@bot.message_handler(func=lambda message: message.text == "🗑️ مسح الجلسة")
def clear(message):
    user_sessions.pop(message.chat.id, None)
    bot.send_message(message.chat.id, "✅ تم تصفير الجلسة.")

@bot.message_handler(func=lambda message: True)
def handle_text(message):
    chat_id = message.chat.id
    if chat_id in user_sessions and user_sessions[chat_id].get('waiting_for_input'):
        user_sessions[chat_id]['inputs'].append(message.text)
        process_next_step(chat_id)
    elif "#include" in message.text:
        handle_cpp_logic(chat_id, message.text)

def handle_cpp_logic(chat_id, code):
    inputs_needed = re.findall(r"cin\s*>>\s*([a-zA-Z0-9_]+)", code)
    prompts = re.findall(r'cout\s*<<\s*"(.*?)";', code)
    if inputs_needed:
        user_sessions[chat_id] = {'code': code, 'inputs_needed': inputs_needed, 'prompts': prompts, 'inputs': [], 'current_step': 0, 'waiting_for_input': True}
        process_next_step(chat_id)
    else:
        compile_and_run_cpp(chat_id, code)

def process_next_step(chat_id):
    session = user_sessions[chat_id]
    step = session['current_step']
    if step < len(session['inputs_needed']):
        prompt = session['prompts'][step] if step < len(session['prompts']) else f"Enter {session['inputs_needed'][step]}:"
        bot.send_message(chat_id, f"📝 {prompt}")
        session['current_step'] += 1
    else:
        all_inputs = "\n".join(session['inputs'])
        compile_and_run_cpp(chat_id, session['code'], all_inputs)
        del user_sessions[chat_id]

# --- تعديل دالة التشغيل لتعمل على السيرفر ---
def compile_and_run_cpp(chat_id, code, inputs_data=None):
    # استخدام امتداد .out ليتناسب مع أنظمة Linux (السيرفرات)
    file_cpp = os.path.join(BASE_DIR, f"code_{chat_id}.cpp")
    file_exe = os.path.join(BASE_DIR, f"code_{chat_id}.out")
    
    with open(file_cpp, "w", encoding="utf-8") as f: f.write(code)

    try:
        # 1. التعديل هنا: إضافة shell=True لضمان العثور على g++ في السيرفر
        compile_cmd = f"g++ {file_cpp} -o {file_exe}"
        if subprocess.run(compile_cmd, shell=True, capture_output=True).returncode != 0:
            bot.send_message(chat_id, "❌ خطأ في الكومبايل. تأكد من صحة الكود أو إعدادات السيرفر.")
            return

        # 2. التعديل هنا: تشغيل الملف الناتج مع إضافة الصلاحيات والـ shell
        run_res = subprocess.run([file_exe], input=inputs_data, capture_output=True, text=True, shell=True, timeout=10)
        
        output = run_res.stdout
        for p in re.findall(r'cout\s*<<\s*"(.*?)";', code): output = output.replace(p, "")

        result_text = output.strip() if output.strip() else "Executed successfully."
        bot.send_message(chat_id, f"💻 <b>النتيجة:</b>\n<pre>{result_text}</pre>\n تم بواسطة بوت @Execut_C_Bot", parse_mode="HTML")

        pdf_path = create_pdf(chat_id, code, inputs_data, result_text)
        with open(pdf_path, 'rb') as f:
            bot.send_document(chat_id, f, caption="📄 التقرير الشامل (Code + Inputs + Result)")
        os.remove(pdf_path)

    except Exception as e:
        bot.send_message(chat_id, f"❌ حدث خطأ: {str(e)}")
    finally:
        if os.path.exists(file_cpp): os.remove(file_cpp)
        if os.path.exists(file_exe): os.remove(file_exe)

bot.infinity_polling()
