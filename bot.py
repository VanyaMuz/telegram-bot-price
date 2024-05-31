import asyncio
from sys import exit
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters.command import Command
from config_reader import config
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import pandas as pd
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder


bot = Bot(token=config.bot_token.get_secret_value())
storage = MemoryStorage()
dp = Dispatcher(bot=bot, storage=storage)


class FSMInputName(StatesGroup):
    name = State()
class FSMInputName2(StatesGroup):
    name = State()

df = pd.read_csv('Price_list_Iveco_2024.csv', sep =';', encoding = "ISO-8859-1", index_col="Part Number")
dt = pd.read_csv('Price TR 2023.csv', sep =';', encoding = "ISO-8859-1", index_col="Part")
dm = pd.read_csv('Остатки.csv', sep =';', encoding = "1251", index_col="Код")
do = pd.read_csv('Заказы.csv', sep =';', encoding = "1251", index_col="Артикул")
do_nan = do[do['Осталось отгрузить'].notnull()]

# def make_window():
#     messagebox.showinfo("Information-bot","The bot is running!")
    
#t1 = threading.Thread(target=make_window)

async def on_startup(bot: Bot):
    await bot.send_message( config.admin_id.get_secret_value(), text = "▶️Bot is running")
dp.startup.register(on_startup)


async def on_shutdown(bot: Bot):
    await bot.send_message( config.admin_id.get_secret_value(), text = "🛑Bot is OFF")
dp.shutdown.register(on_shutdown)

   
#######################   HELP   ################################################################


@dp.message(Command("help"))

async def refresh_handler(message: types.Message):
    
    await message.answer(f"🆘 В этом боте используются следующие команды:" 
                         "\n /start - запуск/перезапуск бота"
                         "\n /find - начать поиск по артикулу"
                        "\n /cancel - отменить поиск "
                         "\n /refresh - после загрузки свежего прайса выполнив эту команду прайс будет обновлен"
                         "\n /shutup - остановка бота(сначала /start потом /shutup)"
                         "\nPS Названия прайсов должны быть точно такие же в формате .csv, а дробная часть цены отделена точкой")

################################  START HANDLER ###################################################
@dp.message(Command("start"))

async def start_handler(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    user_name = message.from_user
    user_full_name = message.from_user.full_name
    logging.info(f'{user_id} {user_full_name}')
    
    builder = ReplyKeyboardBuilder()
    builder.add(types.KeyboardButton(text=str("/start")))
    builder.add(types.KeyboardButton(text=str("/find")))
    builder.add(types.KeyboardButton(text=str("/help")))
    builder.adjust(3)
    do = pd.read_csv('Заказы.csv', sep =';', encoding = "1251", index_col="Артикул")
    do_nan = do[do['Осталось отгрузить'].notnull()]
    await message.answer(f"✅ Привет, { user_full_name } я бот, я помогу тебе найти цену! \nДля поиска воспользуйся кнопками ниже или введи команду:\n /find - начать поиск", reply_markup=builder.as_markup(resize_keyboard=True))
    await state.clear()

######################  REFRESH Handler   ###############################################
@dp.message(Command("refresh"))

async def refresh_handler(message: types.Message):
    global df
    global dt
    global dm
    global do
    df=df[0:0]
    dt=dt[0:0]
    dm=dm[0:0]
    do=do[0:0]
    df = pd.read_csv('Price_list_Iveco_2024.csv', sep =';', encoding = "ISO-8859-1", index_col="Part Number")
    dt = pd.read_csv('Price TR 2023.csv', sep =';', encoding = "ISO-8859-1", index_col="Part")
    dm = pd.read_csv('Остатки.csv', sep =';', encoding = "1251", index_col="Код")
    do = pd.read_csv('Заказы.csv', sep =';', encoding = "1251", index_col="Артикул")

    await message.answer(f"Refreshed!")


################################  BOOM MODE ###################################################
@dp.message(Command("boom"))

async def start_handler_boom(message: types.Message, state: FSMContext):
    user_full_name = message.from_user.full_name
    await message.answer(f"💣 Wow, wow, wow! \n{ user_full_name } you are in the BOOM mode! \nIf you're here, you know what's up, man. Let's get started! 😎")    
    await state.set_state(FSMInputName2.name)
    global part_gl
    global qty_do_gl
    global flag_good_do  
    global mode_flag
    mode_flag = 0 
@dp.message(FSMInputName2.name)
async def state1(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    do_nan = do[do['Осталось отгрузить'].notnull()]
    
    part = message.text
    global stop_flag
    stop_flag = 1
    
################# CHECKING PART IN THE MARI LIST #######################  
    try:
        if part in dm['Производитель']:
            price_m = dm.at[part, 'Стоимость со скидкой ']
            ost_m = dm.at[part, 'Остаток']
            flag_good=1 # flag that part in the list
        else:
            flag_good=0
    except KeyError:     
            await message.answer('❌ Ошибка загрузки прайса')

################# CHECKING PART IN THE ORDER LIST #######################  
    try:
        if part in do_nan['Осталось отгрузить']:
            global part_gl
            global qty_do_gl
            global flag_good_do
            qty_do_gl = do_nan.loc[part]
            flag_good_do=1 # flag that part in the list
        else:
            flag_good_do=0
    except KeyError:     
            await message.answer('❌ Ошибка загрузки файла заказов')


################# CANCEL COMMAND HANDLER ####################### 
    if part == "/cancel":
        await state.clear()
        await message.answer(f"Canceled")

################# CHECKING PART IN THE LISTS #######################
    else:
        try:
          
            if part in df['INDEX']:
                price = df.at[part, 'Price']
                if part in dt['Discr']:
                    Description = dt.at[part, 'Discr']
                else:
                    Description = 'No Description'
                    
                sebest = round(float(price)*1.2*1.38, 2)
                roznica = round(sebest*1.9,2)
                country = "🇫🇷"
                country_name = "FR"
            else:
                price = dt.at[part, 'Price']
                Description = dt.at[part, 'Discr']
                sebest = round(float(price)*1.2*1.1, 2)
                roznica = round(sebest*1.9,2)
                country = "🇹🇷"
                country_name = "TR"
        
##############  ERROR VALUE HANDLER   ############################
        except ValueError:
            await message.answer('❌ Ошибка! {} - нет такого артикула в прайсе либо неправильно введен артикул'.format(part))
            part_gl = 0
            
            
##############  ERROR NOT IN LIST HANDLER   ############################
        except KeyError:     
            await message.answer('❌ Ошибка! {} - нет такого артикула в прайсе либо неправильно введен артикул'.format(part))
            part_gl = 0
            
            
        else:
            if flag_good:
                global part_gl
                
                builder = InlineKeyboardBuilder()
                builder.add(types.InlineKeyboardButton(
                    text="Сколько в заказах?",
                    callback_data="qty_in_orders"))
                                                
                await message.answer(f"💣 {part} - {Description}\nЦена по прайсу  - {price} EUR \
                                     \nСебест - {sebest} EUR с НДС \
                                     \nРозница - {roznica} EUR c НДС \
                                     \nПрайс: {country_name}{country} \
                                     \nОстаток на Мари {ost_m}шт Цена: {price_m} BYN", reply_markup=builder.as_markup())
                part_gl = part
                
            else:
                builder = InlineKeyboardBuilder()
                builder.add(types.InlineKeyboardButton(
                    text="Сколько в заказах?",
                    callback_data="qty_in_orders"))
                await message.answer(f"💣 {part} - {Description}\nЦена по прайсу  - {price} EUR \
                                     \nСебест - {sebest} EUR с НДС \
                                     \nРозница - {roznica} EUR c НДС\
                                     \nПрайс: {country_name}{country} \
                                     \n🚫Нет в наличии на МАРИ", reply_markup=builder.as_markup())
                part_gl = part
                
                
@dp.callback_query(F.data == "qty_in_orders")
async def qty_in_orders(callback: types.CallbackQuery):
    global part_gl
    global qty_do_gl
    global flag_good_do
    global mode_flag
    
    if part_gl!=0 and flag_good_do==1:
        if mode_flag == 1:
            await callback.message.answer(str(qty_do_gl[['Осталось отгрузить', 'Дата']]))
            part_gl=0
        else:
            await callback.message.answer(str(qty_do_gl[['Осталось отгрузить', 'Дата', 'Поставщик']]))
            part_gl=0
    elif flag_good_do==0:
        await callback.message.answer("❌ Ошибка! - такого артикула нет в заказах")
        flag_good_do=2
    else: 
        return

################################  REGULAR MODE ###################################################
@dp.message(Command("find"))

async def start_handler(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    user_name = message.from_user
    user_full_name = message.from_user.full_name
    logging.info(f'{user_id} {user_full_name}')
    global mode_flag
    mode_flag = 1
    
    await message.answer(f"🧐 Введите артикул:") 
    await state.set_state(FSMInputName.name)
 
@dp.message(FSMInputName.name)
async def state1(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    do_nan = do[do['Осталось отгрузить'].notnull()]
    part = message.text
    global stop_flag
    stop_flag = 1
################# CHECKING PART IN THE ORDER LIST #######################  
    try:
        if part in do_nan['Осталось отгрузить']:
            global part_gl
            global qty_do_gl
            global flag_good_do
            qty_do_gl = do_nan.loc[part]
            flag_good_do=1 # flag that part in the list
        else:
            flag_good_do=0
    except KeyError:     
            await message.answer('❌ Ошибка загрузки файла заказов')

################# CANCEL COMMAND HANDLER #######################     
    if part == "/cancel":
        await state.clear()
        await message.answer(f"Canceled")

################# CHECKING PART IN THE LISTS ###################
    else:
        try:
            
            if part in df['INDEX']:
                price = df.at[part, 'Price']
                price_client = round(float(price)*1.2*1.38*1.9, 2)
                if part in dt['Discr']:
                    Description = dt.at[part, 'Discr']
                else:
                    Description = 'No Description'
                
            else:
                price = dt.at[part, 'Price']
                price_client = round(float(price)*1.2*1.1*1.9, 2)
                Description = dt.at[part, 'Discr']
                

##############  ERROR VALUE HANDLER   ############################
        except ValueError:
            await message.answer('❌ Ошибка! {} - нет такого артикула в прайсе либо неправильно введен артикул'.format(part))
            part_gl = 0
            
            
##############  ERROR NOT IN LIST HANDLER   ######################      
        except KeyError:     
            await message.answer('❌ Ошибка! {} - нет такого артикула в прайсе либо неправильно введен артикул'.format(part))
            part_gl = 0
            
           
        else:
            global part_gl
            builder = InlineKeyboardBuilder()
            builder.add(types.InlineKeyboardButton(
                    text="Сколько в заказах?",
                    callback_data="qty_in_orders"))
            await message.answer(f"✅ {part} - {Description} \nРозничная цена: {price_client} EUR c ндс.", reply_markup=builder.as_markup())
            part_gl = part

@dp.message(Command("shutup"))
async def shutup(message: types.Message):
        
    if stop_flag:
        await exit(0)
    else:
        return  

async def main():
    global stop_flag
    stop_flag = 0
    #t1.start()
    
    await dp.start_polling(bot)
  
if __name__ == '__main__':
    # Логгирование в файл
    #logging.basicConfig(level=logging.INFO)
    logging.basicConfig(level=logging.INFO, filename="bot_log.log", filemode='w',
                        format="%(asctime)s %(levelname)s %(message)s")
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('Exit')
    
