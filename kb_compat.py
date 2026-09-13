# kb_compat.py — обход ошибки "Inline keyboard expected"
# Telegram разрешает reply-клавиатуру только у НОВЫХ сообщений,
# поэтому при редактировании медиа с reply-клавиатурой: удаляем и шлём заново.
from telegram import ReplyKeyboardMarkup
import telegram

_orig_media = telegram.Bot.edit_message_media
_orig_caption = telegram.Bot.edit_message_caption

async def safe_edit_message_media(self, media, *args, **kwargs):
    reply_markup = kwargs.get("reply_markup")
    chat_id = kwargs.get("chat_id")
    message_id = kwargs.get("message_id")
    if isinstance(reply_markup, ReplyKeyboardMarkup) and chat_id and message_id:
        try:
            await self.delete_message(chat_id=chat_id, message_id=message_id)
        except Exception:
            pass
        return await self.send_photo(
            chat_id=chat_id,
            photo=media.media,
            caption=media.caption,
            parse_mode=media.parse_mode,
            reply_markup=reply_markup,
        )
    return await _orig_media(self, media, *args, **kwargs)

async def safe_edit_message_caption(self, *args, **kwargs):
    reply_markup = kwargs.get("reply_markup")
    chat_id = kwargs.get("chat_id")
    message_id = kwargs.get("message_id")
    if isinstance(reply_markup, ReplyKeyboardMarkup) and chat_id and message_id:
        caption = kwargs.get("caption") or ""
        try:
            await self.delete_message(chat_id=chat_id, message_id=message_id)
        except Exception:
            pass
        return await self.send_message(
            chat_id=chat_id, text=caption,
            parse_mode=kwargs.get("parse_mode"),
            reply_markup=reply_markup,
        )
    return await _orig_caption(self, *args, **kwargs)

def install():
    telegram.Bot.edit_message_media = safe_edit_message_media
    telegram.Bot.edit_message_caption = safe_edit_message_caption
