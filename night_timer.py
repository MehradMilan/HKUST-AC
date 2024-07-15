# Schdule Turn on and Turn off AC for each user based on thier data
# Use the HKUST class to turn on and off the AC
# User data is stored in a SQLite database
# Columns: user_id, username, password, night_timer_enabled, start_time, end_time, on_time, off_time

import sqlite3
from datetime import datetime
from typing import List, Tuple
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from HKUST.hkust import HKUST
from bot import get_user_credentials

from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, time
# Multiple threads are required to run the bot in the background
from threading import Thread
import time

scheduler = BackgroundScheduler()

def get_user_schedule(user_id: int) -> Tuple[bool, str, str, int, int]:
    conn = sqlite3.connect('user_credentials.db')
    c = conn.cursor()
    c.execute('SELECT night_timer_enabled, start_time, end_time, on_time, off_time FROM credentials WHERE user_id = ?', (user_id,))
    result = c.fetchone()
    conn.close()
    return result

def toggle_ac_scheduled(user_id, end_time, on_time, off_time):
    print('Toggling AC for user {}'.format(user_id))
    username, password = get_user_credentials(user_id)
    if username is None or password is None:
        return
    
    end_time = datetime.strptime(end_time, '%H:%M')
    end_time = datetime.combine(datetime.now().date(), end_time.time())
    while datetime.now() < end_time:
        with HKUST() as bot:
            bot.land_login_page()
            bot.submit_username(username)
            bot.submit_password(password)
            bot.toggle_ac_on()
        time.sleep(on_time * 60)
        with HKUST() as bot:
            bot.land_login_page()
            bot.submit_username(username)
            bot.submit_password(password)
            bot.toggle_ac_off()
        time.sleep(off_time * 60)

def add_user_job(user_id: int):
    night_timer_enabled, start_time, end_time, on_time, off_time = get_user_schedule(user_id)
    scheduler.add_job(
        toggle_ac_scheduled(user_id, end_time, on_time, off_time),
        'cron',
        hour=start_time.split(':')[0],
        minute=start_time.split(':')[1],
        id='ac_{}'.format(user_id)
    )
    

def remove_user_job(user_id: int):
    scheduler.remove_job('ac_{}'.format(user_id))

def update_user_job(user_id: int):
    try:
        remove_user_job(user_id)
    except:
        pass
    add_user_job(user_id)
    print(scheduler.get_jobs())