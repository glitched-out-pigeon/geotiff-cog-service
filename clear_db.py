from app.db import get_connection
with get_connection() as c:
    c.execute('DELETE FROM layers')
    c.commit()
print('cleared')
