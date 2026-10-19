(() => {
  const csrf = () => document.cookie.split('; ').find(row => row.startsWith('csrftoken='))?.split('=')[1] || '';
  const notify = (message) => {
    let node = document.querySelector('.toast');
    if (!node) { node = document.createElement('div'); node.className = 'toast'; node.setAttribute('role', 'status'); document.body.append(node); }
    node.textContent = message;
    clearTimeout(window.iworldToastTimer);
    window.iworldToastTimer = setTimeout(() => node.remove(), 2600);
  };
  document.querySelectorAll('[data-like-url]').forEach(button => {
    button.addEventListener('click', async () => {
      button.disabled = true;
      try {
        const response = await fetch(button.dataset.likeUrl, {method:'POST', headers:{'X-CSRFToken':csrf(), 'X-Requested-With':'XMLHttpRequest'}});
        const data = await response.json();
        if (!response.ok) throw new Error(data.error || 'Could not update like.');
        button.classList.toggle('liked', data.liked);
        button.setAttribute('aria-pressed', String(data.liked));
        button.setAttribute('aria-label', data.liked ? 'Unlike' : 'Like');
        const count = button.closest('.post-card').querySelector('[data-like-count]');
        if (count) count.textContent = data.count;
      } catch (error) { notify(error.message); }
      finally { button.disabled = false; }
    });
  });
  document.querySelectorAll('input[type=file][name=media]').forEach(input => {
    input.addEventListener('change', () => {
      const file = input.files?.[0], preview = document.querySelector('#mediaPreview');
      if (!preview) return;
      preview.replaceChildren();
      if (!file) { preview.classList.add('hidden'); return; }
      const url = URL.createObjectURL(file);
      const element = file.type.startsWith('video/') ? document.createElement('video') : document.createElement('img');
      element.src = url;
      if (element.tagName === 'VIDEO') { element.controls = true; element.muted = true; }
      else element.alt = 'Selected image preview';
      preview.append(element); preview.classList.remove('hidden');
    });
  });
  document.querySelectorAll('[data-confirm]').forEach(button => button.addEventListener('click', event => {
    if (!window.confirm(button.dataset.confirm)) event.preventDefault();
  }));
  document.querySelectorAll('[data-copy-url]').forEach(button => button.addEventListener('click', async () => {
    try { await navigator.clipboard.writeText(button.dataset.copyUrl); notify('Post link copied.'); }
    catch { notify('Could not copy the link on this browser.'); }
  }));
})();
