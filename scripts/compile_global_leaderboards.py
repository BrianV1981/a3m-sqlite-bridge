import sqlite3
import json
import re

db_path = '/home/brian-vasquez/arma3server/a3m_database.sqlite'

def serialize(obj):
    return json.dumps(obj, separators=(',', ':'))

def compile_leaderboards():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, val FROM store WHERE id LIKE 'A3M_PROFILE_%'")
    rows = cursor.fetchall()
    
    killers = []
    shots = []
    distance = []
    wealth = []
    
    for row in rows:
        try:
            profile_id = row[0]
            steam_id = profile_id.replace("A3M_PROFILE_", "")
            
            # Sanitize A3M_PROFILE string: Fix Arma's "" escaping inside strings without breaking empty strings ","
            val_str = row[1]
            val_str = re.sub(r'([^,\[\]])""([^,\[\]])', r'\1\\"\2', val_str)
            
            val = json.loads(val_str)
            if len(val) != 2: continue
            keys = val[0]
            values = val[1]
            
            profile = dict(zip(keys, values))
            name = profile.get("PlayerName", "Unknown")
            
            # Kills
            k = profile.get("Kills_Total", 0)
            if k > 0: killers.append([name, k, steam_id])
                
            # Longest Shot
            top_shots = profile.get("Top_10_Longest_Kills", [])
            if top_shots and len(top_shots) > 0:
                best_shot = top_shots[0][0]
                shots.append([name, best_shot, steam_id])
                
            # Distance
            dist = profile.get("Distance_Walked", 0) + profile.get("Distance_Driven", 0) + profile.get("Distance_Flown", 0)
            if dist > 0: distance.append([name, dist, steam_id])
            
            # Wealth (Bank + Wallet)
            cursor.execute("SELECT val FROM store WHERE id = ?", (f"mcd_grad_persistence_my_persistent_mission_player_{steam_id}",))
            grad_row = cursor.fetchone()
            if grad_row:
                grad_val_str = grad_row[0]
                total_wealth = 0
                
                # Sanitize grad-persistence string: Strip the massive ACE medical string that breaks JSON parsers
                grad_val_str = re.sub(r'"{""ace_medical_openwounds"".*?}"', '"stripped"', grad_val_str)
                
                try:
                    grad_val = json.loads(grad_val_str)
                    if len(grad_val) == 2:
                        grad_keys = grad_val[0]
                        grad_values = grad_val[1]
                        grad_dict = dict(zip(grad_keys, grad_values))
                        
                        wallet = grad_dict.get("money", 0)
                        bank = grad_dict.get("bankMoney", 0)
                        total_wealth = wallet + bank
                except Exception as json_err:
                    print(f"Failed to parse wealth for {steam_id}: {json_err}")
                
                if total_wealth > 0:
                    wealth.append([name, total_wealth, steam_id])
                
        except Exception as e:
            print(f"Error parsing {row[0]}: {e}")
            continue
            
    # Sort descending
    killers.sort(key=lambda x: x[1], reverse=True)
    shots.sort(key=lambda x: x[1], reverse=True)
    distance.sort(key=lambda x: x[1], reverse=True)
    wealth.sort(key=lambda x: x[1], reverse=True)
    
    # Trim to Top 10
    killers = killers[:10]
    shots = shots[:10]
    distance = distance[:10]
    wealth = wealth[:10]
    
    # Format array
    leaderboard_data = [killers, shots, wealth, distance]
    leaderboard_str = serialize(leaderboard_data)
    
    # Save to SQLite
    cursor.execute('''
        INSERT INTO store (id, val) VALUES (?, ?)
        ON CONFLICT(id) DO UPDATE SET val = excluded.val
    ''', ("A3M_GLOBAL_LEADERBOARDS", leaderboard_str))
    
    conn.commit()
    conn.close()
    print("Compiled Global Leaderboards and saved to A3M_GLOBAL_LEADERBOARDS")

if __name__ == "__main__":
    compile_leaderboards()
