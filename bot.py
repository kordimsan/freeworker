import config
import geocoder
import os
import re
import mysql.connector
import pymysql
pymysql.install_as_MySQLdb()
import sqlite3 as SQLighter
from config import database_name
from telegram import ReplyKeyboardMarkup,InlineKeyboardButton,InlineKeyboardMarkup,KeyboardButton,forcereply,InputMediaPhoto
from telegram.ext import Updater,CommandHandler,MessageHandler,Filters,RegexHandler,ConversationHandler,CallbackQueryHandler
import logging
from math import radians, cos, sin, asin, sqrt
from decimal import Decimal
from docxtpl import DocxTemplate
from PIL import Image

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',level=logging.INFO)
logger = logging.getLogger(__name__)
CHOOSING, TYPING_REPLY, TYPING_CHOICE = range(3)

#######################################################################################################################################

user_dic={}
order_dic={}
user_sort={}
order_sort={}
order_status={}
skill_status={}

def start(bot, update):
    chat_id=update.message.chat.id
    print (update)
    txt='Здравствуйте {}'.format(update.message.from_user.first_name)
    bot.send_message(chat_id,txt,parse_mode='Markdown')
    mainmenu(bot, update)

def help(bot, update):
    chat_id=update.message.chat.id
    bot.sendChatAction(chat_id,'typing')
    file=open('description.txt', 'r')
    txt = file.read()
    file.close()
    bot.send_message(chat_id,txt,parse_mode='Markdown')

def mainmenu(bot, update):
    user_id=update.message.from_user.id
    chat_id=update.message.chat.id
    row=dbcon('SELECT status_id FROM t_status WHERE user_id=%s', (user_id,)).fetchone()
    if row is None: emoji='🚦 Мой статус'
    elif row[0]==0: emoji='✅ Мой статус: Свободен'
    elif row[0]==1: emoji='🚸 Мой статус: Занят'
    elif row[0]==2: emoji='🛄 Мой статус: В отпуске'
    
    row=dbcon('SELECT * FROM t_users WHERE user_id=%s', (user_id,)).fetchone()
    if row is None:
        rc=True
        txt='👤 Зарегистрироваться'
    else:
        rc=False
        txt='👤 Мой профиль'
    
    keyb0=KeyboardButton(text='💡 Заказы', request_contact=rc)
    keyb1=KeyboardButton(text='👷 Работники', request_contact=rc)
    keyb2=KeyboardButton(text=emoji)
    keyb3=KeyboardButton(text='🌟 Определить навыки', request_contact=rc)
    keyb4=KeyboardButton(text=txt, request_contact=rc)
    keyb5=KeyboardButton(text='🔧 Настройки')
    keyboard = [[keyb0, keyb1], [keyb2], [keyb3], [keyb4,keyb5]]
    if user_id==477937680: keyboard.append([KeyboardButton('🔑 Сообщение пользователям')])
    reply_markup = ReplyKeyboardMarkup(keyboard,one_time_keyboard=True)
    bot.send_message(chat_id,'👇 Выбери дальнейшее действие!',reply_markup=reply_markup)
    
def echo(bot, update):
    user_id=update.message.from_user.id
    chat_id=update.message.chat.id
    msg=update.message.text
    bot.sendChatAction(chat_id,'typing')
    if   msg=='💡 Заказы':            order_menu_keyb(bot,update)
    elif msg=='🆕 Новый заказ':       order_new(bot,chat_id)
    elif msg=='👋 Текущие заказы':    allwork(bot, update)
    elif msg=='💪 Поиск по навыкам':  bot.send_message(chat_id,'Выбери навык:',reply_markup=structure_inline_keyb(0))
    elif msg=='👋 Мои заказы в работе': mywork(bot, update)
    elif msg=='👷 Работники':         workers_keyb(bot, update)
    elif msg=='🌟 Определить навыки': wizard_keyb(bot, update)
    elif msg=='👤 Мой профиль':       my_profile(bot, update)
    elif msg=='⁉️ О сервисе':        help(bot, update)
    elif msg=='🔧 Настройки':         settings(bot,update)
    elif msg=='🌀 Мой ареал':         my_area(bot, update)
    elif msg=='💪 Мои навыки':        used_skills(bot,chat_id,user_id)
    elif msg=='📣 Написать вопрос или пожелание': bot.send_message(chat_id,'📣 Написать вопрос или пожелание',parse_mode='Markdown',reply_markup=forcereply.ForceReply(selective=True))
    elif msg=='⬅️ Вернуться назад':  mainmenu(bot, update)
    elif msg=='❌ Завершить':         mainmenu(bot, update)
    elif msg=='✅ Свободен':          update_status(bot,update,'0')
    elif msg=='🚸 Занят':             update_status(bot,update,'1')
    elif msg=='🛄 В отпуске':         update_status(bot,update,'2')
    elif msg=='▶️ Продолжить':       run_wizard(bot,chat_id,user_id)
    elif msg=='🔑 Сообщение пользователям': bot.send_message(chat_id,'Введи сообщение для пользователей',parse_mode='Markdown',reply_markup=forcereply.ForceReply(selective=True))
    elif msg=='➕ Добавить фото':     bot.send_message(chat_id,'Нажми на 📎 чтобы загрузить фото:',parse_mode='Markdown',reply_markup=forcereply.ForceReply(selective=True))
    elif msg=='✅ Начать':
        dbcon('delete from t_steps where user_id=%s',(user_id,))
        run_wizard(bot,chat_id,user_id)
    elif msg=='🕠 Время рабочего дня (Автостатус)': 
        bot.send_message(chat_id,'Набери диапазон времени рабочего дня:\nс __:__ по __:__',reply_markup=autostatus_inline_keyb2())
        #bot.send_message(chat_id,'Выбери время *начала* рабочего дня:',parse_mode='Markdown',reply_markup=autostatus_inline_keyb(user_id,'time_start_'))

def admin(bot, update):
    rows=dbcon('SELECT user_id FROM t_users',() ).fetchall()
    txt='🎇 С наступающим *Новый Годом*, уважаемые пользователи сервиса *FreeWorker*, удачи Вам в новом 2️⃣0️⃣1️⃣8️⃣ году'
    #for row in rows:
        #bot.send_message(row[0],text=txt,parse_mode='Markdown')

def my_area(bot, update):
    user_id=update.message.from_user.id
    chat_id=update.message.chat.id
    row=dbcon('SELECT area FROM t_users WHERE user_id =%s', (user_id,)).fetchone()
    bot.send_message(chat_id,'Введи радиус вашего ареала в киломерах\n_(Текущее заначение ареала составляет '+str(row[0])+' километров)_',parse_mode='Markdown',reply_markup=forcereply.ForceReply(selective=True))

def my_profile(bot, update):
    user_id=update.message.from_user.id
    chat_id=update.message.chat.id
    keyboard=[[KeyboardButton('👋 Мои заказы в работе')],[KeyboardButton('⬅️ Вернуться назад')]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    bot.send_message(chat_id,update.message.text,reply_markup=reply_markup)
    bot.send_message(chat_id,user_detail(user_id),parse_mode='Markdown',reply_markup=user_detail_keyb(user_id))

def allwork(bot, update):
    user_id=update.message.from_user.id
    chat_id=update.message.chat.id
    order_sort[user_id]='post_date desc'
    order_status[user_id]=1
    skill_status[user_id]=None
    #update.message.reply_text(update.message.text, reply_markup=ReplyKeyboardMarkup([['⬅️ Вернуться назад']], resize_keyboard=True))
    bot.send_message(chat_id,orders_list(user_id,0),parse_mode='Markdown',reply_markup=orders_inline_keyb(user_id,0))

def mywork(bot, update):
    user_id=update.message.from_user.id
    chat_id=update.message.chat.id
    order_sort[user_id]='post_date desc'
    order_status[user_id]=2
    skill_status[user_id]=None
    update.message.reply_text(update.message.text, reply_markup=ReplyKeyboardMarkup([['⬅️ Вернуться назад']], resize_keyboard=True))
    bot.send_message(chat_id,orders_list(user_id,0),parse_mode='Markdown',reply_markup=orders_inline_keyb(user_id,0))

def No(bot,update):
    chat_id=update.message.chat.id
    user_id=int(update.message.text[4:])
    bot.send_message(chat_id,user_detail(user_id),parse_mode='Markdown',reply_markup=user_detail_keyb(user_id))

def echo_reply(bot, update):
    user_id=update.message.from_user.id
    chat_id=update.message.chat.id
    msg    =update.message.text
    reply  =update.message.reply_to_message.text
    if re.match(r'Вы выбрали оценку.+\n.+Напишите подробнее.+',reply):
        data = {}
        data['user_id'] =int(re.search(r'\d{9}',reply).group(0))
        data['voter_id']=user_id
        data['txt']     =msg
        if msg is None:
            bot.send_message(chat_id=chat_id,text='Ваш отзыв НЕ принят, обнаружен пустой текст')
            mainmenu(bot, update)
        else:
            dbcon('UPDATE t_workers_feedback SET txt=%(txt)s WHERE user_id=%(user_id)s and voter_id=%(voter_id)s',data)
            bot.send_message(chat_id=chat_id,text='Спасибо, Ваш отзыв принят!')
            bot.send_message(chat_id=data['user_id'],text='Новость: Вам столько что оставили отзыв на сервисе FreeWorker! Все отзывы Вы можете посмотреть в разделе "Мой профиль"')
            mainmenu(bot, update)
    elif re.match(r'Введи радиус вашего ареала в киломерах\n.+',reply):
        try:
            area=int(msg)
        except ValueError:
            bot.send_message(chat_id,'Введи радиус вашего ареала в киломерах _(По умолчанию это значение составляет "30")_',parse_mode='Markdown',reply_markup=forcereply.ForceReply(selective=True))
        finally:
            dbcon('UPDATE t_users SET area=%s WHERE user_id=%s',(area,user_id,))
            bot.send_message(chat_id,'Спасибо, Радиус Вашего ареала теперь составляет '+msg+' км!')
            mainmenu(bot, update)
    elif re.split(r'\n',reply,maxsplit=1)[0]=='✏ Кратко изложите суть вашей задачи.':
        bot.sendChatAction(chat_id,'typing')
        dbcon('INSERT INTO t_orders (user_id,txt) VALUES (%s,%s)',(user_id,msg,))
        order_id=dbcon('SELECT max(id) FROM t_orders WHERE user_id=%s',(user_id,)).fetchone()[0]
        words = re.findall(r'[A-Za-zА-Яа-я]+',msg)
        keyboard=[]
        ch=1
        for word in words:
            if len(word)>2:
                pattern = re.compile(word.lower())
                rows=dbcon("SELECT id,skill_name,key_words FROM d_skills where key_words is not null",{})
                for row in rows:
                    if pattern.search(row[2].lower()):
                        if ch==0: emoji='☑️ '
                        else:     emoji='✅ '
                        keyboard.append([InlineKeyboardButton(emoji+row[1], callback_data='order_skill_'+str(order_id)+'_'+str(row[0]) )])
        keyboard.append([InlineKeyboardButton('❓ Нет подходящего варианта', callback_data='order_skill_0')])
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
        bot.send_message(chat_id,'На основании вашего запроса выявлены следующие навыки пользователей, выберите наиболее подходящий для этой задачи:',parse_mode='Markdown',reply_markup=reply_markup)
        
        dts = re.findall(r'\d{4}[\.|\/|,]\d{2}[\.|\/|,]\d{4}|\d{2}[\.|\/|,]\d{2}',msg)
        if len(dts)>0:
            keyboard=[[InlineKeyboardButton('✅ Подтвердить', callback_data='accept'),InlineKeyboardButton('❌ Отклонить', callback_data='decline')]]
            bot.send_message(chat_id,'Так же вы указали дату *"'+dts[0]+'"*, предполагается, это дата действия заявки:',parse_mode='Markdown',reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard))

        order_menu_keyb(bot,update)
    elif reply=='Введи сообщение для пользователей':
        rows=dbcon('SELECT user_id FROM t_users',() ).fetchall()
        for row in rows:
            bot.send_message(row[0],text=msg,parse_mode='Markdown')
        mainmenu(bot, update)
    elif reply=='📣 Написать вопрос или пожелание':
        txt='Сообщение от пользователя ['+update.message.from_user.name+'](tg://user?id='+str(user_id)+')\n〰〰〰〰〰〰〰〰〰\n'+msg
        bot.send_message(477937680,text=txt,parse_mode='Markdown')
        bot.send_message(chat_id,text='Сообщение отправлено! Спасибо!')
        mainmenu(bot, update)
    
def get_contact(bot, update):
    chat_id=update.message.chat.id
    user=update.message.from_user
    contact=update.message.contact
    if contact.user_id != user.id: 
        update.message.reply_text('Зачем Вы мне скидываете не Ваш контакт!')
        return
    bot.sendChatAction(chat_id,'typing')
    data = {}
    data['user_id']     = user.id
    data['user_name']   = user.username
    data['first_name']  = user.first_name
    data['last_name']   = user.last_name
    data['phone_number']= contact.phone_number
    dbcon('INSERT IGNORE INTO t_users (user_id,user_name,user_name_first,user_name_last,phone_number) VALUES (%(user_id)s,%(user_name)s,%(first_name)s,%(last_name)s,%(phone_number)s)',data)
    dbcon('INSERT IGNORE INTO t_status (user_id,status_id) VALUES (%(user_id)s,2)',data)
    dbcon('UPDATE t_users SET user_name=%(user_name)s,user_name_first=%(first_name)s,user_name_last=%(last_name)s,phone_number=%(phone_number)s WHERE user_id=%(user_id)s',data)

    update.message.reply_text('👍 Принято!')
    mainmenu(bot, update)

def get_location(bot, update):
    user    = update.message.from_user
    location= update.message.location
    data = {}
    data['user_id']  = user.id
    data['latitude'] = location.latitude
    data['longitude']= location.longitude
    g = geocoder.yandex([location.latitude, location.longitude], method='reverse',lang='ru-RU')
    if g.city is None: city='Не определен'
    else: city=g.city+', '+g.state
    data['city']= city
    dbcon('UPDATE t_users SET latitude=%(latitude)s,longitude=%(longitude)s,city=%(city)s WHERE user_id=%(user_id)s',data)
    update.message.reply_text('Ваш город: '+city)

    txt='''
Ваш ареал по умолчанию в радиусе 30 км от вашего текущего местоположения.

_(Это означает что в списке работников Вы будете отражаться у пользователей, которые находятся в радиусе 30 км. от Вас)_

*Вы можете поменять данный радиус в настройках* /settings
'''
    update.message.reply_text(txt,parse_mode='Markdown')

def get_photo(bot, update):
    chat_id=update.message.chat.id
    user_id=update.message.from_user.id
    msg    =update.message.caption
    reply  =update.message.reply_to_message.text
    file_id=update.message.photo[-1].file_id
    #if reply=='Нажми на 📎 чтобы загрузить фото:':
    if re.match(r'Вы выбрали оценку.+\n.+Напишите подробнее.+',reply):
        data = {}
        data['user_id'] =int(re.search(r'\d{9}',reply).group(0))
        data['voter_id']=user_id
        data['txt']     =msg
        if msg is not None:
            dbcon('UPDATE t_workers_feedback SET txt=%(txt)s WHERE user_id=%(user_id)s and voter_id=%(voter_id)s',data)
            bot.send_message(chat_id=chat_id,text='Спасибо, Ваш отзыв принят!')
            bot.send_message(chat_id=data['user_id'],text='Новость: Вам столько что оставили отзыв на сервисе FreeWorker! Все отзывы Вы можете посмотреть в разделе "Мой профиль"')
        
        worker_id=data['user_id']
        skill_id =int(re.search(r'\/ZakazNo\d{1,6}',reply).group(0)[9:])
        file_name='photos/'+file_id+'.png'
        newFile = bot.getFile(file_id)
        newFile.download(file_name)
        output_path=watermark_with_transparency(file_name,file_name)
        gg=bot.send_photo(chat_id=-304721253, photo=open(output_path, 'rb'))
        file_id=gg.photo[-1].file_id
        dbcon('INSERT IGNORE INTO t_photos (worker_id,user_id,skill_id,photo_id) VALUES (%s,%s,%s);',(worker_id,user_id,skill_id,file_id,))
        update.message.reply_text('Фото успешно загруженo!',parse_mode='Markdown',reply_to_message_id=update.message.message_id)
        bot.send_message(chat_id=data['user_id'],text='Новость: По вашему выполненному заказу загружена фотография! Все фото Вы можете посмотреть в разделе "Мой профиль"')

        mainmenu(bot, update)

def status_keyb(bot, update):
    keyb0=KeyboardButton(text='✅ Свободен') #, request_location=True
    keyb1=KeyboardButton('🚸 Занят')
    keyb2=KeyboardButton('🛄 В отпуске')
    keyb3=KeyboardButton('🕠 Время рабочего дня (Автостатус)')
    keyb4=KeyboardButton('⬅️ Вернуться назад')
    keyboard = [[keyb0, keyb1, keyb2], [keyb3], [keyb4]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    txt='''
✅ `Свободен:  ` /imfree
🚸 `Занят:     ` /busy
🛄 `В отпуске: ` /holyday'''
    bot.send_message(update.message.chat.id,txt,parse_mode='Markdown',reply_markup=reply_markup)
    #keyboard = [['✅ Свободен', '🚸 Занят','🛄 В отпуске'],['🕠 Время рабочего дня (Автостатус)'],['⬅️ Вернуться назад']]
    #update.message.reply_text(update.message.text, reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))

def imfree (bot, update): update_status(bot,update,'0')
def busy   (bot, update): update_status(bot,update,'1')
def holyday(bot, update): update_status(bot,update,'2')

def update_status(bot,update,status):
    bot.sendChatAction(update.message.chat.id,'typing')
    dbcon('INSERT IGNORE INTO t_status (user_id,status_id) VALUES (%s, '+status+');',(update.message.from_user.id,))
    dbcon('UPDATE t_status SET status_id='+status+',set_date=current_timestamp WHERE user_id=%s;',(update.message.from_user.id,))
    #bot.delete_message(chat_id=update.message.chat_id,message_id=update.message.message_id)
    mainmenu(bot, update)

def workers_keyb(bot, update):
    user_id=update.message.from_user.id
    chat_id=update.message.chat.id
    bot.sendChatAction(chat_id,'typing')
    #update.message.reply_text(update.message.text, reply_markup=ReplyKeyboardMarkup([['⬅️ Вернуться назад']], resize_keyboard=True))
    skill_status[user_id]=None
    bot.send_message(chat_id,workers_list(user_id,0),parse_mode='Markdown',reply_markup=workers_inline_keyb(user_id,0))

def workers_list(user_id,offset,**sorting):    
    if len(sorting)==0: sort='rank desc'
    else: sort=sorting['sort']
    skill_id=skill_status[user_id]
    row=dbcon('SELECT skill_name FROM d_skills where id=%s',(skill_id,)).fetchone()
    head='*Фильтр:* '+row[0]+'\r\n`---------------------`'
    txt=''
    i=0
    #rows=dbcon('SELECT user_name,user_name_first,user_name_last,phone_number,status_id,user_id,rank,cnt,latitude,longitude FROM v_users where user_id<>%s order by '+sort+' LIMIT %s,5',(user_id,offset*5,)).fetchall()
    rows=dbcon('CALL p_get_users_list(%s,%s,%s,%s)',(user_id,sort,offset,skill_id,)).fetchall()
    for row in rows:
        profile='''
Контакт: /uid$user_id
👤` Имя:` *$first_name $last_name*
🚥` Статус:` $status
🚩` Удаленность:` $km
$stars $rank (👥 $fbcnt)
'''#[$first_name $last_name](tg://user?id=user_id)
        if   row[4] is None: emoji='Не установлен'
        elif row[4]==0: emoji='✅ Свободен'
        elif row[4]==1: emoji='🚸 Занят'
        elif row[4]==2: emoji='🛄 В отпуске'
        i+=1
        profile=profile.replace('$status'   ,emoji)
        profile=profile.replace('$num'      ,str(i))
        profile=profile.replace('$user_id'  ,str(row[5]))
        profile=profile.replace('user_name' ,row[0])
        profile=profile.replace('$first_name',row[1].title())
        profile=profile.replace('$last_name' ,row[2].title())
        star='⭐️'*int(row[6])
        blnk='➖'*(5-int(row[6]))
        profile=profile.replace('$stars'    ,star+blnk)
        profile=profile.replace('$rank'     ,'%.1f' % row[6])
        profile=profile.replace('$fbcnt'    ,str(row[7]))
        #ll=dbcon('SELECT latitude,longitude FROM t_users where user_id=%s',(user_id,)).fetchone()
        if row[8] is None or row[8]==99999999:
            profile=profile.replace('$km','Не известно')
        else:
            #profile=profile.replace('$km','%.1f' % haversine(Decimal(str(row[9])), Decimal(str(row[8])), Decimal(str(ll[1])), Decimal(str(ll[0])) ) +' км')
            profile=profile.replace('$km','%.1f' % row[8] +' км')
        txt = txt+('`---------------------`' if i>1 else '')+profile
        #user_dic[str(user_id)+'|/No'+str(i)]=row[5]
    if txt=='' and offset==0: txt=head+'❗️ Работники по близости не найдены!'
    if txt!='': txt=head+txt
    return txt

def workers_inline_keyb(user_id,offset,**sorting):    
    keynum=[]
    if len(sorting)==0: sort='rank desc'
    else: sort=sorting['sort']
    #rows=dbcon('SELECT user_name,user_name_first,user_name_last,phone_number,status_id,user_id,rank,cnt FROM v_users where user_id<>%s order by '+sort+' LIMIT %s,5',(user_id,offset*5,)).fetchall()
    #rows=dbcon('CALL p_get_users_list(%s,%s,%s,%s)',(user_id,sort,offset,skill_id,)).fetchall()
    #i=0
    #ch='❶❷❸❹❺❻❼❽❾❿'
    #for row in rows:
        #i+=1
        #keynum.append(InlineKeyboardButton(text=ch[i-1], callback_data='detail_'+str(row[5])))
    if   sort=='rank desc': txt='🔃 Сортировка по рейтингу 🌟'
    elif sort=='status_id': txt='🔃 Сортировка по статусу 🚦'
    elif sort=='9':         txt='🔃 Сортировка по удаленности 🚩'

    keyboard=[#keynum,
             [InlineKeyboardButton(text=txt, callback_data='workers_sort_'+sort)]
             #,[InlineKeyboardButton(text='✅ Фильтр по статусу', callback_data='filter_status')]
             ,[InlineKeyboardButton(text='◀️', callback_data='workers_list_prev_'+str(offset)),InlineKeyboardButton(text='🔄', callback_data='workers_refresh'),InlineKeyboardButton(text='▶️', callback_data='workers_list_next_'+str(offset))]
             ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def run_wizard(bot,chat_id,user_id):
    rows=dbcon('select id,idp,wizard_name,path from v_wizard where user_id=%s LIMIT 1',(user_id,) ).fetchall()
    if len(rows)>0:
        row=rows[0]
        keyboard = wizard_inline_keyb(row[0])
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
        bot.send_message(chat_id=chat_id,text=row[2],reply_markup=reply_markup)
    else:
        bot.send_message(chat_id=chat_id,text='Тест завершен! Спасибо!')
        used_skills(bot,chat_id,user_id)

def wizard_keyb(bot, update):
    keyboard =[['✅ Начать','▶️ Продолжить','❌ Завершить']]
    update.message.reply_text(update.message.text, reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))

def wizard_inline_keyb(answer_id):
    keyboard = []
    rows=dbcon('SELECT id,idp,wizard_name,path FROM v_wizard_tree WHERE idp =%s', (answer_id,)).fetchall()
    if len(rows)>2: c='0'
    else: c='2'
    for row in rows:
        keyboard.append([InlineKeyboardButton('☑️ '+row[2], callback_data='answer_'+c+'_'+row[3] )])
    if len(rows)>2:
        keyboard.append([InlineKeyboardButton('➡️', callback_data='NextQuest')])
    return keyboard

def wizard_answer(bot,update):
    query = update.callback_query
    me_id=query.from_user.id
    chat_id=query.message.chat.id
    bot.sendChatAction(query.message.chat.id,'typing')
    data = {}
    data['user_id']    = me_id
    data['wizard_id']  = query.data.split('_')[len(query.data.split('_'))-1]
    data['wizard_idp'] = query.data.split('_')[len(query.data.split('_'))-2]
    if len(query.data.split('_'))>4:
        data['wizard_pid'] = query.data.split('_')[len(query.data.split('_'))-3]
    else:
        data['wizard_pid'] = '0000'
    data['path'] = query.data.split('_', maxsplit=2)[2]
    dbcon('delete from t_steps where user_id=%(user_id)s and wizard_id=%(wizard_id)s and wizard_idp=%(wizard_idp)s and wizard_pid=%(wizard_pid)s;',data)
    if query.data.split('_', maxsplit=2)[1]=='0' or query.data.split('_', maxsplit=2)[1]=='2':
        dbcon('INSERT INTO t_steps (user_id,wizard_id,wizard_idp,wizard_pid,path) VALUES (%(user_id)s,%(wizard_id)s,%(wizard_idp)s,%(wizard_pid)s,%(path)s);',data)
        c='1'
    else:
        c='0'
    keyboard = []
    rows=dbcon('SELECT id,idp,wizard_name,path FROM v_wizard_tree WHERE idp =%s', (data['wizard_idp'],)).fetchall()
    if len(rows)<=2: c='2'
    for row in rows:
        data = {}
        data['user_id']    = me_id
        data['wizard_id']  = row[0]
        check = '☑️ '
        ch = dbcon('SELECT 1 FROM t_steps WHERE user_id=%(user_id)s and wizard_id=%(wizard_id)s',data).fetchall()
        if len(ch)>0: check = '✅ '
        keyboard.append([InlineKeyboardButton(check+row[2], callback_data='answer_'+c+'_'+row[3])])
    if len(rows)>2:
        keyboard.append([InlineKeyboardButton('➡️', callback_data='NextQuest')])
    reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
    bot.edit_message_text(chat_id=chat_id,message_id=query.message.message_id,text=query.message.text,reply_markup=reply_markup)
    if query.data.split('_', maxsplit=2)[1]=='2': run_wizard(bot,chat_id,me_id)
    bot.answer_callback_query(query.id)

def show_photo(bot,update):
    query  =update.callback_query
    me_id=query.from_user.id
    chat_id=query.message.chat.id
    msg_id =query.message.message_id
    user_id=int(query.data.split('_')[2])
    bot.edit_message_text(chat_id=chat_id,message_id=query.message.message_id,text=user_detail(user_id),reply_markup=show_photo_keyb(user_id),parse_mode='Markdown')
    bot.answer_callback_query(query.id, show_alert=False, text="Портфолио!")

def next_photo(bot,update):
    query  =update.callback_query
    me_id  =query.from_user.id
    chat_id=query.message.chat.id
    msg_id =query.message.message_id
    #offset =int(query.data.split('_')[1])
    user_id=int(query.data.split('_')[2])
    skill_id=int(query.data.split('_')[3])
    
    cnt=dbcon('SELECT count(*) FROM t_photos WHERE worker_id=%s and skill_id=%s',(user_id,skill_id,)).fetchone()[0]
    if cnt<0:
        if offset<0: offset=cnt-1
        elif offset>=cnt: offset=0
        row=dbcon('SELECT photo_id FROM t_photos WHERE worker_id=%s LIMIT %s,1',(user_id,offset,)).fetchone()
        if row is not None:
            keyboard=[[InlineKeyboardButton('◀️',callback_data='photo_'+str(offset-1)+'_'+str(user_id)),InlineKeyboardButton('▶️',callback_data='photo_'+str(offset+1)+'_'+str(user_id))]]
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
            #bot.send_photo(chat_id=chat_id,photo=row[0],reply_markup=reply_markup)
            bot.send_photo(chat_id=chat_id, photo=open('photos/'+row[0]+'.png', 'rb'),reply_markup=reply_markup,disable_notification=True)
            if len(query.message.photo)>0: bot.delete_message(chat_id=chat_id,message_id=msg_id)
    
    cnt=dbcon('SELECT count(*) FROM t_photos WHERE worker_id=%s and skill_id=%s',(user_id,skill_id,)).fetchone()[0]
    if cnt>0:
        bot.sendChatAction(chat_id,'upload_photo')
        media=[]
        rows=dbcon('SELECT photo_id,worker_name_full,user_name_full,skill_name FROM v_photos WHERE worker_id=%s and skill_id=%s',(user_id,skill_id,)).fetchall()
        for row in rows: #os.listdir('photos'):
            #if re.match(r'\d{9}_.+', files):
                #if user_id==int(files.split('_')[0]):
                    #bot.send_photo(chat_id=chat_id, photo=open('photos/'+files, 'rb'))
            media.append(InputMediaPhoto(media=row[0],caption='Фото пользователя "'+row[2]+'" для навыка "'+row[3]+'"'))
        bot.send_media_group(chat_id=chat_id, media=media)
        bot.answer_callback_query(query.id)
    else: 
        bot.answer_callback_query(query.id, show_alert=False, text="Нет фотографий!")

def button(bot,update):
    query = update.callback_query
    me_id=query.from_user.id
    chat_id=query.message.chat.id
    msg_id=query.message.message_id
    if   query.data=='Done':
        bot.answer_callback_query(query.id, show_alert=False, text="Нет действия")
    elif query.data=='NextQuest':
        run_wizard(bot,chat_id,me_id)
        bot.answer_callback_query(query.id)
    elif re.match(r'skill_.+', query.data):
        bot.sendChatAction(chat_id,'typing')
        skill_id=query.data.split('_')[1]
        dbcon('INSERT IGNORE INTO t_used_skills (user_id,skill_id,used) VALUES (%s,%s,1);',(me_id,skill_id,))
        dbcon('UPDATE t_used_skills SET used=case used when 1 then 0 else 1 end WHERE user_id=%s and skill_id=%s', (me_id,skill_id,))
        rows=dbcon('SELECT id,skill_name,used FROM v_users_skills WHERE user_id =%s', (me_id,)).fetchall()
        if len(rows)==0:
            update.message.reply_text('К сожалению, по результатам теста у вас не выявлено ни одного навыка!')
        else:
            keyboard=[]
            for row in rows:
                if row[2]==0: emoji='☑️ '
                else:         emoji='✅ '
                keyboard.append([InlineKeyboardButton(emoji+row[1], callback_data='skill_'+str(row[0]) )])
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
            txt='Вот ваши навыки:\r\n_(нажмите на навык чтобы включить ✅ или исключить ☑️ его)_'
            bot.edit_message_text(chat_id=chat_id,message_id=query.message.message_id,text=txt,parse_mode='Markdown',reply_markup=reply_markup)
        bot.answer_callback_query(query.id)
    elif re.match(r'detail_.+', query.data):
        user_id=int(query.data.split('_')[1])
        bot.answer_callback_query(query.id)
        bot.edit_message_text(chat_id=chat_id,message_id=query.message.message_id,text=user_detail(user_id),parse_mode='Markdown',reply_markup=user_detail_keyb(user_id))
    elif re.match(r'show_contact_.+', query.data):
        user_id=int(query.data.split('_')[2])
        row=dbcon('SELECT user_name,user_name_full,phone_number,status_id,latitude,longitude FROM v_users WHERE /*status_id<>2 AND skill_cnt>0 AND*/ user_id =%s', (user_id,)).fetchone()
        bot.sendContact(chat_id,row[2],str(row[1]).title())
        bot.answer_callback_query(query.id, show_alert=False, text="Готово!")
    elif re.match(r'show_feedback_.+', query.data):
        user_id=int(query.data.split('_')[2])
        reply_markup=InlineKeyboardMarkup(inline_keyboard=feedback_inline_keyb(user_id))
        bot.edit_message_text(chat_id=chat_id,message_id=query.message.message_id,text=feedback_list(user_id),reply_markup=reply_markup,parse_mode='Markdown')
        bot.answer_callback_query(query.id, show_alert=False, text="Готово!")
    elif re.match(r'feedback_refresh_.+', query.data):
        user_id=int(query.data.split('_')[2])
        reply_markup=InlineKeyboardMarkup(inline_keyboard=feedback_inline_keyb(user_id))
        bot.edit_message_text(chat_id=chat_id,message_id=query.message.message_id,text=feedback_list(user_id),reply_markup=reply_markup,parse_mode='Markdown')
    elif re.match(r'feedback_new_.+', query.data):
        user_id=int(query.data.split('_')[2])
        reply_markup=InlineKeyboardMarkup(inline_keyboard=feedback_stars_keyb(user_id))
        bot.edit_message_text(chat_id=chat_id,message_id=query.message.message_id,text=feedback_list(user_id),reply_markup=reply_markup,parse_mode='Markdown')
    elif re.match(r'Star_.+', query.data):
        rank=int(query.data.split('_')[1])
        data = {}
        data['user_id'] =int(query.data.split('_')[2])
        data['skill_id'] =int(query.data.split('_')[3])
        data['voter_id']=me_id
        data['rank']    =rank
        dbcon('INSERT IGNORE INTO t_workers_feedback (user_id,voter_id,rank) VALUES (%(user_id)s,%(voter_id)s,%(rank)s)',data)
        dbcon('UPDATE t_workers_feedback SET rank=%(rank)s WHERE user_id=%(user_id)s and voter_id=%(voter_id)s',data)
        txt='*Вы выбрали оценку* '+'⭐️'*rank+' для пользователя [@'+data['user_id']+'](tg://user?id='+data['user_id']+') по заказу /ZakazNo'+data['skill_id']+' \r\n⬇️ _Напишите подробнее о работнике и прикрепите фото_'
        bot.send_message(chat_id,txt,parse_mode='Markdown',reply_markup=forcereply.ForceReply(selective=True))
        bot.answer_callback_query(query.id, show_alert=False)
    elif re.match(r'show_skills_.+', query.data):
        user_id=int(query.data.split('_')[2])
        bot.edit_message_text(chat_id=chat_id,message_id=query.message.message_id,text=user_detail(user_id),reply_markup=show_skills_keyb(user_id),parse_mode='Markdown')
        bot.answer_callback_query(query.id, show_alert=False, text="Навыки!")
    elif re.match(r'back_user_list_.+', query.data):
        user_id=int(query.data.split('_')[3])
        bot.edit_message_text(chat_id=chat_id,message_id=query.message.message_id,text=workers_list(me_id,0),reply_markup=workers_inline_keyb(me_id,0),parse_mode='Markdown')
        bot.answer_callback_query(query.id, show_alert=False, text="Вернулся!")
    elif re.match(r'back_orders_list_.+', query.data):
        order_sort[me_id]='post_date desc'
        bot.edit_message_text(chat_id=chat_id,message_id=query.message.message_id,text=orders_list(me_id,0),reply_markup=orders_inline_keyb(me_id,0),parse_mode='Markdown')
        bot.answer_callback_query(query.id, show_alert=False, text="Вернулся!")
    elif re.match(r'workers_list_prev_.+', query.data):
        offset=int(query.data.split('_')[3])-1
        if offset<0:
            bot.answer_callback_query(query.id, show_alert=False, text="Вы в начале списка...")
        else:
            bot.edit_message_text(chat_id=chat_id,message_id=query.message.message_id,text=workers_list(me_id,offset),reply_markup=workers_inline_keyb(me_id,offset),parse_mode='Markdown')
            bot.answer_callback_query(query.id, show_alert=False, text="Предыдущий!")
    elif re.match(r'orders_list_prev_.+', query.data):
        offset=int(query.data.split('_')[3])-1
        if offset<0:
            bot.answer_callback_query(query.id, show_alert=False, text="Вы в начале списка...")
        else:
            bot.edit_message_text(chat_id=chat_id,message_id=query.message.message_id,text=orders_list(me_id,offset),reply_markup=orders_inline_keyb(me_id,offset),parse_mode='Markdown')
            bot.answer_callback_query(query.id, show_alert=False, text="Предыдущий!")
    elif re.match(r'workers_list_next_.+', query.data):
        offset=int(query.data.split('_')[3])+1
        if workers_list(me_id,offset)=='':
            bot.answer_callback_query(query.id, show_alert=False, text="Конец списка!")
        else:
            bot.edit_message_text(chat_id=chat_id,message_id=query.message.message_id,text=workers_list(me_id,offset),reply_markup=workers_inline_keyb(me_id,offset),parse_mode='Markdown')
            bot.answer_callback_query(query.id, show_alert=False, text="Следующий!")
    elif re.match(r'orders_list_next_.+', query.data):
        offset=int(query.data.split('_')[3])+1
        if orders_list(me_id,offset)=='': 
            bot.answer_callback_query(query.id, show_alert=False, text="Конец списка!")
        else: 
            bot.edit_message_text(chat_id=chat_id,message_id=query.message.message_id,text=orders_list(me_id,offset),reply_markup=orders_inline_keyb(me_id,offset),parse_mode='Markdown')
            bot.answer_callback_query(query.id, show_alert=False, text="Следующий!")
    elif re.match(r'workers_sort_.+', query.data):
        bot.answer_callback_query(query.id, show_alert=False, text="Сортировка...")
        sort=query.data.split('_',maxsplit=2)[2]
        if sort=='rank desc':   sort='status_id'
        elif sort=='status_id': sort='9'
        elif sort=='9': sort='rank desc'
        bot.edit_message_text(chat_id=chat_id,message_id=query.message.message_id,text=workers_list(me_id,0,sort=sort),reply_markup=workers_inline_keyb(me_id,0,sort=sort),parse_mode='Markdown')
    elif re.match(r'orders_sort_.+', query.data):
        bot.answer_callback_query(query.id, show_alert=False, text="Сортировка...")
        if   order_sort[me_id]=='post_date desc': order_sort[me_id]='10'
        elif order_sort[me_id]=='10':             order_sort[me_id]='fee desc'
        elif order_sort[me_id]=='fee desc':       order_sort[me_id]='post_date desc'
        bot.edit_message_text(chat_id=chat_id,message_id=query.message.message_id,text=orders_list(me_id,0),reply_markup=orders_inline_keyb(me_id,0),parse_mode='Markdown')
    elif re.match(r'back_user_.+', query.data):
        user_id=int(query.data.split('_')[2])
        bot.edit_message_text(chat_id=chat_id,message_id=query.message.message_id,text=user_detail(user_id),reply_markup=user_detail_keyb(user_id),parse_mode='Markdown')
        bot.answer_callback_query(query.id, show_alert=False, text="Вернулся!")
    elif query.data=='order_skill_0':
        order_new(bot,chat_id)
    elif re.match(r'order_skill_.+', query.data):
        order_id=int(query.data.split('_')[2])
        skill_id=int(query.data.split('_')[3])
        dbcon('UPDATE t_orders SET skill_id=%s WHERE id=%s',(skill_id,order_id,))
        txt='Введите стоимость, которую вы готовы заплатить за выполнение Вашего заказа:\n💰 `$fee` руб.'
        txt=txt.replace('$fee','_'*10)
        bot.edit_message_text(chat_id=chat_id,message_id=query.message.message_id,text=txt,parse_mode='Markdown',reply_markup=fee_inline_keyb(order_id))
    elif re.match(r'apply_order_.+', query.data):
        order_id=int(query.data.split('_')[2])
        fee=re.findall(r'(?<=💰 ).+(?= руб)',query.message.text)[0]
        fee=fee.replace(' ','')
        if fee.isnumeric():
            dbcon('UPDATE t_orders SET status_id=1,fee=%s WHERE id=%s',(int(fee),order_id,))
        bot.answer_callback_query(query.id, show_alert=False, text="Заказ размещен!")
        bot.edit_message_text(chat_id=chat_id,message_id=query.message.message_id,text="👍 Отлично, заказ размещен!")
        rows=dbcon('SELECT user_id,skill_name FROM v_order_notify WHERE id=%s', (order_id,)).fetchall()
        for row in rows:
            txt='💡 По Вашему навыку *"'+row[1]+'"* размещен новый заказ!\r\n`---------------------`'+order_detail_txt(order_id)
            bot.send_message(row[0],text=txt,parse_mode='Markdown',reply_markup=order_detail_keyb(order_id))
    elif re.match(r'fee_.+', query.data):
        qd=query.data.split('_')
        order_id=qd[2]
        fee=re.findall(r'(?<=💰 ).+(?= руб)',query.message.text)[0]
        fee=fee.replace(' ','')
        fee=fee.replace('_','')
        txt='Введите стоимость, которую вы готовы заплатить за выполнение Вашего заказа:\n💰 `$fee` руб.'
        if qd[1]=='clr': fee='_'*10
        else: fee='{0:,}'.format(int(fee+qd[1])).replace(',', ' ')
        txt=txt.replace('$fee',fee)
        bot.edit_message_text(chat_id=chat_id,message_id=query.message.message_id,text=txt,parse_mode='Markdown',reply_markup=fee_inline_keyb(order_id))
        bot.answer_callback_query(query.id)
    elif query.data=='contract':
        bot.answer_callback_query(query.id, show_alert=False, text="Генерирую договор...")
        doc = DocxTemplate("tmp.docx")
        context = {'ФИО':'Корзунин Дмитрий'}
        doc.render(context)
        doc.save("Договор.docx")
        bot.sendDocument(chat_id,open('Договор.docx', 'rb'),caption='Договор оказания услуг')
    else: 
        bot.answer_callback_query(query.id, show_alert=False, text="Команда не распознана")

def feedback_list(user_id):
    rows=dbcon('SELECT id,voter_id,user_name_full,rank,txt FROM v_workers_feedback WHERE user_id=%s order by id desc LIMIT 5', (user_id,)).fetchall()
    if len(rows)==0:
        txt = 'Нет отзывов о работнике!'
    else:
        i=0
        un=dbcon('SELECT user_name_full FROM v_users WHERE user_id=%s', (user_id,)).fetchone()
        txt = '`Отзывы о работнике:` *'+un[0]+'*\r\n`---------------------`'
        for row in rows:
            i+=1
            t='''
*Отзыв* /No$num
👤` От:` [$user_name](tg://user?id=$user_id)
🌟` Оценка:` $stars *$rank*
💬` Описание:` $txt
'''
            t=t.replace('$num'       ,str(row[0]))
            t=t.replace('$user_id'   ,str(row[1]))
            t=t.replace('$user_name' ,str(row[2]).title())
            #t=t.replace('$stars'     ,'⭐️'*row[3]+'➖'*(5-row[3]))
            t=t.replace('$stars'     ,'★'*row[3]+'☆'*(5-row[3]))
            t=t.replace('$rank'      ,'%.0f' % row[3])
            t=t.replace('$txt'       ,row[4])
            txt=txt+('`---------------------`' if i>1 else '')+t
    return txt

def feedback_inline_keyb(user_id):
    keyboard=[[InlineKeyboardButton(text='🔙', callback_data='back_user_'+str(user_id))
              ,InlineKeyboardButton(text='◀️', callback_data='feedback_prev_'+str(user_id))
              ,InlineKeyboardButton(text='🔄', callback_data='feedback_refresh_'+str(user_id))
              ,InlineKeyboardButton(text='▶️', callback_data='feedback_next_'+str(user_id))]]
             #,[InlineKeyboardButton(text='🆕 Новый отзыв', callback_data='feedback_new_'+str(user_id))]]
    return keyboard

def feedback_stars_keyb(user_id,skill_id):
    keyboard=[#[InlineKeyboardButton(text='🔙', callback_data='back_user_'+str(user_id))
              #,InlineKeyboardButton(text='◀️', callback_data='feedback_prev_'+str(user_id))
              #,InlineKeyboardButton(text='🔄', callback_data='feedback_refresh_'+str(user_id))
              #,InlineKeyboardButton(text='▶️', callback_data='feedback_next_'+str(user_id))]
             #,
              [InlineKeyboardButton(text='⭐️', callback_data='Star_1_'+str(user_id)+'_'+str(skill_id))
              ,InlineKeyboardButton(text='⭐️', callback_data='Star_2_'+str(user_id)+'_'+str(skill_id))
              ,InlineKeyboardButton(text='⭐️', callback_data='Star_3_'+str(user_id)+'_'+str(skill_id))
              ,InlineKeyboardButton(text='⭐️', callback_data='Star_4_'+str(user_id)+'_'+str(skill_id))
              ,InlineKeyboardButton(text='⭐️', callback_data='Star_5_'+str(user_id)+'_'+str(skill_id))]]
    return keyboard

def user_detail(user_id):
    row=dbcon('SELECT user_name,user_name_first,user_name_last,phone_number,status_caption,latitude,longitude,rank,cnt,cnt_done,cnt_all,city FROM v_users WHERE user_id =%s', (user_id,)).fetchone()
    if row is None: txt='Вы не зарегистрированы!'
    else: txt='''
👤` Имя:` _$first_name_
💼` Опыт:` _$cnddone из $cntall заданий выполнено_
📍` Город:` _$city_
🚥` Статус:` $status
🌟` Рейтинг:` $stars _$rank_
👥` Кол-во отзывов:` _$fbcnt_'''
#📒` Контакт: `[@user_name](tg://user?id=user_id)
#📞` Телефон: `phone
    txt=txt.replace('$user_id'   ,str(user_id))
    txt=txt.replace('$user_name' ,row[0])
    txt=txt.replace('$first_name',row[1].title()+' '+row[2].title())
    txt=txt.replace('$last_name' ,row[2].title())
    txt=txt.replace('$phone'     ,row[3])
    txt=txt.replace('$status'    ,row[4])
    txt=txt.replace('$stars'     ,'⭐️'*int(row[7])+'➖'*(5-int(row[7])) )
    txt=txt.replace('$rank'      ,'%.1f' % row[7])
    txt=txt.replace('$fbcnt'     ,str(row[8]))
    txt=txt.replace('$cnddone'   ,str(row[9]))
    txt=txt.replace('$cntall'    ,str(row[10]))
    txt=txt.replace('$city'      ,row[11])
    return txt

def user_detail_keyb(user_id):
    keyboard=[[InlineKeyboardButton(text='🔙', callback_data='back_user_list_'+str(user_id))
              ,InlineKeyboardButton(text='💪', callback_data='show_skills_'+str(user_id))
              ,InlineKeyboardButton(text='💬', callback_data='show_feedback_'+str(user_id))
              ,InlineKeyboardButton(text='🎆', callback_data='photo_0_'+str(user_id))
              ,InlineKeyboardButton(text='⬇️', callback_data='show_contact_'+str(user_id))]]
    return InlineKeyboardMarkup(keyboard, resize_keyboard=True)

def show_skills_keyb(user_id):
    rows=dbcon('SELECT id,skill_name FROM v_users_skills WHERE used=1 and user_id =%s', (user_id,)).fetchall()    
    keyboard=[[InlineKeyboardButton('⬅️ Навыки:', callback_data='back_user_'+str(user_id) )]]
    for row in rows:
        emoji='🔸 '
        keyboard.append([InlineKeyboardButton(emoji+row[1], callback_data='show_skill_users_'+str(user_id) )])
    keyboard.append([InlineKeyboardButton('⬅️ Назад', callback_data='back_user_'+str(user_id) )])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def show_photo_keyb(user_id):
    rows=dbcon('SELECT id,skill_name FROM v_users_skills WHERE used=1 and user_id =%s', (user_id,)).fetchall()    
    keyboard=[[InlineKeyboardButton(text='🔙', callback_data='back_user_'+str(user_id))
              ,InlineKeyboardButton(text='💪', callback_data='show_skills_'+str(user_id))
              ,InlineKeyboardButton(text='💬', callback_data='show_feedback_'+str(user_id))
              ,InlineKeyboardButton(text='🎆', callback_data='photo_0_'+str(user_id))
              ,InlineKeyboardButton(text='⬇️', callback_data='show_contact_'+str(user_id))]]
    for row in rows:
        emoji='🎆 '
        keyboard.append([InlineKeyboardButton(emoji+row[1], callback_data='photo_skill_'+str(user_id)+'_'+str(row[0]) )])
    keyboard.append([InlineKeyboardButton('⬅️ Назад', callback_data='back_user_'+str(user_id) )])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def used_skills(bot,chat_id,user_id):
    rows=dbcon('SELECT id,skill_name,used FROM v_users_skills WHERE user_id = %s', user_id).fetchall()
    if len(rows)==0:
        bot.send_message(chat_id=chat_id,text='Вы не выбрали ни одного навыка, вы можете только размещать заказы!')
    else:
        keyboard=[]
        for row in rows:
            if row[2]==0: emoji='☑️ '
            else:         emoji='✅ '
            keyboard.append([InlineKeyboardButton(emoji+row[1], callback_data='skill_'+str(row[0]) )])
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
        txt='Вот ваши навыки:\r\n_(нажмите на навык чтобы включить ✅ или исключить ☑️ его)_'
        bot.send_message(chat_id=chat_id,text=txt,parse_mode='Markdown',reply_markup=reply_markup)

def order_menu_keyb(bot,update):
    keyboard=[[KeyboardButton(text='🆕 Новый заказ', request_location=False)]
            ,[KeyboardButton(text='👋 Текущие заказы')]
            ,[KeyboardButton(text='💪 Поиск по навыкам')]
            ,[KeyboardButton(text='⬅️ Вернуться назад')]
            ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True,one_time_keyboard=True)
    message=bot.send_message(update.message.chat.id,'...',reply_markup=reply_markup,disable_notification=True)
    #bot.delete_message(chat_id=update.message.chat_id,message_id=message.message_id)

def take_order(bot,update):
    query   =update.callback_query
    me_id   =query.from_user.id
    chat_id =query.message.chat.id
    qd      =query.data.split('_')
    order_id=int(qd[2])
    row=dbcon('SELECT worker_id,user_id FROM t_orders WHERE status_id=1 AND id=%s', order_id).fetchone()
    if row is not None:
        dbcon('UPDATE t_orders SET status_id=2,worker_id=%s WHERE id=%s',(me_id,order_id,))
        bot.answer_callback_query(query.id, show_alert=False, text="В работе!")
        txt='💡 На Ваш заказ откликнулся работник!\r\n`---------------------`'+user_detail(me_id)
        bot.send_message(row[1],text=txt,parse_mode='Markdown',reply_markup=user_detail_keyb(me_id))
    bot.edit_message_text(chat_id=chat_id,message_id=query.message.message_id,text=order_detail_txt(order_id),parse_mode='Markdown',reply_markup=order_detail_keyb(order_id))

def close_order(bot,update):
    query   =update.callback_query
    me_id   =query.from_user.id
    chat_id =query.message.chat.id
    qd      =query.data.split('_')
    order_id=int(qd[2])    
    dbcon('UPDATE t_orders SET status_id=0 WHERE id=%s',(order_id,))
    bot.answer_callback_query(query.id, show_alert=False, text="Заказ закрыт!")
    txt='''
💡 Ваш заказ завершен!
`---------------------`
&order
`---------------------`
*Ваш работник:*
&worker
`---------------------`
🌟 Оставьте ваш отзыв! Вы так же можете вложить фотографии по заказу с описанием!'''
    txt=txt.replace('&order',order_detail_txt(order_id))
    txt=txt.replace('&worker',user_detail(me_id))
    row=dbcon('SELECT worker_id,user_id,skill_id FROM t_orders WHERE id=%s', order_id).fetchone()
    reply_markup=InlineKeyboardMarkup(inline_keyboard=feedback_stars_keyb(row[0],row[2]))
    bot.send_message(row[1],text=txt,parse_mode='Markdown',reply_markup=reply_markup)
    bot.edit_message_text(chat_id=chat_id,message_id=query.message.message_id,text=order_detail_txt(order_id),parse_mode='Markdown',reply_markup=order_detail_keyb(order_id))

def decline_order(bot,update):
    query   =update.callback_query
    me_id   =query.from_user.id
    chat_id =query.message.chat.id
    qd      =query.data.split('_')
    order_id=int(qd[2])    
    dbcon('UPDATE t_orders SET status_id=1 WHERE id=%s',(order_id,))
    bot.answer_callback_query(query.id, show_alert=False, text="Заказ отклонен!")
    txt='''❌ Ваш заказ отклонен заботником!
`---------------------`&order
`---------------------`*Ваш работник:*&worker'''
    txt=txt.replace('&order',order_detail_txt(order_id))
    txt=txt.replace('&worker',user_detail(me_id))
    row=dbcon('SELECT worker_id,user_id FROM t_orders WHERE id=%s', order_id).fetchone()
    bot.send_message(row[1],text=txt,parse_mode='Markdown',reply_markup=user_detail_keyb(me_id))
    bot.edit_message_text(chat_id=chat_id,message_id=query.message.message_id,text=order_detail_txt(order_id),parse_mode='Markdown',reply_markup=order_detail_keyb(order_id))

def order_new(bot,chat_id):
    txt='''
✏ Кратко изложите суть вашей задачи.

*Например:*_
🔸 Переезд из квартиры
🔸 Подстричься
🔸 Обучение Английскому
🔸 Заменить унитаз_

Или нажмите чтобы вернуться /orders'''
    bot.send_message(chat_id,txt,parse_mode='Markdown',reply_markup=forcereply.ForceReply(selective=True))

def order_detail(bot,update):
    chat_id=update.message.chat.id
    user_id=update.message.from_user.id
    order_id=int(update.message.text[8:])
    row=dbcon('SELECT user_id,worker_id FROM t_orders WHERE id=%s', (order_id,)).fetchone()
    if row[1] is None or row[1]==user_id:
        #bot.send_message(chat_id,'👋 Текущие заказы')
        bot.send_message(chat_id,order_detail_txt(order_id),parse_mode='Markdown',reply_markup=order_detail_keyb(order_id))

def order_detail_txt(order_id):
    row=dbcon('SELECT id,skill_id,skill_name,user_id,user_name_full,txt,post_date,end_date,status_id,latitude,longitude,fee FROM v_orders WHERE id=%s', (order_id,)).fetchone()
    if row is None: txt='Заказ не найден!'
    else: 
        t='''
Заказ: /ZakazNo$num 
от `$post_date`
👤` Заказчик:` *$user_name*
🚩` Удаленность:` $km
💪` Навык:` $skill
💰` Стоимость:` $fee
📝` Описание:` $txt
'''     
        
        if row[11] is None: fee='Не указана'
        else:              fee='{0:,}'.format(row[11]).replace(',', ' ')+' руб.'
        ll=dbcon('SELECT latitude,longitude FROM t_users where user_id=%s',(row[3],)).fetchone()
        if row[10] is None: km='Не известно'
        else:               km='%.1f' % haversine(Decimal(str(row[10])), Decimal(str(row[9])), Decimal(str(ll[1])), Decimal(str(ll[0])) ) +' км'
        t=t.replace('$num'      ,str(row[0]))
        t=t.replace('$post_date',str(row[6]))
        t=t.replace('$user_name',row[4])
        t=t.replace('$skill'    ,row[2])
        t=t.replace('$txt'      ,row[5])
        t=t.replace('$fbcnt'    ,str(row[7]))
        t=t.replace('$km'       ,km)
        t=t.replace('$fee'      ,fee)
        txt = t
    return txt

def order_detail_keyb(order_id):
    row=dbcon('SELECT user_id,worker_id,status_id FROM t_orders WHERE id=%s', (order_id,)).fetchone()
    user_id=row[0]
    keyboard=[[InlineKeyboardButton(text='🔙', callback_data='back_orders_list_'+str(order_id))
              ,InlineKeyboardButton(text='📝', callback_data='contract')
              ,InlineKeyboardButton(text='⬇️',callback_data='show_contact_'+str(user_id))]]
    if row[1] is None and row[2]==1:
        keyboard.append([InlineKeyboardButton(text='✅ Взять в работу', callback_data='take_order_'+str(order_id))])    
    elif row[2]==2:
        keyboard.append([InlineKeyboardButton(text='❎ Завершить задание', callback_data='close_order_'+str(order_id))])
        keyboard.append([InlineKeyboardButton(text='❌ Отклонить задание', callback_data='decline_order_'+str(order_id))])
    elif row[2]==0:
        keyboard.append([InlineKeyboardButton(text='🏁 Заказ завершен', callback_data='Done')])
    return InlineKeyboardMarkup(keyboard, resize_keyboard=True)

def orders_list(user_id,offset):
    sort     =order_sort[user_id]
    status_id=order_status[user_id]
    skill_id =skill_status[user_id]
    txt=''
    i=0
    #rows=dbcon('SELECT id,skill_id,skill_name,user_id,user_name_full,txt,post_date,end_date,status,latitude,longitude FROM v_orders where status>=0 order by '+sort+' LIMIT %s,5',(offset*5,)).fetchall()
    rows=dbcon('CALL p_get_orders_list(%s,%s,%s,%s,%s)',(user_id,sort,offset,status_id,skill_id)).fetchall()
    for row in rows:
        t='''
*➤ Заказ:* /ZakazNo$num
от `$post_date`
🚩` Удаленность:` $km
💪` Навык:` $skill
💰` Стоимость:` $fee
'''#[$first_name $last_name](tg://user?id=user_id)
        if row[6] is None: fee='Не указана'
        else:              fee='{0:,}'.format(row[6]).replace(',', ' ')+' руб.'
        if row[10]==99999999: km='Не известно'
        else:                 km='%.1f' % row[10] +' км'
        t=t.replace('$num'      ,str(row[0]))
        t=t.replace('$post_date',str(row[7]))
        t=t.replace('$user_name',row[4])
        t=t.replace('$skill'    ,row[2])
        t=t.replace('$txt'      ,row[5])
        t=t.replace('$km',km)
        t=t.replace('$fee',fee)
        i+=1
        txt = txt+('`---------------------`' if i>1 else '')+t
    if txt=='' and offset==0: txt='❗️ Заказы в Вашем ареале не найдены!'
    return txt

def orders_inline_keyb(user_id,offset):
    sort=order_sort[user_id]
    if   sort=='post_date desc': txt='🔃 Сортировка по дате 🌟'
    elif sort=='10':             txt='🔃 Сортировка по удаленности 🚩'
    elif sort=='fee desc':       txt='🔃 Сортировка по цене 💰'
    keyboard=[[InlineKeyboardButton(text=txt, callback_data='orders_sort_'+sort)]
             ,[InlineKeyboardButton(text='◀️',callback_data='orders_list_prev_'+str(offset))
              ,InlineKeyboardButton(text='🔄', callback_data='orders_refresh')
              ,InlineKeyboardButton(text='▶️',callback_data='orders_list_next_'+str(offset))]
             ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def autostatus_inline_keyb(user_id,s):
    keyboard=[]
    emoji='🕛🕐🕑🕒🕓🕔🕕🕖🕗🕘🕙🕚🕛🕐🕑🕒🕓🕔🕕🕖🕗🕘🕙🕚'
    for t in range(0,24):
        if t % 3 == 0:
            keyboard.append([InlineKeyboardButton(text=emoji[t+0]+' '+str(t+0).zfill(2)+':00',callback_data=s+str(t+0).zfill(2)+'')
                            ,InlineKeyboardButton(text=emoji[t+1]+' '+str(t+1).zfill(2)+':00',callback_data=s+str(t+1).zfill(2)+'')
                            ,InlineKeyboardButton(text=emoji[t+2]+' '+str(t+2).zfill(2)+':00',callback_data=s+str(t+2).zfill(2)+'')])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def autostatus_inline_keyb2():
    keyboard=[[InlineKeyboardButton(text='1️⃣',callback_data='time_1')
              ,InlineKeyboardButton(text='2️⃣',callback_data='time_2')
              ,InlineKeyboardButton(text='3️⃣',callback_data='time_3')]
             ,[InlineKeyboardButton(text='4️⃣',callback_data='time_4')
              ,InlineKeyboardButton(text='5️⃣',callback_data='time_5')
              ,InlineKeyboardButton(text='6️⃣',callback_data='time_6')]
             ,[InlineKeyboardButton(text='7️⃣',callback_data='time_7')
              ,InlineKeyboardButton(text='8️⃣',callback_data='time_8')
              ,InlineKeyboardButton(text='9️⃣',callback_data='time_9')]
             ,[InlineKeyboardButton(text='⬅️',callback_data='time_del')
              ,InlineKeyboardButton(text='0️⃣',callback_data='time_0')
              ,InlineKeyboardButton(text='🚮',callback_data='time_clr')]]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def fee_inline_keyb(order_id):
    keyboard=[[InlineKeyboardButton(text='1️⃣',callback_data='fee_1_'+str(order_id))
              ,InlineKeyboardButton(text='2️⃣',callback_data='fee_2_'+str(order_id))
              ,InlineKeyboardButton(text='3️⃣',callback_data='fee_3_'+str(order_id))]
             ,[InlineKeyboardButton(text='4️⃣',callback_data='fee_4_'+str(order_id))
              ,InlineKeyboardButton(text='5️⃣',callback_data='fee_5_'+str(order_id))
              ,InlineKeyboardButton(text='6️⃣',callback_data='fee_6_'+str(order_id))]
             ,[InlineKeyboardButton(text='7️⃣',callback_data='fee_7_'+str(order_id))
              ,InlineKeyboardButton(text='8️⃣',callback_data='fee_8_'+str(order_id))
              ,InlineKeyboardButton(text='9️⃣',callback_data='fee_9_'+str(order_id))]
             ,[InlineKeyboardButton(text='0️⃣0️⃣0️⃣',callback_data='fee_000_'+str(order_id))
              ,InlineKeyboardButton(text='0️⃣',callback_data='fee_0_'+str(order_id))
              ,InlineKeyboardButton(text='🚮',callback_data='fee_clr_'+str(order_id))]
             ,[InlineKeyboardButton(text='✅ Разместить заявку',callback_data='apply_order_'+str(order_id))]]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def structure_callback(bot,update):
    query  =update.callback_query
    me_id  =query.from_user.id
    chat_id=query.message.chat.id
    qd     =query.data.split('_')
    idp=int(qd[2])
    if qd[1]=='folder':
        bot.edit_message_text(chat_id=chat_id,message_id=query.message.message_id,text=query.message.text,parse_mode='Markdown',reply_markup=structure_inline_keyb(idp))
    elif qd[1]=='item':
        row=dbcon('SELECT idp,skill_name FROM d_skills WHERE id=%s',(idp,)).fetchone()
        order_sort[me_id]='post_date desc'
        order_status[me_id]=1
        skill_status[me_id]=idp
        bot.edit_message_text(chat_id=chat_id,message_id=query.message.message_id,text=workers_list(me_id,0),reply_markup=workers_inline_keyb(me_id,0),parse_mode='Markdown')
        #bot.edit_message_text(chat_id=chat_id,message_id=query.message.message_id,text=orders_list(me_id,0),reply_markup=orders_inline_keyb(me_id,0),parse_mode='Markdown')
        #bot.edit_message_text(chat_id=chat_id,message_id=query.message.message_id,text='Выбрано: '+row[1],parse_mode='Markdown',reply_markup=structure_inline_keyb(row[0]))

def structure_inline_keyb(idp):
    keyboard=[]
    row=dbcon('SELECT idp,skill_name FROM d_skills WHERE id=%s',(idp,)).fetchone()
    if not row is None:
        keyboard.append([InlineKeyboardButton('🔙 '+row[1], callback_data='structure_folder_'+str(row[0]) )])
    
    #rows=dbcon('SELECT id,skill_name FROM d_skills WHERE idp=%s',(idp,)).fetchall()
    rows=dbcon('CALL p_get_skills_cnt(%s)',(idp,)).fetchall()
    for row in rows:
        cnt=dbcon('SELECT 1 FROM d_skills WHERE idp=%s',(row[0],)).fetchone()
        if cnt is None: 
            keyboard.append([InlineKeyboardButton(text='🔹 '+row[1]+' ('+str(row[2])+')',callback_data='structure_item_'+str(row[0]) )])
        else: 
            keyboard.append([InlineKeyboardButton(text='🗂 '+row[1]+' ('+str(row[2])+')',callback_data='structure_folder_'+str(row[0]) )])
    
    row=dbcon('SELECT idp,skill_name FROM d_skills WHERE id=%s',(idp,)).fetchone()
    if not row is None:
        keyboard.append([InlineKeyboardButton('🔙 '+row[1], callback_data='structure_folder_'+str(row[0]) )])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def autostatus_callback(bot,update):
    query  =update.callback_query
    me_id  =query.from_user.id
    chat_id=query.message.chat.id
    qd     =query.data.split('_')
    if qd[1]=='start':
        bot.send_message(chat_id,'Выбери время *окончания* рабочего дня:',parse_mode='Markdown',reply_markup=autostatus_inline_keyb(me_id,'time_stop_'))
        time_start=qd[2]
        dbcon('UPDATE t_status SET status_time_start=%s WHERE user_id=%s',(time_start+':00:00',me_id,))
        keyboard=[[InlineKeyboardButton(text='✅ '+time_start+':00', callback_data='Done')]]
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
        bot.edit_message_text(chat_id=chat_id,message_id=query.message.message_id,text=query.message.text,parse_mode='Markdown',reply_markup=reply_markup)
        bot.answer_callback_query(query.id, show_alert=False, text="Принято!")
    elif qd[1]=='stop':
        time_stop=qd[2]
        dbcon('UPDATE t_status SET status_time_stop=%s WHERE user_id=%s',(time_stop+':00:00',me_id,))
        keyboard=[[InlineKeyboardButton(text='✅ '+time_stop+':00', callback_data='Done')]]
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
        bot.edit_message_text(chat_id=chat_id,message_id=query.message.message_id,text=query.message.text,parse_mode='Markdown',reply_markup=reply_markup)
        bot.answer_callback_query(query.id, show_alert=False, text="Принято!")
    else:
        if qd[1]=='clr':
            txt='Набери диапазон времени рабочего дня:\nс __:__ по __:__'
            bot.edit_message_text(chat_id=chat_id,message_id=query.message.message_id,text=txt,reply_markup=autostatus_inline_keyb2())
        else:
            txt=query.message.text
            i=txt.find('_')
            if i>0:
                txt=txt[:i]+qd[1]+txt[i+1:]
                bot.edit_message_text(chat_id=chat_id,message_id=query.message.message_id,text=txt,reply_markup=autostatus_inline_keyb2())
        bot.answer_callback_query(query.id)

def settings(bot,update):
    keyboard=[[KeyboardButton(text='📍 Моё местоположение', request_location=True),KeyboardButton('🌀 Мой ареал')]
            ,[KeyboardButton(text='💪 Мои навыки')]
            ,[KeyboardButton(text='⁉️ О сервисе')]
            ,[KeyboardButton(text='📣 Написать вопрос или пожелание')]
            ,[KeyboardButton(text='⬅️ Вернуться назад')]
            ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    bot.send_message(update.message.chat.id,update.message.text,reply_markup=reply_markup)

def dbcon(sql,data):
    #db = pymysql.connect(host="localhost",user="root",passwd="123",db="fwbot",charset='utf8')
    db = mysql.connector.connect(host="localhost", user="root", password="123", database="fwbot", charset='utf8')
    #db = SQLighter.connect(database_name)
    with db:
        cur=db.cursor()
        cur.execute(sql,data)
        return cur

def haversine(lon1, lat1, lon2, lat2):
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1 
    dlat = lat2 - lat1 
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a)) 
    km = 6371* c
    return km

def watermark_with_transparency(input_image_path,output_image_path):
    logo_image_path='photos/logo.png'
    link_image_path='photos/link.png'
    baseheight = 600
    base_image = Image.open(input_image_path)
    hpercent = (baseheight / float(base_image.size[1]))
    wsize = int((float(base_image.size[0]) * float(hpercent)))
    base_image = base_image.resize((wsize, baseheight), Image.ANTIALIAS)
    bw,bh = base_image.size

    logo = Image.open(logo_image_path)
    ww,wh = logo.size
    rw=int(bw*0.25)
    rh=int(wh/ww*rw)
    resized_logo = logo.resize((rw, rh), Image.ANTIALIAS)

    link = Image.open(link_image_path)
    ww,wh = link.size
    tw=int(bw*0.25)
    th=int(wh/ww*rw)
    resized_link = link.resize((tw, th), Image.ANTIALIAS)

    transparent = Image.new('RGBA', (bw, bh), (0,0,0,0))
    transparent.paste(base_image, (0,0))
    transparent.paste(resized_logo, (bw-rw-20,bh-rh-20), mask=resized_logo)
    transparent.paste(resized_link, (20,20), mask=resized_link)
    transparent.show()
    transparent.save(output_image_path)
    return output_image_path

#####################################################################################################################################################
def error(bot, update, error): logger.warn('Update "%s" caused error "%s"' % (update, error))

def main():
    updater = Updater(os.getenv('TOKEN'))
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start"           ,start))
    dp.add_handler(CommandHandler("settings"        ,settings))
    dp.add_handler(CallbackQueryHandler(take_order ,pattern='take_order_.+'))
    dp.add_handler(CallbackQueryHandler(close_order,pattern='close_order_.+'))
    dp.add_handler(CallbackQueryHandler(decline_order,pattern='decline_order_.+'))
    dp.add_handler(CallbackQueryHandler(autostatus_callback,pattern='time_.+'))
    dp.add_handler(CallbackQueryHandler(wizard_answer,pattern='answer_.+'))
    dp.add_handler(CallbackQueryHandler(show_photo,pattern='photo_0_.+'))
    dp.add_handler(CallbackQueryHandler(next_photo,pattern='photo_.+'))
    dp.add_handler(CallbackQueryHandler(structure_callback,pattern='structure_.+'))
    dp.add_handler(CallbackQueryHandler(button))
    dp.add_handler(RegexHandler('.*(М|м)ой статус.*',status_keyb))
    dp.add_handler(CommandHandler("status"          ,status_keyb))
    dp.add_handler(CommandHandler("imfree"          ,imfree))
    dp.add_handler(CommandHandler("busy"            ,busy))
    dp.add_handler(CommandHandler("holyday"         ,holyday))
    dp.add_handler(CommandHandler("help"            ,help))
    dp.add_handler(CommandHandler("workers"         ,workers_keyb))
    dp.add_handler(CommandHandler("orders"          ,order_menu_keyb))
    dp.add_handler(CommandHandler("area"            ,my_area))
    dp.add_handler(RegexHandler('\/ZakazNo\d+', order_detail))
    dp.add_handler(RegexHandler('\/uid\d+', No))
    dp.add_handler(MessageHandler(Filters.text & (~ Filters.reply)       , echo))
    dp.add_handler(MessageHandler(Filters.text  & Filters.reply          , echo_reply))
    dp.add_handler(MessageHandler(Filters.photo & Filters.reply          , get_photo)) 
    dp.add_handler(MessageHandler(Filters.contact & (~ Filters.forwarded), get_contact))
    dp.add_handler(MessageHandler(Filters.location                       , get_location))
    dp.add_error_handler(error)
    updater.start_polling()
    updater.idle()


if __name__ == '__main__': main()