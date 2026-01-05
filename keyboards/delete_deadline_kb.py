from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def delete_deadline_kb(deadline_id: int):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Delete", callback_data=f"delete_deadline_{deadline_id}"
                )
            ]
        ]
    )
