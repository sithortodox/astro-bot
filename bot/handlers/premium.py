from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from datetime import datetime

from bot.handlers.start import get_user
from bot.services.payment_service import (
    PRODUCTS,
    is_premium,
    activate_premium,
    get_user_payments,
    get_all_products,
)

router = Router()


@router.message(Command("premium"))
async def cmd_premium(message: Message):
    user = await get_user(message.from_user.id)
    if not user:
        await message.answer("Please /start the bot first.")
        return

    premium_status = await is_premium(message.from_user.id)

    if premium_status and user.premium_until:
        try:
            until = datetime.fromisoformat(user.premium_until)
            days_left = (until - datetime.now()).days
            status_text = f" Premium Active\nExpires: {until.strftime('%d.%m.%Y')}\nDays left: {days_left}"
        except ValueError:
            status_text = " Premium Active"
    elif premium_status:
        status_text = " Premium Active (Lifetime)"
    else:
        status_text = " Free Plan\nUpgrade to Premium for unlimited access!"

    products = get_all_products()

    keyboard = []
    for key, product in products.items():
        if product.get("duration_days", 0) > 0:
            keyboard.append([
                InlineKeyboardButton(
                    text=f"{product['name']} - {product['price_stars']} Stars",
                    callback_data=f"buy:{key}"
                )
            ])

    keyboard.append([
        InlineKeyboardButton(text="\U0001f4b3 My Payments", callback_data="my_payments")
    ])

    markup = InlineKeyboardMarkup(inline_keyboard=keyboard)

    text = (
        f"Premium Subscription\n\n"
        f"{status_text}\n\n"
        f"Premium Benefits:\n"
        f"  Unlimited tarot readings\n"
        f"  Detailed interpretations\n"
        f"  Monthly forecasts\n"
        f"  Priority AI adaptation\n"
        f"  No daily limits\n\n"
        f"Choose a plan:"
    )

    await message.answer(text, reply_markup=markup)


@router.callback_query(lambda c: c.data and c.data.startswith("buy:"))
async def callback_buy(callback_query: CallbackQuery):
    product_key = callback_query.data.split(":", 1)[1]
    product = PRODUCTS.get(product_key)

    if not product:
        await callback_query.answer("Product not found.")
        return

    await callback_query.answer()

    await callback_query.message.answer(
        f" Purchase: {product['name']}\n"
        f"Price: {product['price_stars']} Telegram Stars\n\n"
        f"{product['description']}\n\n"
        f"Click the button below to pay:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text=f"Pay {product['price_stars']} Stars",
                pay=True,
            )]
        ]),
    )


@router.pre_checkout_query()
async def process_pre_checkout(pre_checkout_query):
    await pre_checkout_query.answer(ok=True)


@router.message(F.successful_payment)
async def process_successful_payment(message: Message):
    payment = message.successful_payment
    product_key = None

    for key, product in PRODUCTS.items():
        if product["price_stars"] == payment.total_amount // 100:
            product_key = key
            break

    if not product_key:
        for key, product in PRODUCTS.items():
            if product["price_stars"] == payment.total_amount:
                product_key = key
                break

    if product_key:
        success = await activate_premium(
            message.from_user.id,
            product_key,
            payment.telegram_payment_charge_id,
            "telegram_stars",
        )

        if success:
            await message.answer(
                f" Payment Successful!\n\n"
                f"Product: {PRODUCTS[product_key]['name']}\n"
                f"Amount: {payment.total_amount} Stars\n\n"
                f"Thank you! Your premium has been activated."
            )
        else:
            await message.answer("Payment received but activation failed. Contact support.")
    else:
        await message.answer("Payment received. Thank you!")


@router.callback_query(lambda c: c.data == "my_payments")
async def callback_my_payments(callback_query: CallbackQuery):
    payments = await get_user_payments(callback_query.from_user.id)

    if not payments:
        await callback_query.message.answer("No payment history.")
        await callback_query.answer()
        return

    lines = [" Payment History:\n"]
    for p in payments:
        lines.append(
            f"  {p['date']} - {p['product']} - {p['amount']} {p['currency']} ({p['status']})"
        )

    await callback_query.message.answer("\n".join(lines))
    await callback_query.answer()
