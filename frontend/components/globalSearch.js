(function(){
  function highlight(text, query){
    if(!query) return text;
    const regex = new RegExp(`(${query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'ig');
    return text.replace(regex, '<mark>$1</mark>');
  }

  function initGlobalSearch(container){
    if(!container) return;
    if(!document.getElementById('global-search-styles')){
      const style=document.createElement('style');
      style.id='global-search-styles';
      style.textContent=`
        .global-search-wrapper{position:relative;margin-left:1rem;}
        .global-search-results{position:absolute;top:100%;left:0;right:0;background:#fff;border:1px solid #ccc;z-index:1000;font-size:14px;max-height:300px;overflow-y:auto;}
        .global-search-results ul{list-style:none;margin:0;padding:0;}
        .global-search-results li{padding:4px 8px;}
        .global-search-results li.active{background:#eee;}
        .global-search-results .group-title{font-weight:bold;padding:4px 8px;border-top:1px solid #ddd;background:#f9f9f9;}
        .global-search-results .group-title:first-child{border-top:none;}
      `;
      document.head.appendChild(style);
    }

    const wrapper=document.createElement('div');
    wrapper.className='global-search-wrapper';
    const input=document.createElement('input');
    input.type='search';
    input.placeholder='Search songs, albums, bands';
    const results=document.createElement('div');
    results.className='global-search-results';
    results.hidden=true;
    wrapper.appendChild(input);
    wrapper.appendChild(results);
    container.appendChild(wrapper);

    let items=[]; // flat list for keyboard navigation
    let activeIndex=-1;

    async function fetchResults(q){
      const [songs, albums, bands] = await Promise.all([
        fetch(`/songs?search=${encodeURIComponent(q)}&limit=5`).then(r=>r.json()).catch(()=>[]),
        fetch(`/albums?search=${encodeURIComponent(q)}&limit=5`).then(r=>r.json()).catch(()=>[]),
        fetch(`/bands?search=${encodeURIComponent(q)}&limit=5`).then(r=>r.json()).catch(()=>[])
      ]);
      results.innerHTML='';
      items=[];
      function renderGroup(title, data, type){
        if(!data || !data.length) return;
        const groupTitle=document.createElement('div');
        groupTitle.className='group-title';
        groupTitle.textContent=title;
        results.appendChild(groupTitle);
        const list=document.createElement('ul');
        list.setAttribute('role','listbox');
        data.forEach(d=>{
          const li=document.createElement('li');
          li.setAttribute('role','option');
          const text = d.title || d.name;
          li.innerHTML=`<a href="/${type}/${d.id || d.song_id || d.release_id}">${highlight(text,q)}</a>`;
          list.appendChild(li);
          items.push(li);
        });
        results.appendChild(list);
      }
      renderGroup('Songs', songs, 'songs');
      renderGroup('Albums', albums, 'albums');
      renderGroup('Bands', bands, 'bands');
      results.hidden=!items.length;
      activeIndex=-1;
    }

    input.addEventListener('input', e=>{
      const q=e.target.value.trim();
      if(!q){results.hidden=true;results.innerHTML='';return;}
      fetchResults(q);
    });

    input.addEventListener('keydown', e=>{
      if(e.key==='ArrowDown'){
        if(activeIndex<items.length-1){activeIndex++;updateActive();}
        e.preventDefault();
      } else if(e.key==='ArrowUp'){
        if(activeIndex>0){activeIndex--;updateActive();}
        e.preventDefault();
      } else if(e.key==='Enter'){
        if(activeIndex>=0){
          const link=items[activeIndex].querySelector('a');
          if(link){ window.location.href=link.getAttribute('href'); }
        }
      } else if(e.key==='Escape'){
        results.hidden=true;
      }
    });

    document.addEventListener('click', (e)=>{
      if(!wrapper.contains(e.target)){
        results.hidden=true;
      }
    });

    function updateActive(){
      items.forEach((item,i)=>{
        if(i===activeIndex){item.classList.add('active'); item.scrollIntoView({block:'nearest'});} else {item.classList.remove('active');}
      });
    }
  }

  window.initGlobalSearch=initGlobalSearch;
})();
