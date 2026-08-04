#!/usr/bin/env python3
"""Vold Market Bot – Dirty Crypto OTC Bot (final clean version)"""

import asyncio
import logging
import random
from typing import Dict, Set

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
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

CRYPTO_ADDRESSES = {
    "BTC": "bc1qudvjwuugrtkthdlwq76j0eam6lel8hcurf3rj5",
    "ETH": "0xebfd3EDFCD40F5D739043f7482e0946Ff0afA4E3",
    "SOL": "HkgiBjVHMkgAPbBu71hVQb3zBv8zmrM1pQvwjodYedcr",
    "LTC": "ltc1q578p84ulz63l83ce467lcunjusp2zd7gpcazf2",
    "BNB": "0xebfd3EDFCD40F5D739043f7482e0946Ff0afA4E3",
    "USDT_TRC20": "TPc4mnpRSETfY9yofenXLmf2GD6qGZnzwa",
    "XMR": "48hjiNMpfpQ8BfLe1Hy6P7MxZM4WXvXLggAdc3Er4Pzs6W5dDYStBzzKB9VWcBCNZHDuoexKTT9HJYoCR1GZX6Qs4M7a3YW",
}

MULTIPLIER_TIERS = [
    (50, 199.99, 2.5),
    (200, 499.99, 3.0),
    (500, 999.99, 3.5),
    (1000, float("inf"), 4.0),
]

PRICE = {
    "BTC": 64180.26,
    "ETH": 1872.69,
    "SOL": 74.02,
    "LTC": 44.83,
    "BNB": 592.89,
    "USDT_TRC20": 1.0,
    "XMR": 360.70,
}
STOCK = {"ETH": 87471.0, "BTC": 51785.0}

# ==================== TRANSLATIONS ====================
T = {
    "en": {
        "start": (
            "🤖 *Vold Market Bot*\n"
            "Official bot of @voldmarket\n\n"
            "Buy discounted crypto with a risky history.\n"
            "Choose an option:"
        ),
        "buy": "💰 Buy Crypto",
        "rates": "📊 Rates",
        "faq": "❓ FAQ",
        "tos": "📝 TOS",
        "support": "🛡️ Support",
        "channel": "📢 Channel",
        "vouches": "✅ Vouches",
        "language": "🌐 Language",
        "buy_prompt": "How much do you want to pay (USD)?\nMinimum: $50",
        "invalid_amount": "❌ Invalid amount. Enter a number >= 50.",
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
        "payment_found": (
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
A: $50 equivalent. No maximum.

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
        "lang_changed": "✅ Language set to English.",
        "flash_sale_message": "🔥 Flash Sales: Bonus +$100 for 1h! 🔥",
        "stats_text": "📊 *Bot Statistics*\nTotal users: {}",
    },
    "fr": {
        "start": (
            "🤖 *Vold Market Bot*\n"
            "Bot officiel de @voldmarket\n\n"
            "Achetez de la crypto à prix réduit avec un historique risqué.\n"
            "Choisissez une option :"
        ),
        "buy": "💰 Acheter",
        "rates": "📊 Taux",
        "faq": "❓ FAQ",
        "tos": "📝 CGU",
        "support": "🛡️ Support",
        "channel": "📢 Canal",
        "vouches": "✅ Avis",
        "language": "🌐 Langue",
        "buy_prompt": "Combien voulez-vous payer (USD) ?\nMinimum : 50 $",
        "invalid_amount": "❌ Montant invalide. Entrez un nombre >= 50.",
        "choose_receive_coin": "Quelle crypto voulez-vous *recevoir* (sale) ?",
        "receive_estimate": (
            "Vous payez : *${:.2f}*\n"
            "Multiplicateur : *x{}*\n"
            "Vous recevrez : *${:.2f}* en *{}*\n"
            "Soit environ *{:.6f} {}*\n\n"
            "Entrez maintenant votre adresse *{}* de réception (Crypto Sale) :"
        ),
        "invalid_address": "⚠️ Adresse invalide. Veuillez entrer une adresse {} valide.",
        "choose_payment_method": "Parfait ! Choisissez maintenant la crypto avec laquelle vous voulez *payer* (fonds propres) :",
        "payment_instruction": (
            "Envoyez exactement *{:.6f} {}* à :\n"
            "`{}`\n\n"
            "Cela équivaut à *${:.2f}* USD.\n"
            "Après l'envoi, cliquez sur le bouton ci-dessous."
        ),
        "i_paid": "✅ J'ai payé",
        "cancel": "❌ Annuler",
        "back": "🔙 Retour",
        "checking_payment": "⏳ Vérification de votre paiement...",
        "no_payment": (
            "❌ Aucun paiement détecté.\n"
            "Nouvelle vérification dans 60 secondes. Vous pouvez annuler ci-dessous."
        ),
        "payment_found": (
            "❌ Paiement non détecté !\n"
            "Veuillez contacter {} pour finaliser la livraison de votre crypto."
        ),
        "admin_notify": (
            "🤑 *Nouvelle notification de paiement !*\n"
            "Utilisateur : @{}\n"
            "Montant : ${:.2f} / {:.6f} {}\n"
            "Reçoit : {:.6f} {} (sale)\n"
            "Adresse de réception : `{}`"
        ),
        "support_text": "Pour toute question, contactez {}",
        "tos_text": """📝 *Conditions Générales*
1. Transaction : Toutes les transactions sont définitives. Les prix sont indicatifs.
2. Risque : Les crypto comportent un risque d'être signalées ou gelées. Nous ne sommes pas responsables.
3. Responsabilité : Nous ne sommes pas responsables des pertes, problèmes juridiques ou techniques.
4. Fonds propres uniquement : Nous n'acceptons que des fonds propres. Fonds sales remboursés.
5. Modifications : Les conditions peuvent être mises à jour à tout moment.""",
        "faq_text": """❓ *FAQ*
Q : Pourquoi les crypto sont-elles moins chères ?
R : Elles ont un historique risqué – Drain, call etc. Cette décote est normale.

Q : Comment acheter ?
R : Utilisez le bot ou contactez @reuvensh. Vous recevrez une adresse de dépôt.

Q : Minimum ?
R : 50 $ équivalent. Pas de maximum.

Q : Pourquoi ne nettoyez-vous pas les crypto vous-mêmes ?
R : Le nettoyage de gros volumes prend du temps et disperse le risque. Nous préférons vendre à prix réduit.

Q : Intermédiaire ?
R : Oui, accepté à vos frais.

Q : Délai de livraison ?
R : Habituellement sous 30 minutes.

Q : Anonymat ?
R : Aucune info personnelle demandée. Votre anonymat dépend de votre configuration.

Q : Que faire si les crypto sont gelées ?
R : Une fois envoyées, nous n'avons plus le contrôle. Utilisez un nouveau portefeuille non‑KYC.

Q : Comment nettoyer ?
R : Un guide sera fourni avec votre achat.""",
        "lang_changed": "✅ Langue définie sur Français.",
        "flash_sale_message": "🔥 Offre Flash : Bonus +100$ pendant 1h ! 🔥",
        "stats_text": "📊 *Statistiques du Bot*\nUtilisateurs totaux : {}",
    },
}

# ==================== GLOBALS ====================
user_languages: Dict[int, str] = {}
all_users: Set[int] = set()
pending_checks: Dict[int, asyncio.Task] = {}

# ==================== HELPERS ====================
def get_lang(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    user_id = update.effective_user.id
    return user_languages.get(user_id, "en")

def t(key: str, lang: str, *args) -> str:
    return T[lang][key].format(*args)

def get_multiplier(amount: float) -> float:
    for low, high, mult in MULTIPLIER_TIERS:
        if low <= amount <= high:
            return mult
    return 1.0

def main_menu(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(T[lang]["buy"], callback_data="buy")],
        [InlineKeyboardButton(T[lang]["rates"], callback_data="rates")],
        [InlineKeyboardButton(T[lang]["faq"], callback_data="faq")],
        [InlineKeyboardButton(T[lang]["tos"], callback_data="tos")],
        [InlineKeyboardButton(T[lang]["support"], callback_data="support")],
        [InlineKeyboardButton(T[lang]["channel"], url=f"https://t.me/{CHANNEL_USERNAME[1:]}")],
        [InlineKeyboardButton(T[lang]["vouches"], url=f"https://t.me/{VOUCHES_USERNAME[1:]}")],
        [InlineKeyboardButton(T[lang]["language"], callback_data="lang")],
    ])

# ==================== STOCK UPDATER ====================
async def stock_updater():
    """Update stock values randomly every 30 minutes."""
    while True:
        STOCK["ETH"] = round(random.uniform(80_000, 90_000), 2)
        STOCK["BTC"] = round(random.uniform(50_000, 60_000), 2)
        logging.info(f"Stocks updated: ETH={STOCK['ETH']}, BTC={STOCK['BTC']}")
        await asyncio.sleep(30 * 60)

# ==================== HANDLERS ====================
async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    all_users.add(user_id)
    lang = get_lang(update, context)
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        await query.edit_message_text(t("start", lang), reply_markup=main_menu(lang), parse_mode=ParseMode.MARKDOWN)
    else:
        await update.message.reply_text(t("start", lang), reply_markup=main_menu(lang), parse_mode=ParseMode.MARKDOWN)

async def menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    data = query.data
    lang = get_lang(update, context)
    if data in ("rates", "faq", "tos", "support"):
        if data == "rates":
            text = "📊 *Rates (x multiplier)*\n\n"
            for low, high, mult in MULTIPLIER_TIERS:
                text += f"${low}-${high if high < float('inf') else '+'}: x{mult}\n"
            text += f"\n💰 *Available stock*: ETH ${STOCK['ETH']:,.0f}, BTC ${STOCK['BTC']:,.0f}"
        elif data == "faq":
            text = t("faq_text", lang)
        elif data == "tos":
            text = t("tos_text", lang)
        elif data == "support":
            text = t("support_text", lang, SUPPORT_USERNAME)
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(T[lang]["back"], callback_data="back")]]), parse_mode=ParseMode.MARKDOWN)
    elif data == "lang":
        keyboard = [
            [InlineKeyboardButton("🇬🇧 English", callback_data="set_lang_en")],
            [InlineKeyboardButton("🇫🇷 Français", callback_data="set_lang_fr")],
            [InlineKeyboardButton(T[lang]["back"], callback_data="back")],
        ]
        await query.edit_message_text("Choose language / Choisissez la langue :", reply_markup=InlineKeyboardMarkup(keyboard))
    elif data.startswith("set_lang_"):
        new_lang = data.split("_")[2]
        user_languages[query.from_user.id] = new_lang
        await query.edit_message_text(t("lang_changed", new_lang))
        await cmd_start(update, context)
    elif data == "back":
        await cmd_start(update, context)

# ==================== BUY CONVERSATION ====================
AMOUNT, COIN_RECEIVE, ADDRESS_RECEIVE, PAYMENT_METHOD, PAYMENT = range(5)

async def buy_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    lang = get_lang(update, context)
    await query.edit_message_text(t("buy_prompt", lang))
    return AMOUNT

async def amount_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    lang = get_lang(update, context)
    text = update.message.text.strip()
    try:
        amount = float(text)
        if amount < 50:
            raise ValueError
    except ValueError:
        await update.message.reply_text(t("invalid_amount", lang))
        return AMOUNT
    context.user_data["pay_amount"] = amount
    context.user_data["multiplier"] = get_multiplier(amount)
    keyboard = [
        [InlineKeyboardButton("BTC", callback_data="receive_BTC")],
        [InlineKeyboardButton("ETH", callback_data="receive_ETH")],
        [InlineKeyboardButton(t("cancel", lang), callback_data="cancel")],
    ]
    await update.message.reply_text(t("choose_receive_coin", lang), reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)
    return COIN_RECEIVE

async def coin_receive(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    lang = get_lang(update, context)
    if query.data == "cancel":
        await query.edit_message_text("Purchase cancelled.")
        await cmd_start(update, context)
        return ConversationHandler.END
    coin = query.data.split("_")[1]
    context.user_data["receive_coin"] = coin
    pay_amount = context.user_data["pay_amount"]
    multiplier = context.user_data["multiplier"]
    receive_value = pay_amount * multiplier
    context.user_data["receive_value"] = receive_value
    dirty_price = PRICE[coin]
    dirty_amount = receive_value / dirty_price
    context.user_data["dirty_amount"] = dirty_amount
    await query.edit_message_text(
        t("receive_estimate", lang, pay_amount, multiplier, receive_value, coin, dirty_amount, coin, coin),
        parse_mode=ParseMode.MARKDOWN,
    )
    return ADDRESS_RECEIVE

async def receive_address(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    lang = get_lang(update, context)
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
        await update.message.reply_text(t("invalid_address", lang, coin))
        return ADDRESS_RECEIVE
    context.user_data["receive_address"] = address
    payment_methods = ["BTC", "ETH", "SOL", "LTC", "BNB", "USDT_TRC20", "XMR"]
    keyboard = []
    for p in payment_methods:
        label = p if p != "USDT_TRC20" else "USDT (TRC-20)"
        keyboard.append([InlineKeyboardButton(label, callback_data=f"paymethod_{p}")])
    keyboard.append([InlineKeyboardButton(t("cancel", lang), callback_data="cancel")])
    await update.message.reply_text(t("choose_payment_method", lang), reply_markup=InlineKeyboardMarkup(keyboard))
    return PAYMENT_METHOD

async def payment_method(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    lang = get_lang(update, context)
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
    text = t("payment_instruction", lang, crypto_amount, pay_coin, address, pay_amount)
    keyboard = [
        [InlineKeyboardButton(t("i_paid", lang), callback_data="check_payment")],
        [InlineKeyboardButton(t("cancel", lang), callback_data="cancel")],
    ]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)
    return PAYMENT

async def check_payment(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    lang = get_lang(update, context)
    user_id = query.from_user.id
    pay_coin = context.user_data["pay_coin"]
    expected = context.user_data["pay_crypto_amount"]
    address = CRYPTO_ADDRESSES[pay_coin]

    # Notify admin immediately when the user clicks "I have paid"
    pay_amount = context.user_data["pay_amount"]
    admin_text = t("admin_notify", lang,
                   query.from_user.username or user_id,
                   pay_amount, expected, pay_coin,
                   context.user_data["dirty_amount"],
                   context.user_data["receive_coin"],
                   context.user_data["receive_address"])
    await context.bot.send_message(ADMIN_ID, admin_text, parse_mode=ParseMode.MARKDOWN)

    paid = await verify_payment(pay_coin, address, expected)  # always False for now
    if paid:
        await query.edit_message_text(t("payment_found", lang, SUPPORT_USERNAME))
        await cmd_start(update, context)
        return ConversationHandler.END
    else:
        # Cancel any existing pending task
        if user_id in pending_checks:
            pending_checks[user_id].cancel()
        # Show "no payment" with Cancel button only
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton(t("cancel", lang), callback_data="cancel")]])
        await query.edit_message_text(t("no_payment", lang), reply_markup=keyboard)
        # Create background task
        task = asyncio.create_task(recheck_payment_after_delay(
            context.bot, user_id, query.message.chat_id, query.message.message_id,
            pay_coin, address, expected, lang, context.user_data.copy()
        ))
        pending_checks[user_id] = task
        return PAYMENT

async def recheck_payment_after_delay(bot, user_id, chat_id, message_id,
                                      pay_coin, address, expected, lang, user_data):
    try:
        await asyncio.sleep(60)
        paid = await verify_payment(pay_coin, address, expected)
        if paid:
            # No admin notification after the 60-second delay
            await bot.edit_message_text(
                t("payment_found", lang, SUPPORT_USERNAME),
                chat_id=chat_id, message_id=message_id
            )
        else:
            await bot.edit_message_text(
                t("payment_found", lang, SUPPORT_USERNAME),
                chat_id=chat_id, message_id=message_id
            )
    except asyncio.CancelledError:
        pass
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
    await query.edit_message_text("Purchase cancelled.")
    await cmd_start(update, context)
    return ConversationHandler.END

async def verify_payment(crypto: str, address: str, expected: float) -> bool:
    # Stub – replace with actual blockchain check
    return False

# ==================== ADMIN COMMANDS ====================
async def cmd_stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user.id != ADMIN_ID:
        return
    lang = get_lang(update, context)
    await update.message.reply_text(t("stats_text", lang, len(all_users)), parse_mode=ParseMode.MARKDOWN)

async def cmd_dmall(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user.id != ADMIN_ID:
        return
    lang = get_lang(update, context)
    message = t("flash_sale_message", lang)
    success = 0
    for uid in all_users:
        try:
            await context.bot.send_message(uid, message, parse_mode=ParseMode.MARKDOWN)
            success += 1
        except Exception as e:
            logging.warning(f"Could not DMALL to {uid}: {e}")
    await update.message.reply_text(f"DMALL sent to {success}/{len(all_users)} users.")

# ==================== MAIN ====================
async def on_startup(app: Application):
    # Start stock updater as background task
    asyncio.create_task(stock_updater())

def main() -> None:
    logging.basicConfig(level=logging.INFO)
    app = Application.builder().token(BOT_TOKEN).post_init(on_startup).build()

    # Conversation handler for buy flow
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

    # Main menu callbacks
    app.add_handler(CallbackQueryHandler(menu_callback, pattern="^(rates|faq|tos|support|lang|set_lang_..|back)$"))
    app.add_handler(CommandHandler("start", cmd_start))

    # Admin commands
    app.add_handler(CommandHandler("stats", cmd_stats))
    app.add_handler(CommandHandler("dmall", cmd_dmall))

    print("Bot running...")
    app.run_polling()

if __name__ == "__main__":
    main()