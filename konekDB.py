import mysql.connector

class konekDB:
    def __init__(self):
        pass

    def querryResult(self, strsql):
        cnx = mysql.connector.connect(user='andriefendy', password='Andri2608.', host='127.0.0.1', database='warungme')
        conn = cnx.cursor()
        conn.execute(strsql)
        result = conn.fetchall()
        return result
        pass


    def querryExecute(self, strsql):
        cnx = mysql.connector.connect(user='andriefendy', password='Andri2608.', host='127.0.0.1', database='warungme')
        conn = cnx.cursor()
        conn.execute(strsql)
        cnx.commit()
        pass
