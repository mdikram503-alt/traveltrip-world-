import threading
from urllib.parse import urlencode
import requests
from kivy.clock import Clock

BASE_URL = 'https://traveltrip.world'
class TravelerAPI:
    def __init__(self):
        # Production authentication uses a secure session cookie, not a token.
        self.session = requests.Session()
        self.session.headers.update({'Accept': 'application/json'})
    def _run(self, work, callback):
        def worker():
            try: result=work()
            except Exception: result=[]
            Clock.schedule_once(lambda *_: callback(result),0)
        threading.Thread(target=worker,daemon=True).start()
    def catalog(self, term, callback):
        def work():
            r=self.session.get(BASE_URL+'/catalog/esim/packages',params={'location':'ALL'},timeout=15); r.raise_for_status(); rows=r.json().get('packages',[])
            query=(term or '').strip().lower()
            return rows if not query else [x for x in rows if query in ' '.join(str(x.get(k,'')) for k in ('name','region','network','packageCode')).lower()]
        self._run(work,callback)
    def login(self,email,password,callback):
        def work():
            r=self.session.post(BASE_URL+'/api/auth/login',json={'email':email,'password':password},timeout=15); r.raise_for_status(); return (True,'Signed in successfully')
        self._run(work,lambda value: callback(*value) if isinstance(value,tuple) else callback(False,'Sign-in failed. Please check your details.'))
    def orders(self,callback):
        def work():
            r=self.session.get(BASE_URL+'/api/account/orders',timeout=15)
            if r.status_code==401:return 'Sign in to see your eSIMs.'
            r.raise_for_status(); rows=r.json().get('orders',[])
            return '\n\n'.join(f"{x.get('package_name',x.get('name','eSIM'))}\nStatus: {x.get('esim_status',x.get('status','Pending'))}\nQR: {x.get('qr_code_data',x.get('qr_code_url','Available after fulfillment'))}" for x in rows) or 'No orders yet.'
        self._run(work,callback)
    def checkout_url(self, plan_id):
        # Payments stay in the existing web checkout; the app holds no secrets.
        return BASE_URL + '/checkout?' + urlencode({'code': plan_id})
