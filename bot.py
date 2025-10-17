import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import pymongo
from datetime import datetime, timedelta

# MongoDB setup
client = pymongo.MongoClient(os.getenv("MONGO_URI"))
db = client.illumi_bot
users = db.users

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username
    
    # Check if user exists
    user = users.find_one({"user_id": user_id})
    
    if not user:
        # New user registration
        users.insert_one({
            "user_id": user_id,
            "username": username,
            "balance": 0,
            "last_mine": None,
            "referral_code": str(user_id),
            "referred_by": None,
            "referral_count": 0,
            "created_at": datetime.now()
        })
        await update.message.reply_text(
            "🚀 Welcome to ILLUMI Mining Bot!\n\n"
            "Start mining ILLUMI tokens with /mine command\n"
            "Check balance with /balance\n"
            "Refer friends and earn bonuses!"
        )
    else:
        await update.message.reply_text(
            "Welcome back to ILLUMI Mining Bot!\n"
            "Use /mine to start mining tokens!"
        )

async def mine(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user = users.find_one({"user_id": user_id})
    
    if not user:
        await update.message.reply_text("Please use /start first")
        return
    
    current_time = datetime.now()
    last_mine = user.get("last_mine")
    
    # Check if 1 hour has passed since last mine
    if last_mine and (current_time - last_mine) < timedelta(hours=1):
        remaining = timedelta(hours=1) - (current_time - last_mine)
        minutes = int(remaining.total_seconds() / 60)
        await update.message.reply_text(f"⏳ You can mine again in {minutes} minutes!")
        return
    
    # Calculate mining reward (10-50 tokens)
    import random
    tokens_mined = random.randint(10, 50)
    
    # Update user balance and last mine time
    users.update_one(
        {"user_id": user_id},
        {
            "$set": {"last_mine": current_time},
            "$inc": {"balance": tokens_mined}
        }
    )
    
    await update.message.reply_text(
        f"🎉 You mined {tokens_mined} ILLUMI tokens!\n"
        f"💰 Total balance: {user['balance'] + tokens_mined} ILLUMI\n"
        f"⏰ Next mining available in 1 hour"
    )

async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user = users.find_one({"user_id": user_id})
    
    if not user:
        await update.message.reply_text("Please use /start first")
        return
    
    await update.message.reply_text(f"💰 Your balance: {user['balance']} ILLUMI tokens")

async def referral(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user = users.find_one({"user_id": user_id})
    
    if not user:
        await update.message.reply_text("Please use /start first")
        return
    
    referral_link = f"https://t.me/IllumiMiningBot?start={user_id}"
    
    await update.message.reply_text(
        f"📣 Referral Program\n\n"
        f"Your referral link:\n{referral_link}\n\n"
        f"Earn 100 ILLUMI tokens for each friend who joins!\n"
        f"Total referrals: {user['referral_count']}"
    )

async def leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    top_users = users.find().sort("balance", -1).limit(10)
    
    leaderboard_text = "🏆 Top Miners Leaderboard\n\n"
    for idx, user in enumerate(top_users, 1):
        username = user.get('username', 'Anonymous')
        balance = user.get('balance', 0)
        leaderboard_text += f"{idx}. {username}: {balance} ILLUMI\n"
    
    await update.message.reply_text(leaderboard_text)

def main():
    # Create application
    application = Application.builder().token(os.getenv("TELEGRAM_BOT_TOKEN")).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("mine", mine))
    application.add_handler(CommandHandler("balance", balance))
    application.add_handler(CommandHandler("referral", referral))
    application.add_handler(CommandHandler("leaderboard", leaderboard))
    
    # Start bot
    application.run_polling()

if __name__ == '__main__':
    main()
