import sqlite3

conn = sqlite3.connect(r'C:\Users\zzx05\Desktop\大床课题\my-asthma-system\asthma-core\data\asthma_v2.db')
cur = conn.cursor()
tables = [r[0] for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
print('数据表:', tables)
for t in tables:
    try:
        n = cur.execute(f'SELECT COUNT(*) FROM "{t}"').fetchone()[0]
        print(f'  {t}: {n} 条')
    except Exception as e:
        print(f'  {t}: 错误 {e}')
conn.close()
