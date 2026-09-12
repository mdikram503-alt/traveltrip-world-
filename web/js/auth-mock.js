export function currentUser(){ return JSON.parse(localStorage.getItem('traveler.user')||'null'); }
