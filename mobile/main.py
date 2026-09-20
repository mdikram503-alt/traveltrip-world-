from kivy.config import Config
Config.set('graphics', 'width', '390')
Config.set('graphics', 'height', '844')

from kivy.app import App
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.properties import ListProperty, StringProperty
from kivy.uix.screenmanager import ScreenManager
from api import TravelerAPI

KV = '''
#:import dp kivy.metrics.dp
<TopBar@BoxLayout>:
    size_hint_y: None; height: dp(64); padding: dp(18), 0
    canvas.before:
        Color: rgba: .027,.106,.20,1
        Rectangle: pos: self.pos; size: self.size
    Label: text: '[b]Traveler[/b]'; markup: True; color: 1,1,1,1; font_size: '22sp'; halign: 'left'; text_size: self.size
    Button: text: 'Support'; size_hint_x: .3; background_normal: ''; background_color: .07,.41,.91,1; on_release: app.root.current='support'
<Home>:
    BoxLayout: orientation: 'vertical'
    TopBar:
    ScrollView:
        BoxLayout: orientation: 'vertical'; size_hint_y: None; height: self.minimum_height; spacing: dp(14); padding: dp(18)
            Label: text: '[b]Stay connected,\nwherever you go.[/b]'; markup: True; font_size: '29sp'; size_hint_y: None; height: dp(86); color: .02,.10,.20,1; halign: 'left'; text_size: self.width, None
            TextInput: id: query; hint_text: 'Search country or region'; size_hint_y: None; height: dp(50); multiline: False; on_text: app.search_plans(self.text)
            Label: text: 'Popular plans'; size_hint_y: None; height: dp(24); color: .02,.10,.20,1; font_size: '18sp'; halign: 'left'; text_size: self.width, None
            RecycleView:
                viewclass: 'PlanCard'; size_hint_y: None; height: dp(440); data: app.plans
    BoxLayout: size_hint_y: None; height: dp(62); padding: dp(12), dp(8); spacing: dp(8)
        Button: text: 'Shop'; on_release: app.root.current='home'
        Button: text: 'My eSIMs'; on_release: app.load_orders()
        Button: text: 'Account'; on_release: app.root.current='account'
<PlanCard@Button>:
    text: '[b]'+root.title+'[/b]\n'+root.data+' · '+root.validity+'\n[b]'+root.price+'[/b]'; markup: True; size_hint_y: None; height: dp(86); background_normal: ''; background_color: .96,.98,1,1; color: .02,.10,.20,1
    on_release: app.open_checkout(root.plan_id, root.title, root.price)
<Checkout>:
    BoxLayout: orientation: 'vertical'
    TopBar:
    BoxLayout: orientation: 'vertical'; padding: dp(22); spacing: dp(16)
        Label: text: app.checkout_title; font_size: '25sp'; color: .02,.10,.20,1; halign: 'left'; text_size: self.width, None
        Label: text: app.checkout_price; font_size: '22sp'; color: .07,.41,.91,1; halign: 'left'; text_size: self.width, None
        Label: text: 'Payment is completed securely in Traveler checkout. Your eSIM and QR code appear in My eSIMs after payment.'; color: .18,.25,.33,1; halign: 'left'; text_size: self.width, None
        Button: text: 'Continue to secure checkout'; size_hint_y: None; height: dp(52); background_normal: ''; background_color: .07,.41,.91,1; on_release: app.start_checkout()
        Button: text: 'Back'; size_hint_y: None; height: dp(46); on_release: app.root.current='home'
<Orders>:
    BoxLayout: orientation: 'vertical'
    TopBar:
    ScrollView:
        Label: text: app.orders_text; color: .02,.10,.20,1; padding: dp(20),dp(20); text_size: self.width-dp(40),None; size_hint_y: None; height: max(self.texture_size[1]+dp(40), dp(500)); halign: 'left'; valign: 'top'
<Account>:
    BoxLayout: orientation: 'vertical'
    TopBar:
    BoxLayout: orientation: 'vertical'; padding: dp(22); spacing: dp(12)
        Label: text: '[b]Your Traveler account[/b]'; markup: True; font_size: '24sp'; color: .02,.10,.20,1; size_hint_y: None; height: dp(44)
        TextInput: id: email; hint_text: 'Email address'; multiline: False
        TextInput: id: password; hint_text: 'Password'; password: True; multiline: False
        Button: text: 'Sign in'; size_hint_y: None; height: dp(52); background_normal: ''; background_color: .07,.41,.91,1; on_release: app.sign_in(email.text,password.text)
        Label: text: app.account_message; color: .18,.25,.33,1
<Support>:
    BoxLayout: orientation: 'vertical'
    TopBar:
    BoxLayout: orientation: 'vertical'; padding: dp(22); spacing: dp(15)
        Label: text: '[b]Need help?[/b]\n\nUse WhatsApp or email support. For an eSIM issue, include your order number and destination.'; markup: True; color: .02,.10,.20,1; text_size: self.width,None; halign: 'left'
        Button: text: 'Email support'; size_hint_y: None; height: dp(52); on_release: app.open_link('mailto:hello@traveltrip.world')
        Button: text: 'Back'; size_hint_y: None; height: dp(46); on_release: app.root.current='home'
'''

class Home(ScreenManager): pass
class Checkout(ScreenManager): pass
class Orders(ScreenManager): pass
class Account(ScreenManager): pass
class Support(ScreenManager): pass

class TravelerApp(App):
    plans = ListProperty([]); checkout_title = StringProperty(''); checkout_price = StringProperty(''); orders_text = StringProperty('Sign in to see your eSIMs.'); account_message = StringProperty('')
    def build(self):
        Builder.load_string(KV); self.api = TravelerAPI(); sm = ScreenManager()
        for name, cls in [('home',Home),('checkout',Checkout),('orders',Orders),('account',Account),('support',Support)]: sm.add_widget(cls(name=name))
        Clock.schedule_once(lambda *_: self.search_plans(''), .2); return sm
    def search_plans(self, term):
        def done(rows): self.plans = [{'plan_id':str(x.get('id',x.get('package_code',''))),'title':x.get('name','Travel data plan'),'data':x.get('data','Flexible data'),'validity':x.get('validity','See details'),'price':x.get('price_display',x.get('price','View price'))} for x in rows]
        self.api.catalog(term, done)
    def open_checkout(self, pid, title, price): self.selected_plan=pid; self.checkout_title=title; self.checkout_price=str(price); self.root.current='checkout'
    def start_checkout(self): self.api.checkout(self.selected_plan, self.open_link)
    def sign_in(self,email,password): self.api.login(email,password,lambda ok,msg: setattr(self,'account_message',msg))
    def load_orders(self): self.api.orders(lambda text: (setattr(self,'orders_text',text), setattr(self.root,'current','orders')))
    def open_link(self,url): __import__('webbrowser').open(url)
TravelerApp().run()
