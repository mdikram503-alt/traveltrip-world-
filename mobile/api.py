import json, threading, requests
from kivy.clock import Clock
from storage import TokenStore

BASE_URL = 'https://traveltrip.world'  # change only if your production API is different
class TravelerAPI:
    def __init__(self): self.store=TokenStore()
    def _run(self, work, callback):
        def worker():
            try: result=work()
            except Exception: result=[]
            Clock.schedule_once(lambda *_: callback(result),0)
        threading.Thread(target=worker,daemon=True).start()
    def catalog(self, term, callback):
        def work():
            r=requests.get(BASE_URL+'/catalog/esim/packages',params={'q':term},timeout=15); r.raise_for_status(); data=r.json(); return data.get('packages',data if isinstance(data,list) else [])
        self._run(work,callback)
    def login(self,email,password,callback):
        def work():
            r=requests.post(BASE_URL+'/api/auth/login',json={'email':email,'password':password},timeout=15); r.raise_for_status(); token=r.json().get('token'); self.store.save(token); return (True,'Signed in successfully')
        self._run(work,lambda value: callback(*value) if isinstance(value,tuple) else callback(False,'Sign-in failed. Please check your details.'))
    def orders(self,callback):
        def work():
            token=self.store.load()
            if not token:return 'Sign in to see your eSIMs.'
            r=requests.get(BASE_URL+'/api/orders',headers={'Authorization':'Bearer '+token},timeout=15); r.raise_for_status(); rows=r.json().get('orders',[])
            return '\n\n'.join(f"{x.get('name','eSIM')}\nStatus: {x.get('status','Pending')}\nQR: {x.get('qr_code_url','Available after fulfillment')}" for x in rows) or 'No orders yet.'
        self._run(work,callback)
    def checkout(self,plan_id,callback):
        def work():
            r=requests.post(BASE_URL+'/api/checkout/session',json={'package_id':plan_id},timeout=15); r.raise_for_status(); return r.json()['url']
        self._run(work,callback)
