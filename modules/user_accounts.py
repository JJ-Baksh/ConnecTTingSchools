import os
from pymongo import MongoClient

class UserAccounts:

    def __init__(self):
        self.cluster = MongoClient(os.environ['3020_DB_uri'], connectTimeoutMS=30000, socketTimeoutMS=None, socketKeepAlive=True, connect=False, maxPoolsize=1)
        self.db = self.cluster['ECNG3020']['UserAccounts']

    # add user entry to the database
    def AddtoDB(self, reg_form):
        self.db.insert_one(reg_form)
        self.cluster.close()

    # for email validation on registartion
    def ValidateRegistration(self, error, email, password):
        # validate email (must contain @ and must not exist in database)
        if not '@' in email:
            error['status'] = True
            error['email'] = 'Please enter a valid email (must contain @)'
        
        elif self.db.find_one({"email" : email}):
                error['status'] = True
                error['email'] = 'Email already in use'
        
        # validate password
        if len(password) < 8 or len(password) > 32:
            error['status'] = True
            error['password'] = 'Your password should be between 8 and 32 characters.'

        self.cluster.close()
        return error


    def ValidateUserAccount(self, form):
        # search for an entry in database with a matching email and password
        result = self.db.find_one({
            "$and":
                [{"email": form['email'], "password" : form['password']}]
            })
        self.cluster.close()
        
        if not result: return None
        elif not result['verified']: return None
            
        return {'firstName': result['firstName']}
    
    
    def VerifyEmail(self, email):
        result = self.db.find_one({"email" : email})
        
        self.db.update_one({"email" : email}, 
        {'$set': {
            "verified": True
        }})
        
        self.cluster.close()
        
        return result['firstName']