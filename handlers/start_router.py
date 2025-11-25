from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

start_router = Router()


@start_router.message(Command("start"))
async def start(msg: Message):
    await msg.answer("Welcome to the deadline bot!")
