(function(){
  if (!document.getElementById('notification-styles')) {
    const style = document.createElement('style');
    style.id = 'notification-styles';
    style.textContent = `
      .notification{position:fixed;top:20px;right:20px;padding:10px 15px;color:#fff;border-radius:4px;z-index:1000;font-family:sans-serif;}
      .notification.success{background:#4caf50;}
      .notification.error{background:#f44336;}
    `;
    document.head.appendChild(style);
  }
  function showNotification(message, type='success'){
    const note=document.createElement('div');
    note.className=`notification ${type}`;
    note.textContent=message;
    document.body.appendChild(note);
    setTimeout(()=>{
      note.remove();
    },3000);
  }
  window.showNotification=showNotification;
})();
