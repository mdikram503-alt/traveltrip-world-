from kivy.storage.jsonstore import JsonStore
class TokenStore:
    def __init__(self): self.db=JsonStore('traveler_session.json')
    def save(self,token): self.db.put('session',token=token)
    def load(self): return self.db.get('session')['token'] if self.db.exists('session') else None
