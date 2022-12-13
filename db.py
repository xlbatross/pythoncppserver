import pymysql

class DB:
    def __init__(self):
        self.host = '127.0.0.1'
        self.port = 3306
        self.user = "root"
        self.password = "1234"
        self.dbname = "lecture"
        self.charset = "utf8"

    def connect(self):
        return pymysql.connect(
            host=self.host,
            port=self.port,
            user=self.user,
            password=self.password,
            db=self.dbname,
            charset=self.charset
        )

    #로그인
    def login(self,num,pw):
        conn = self.connect()
        cursor = conn.cursor() 
        sql = f"""select num from lecture.user_info where num = "{num}";"""
        cursor.execute(sql)
        result = cursor.fetchone()
        if result == None:
            return False, "없는 학번입니다. 회원가입을 진행해주세요"
        # else:
            # return True, result
        sql = f"""select * from lecture.user_info where num = "{num}";"""
        cursor.execute(sql)
        result = cursor.fetchone()

        if result[2] != pw:
            return False, "비밀번호 오류"
        else:
            return True, "로그인 성공!"

    def signUp(self,name,num,pw,cate):
        conn = self.connect()
        cursor = conn.cursor() 
        sql = f"""insert into lecture.user_info (name,num,pw,cate) value ("{name}","{num}", "{pw}","{cate}");"""
        cursor.execute(sql)
        conn.commit()
        conn.close()

    def search(self, num):
        conn = self.connect()
        cursor = conn.cursor() 
        sql = f"""select * from lecture.user_info where num = "{num}";"""
        cursor.execute(sql)
        result = cursor.fetchone()
        conn.commit()
        conn.close()
        return result
        
# stu1 = DB()
# stu1_login = stu1.login(1234,0000)
# print(stu1_login)
