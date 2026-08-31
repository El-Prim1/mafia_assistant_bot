from aiogram import Router

# Импортируем роутеры из всех модулей текущего пакета
from handlers.main_menu import base_router
from handlers.reveal import reveal_router
from handlers.advocate import advocate_router
from handlers.lists import list_builder_router
from handlers.back_btn import back_btn_router

main_router = Router()

# Порядок подключения КРИТИЧЕН:
# 1. Сначала специфичные роутеры (команды, FSM-сценарии, inline-кнопки)
# 2. В самом конце — базовые текстовые хэндлеры (base_router)
main_router.include_routers(
    list_builder_router,
    reveal_router,
    advocate_router,
    back_btn_router,
    base_router
)

__all__ = ["main_router"]