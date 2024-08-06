import sqlite3
import json
from common import log, get_time

def add_buff_to_user(user_id, buff):
    conn = sqlite3.connect("databases/user_data.db")
    c = conn.cursor()
    c.execute("SELECT buffs FROM USERINFO WHERE user_id=?", (user_id,))
    data = c.fetchone()
    if data:
        buffs = json.loads(data[0])
        buffs.append(buff)
        c.execute("UPDATE USERINFO SET buffs=? WHERE user_id=?", (json.dumps(buffs), user_id))
    else:
        c.execute("INSERT INTO USERINFO (user_id, buffs) VALUES (?, ?)", (user_id, json.dumps([buff])))
    conn.commit()
    conn.close()
    return True

def remove_buff_from_user(user_id, buff):
    conn = sqlite3.connect("databases/user_data.db")
    c = conn.cursor()
    c.execute("SELECT buffs FROM USERINFO WHERE user_id=?", (user_id,))
    data = c.fetchone()
    if data:
        buffs = json.loads(data[0])
        if buff in buffs:
            buffs.remove(buff)
            c.execute("UPDATE USERINFO SET buffs=? WHERE user_id=?", (json.dumps(buffs), user_id))
    conn.commit()
    conn.close()
    return True

def get_all_user_buffs(user_id):
    conn = sqlite3.connect("databases/user_data.db")
    c = conn.cursor()
    c.execute("SELECT buffs FROM USERINFO WHERE user_id=?", (user_id,))
    data = c.fetchone()
    conn.close()
    if data:
        return json.loads(data[0])
    return []

def get_kind_user_buffs(user_id, kind='XP'):
    buffs = get_all_user_buffs(user_id)
    with open("shared_config/buffs.json", "r") as file:
        BUFFS = json.load(file)
    return [buff for buff in buffs if BUFFS[buff]['type'] == kind]
    #return [buff for buff in buffs if buff['type'] == kind]


def get_buffs_info(buffs):
    with open ("shared_config/buffs.json") as f:
        data = json.load(f)
    return [data[buff] for buff in buffs]

def get_xp_after_buffs(user_id, XP, kind='XP'):
    log("BUFFS", f"Getting XP after buffs for user {user_id}, XP: {XP}, kind: {kind}")
    buffs = get_kind_user_buffs(user_id, kind)
    mod_mult = 0
    mod_flat = 0
    with open("shared_config/buffs.json", "r") as file:
        BUFFS = json.load(file)
    for buff in buffs:
        if BUFFS[buff]['modifier'] == "flat":
            mod_flat += BUFFS[buff]['value']
        if BUFFS[buff]['modifier'] == "mult":
            mod_mult += BUFFS[buff]['value']
    print(mod_flat, mod_mult)
    return XP + mod_flat + (XP * mod_mult)


 
