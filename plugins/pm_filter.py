#Kanged From @TroJanZheX
import asyncio
import re
import ast
import random
from pyrogram.errors.exceptions.bad_request_400 import MediaEmpty, PhotoInvalidDimensions, WebpageMediaEmpty
from Script import script
import pyrogram
from database.connections_mdb import active_connection, all_connections, delete_connection, if_active, make_active, make_inactive
from info import ADMINS, AUTH_CHANNEL, AUTH_USERS, CUSTOM_FILE_CAPTION, AUTH_GROUPS, P_TTI_SHOW_OFF, IMDB, SINGLE_BUTTON, SPELL_CHECK_REPLY, DELETE_TIME, IMDB_TEMPLATE, STC
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram import Client, filters
from pyrogram.errors import FloodWait, UserIsBlocked, MessageNotModified, PeerIdInvalid
from utils import get_size, is_subscribed, get_poster, search_gagala, temp
from database.users_chats_db import db
from database.ia_filterdb import Media, get_file_details, get_search_results
from database.filters_mdb import(
   del_all,
   find_filter,
   get_filters,
)
import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)

BUTTONS = {}
SPELL_CHECK = {}

@Client.on_message(filters.group & filters.text & ~filters.edited & filters.incoming)
async def give_filter(client,message):
    group_id = message.chat.id
    name = message.text

    keywords = await get_filters(group_id)
    for keyword in reversed(sorted(keywords, key=len)):
        pattern = r"( |^|[^\w])" + re.escape(keyword) + r"( |$|[^\w])"
        if re.search(pattern, name, flags=re.IGNORECASE):
            reply_text, btn, alert, fileid = await find_filter(group_id, keyword)

            if reply_text:
                reply_text = reply_text.replace("\\n", "\n").replace("\\t", "\t")

            if btn is not None:
                try:
                    if fileid == "None":
                        if btn == "[]":
                            await message.reply_text(reply_text, disable_web_page_preview=True)
                        else:
                            button = eval(btn)
                            await message.reply_text(
                                reply_text,
                                disable_web_page_preview=True,
                                reply_markup=InlineKeyboardMarkup(button)
                            )
                    elif btn == "[]":
                        await message.reply_cached_media(
                            fileid,
                            caption=reply_text or ""
                        )
                    else:
                        button = eval(btn) 
                        await message.reply_cached_media(
                            fileid,
                            caption=reply_text or "",
                            reply_markup=InlineKeyboardMarkup(button)
                        )
                except Exception as e:
                    logger.exception(e)
                break 

    else:
        await auto_filter(client, message)   

@Client.on_callback_query(filters.regex(r"^next"))
async def next_page(bot, query):

    ident, req, key, offset = query.data.split("_")
    if int(req) not in [query.from_user.id, 0]:
        return await query.answer("നിനക്ക് മൂവി വേണമെങ്കിൽ അക്ഷരം തെറ്റാതെ ഇംഗിഷിൽ മൂവിന്റെ പേര് അയക്ക്😁", show_alert=True)
    try:
        offset = int(offset)
    except:
        offset = 0
    search = BUTTONS.get(key)
    if not search:
        await query.answer("ഇത് മുമ്പ് ചോദിച്ച ഫയൽ ആണ്, ദയവ് ചെയ്ത് നിങ്ങൾക്ക് വേണ്ട മൂവി ടൈപ്പ് ചെയ്ത് അയക്കുക .",show_alert=True)
        return

    files, n_offset, total = await get_search_results(search, offset=offset, filter=True)
    try:
        n_offset = int(n_offset)
    except:
        n_offset = 0

    if not files:
        return
    
    if SINGLE_BUTTON:
        btn = [
            [
                InlineKeyboardButton(
                    text=f"🍿[{get_size(file.file_size)}]🍿{file.file_name}", callback_data=f'files#{file.file_id}'
                ),
            ]  
            for file in files
        ]
    else:
    
        btn = [
            [
                InlineKeyboardButton(
                    text=f"🍿{file.file_name}", callback_data=f'files#{file.file_id}'
                ),
                InlineKeyboardButton(
                    text=f"🍿{get_size(file.file_size)}",
                    callback_data=f'files_#{file.file_id}',
                ),
            ]
            for file in files
        ]

    if 0 < offset <= 10:
        off_set = 0
    elif offset == 0:
        off_set = None
    else:
        off_set = offset - 10
    if n_offset == 0:
        btn.append(
            [InlineKeyboardButton("🔻𝐁𝐚𝐜𝐤🔻", callback_data=f"next_{req}_{key}_{off_set}"), InlineKeyboardButton(f"📃 Pages {round(int(offset)/10)+1} / {round(total/10)}", callback_data="pages")]
        )
    elif off_set is None:
        btn.append([InlineKeyboardButton(f"📍 {round(int(offset)/10)+1} / {round(total/10)}📍", callback_data="pages"), InlineKeyboardButton("🔺𝐍𝐞𝐱𝐭🔺", callback_data=f"next_{req}_{key}_{n_offset}")])
    else:
        btn.append(
            [
                InlineKeyboardButton("🔻𝐁𝐚𝐜𝐤🔻", callback_data=f"next_{req}_{key}_{off_set}"),
                InlineKeyboardButton(f"📍 {round(int(offset)/10)+1} / {round(total/10)}📍", callback_data="pages"),
                InlineKeyboardButton("🔺𝐍𝐞𝐱𝐭🔺", callback_data=f"next_{req}_{key}_{n_offset}")
            ],
        )
    btn.insert(0, [
        InlineKeyboardButton("📌 ɴᴇᴡ ᴍᴏᴠɪᴇs 📌", url="https://t.me/bigmoviesworld")
    ])
    try:
        await query.edit_message_reply_markup( 
            reply_markup=InlineKeyboardMarkup(btn)
        )
    except MessageNotModified:
        pass
    await query.answer()

@Client.on_callback_query(filters.regex(r"^spolling"))
async def advantage_spoll_choker(bot, query):
    _, user, movie_ = query.data.split('#')
    if int(user) != 0 and query.from_user.id != int(user):
        return await query.answer("😌തനിക്ക് ഇതിന്റെ ആവിശ്യം ഉണ്ടോന്നു തോന്നുന്നില്ല😌", show_alert=True)
    if movie_  == "close_spellcheck":
        return await query.message.delete()
    movies = SPELL_CHECK.get(query.message.reply_to_message.message_id)
    if not movies:
        return await query.answer("ഈ ബട്ടണിൽ തൊടാതെ നിങ്ങൾ ആദ്യം മുതൽ സിനിമ ചോദിക്കുക.", show_alert=True)
    movie = movies[(int(movie_))]
    await query.answer('😌താങ്കളുടെ സിനിമ ഉണ്ടോന്ന് പരിശോധിക്കുന്നു...')
    files, offset, total_results = await get_search_results(movie, offset=0, filter=True)
    if files:
        k = (movie, files, offset, total_results)
        await auto_filter(bot, query, k)
    else:
        k = await query.message.edit('😄നിങ്ങളുടെ മൂവീസ് ഞങ്ങളുടെ പക്കലില്ലെന്ന് കണ്ടത്തിയിട്ടുണ്ട്. നിങ്ങൾ ചോദിച്ച മൂവീസ് കിട്ടാതിരിക്കാനുള്ള കാരണങ്ങൾ \n DVD ഇറങ്ങിയിട്ടുണ്ടാകില്ല \n നിങ്ങൾ ചോദിച്ച മൂവീസ് തെറ്റായിരിക്കും \n അല്ലെങ്കിൽ ഞങ്ങളുടെ ഡാറ്റാബേസിൽ ഇല്ലായിരിക്കും.. follow admins..')
        await asyncio.sleep(35)
        await k.delete()
        
        

@Client.on_callback_query(filters.regex("alert"))
async def alert(client, query):
    await query.answer("text", show_alert=True)


@Client.on_callback_query()
async def cb_handler(client: Client, query: CallbackQuery):
    if query.data == "close_data":
        await query.message.delete()
    elif query.data == "delallconfirm":
        userid = query.from_user.id
        chat_type = query.message.chat.type

        if chat_type == "private":
            grpid  = await active_connection(str(userid))
            if grpid is not None:
                grp_id = grpid
                try:
                    chat = await client.get_chat(grpid)
                    title = chat.title
                except:
                    await query.message.edit_text("Make sure I'm present in your group!!", quote=True)
                    return
            else:
                await query.message.edit_text(
                    "I'm not connected to any groups!\nCheck /connections or connect to any groups",
                    quote=True
                )
                return

        elif chat_type in ["group", "supergroup"]:
            grp_id = query.message.chat.id
            title = query.message.chat.title

        else:
            return

        st = await client.get_chat_member(grp_id, userid)
        if (st.status == "creator") or (str(userid) in ADMINS):    
            await del_all(query.message, grp_id, title)
        else:
            await query.answer("താൻ എന്തൊരു വെറുപ്പിക്കലാടോ😌!",show_alert=True)

    elif query.data == "delallcancel":
        userid = query.from_user.id
        chat_type = query.message.chat.type

        if chat_type == "private":
            await query.message.reply_to_message.delete()
            await query.message.delete()

        elif chat_type in ["group", "supergroup"]:
            grp_id = query.message.chat.id
            st = await client.get_chat_member(grp_id, userid)
            if (st.status == "creator") or (str(userid) in ADMINS):
                await query.message.delete()
                try:
                    await query.message.reply_to_message.delete()
                except:
                    pass
            else:
                await query.answer("😜ഇത് താങ്കളുടെ അല്ല😜!!",show_alert=True)


    elif "groupcb" in query.data:
        await query.answer()

        group_id = query.data.split(":")[1]
        title = query.data.split(":")[2]
        act = query.data.split(":")[3]
        user_id = query.from_user.id

        if act == "":
            stat = "CONNECT"
            cb = "connectcb"
        else:
            stat = "DISCONNECT"
            cb = "disconnect"

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(f"{stat}", callback_data=f"{cb}:{group_id}:{title}"),
                InlineKeyboardButton("DELETE", callback_data=f"deletecb:{group_id}")],
            [InlineKeyboardButton("BACK", callback_data="backcb")]
        ])

        await query.message.edit_text(
            f"Group Name : **{title}**\nGroup ID : `{group_id}`",
            reply_markup=keyboard,
            parse_mode="md"
        )
        return

    elif "connectcb" in query.data:
        await query.answer()

        group_id = query.data.split(":")[1]
        title = query.data.split(":")[2]
        user_id = query.from_user.id

        mkact = await make_active(str(user_id), str(group_id))

        if mkact:
            await query.message.edit_text(
                f"Connected to **{title}**",
                parse_mode="md"
            )
        else:
            await query.message.edit_text('Some error occured!!', parse_mode="md")
        return
    elif "disconnect" in query.data:
        await query.answer()

        title = query.data.split(":")[2]
        user_id = query.from_user.id

        mkinact = await make_inactive(str(user_id))

        if mkinact:
            await query.message.edit_text(
                f"Disconnected from **{title}**",
                parse_mode="md"
            )
        else:
            await query.message.edit_text('Some error occured!!', parse_mode="md")
        return
    elif "deletecb" in query.data:
        await query.answer()

        user_id = query.from_user.id
        group_id = query.data.split(":")[1]

        delcon = await delete_connection(str(user_id), str(group_id))

        if delcon:
            await query.message.edit_text(
                "Successfully deleted connection"
            )
        else:
            await query.message.edit_text('Some error occured!!', parse_mode="md")
        return
    elif query.data == "backcb":
        await query.answer()

        userid = query.from_user.id

        groupids = await all_connections(str(userid))
        if groupids is None:
            await query.message.edit_text(
                "There are no active connections!! Connect to some groups first.",
            )
            return
        buttons = []
        for groupid in groupids:
            try:
                ttl = await client.get_chat(int(groupid))
                title = ttl.title
                active = await if_active(str(userid), str(groupid))
                act = " - ACTIVE" if active else ""
                buttons.append(
                    [
                        InlineKeyboardButton(
                            text=f"{title}{act}", callback_data=f"groupcb:{groupid}:{title}:{act}"
                        )
                    ]
                )
            except:
                pass
        if buttons:
            await query.message.edit_text(
                "Your connected group details ;\n\n",
                reply_markup=InlineKeyboardMarkup(buttons)
            )

    elif "alertmessage" in query.data:
        grp_id = query.message.chat.id
        i = query.data.split(":")[1]
        keyword = query.data.split(":")[2]
        reply_text, btn, alerts, fileid = await find_filter(grp_id, keyword)
        if alerts is not None:
            alerts = ast.literal_eval(alerts)
            alert = alerts[int(i)]
            alert = alert.replace("\\n", "\n").replace("\\t", "\t")
            await query.answer(alert,show_alert=True)

    if query.data.startswith("file"):
        ident, file_id = query.data.split("#")
        files_ = await get_file_details(file_id)
        if not files_:
            return await query.answer('No such file exist.')
        files = files_[0]
        title = files.file_name
        size=get_size(files.file_size)
        f_caption=files.caption
        if CUSTOM_FILE_CAPTION:
            try:
                f_caption=CUSTOM_FILE_CAPTION.format(file_name=title, file_size=size, file_caption=f_caption)
            except Exception as e:
                logger.exception(e)
            f_caption=f_caption
        if f_caption is None:
            f_caption = f"{files.file_name}"
            
        try:
            if AUTH_CHANNEL and not await is_subscribed(client, query):
                await query.answer(url=f"https://t.me/{temp.U_NAME}?start={file_id}")
                return
            elif P_TTI_SHOW_OFF:
                await query.answer(url=f"https://t.me/{temp.U_NAME}?start={file_id}")
                return
            else:
                await client.send_cached_media(
                    chat_id=query.from_user.id,
                    file_id=file_id,
                    caption=f_caption
                    )
                await query.answer('നിങ്ങളുടെ സിനിമ ഈ ബോട്ടിന്റെ പിഎം അയച്ചിട്ടുണ്ട്. ദയവായി ബോട്ട് ഓപ്പൺ ചെയ്യുക',show_alert = True)
        except UserIsBlocked:
            await query.answer('Unblock the bot mahn !',show_alert = True)
        except PeerIdInvalid:
            await query.answer(url=f"https://t.me/{temp.U_NAME}?start={file_id}")
        except Exception as e:
            await query.answer(url=f"https://t.me/{temp.U_NAME}?start={file_id}")

    elif query.data.startswith("checksub"):
        if AUTH_CHANNEL and not await is_subscribed(client, query):
            await query.answer("ചാനലിൽ ജോയിൻ ചെയ്താൽ മാത്രമേ നിങ്ങൾക്ക് മൂവി കിട്ടുള്ളു😒",show_alert=True)
            return
        ident, file_id = query.data.split("#")
        files_ = await get_file_details(file_id)
        if not files_:
            return await query.answer('No such file exist.')
        files = files_[0]
        title = files.file_name
        size=get_size(files.file_size)
        f_caption=files.caption
        if CUSTOM_FILE_CAPTION:
            try:
                f_caption=CUSTOM_FILE_CAPTION.format(file_name=title, file_size=size, file_caption=f_caption)
            except Exception as e:
                logger.exception(e)
                f_caption=f_caption
        if f_caption is None:
            f_caption = f"{title}"
        await query.answer()
        await client.send_cached_media(
            chat_id=query.from_user.id,
            file_id=file_id,
            caption=f_caption
            )

    elif query.data == "pages":
        await query.answer()
    elif query.data == "start":
        buttons = [[
            InlineKeyboardButton('🎁🔺𝐌𝐄𝐍𝐔🔺🎁', callback_data='help')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.START_TXT.format(query.from_user.mention),
            reply_markup=reply_markup,
            parse_mode='html'
        )
    elif query.data == "help":
        buttons = [[
            InlineKeyboardButton('🗂𝐈𝐧𝐥𝐢𝐧𝐞🗂', callback_data='inline')
            ],[
            InlineKeyboardButton('🗂𝐁𝐚𝐭𝐜𝐡🗂', callback_data='batch'),
            InlineKeyboardButton('🗂𝐅𝐢𝐥𝐭𝐞𝐫🗂', callback_data='filter')            
            ],[
            InlineKeyboardButton('🗂𝐆𝐏𝐥𝐢𝐧𝐤🗂', callback_data='gplink'),
            InlineKeyboardButton('🗂𝐋𝐲𝐫𝐢𝐜𝐬🗂', callback_data='lyrics')
            ],[        
            InlineKeyboardButton('🗂𝐑𝐦𝐁𝐠🗂', callback_data='rmbg'),
            InlineKeyboardButton('🗂𝐒𝐨𝐧𝐠🗂', callback_data='song')
            ],[
            InlineKeyboardButton('🗂𝐒𝐭𝐢𝐜𝐤𝐞𝐫🗂', callback_data='sticker'),            
            InlineKeyboardButton('🗂𝐓𝐞𝐥𝐞𝐠𝐫𝐚𝐩𝐡🗂', callback_data='telegraph')
            ],[
            InlineKeyboardButton('🗂𝐓𝐨𝐫𝐫𝐞𝐧𝐭🗂', callback_data='torrent'),            
            InlineKeyboardButton('🗂𝐓𝐫𝐚𝐧𝐬𝐥𝐚𝐭𝐢𝐨𝐧🗂', callback_data='translation')
            ],[
            InlineKeyboardButton('🗂𝐕𝐢𝐝𝐞𝐨🗂', callback_data='video'),            
            InlineKeyboardButton('🗂𝐎𝐭𝐡𝐞𝐫🗂', callback_data='other')
            ],[
            InlineKeyboardButton('🏠𝐇𝐨𝐦𝐞🏠', callback_data='start'),
            InlineKeyboardButton('🔻𝐁𝐚𝐜𝐤🔻', callback_data='menu')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.HELP_TXT.format(query.from_user.mention),
            reply_markup=reply_markup,
            parse_mode='html'
        )
    elif query.data == "menu":
        buttons = [[
            InlineKeyboardButton('🎁𝐀𝐝𝐝 𝐌𝐞 𝐓𝐨 𝐘𝐨𝐮𝐫 𝐆𝐫𝐨𝐮𝐩𝐬🎁', url=f'http://t.me/{temp.U_NAME}?startgroup=true')
            ],[
            InlineKeyboardButton('🕵️𝐇𝐞𝐥𝐩🕵️', callback_data='help'),
            InlineKeyboardButton('😊𝐀𝐛𝐨𝐮𝐭😊', callback_data='about')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.MENU_TXT.format(query.from_user.mention),
            reply_markup=reply_markup,
            parse_mode='html'
        )
    elif query.data == "telegraph":
        buttons = [[
            InlineKeyboardButton('🔻🔻𝐁𝐚𝐜𝐤🔻🔻', callback_data='help')
            ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.TELEGRAPH_TXT.format(query.from_user.mention),
            reply_markup=reply_markup,
            parse_mode='html'
        )
    elif query.data == "sticker":
        buttons = [[
            InlineKeyboardButton('🔻🔻𝐁𝐚𝐜𝐤🔻🔻', callback_data='help')
            ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.STICKER_TXT.format(query.from_user.mention),
            reply_markup=reply_markup,
            parse_mode='html'
        )
    elif query.data == "inline":
        buttons = [[
            InlineKeyboardButton('🔍𝐈𝐧𝐥𝐢𝐧𝐞 𝐒𝐞𝐚𝐫𝐜𝐡🔎', switch_inline_query_current_chat='')
            ],[
            InlineKeyboardButton('🔻🔻𝐁𝐚𝐜𝐤🔻🔻', callback_data='help')
            ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.INLINE_TXT.format(query.from_user.mention),
            reply_markup=reply_markup,
            parse_mode='html'
        )
    elif query.data == "sticker":
        buttons = [[
            InlineKeyboardButton('🔻🔻𝐁𝐚𝐜𝐤🔻🔻', callback_data='help')
            ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.STICKER_TXT.format(query.from_user.mention),
            reply_markup=reply_markup,
            parse_mode='html'
        )
    elif query.data == "torrent":
        buttons = [[
            InlineKeyboardButton('🔻🔻𝐁𝐚𝐜𝐤🔻🔻', callback_data='help')
            ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.TORRENT_TXT.format(query.from_user.mention),
            reply_markup=reply_markup,
            parse_mode='html'
        )
    elif query.data == "lyrics":
        buttons = [[
            InlineKeyboardButton('🔻🔻𝐁𝐚𝐜𝐤🔻🔻', callback_data='help')
            ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.LYRICS_TXT.format(query.from_user.mention),
            reply_markup=reply_markup,
            parse_mode='html'
        )
    elif query.data == "video":
        buttons = [[
            InlineKeyboardButton('🔻🔻𝐁𝐚𝐜𝐤🔻🔻', callback_data='help')
            ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.VIDEO_TXT.format(query.from_user.mention),
            reply_markup=reply_markup,
            parse_mode='html'
        )
    elif query.data == "rmbg":
        buttons = [[
            InlineKeyboardButton('🔻🔻𝐁𝐚𝐜𝐤🔻🔻', callback_data='help')
            ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.RMBG_TXT.format(query.from_user.mention),
            reply_markup=reply_markup,
            parse_mode='html'
        )
    elif query.data == "batch":
        buttons = [[
            InlineKeyboardButton('🔻🔻𝐁𝐚𝐜𝐤🔻🔻', callback_data='help')
            ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.BATCH_TXT.format(query.from_user.mention),
            reply_markup=reply_markup,
            parse_mode='html'
        )
    elif query.data == "filter":
        buttons = [[
            InlineKeyboardButton('🔻🔻𝐌𝐚𝐧𝐮𝐞𝐥 𝐅𝐢𝐥𝐭𝐞𝐫🔻🔻', callback_data='manuelfilter'),
            InlineKeyboardButton('🔻🔻𝐀𝐮𝐭𝐨 𝐅𝐢𝐥𝐭𝐞𝐫🔻🔻', callback_data='autofilter')
            ],[
            InlineKeyboardButton('🔻🔻𝐁𝐚𝐜𝐤🔻🔻', callback_data='help')
            ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.FILTER_TXT.format(query.from_user.mention),
            reply_markup=reply_markup,
            parse_mode='html'
        )
    elif query.data == "other":
        buttons = [[
            InlineKeyboardButton('🔻🔻𝐀𝐝𝐦𝐢𝐧 𝐂𝐨𝐦𝐦𝐚𝐧𝐝𝐬🔻🔻', callback_data='admin')
            ],[
            InlineKeyboardButton('🔻🔻𝐁𝐚𝐜𝐤🔻🔻', callback_data='help')
            ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.ADMIN_TXT.format(query.from_user.mention),
            reply_markup=reply_markup,
            parse_mode='html'
        )
    elif query.data == "translation":
        buttons = [[
            InlineKeyboardButton('🔻🔻𝐁𝐚𝐜𝐤🔻🔻', callback_data='help')
            ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.GTRNS_TXT.format(query.from_user.mention),
            reply_markup=reply_markup,
            parse_mode='html'
        )
    elif query.data == "games":
        buttons = [[
            InlineKeyboardButton('🔻🔻𝐁𝐚𝐜𝐤🔻🔻', callback_data='help')
            ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.GAMES_TXT.format(query.from_user.mention),
            reply_markup=reply_markup,
            parse_mode='html'
        )
    elif query.data == "json":
        buttons = [[
            InlineKeyboardButton('🔻🔻𝐁𝐚𝐜𝐤🔻🔻', callback_data='help')
            ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.JSON_TXT.format(query.from_user.mention),
            reply_markup=reply_markup,
            parse_mode='html'
        )
    elif query.data == "song":
        buttons = [[
            InlineKeyboardButton('🔻🔻𝐁𝐚𝐜𝐤🔻🔻', callback_data='help')
            ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.SONG_TXT.format(query.from_user.mention),
            reply_markup=reply_markup,
            parse_mode='html'
        )
    elif query.data == "gplink":
        buttons = [[
            InlineKeyboardButton('🔻🔻𝐁𝐚𝐜𝐤🔻🔻', callback_data='help')
            ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.GPLINK_TXT.format(query.from_user.mention),
            reply_markup=reply_markup,
            parse_mode='html'
        )
    elif query.data == "about":
        buttons = [[
            InlineKeyboardButton('🔻🏠𝐇𝐨𝐦𝐞🏠🔻', callback_data='start')
            ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.ABOUT_TXT.format(query.from_user.mention),
            reply_markup=reply_markup,
            parse_mode='html'
        )
    elif query.data == "purge":
        buttons = [[
            InlineKeyboardButton('🔻🔻𝐁𝐚𝐜𝐤🔻🔻', callback_data='help')
            ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.PURGE_TXT.format(query.from_user.mention),
            reply_markup=reply_markup,
            parse_mode='html'
        )
    elif query.data == "telegraph":
        buttons = [[
            InlineKeyboardButton('🔻𝐁𝐚𝐜𝐤🔻', callback_data='help')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.TELEGRAPH_TXT,
            reply_markup=reply_markup,
            parse_mode='html'
        )
    elif query.data == "source":
        buttons = [[
            InlineKeyboardButton('🔻𝐁𝐚𝐜𝐤🔻', callback_data='help'),
            InlineKeyboardButton('🕹𝐁𝐮𝐭𝐭𝐨𝐧𝐬🕹', callback_data='button')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.SOURCE_TXT,
            reply_markup=reply_markup,
            parse_mode='html'
        )
    elif query.data == "manuelfilter":
        buttons = [[
            InlineKeyboardButton('🔻𝐁𝐚𝐜𝐤🔻', callback_data='filter'),
            InlineKeyboardButton('🕹𝐁𝐮𝐭𝐭𝐨𝐧𝐬🕹', callback_data='button')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.MANUELFILTER_TXT,
            reply_markup=reply_markup,
            parse_mode='html'
        )
    elif query.data == "button":
        buttons = [[
            InlineKeyboardButton('🔻𝐁𝐚𝐜𝐤🔻', callback_data='filter')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.BUTTON_TXT,
            reply_markup=reply_markup,
            parse_mode='html'
        )
    elif query.data == "start":
        buttons = [[
            InlineKeyboardButton('🎁🔺𝐌𝐄𝐍𝐔🔺🎁', callback_data='help')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.START_TXT,
            reply_markup=reply_markup,
            parse_mode='html'
        )
    elif query.data == "autofilter":
        buttons = [[
            InlineKeyboardButton('🔻𝐁𝐚𝐜𝐤🔻', callback_data='filter')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.AUTOFILTER_TXT,
            reply_markup=reply_markup,
            parse_mode='html'
        )
    elif query.data == "coct":
        buttons = [[
            InlineKeyboardButton('🔻𝐁𝐚𝐜𝐤🔻', callback_data='help')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.CONNECTION_TXT,
            reply_markup=reply_markup,
            parse_mode='html'
        )
    elif query.data == "extra":
        buttons = [[
            InlineKeyboardButton('🔻𝐁𝐚𝐜𝐤🔻', callback_data='help'),
            InlineKeyboardButton('👺𝐀𝐝𝐦𝐢𝐧👺', callback_data='admin')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.EXTRAMOD_TXT,
            reply_markup=reply_markup,
            parse_mode='html'
        )
    elif query.data == "admin":
        buttons = [[
            InlineKeyboardButton('🔻𝐁𝐚𝐜𝐤🔻', callback_data='other')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.ADMIN_TXT,
            reply_markup=reply_markup,
            parse_mode='html'
        )
    elif query.data == "stats":
        buttons = [[
            InlineKeyboardButton('🔻𝐁𝐚𝐜𝐤🔻', callback_data='help'),
            InlineKeyboardButton('⏳𝐑𝐞𝐟𝐫𝐞𝐬𝐡 𝐃𝐁⏳', callback_data='rfrsh')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        total = await Media.count_documents()
        users = await db.total_users_count()
        chats = await db.total_chat_count()
        monsize = await db.get_db_size()
        free = 536870912 - monsize
        monsize = get_size(monsize)
        free = get_size(free)
        await query.message.edit_text(
            text=script.STATUS_TXT.format(total, users, chats, monsize, free),
            reply_markup=reply_markup,
            parse_mode='html'
        )
    elif query.data == "rfrsh":
        await query.answer("Fetching MongoDb DataBase")
        buttons = [[
            InlineKeyboardButton('🔻𝐁𝐚𝐜𝐤🔻', callback_data='help'),
            InlineKeyboardButton('⏳𝐑𝐞𝐟𝐫𝐞𝐬𝐡 𝐃𝐁⏳', callback_data='rfrsh')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        total = await Media.count_documents()
        users = await db.total_users_count()
        chats = await db.total_chat_count()
        monsize = await db.get_db_size()
        free = 536870912 - monsize
        monsize = get_size(monsize)
        free = get_size(free)
        await query.message.edit_text(
            text=script.STATUS_TXT.format(total, users, chats, monsize, free),
            reply_markup=reply_markup,
            parse_mode='html'
      )
    

async def auto_filter(client, msg, spoll=False):
    if not spoll:
        message = msg
        if re.findall("((^\/|^,|^!|^\.|^[\U0001F600-\U000E007F]).*)", message.text):
            return
        if 2 < len(message.text) < 100:
            search = message.text
            files, offset, total_results = await get_search_results(search.lower(), offset=0, filter=True)
            if not files:
                if SPELL_CHECK_REPLY:
                    k = await advantage_spell_chok(msg)
                    await asyncio.sleep(30)
                    await k.delete()
                    return
                else:
                    return
        else:
            return
    else:
        message = msg.message.reply_to_message # msg will be callback query
        search, files, offset, total_results = spoll
    if SINGLE_BUTTON:
        btn = [
            [
                InlineKeyboardButton(
                    text=f"🌻[{get_size(file.file_size)}]🌻{file.file_name}🌻", callback_data=f'files#{file.file_id}'
                ),
            ]
            for file in files
        ]
    else:
        btn = [
            [
                InlineKeyboardButton(
                    text=f"🎄{file.file_name}",
                    callback_data=f'files#{file.file_id}',
                ),
                InlineKeyboardButton(
                    text=f"🌻{get_size(file.file_size)}",
                    callback_data=f'files_#{file.file_id}',
                ),
            ]
            for file in files
        ]
    await message.reply_chat_action("Typing")
    m=await message.reply_sticker("CAACAgUAAx0CQTCW0gABB5EUYkx6-OZS7qCQC6kNGMagdQOqozoAAgQAA8EkMTGJ5R1uC7PIECME") 
    await asyncio.sleep(2)
    await m.delete()
    

    if offset != "":
        key = f"{message.chat.id}-{message.message_id}"
        BUTTONS[key] = search
        req = message.from_user.id if message.from_user else 0
        btn.append(
            [InlineKeyboardButton(text=f"🏷️𝐂𝐨𝐮𝐧𝐭1/{round(int(total_results)/10)}🏷️",callback_data="pages"), InlineKeyboardButton(text="🔺𝐍𝐞𝐱𝐭🔺",callback_data=f"next_{req}_{key}_{offset}")]
        )
    else:
        btn.append(
            [InlineKeyboardButton(text="🔖1/1🔖",callback_data="pages")]
        )
 
    btn.insert(0, [
        InlineKeyboardButton("📀⚜ɴᴇᴡ ᴍᴏᴠɪᴇs⚜📀", url=f"https://t.me/nasrani_update")
    ])
    btn.insert(11, [
        InlineKeyboardButton("📀⚜ɴᴇᴡ ᴍᴏᴠɪᴇs⚜📀", url=f"https://t.me/nasrani_update")
    ])
    


        
    imdb = await get_poster(search, file=(files[0]).file_name) if IMDB else None
    if imdb:
        cap = IMDB_TEMPLATE.format(
            query = search,
            title = imdb['title'],
            votes = imdb['votes'],
            aka = imdb["aka"],
            seasons = imdb["seasons"],
            box_office = imdb['box_office'],
            localized_title = imdb['localized_title'],
            kind = imdb['kind'],
            imdb_id = imdb["imdb_id"],
            cast = imdb["cast"],
            runtime = imdb["runtime"],
            countries = imdb["countries"],
            certificates = imdb["certificates"],
            languages = imdb["languages"],
            director = imdb["director"],
            writer = imdb["writer"],
            producer = imdb["producer"],
            composer = imdb["composer"],
            cinematographer = imdb["cinematographer"],
            music_team = imdb["music_team"],
            distributors = imdb["distributors"],
            release_date = imdb['release_date'],
            year = imdb['year'],
            genres = imdb['genres'],
            poster = imdb['poster'],
            plot = imdb['plot'],
            rating = imdb['rating'],
            url = imdb['url'],
            **locals()
        )
    else:
        cap = f"👮‍♂ ɴᴏᴛɪᴄᴇ :ɪ𝙵 ʏᴏᴜ ᴅᴏ ɴᴏᴛ sᴇᴇ ᴛʜᴇ 𝙵ɪʟᴇ𝚂 ᴏ𝙵 ᴛʜɪ𝚂 ᴍᴏᴠɪᴇ ʏᴏᴜ ᴀ𝚂ᴋᴇᴅ 𝙵ᴏʀ. ʟᴏᴏᴋ ᴀᴛ ɴᴇ𝚇ᴛ ᴘᴀɢᴇ🔎\n©️քօաɛʀɛɖ ɮʏ :{message.chat.title}"
    if imdb and imdb.get('poster'):
        try:
            fmsg = await message.reply_photo(photo=imdb.get('poster'), caption=cap[:1024],
                                      reply_markup=InlineKeyboardMarkup(btn))
        except (MediaEmpty, PhotoInvalidDimensions, WebpageMediaEmpty):
            pic = imdb.get('poster')
            poster = pic.replace('.jpg', "._V1_UX360.jpg")
            fmsg = await message.reply_photo(photo=poster, caption=cap[:1024], reply_markup=InlineKeyboardMarkup(btn))
        except Exception as e:
            logger.exception(e)
            fmsg = await message.reply_text(cap, reply_markup=InlineKeyboardMarkup(btn))
    else:
        fmsg = await message.reply_text(cap, reply_markup=InlineKeyboardMarkup(btn))
    
    await asyncio.sleep(180)
    await fmsg.delete()
    await message.reply_text(
    text=f"⚙️ {message.from_user.mention} Fɪʟᴛᴇʀ Fᴏʀ {search} Cʟᴏꜱᴇᴅ 🗑️",
    parse_mode="html",
    reply_markup=InlineKeyboardMarkup(
                        [
                            [
                                InlineKeyboardButton('🎁𝐆𝐫𝐨𝐮𝐩🎁', url="http://t.me/nasrani_update")
                            ],
                                                        
                        ]
                    )
                )

    if spoll:
        await msg.message.delete()
    
    
        

async def advantage_spell_chok(msg):
    query = re.sub(r"\b(pl(i|e)*?(s|z+|ease|se|ese|(e+)s(e)?)|((send|snd|giv(e)?|gib)(\sme)?)|movie(s)?|new|latest|br((o|u)h?)*|^h(e)?(l)*(o)*|mal(ayalam)?|tamil|file|that|find|und(o)*|kit(t(i|y)?)?o(w)?|thar(o)*w?|kittum(o)*|aya(k)*(um(o)*)?|full\smovie|any(one)|with\ssubtitle)", "", msg.text, flags=re.IGNORECASE) # plis contribute some common words 
    query = query.strip() + " movie"
    g_s = await search_gagala(query)
    g_s += await search_gagala(msg.text)
    gs_parsed = []
    if not g_s:
        k = await msg.reply("റിലീസ് ആകാത്ത മൂവീ ഇവിടെ കിട്ടില്ല. ചോദിക്കുന്ന മൂവി ഇതിലുണ്ടോന്ന് ഉറപ്പ് വരുത്തുക.")
        await asyncio.sleep(8)
        await k.delete()
        return
    regex = re.compile(r".*(imdb|wikipedia).*", re.IGNORECASE) # look for imdb / wiki results
    gs = list(filter(regex.match, g_s))
    gs_parsed = [re.sub(r'\b(\-([a-zA-Z-\s])\-\simdb|(\-\s)?imdb|(\-\s)?wikipedia|\(|\)|\-|reviews|full|all|episode(s)?|film|movie|series)', '', i, flags=re.IGNORECASE) for i in gs]
    if not gs_parsed:
        reg = re.compile(r"watch(\s[a-zA-Z0-9_\s\-\(\)]*)*\|.*", re.IGNORECASE) # match something like Watch Niram | Amazon Prime 
        for mv in g_s:
            match  = reg.match(mv)
            if match:
                gs_parsed.append(match.group(1))
    user = msg.from_user.id if msg.from_user else 0
    movielist = []
    gs_parsed = list(dict.fromkeys(gs_parsed)) # removing duplicates https://stackoverflow.com/a/7961425
    if len(gs_parsed) > 3:
        gs_parsed = gs_parsed[:3]
    if gs_parsed:
        for mov in gs_parsed:
            imdb_s = await get_poster(mov.strip(), bulk=True) # searching each keyword in imdb
            if imdb_s:
                movielist +=[movie.get('title') for movie in imdb_s]
    movielist += [(re.sub(r'(\-|\(|\)|_)', '', i, flags=re.IGNORECASE)).strip() for i in gs_parsed]
    movielist = list(dict.fromkeys(movielist)) # removing duplicates
    if not movielist:

        
        k = await msg.reply_video(
        video= "https://telegra.ph/file/ec5404d035924f1113d8d.mp4",
        caption=f"<b>📍Hello:-നിങ്ങൾ ചോദിച്ച മൂവി വേണമെങ്കിൽ മുകളിലെ വീഡിയോ കണ്ട് അത് പോലെ സ്പെല്ലിങ് തെറ്റാതെ അയക്കുക.😌</b>",
        parse_mode="html",
        reply_markup=InlineKeyboardMarkup(
                        [
                            [
                                InlineKeyboardButton('🎁𝐀𝐝𝐝 𝐌𝐞 𝐓𝐨 𝐘𝐨𝐮𝐫 𝐆𝐫𝐨𝐮𝐩𝐬🎁', url="http://t.me/nasrani_bot?startgroup=true")
                            ],
                            [
                                InlineKeyboardButton('🧩𝐆𝐨𝐨𝐠𝐥𝐞🧩', url=f"google.com/search?q={query.replace(' ','+')}"),
                                InlineKeyboardButton('☘𝐈𝐦𝐝𝐛☘', url="https://imdb.com")
                            ]                            
                        ]
                    )
                )         
        

                            

        await asyncio.sleep(60)
        await k.delete()
        return
    SPELL_CHECK[msg.message_id] = movielist
    btn = [[
                InlineKeyboardButton(
                    text=movie.strip(),
                    callback_data=f"spolling#{user}#{k}",
                )
            ] for k, movie in enumerate(movielist)]    
    btn.append(
            [
                InlineKeyboardButton("🔐𝐂𝐥𝐨𝐬𝐞🔐", callback_data=f'spolling#{user}#close_spellcheck'),
                InlineKeyboardButton("☘𝐂𝐡𝐚𝐧𝐧𝐞𝐥☘", url='https://t.me/bigmoviesworld')       
            ],
        )
    
    k = await msg.reply_sticker(
        sticker= "CAACAgUAAxkBAAJXA2GiaMWYAAEvGr39FQLCuU_qW4rH1AACHwADhq-BGkoDm80BdFrWIgQ",
        reply_markup=InlineKeyboardMarkup(btn))
    return k

    


