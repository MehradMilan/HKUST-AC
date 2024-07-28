import sqlite3
from datetime import datetime
from typing import List, Tuple
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from HKUST.hkust import HKUST

from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, time, timedelta
import time

scheduler = BackgroundScheduler()

def get_user_schedule(user_id: int) -> Tuple[bool, str, str, int, int]:
    conn = sqlite3.connect('user_credentials.db')
    c = conn.cursor()
    c.execute('SELECT night_timer_enabled, start_time, end_time, on_time, off_time FROM credentials WHERE user_id = ?', (user_id,))
    result = c.fetchone()
    conn.close()
    return result


def get_user_credentials(user_id: int) -> Tuple[str, str]:
    conn = sqlite3.connect('user_credentials.db')
    c = conn.cursor()
    c.execute('SELECT username, password FROM credentials WHERE user_id = ?', (user_id,))
    result = c.fetchone()
    conn.close()
    return result

def toggle_ac_scheduled(user_id, end_time, on_time, off_time, is_temp=False):
    print('Toggling AC')
    username, password = get_user_credentials(user_id)
    if username is None or password is None:
        return
    
    end_time = datetime.strptime(end_time, '%H:%M')
    end_time = datetime.combine(datetime.now().date(), end_time.time())
    while datetime.now() < end_time:
        try:
            with HKUST(teardown=True) as bot:
                bot.land_login_page()
                bot.submit_username(username)
                bot.submit_password(password)
                bot.toggle_ac_on()
            time.sleep(on_time * 60)
            with HKUST(teardown=True) as bot:
                bot.land_login_page()
                bot.submit_username(username)
                bot.submit_password(password)
                bot.toggle_ac_off()
            time.sleep(off_time * 60)
        except:
            pass
    if is_temp:
        remove_user_job(user_id)
        add_user_job(user_id)

def add_user_job(user_id: int):
    print('Adding job')
    night_timer_enabled, start_time, end_time, on_time, off_time = get_user_schedule(user_id)
    if not night_timer_enabled:
        return

    now = datetime.now()
    hour, minute = start_time.strip().split(':')
    start_datetime = now.replace(hour=int(hour), minute=int(minute), second=0, microsecond=0)

    if now > start_datetime:
        print('Start time is in the past')
        remaining_end_time = datetime.strptime(end_time.strip(), '%H:%M')
        remaining_end_time = datetime.combine(now.date(), remaining_end_time.time())
        if now < remaining_end_time:
            scheduler.add_job(
                toggle_ac_scheduled,
                'cron',
                hour=now.hour,
                minute=now.minute + 1,
                id='ac_{}'.format(user_id),
                args=[user_id, end_time.strip(), on_time, off_time, True]
            )
        else:
            return
    else:
        scheduler.add_job(
            toggle_ac_scheduled,
            'cron',
            hour=int(hour),
            minute=int(minute),
            id='ac_{}'.format(user_id),
            args=[user_id, end_time.strip(), on_time, off_time, False]
        )

def remove_user_job(user_id: int):
    try:
        scheduler.remove_job('ac_{}'.format(user_id))
    except:
        pass

def update_user_job(user_id: int):
    remove_user_job(user_id)
    add_user_job(user_id)

def start_scheduler():
    scheduler.start()