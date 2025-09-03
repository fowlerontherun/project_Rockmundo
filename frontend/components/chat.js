(function(){
  const HISTORY_KEY = 'chat_history';
  const userId = parseInt(localStorage.getItem('user_id') || '1', 10);
  const state = { conversations: {}, current: null };

  function persist(){
    try{ localStorage.setItem(HISTORY_KEY, JSON.stringify(state.conversations)); }
    catch(e){ console.error('persist failed', e); }
  }

  function loadLocal(){
    const raw = localStorage.getItem(HISTORY_KEY);
    if(raw){
      try{ state.conversations = JSON.parse(raw); }
      catch(e){ state.conversations = {}; }
    }
  }

  function renderConversationList(){
    const list = document.getElementById('conversation-list');
    if(!list) return;
    list.innerHTML = '';
    Object.entries(state.conversations).forEach(([key, conv]) => {
      const div = document.createElement('div');
      div.className = 'conversation';
      div.textContent = conv.type === 'group' ? `Group ${conv.id}` : `User ${conv.id}`;
      div.dataset.key = key;
      div.onclick = () => { state.current = key; renderThread(); };
      list.appendChild(div);
    });
  }

  function renderThread(){
    const thread = document.getElementById('message-thread');
    if(!thread) return;
    thread.innerHTML = '';
    if(!state.current) return;
    const conv = state.conversations[state.current];
    conv.messages.forEach(msg => {
      const div = document.createElement('div');
      div.className = 'msg' + (msg.sender_id === userId ? ' me' : '');
      div.textContent = `${msg.sender_id}: ${msg.content}`;
      thread.appendChild(div);
    });
  }

  async function fetchHistory(){
    try{
      const res = await fetch(`/chat/history/?user_id=${userId}`);
      if(!res.ok) return;
      const data = await res.json();
      data.direct_messages.forEach(msg => {
        const peer = msg.sender_id === userId ? msg.recipient_id : msg.sender_id;
        const key = `u:${peer}`;
        if(!state.conversations[key]){
          state.conversations[key] = {type:'direct', id: peer, messages: []};
        }
        state.conversations[key].messages.push(msg);
      });
      Object.entries(data.group_chats || {}).forEach(([gid, msgs]) => {
        const key = `g:${gid}`;
        if(!state.conversations[key]){
          state.conversations[key] = {type:'group', id: gid, messages: []};
        }
        state.conversations[key].messages.push(...msgs);
      });
      persist();
      renderConversationList();
    }catch(err){ console.error('history error', err); }
  }

  async function sendMessage(text){
    if(!state.current) return;
    const conv = state.conversations[state.current];
    let url, payload;
    if(conv.type === 'group'){
      url = '/chat/send_group';
      payload = {sender_id: userId, group_id: conv.id, content: text};
    } else {
      url = '/chat/send_direct';
      payload = {sender_id: userId, recipient_id: conv.id, content: text};
    }
    try{
      const res = await fetch(url, {
        method: 'POST',
        headers: {'Content-Type':'application/json'},
        body: JSON.stringify(payload)
      });
      if(res.ok){
        let msg;
        try {
          const data = await res.json();
          msg = data.message || {...payload, timestamp: new Date().toISOString()};
        } catch(_) {
          msg = {...payload, timestamp: new Date().toISOString()};
        }
        conv.messages.push(msg);
        persist();
        renderThread();
      }
    }catch(err){ console.error('send error', err); }
  }

  function setup(){
    loadLocal();
    renderConversationList();
    fetchHistory();

    const sendBtn = document.getElementById('send-btn');
    const input = document.getElementById('message-input');
    if(sendBtn && input){
      sendBtn.addEventListener('click', () => {
        const text = input.value.trim();
        if(text){ sendMessage(text); input.value=''; }
      });
    }

    // Optional WebSocket realtime updates
    const token = localStorage.getItem('jwt');
    try {
      const protocol = location.protocol === 'https:' ? 'wss' : 'ws';
      const ws = new WebSocket(`${protocol}://${location.host}/realtime/ws${token ? `?token=${encodeURIComponent(token)}` : ''}`);
      ws.onmessage = (evt) => {
        try {
          const msg = JSON.parse(evt.data);
          const payload = msg.data || msg; // accept either wrapper or raw
          if(payload){
            const key = payload.group_id ? `g:${payload.group_id}` : `u:${payload.sender_id}`;
            if(!state.conversations[key]){
              state.conversations[key] = {type: payload.group_id ? 'group' : 'direct', id: payload.group_id || payload.sender_id, messages: []};
            }
            state.conversations[key].messages.push(payload);
            persist();
            renderConversationList();
            if(state.current === key) renderThread();
          }
        } catch(e){ console.error('ws message', e); }
      };
    } catch(err){ console.warn('WebSocket unsupported', err); }
  }

  window.addEventListener('load', setup);
})();
