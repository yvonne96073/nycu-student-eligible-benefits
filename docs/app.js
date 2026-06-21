(() => {
  const DATA_URL = './data.json';

  let allItems = [];
  let activeFilter = 'all';
  let activeLoc = 'all';

  // ── Load data ──────────────────────────────────────────────
  async function loadData() {
    try {
      const resp = await fetch(DATA_URL);
      if (!resp.ok) throw new Error(resp.status);
      const data = await resp.json();

      // Filter out expired items (client-side check)
      const today = new Date().toISOString().slice(0, 10);
      allItems = (data.items || []).filter(item => {
        if (item.end_date && item.end_date < today) return false;
        return true;
      });

      // Update hero meta
      const timeEl = document.getElementById('update-time');
      const countEl = document.getElementById('total-count');
      if (data.updated_at) {
        const d = new Date(data.updated_at);
        timeEl.textContent = `更新：${d.toLocaleDateString('zh-TW')}`;
      }
      countEl.textContent = `共 ${allItems.length} 筆優惠`;

      render();
    } catch (e) {
      document.getElementById('benefits-list').innerHTML =
        '<div class="loading">無法載入資料，請稍後再試</div>';
    }
  }

  // ── Render ─────────────────────────────────────────────────
  function render() {
    const container = document.getElementById('benefits-list');

    const filtered = allItems.filter(item => {
      if (activeFilter !== 'all' && item.final_result !== activeFilter) return false;
      if (activeLoc !== 'all' && item.location_scope !== activeLoc) return false;
      return true;
    });

    if (filtered.length === 0) {
      container.innerHTML = '<div class="no-results">沒有符合條件的優惠</div>';
      return;
    }

    // Group by result
    const usable = filtered.filter(i => i.final_result === '可用');
    const maybe  = filtered.filter(i => i.final_result === '可能可用');

    let html = '';

    if (usable.length > 0) {
      html += renderSection('CONFIRMED', '確認可用', usable, 'usable');
    }
    if (maybe.length > 0) {
      html += renderSection('MAYBE', '可能可用', maybe, 'maybe');
    }

    container.innerHTML = html;
    bindToggle();
  }

  function renderSection(label, title, items, type) {
    let html = `
      <div class="section-header">
        <p class="section-label">${label}</p>
        <p class="section-count">${title} — ${items.length} 筆</p>
      </div>`;

    for (const item of items) {
      html += renderItem(item, type);
    }
    return html;
  }

  function renderItem(item, type) {
    const badgeClass = type === 'usable' ? 'badge-usable' : 'badge-maybe';
    const badgeText  = type === 'usable' ? '可用' : '可能可用';

    const title = escHtml(item.title || '');
    const url = item.source_url || '';
    const titleHtml = url
      ? `<a href="${escAttr(url)}" target="_blank" rel="noopener">${title}</a>`
      : title;

    // Meta tags
    let metaHtml = '';
    if (item.location_scope && item.location_scope !== '不明') {
      metaHtml += `<span class="meta-loc">${escHtml(item.location_scope)}</span>`;
    }
    if (item.required_document && item.required_document !== '不明') {
      metaHtml += `<span class="meta-doc">${escHtml(item.required_document)}</span>`;
    }
    if (item.end_date) {
      const dateStr = item.start_date
        ? `${item.start_date} ~ ${item.end_date}`
        : `截止 ${item.end_date}`;
      metaHtml += `<span class="meta-date">${escHtml(dateStr)}</span>`;
    }
    if (item.source_name) {
      metaHtml += `<span class="meta-source">${escHtml(item.source_name)}</span>`;
    }

    // Discount / products
    let discountHtml = '';
    const discount = item.discount || '';
    const mergedCount = item._merged_count || 1;

    if (mergedCount > 1 && discount.includes('\n')) {
      // Merged item with product list
      const lines = discount.split('\n');
      const header = lines[0]; // "共 N 項優惠："
      const products = lines.slice(1);

      discountHtml = `
        <div class="benefit-products">
          <button class="products-toggle" data-id="${escAttr(item.title)}">
            ${escHtml(header)} ▾
          </button>
          <div class="products-list" id="pl-${hashStr(item.title)}">
            ${products.map(p => renderProductLine(p)).join('')}
          </div>
        </div>`;
    } else if (discount) {
      discountHtml = `<div class="benefit-discount">${escHtml(discount)}</div>`;
    }

    // Reason (for maybe items)
    let reasonHtml = '';
    if (type === 'maybe' && item.reason) {
      reasonHtml = `<div class="benefit-reason">${escHtml(item.reason)}</div>`;
    }

    return `
      <article class="benefit-item">
        <div class="benefit-top">
          <h3 class="benefit-title">${titleHtml}</h3>
          <span class="badge ${badgeClass}">${badgeText}</span>
        </div>
        <div class="benefit-meta">${metaHtml}</div>
        ${discountHtml}
        ${reasonHtml}
      </article>`;
  }

  function renderProductLine(line) {
    // "  • ProductName：Price" → split on ：
    const clean = line.replace(/^\s*•\s*/, '');
    const idx = clean.indexOf('：');
    if (idx > 0) {
      const name = clean.slice(0, idx);
      const price = clean.slice(idx + 1);
      return `<div class="product-line">${escHtml(name)} <span class="product-price">${escHtml(price)}</span></div>`;
    }
    return `<div class="product-line">${escHtml(clean)}</div>`;
  }

  // ── Toggle expand/collapse ─────────────────────────────────
  function bindToggle() {
    document.querySelectorAll('.products-toggle').forEach(btn => {
      btn.addEventListener('click', () => {
        const id = 'pl-' + hashStr(btn.dataset.id);
        const list = document.getElementById(id);
        if (list) {
          list.classList.toggle('open');
          btn.textContent = list.classList.contains('open')
            ? btn.textContent.replace('▾', '▴')
            : btn.textContent.replace('▴', '▾');
        }
      });
    });
  }

  // ── Filter buttons ─────────────────────────────────────────
  document.querySelectorAll('.filter-btn[data-filter]').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.filter-btn[data-filter]').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      activeFilter = btn.dataset.filter;
      render();
    });
  });

  document.querySelectorAll('.filter-btn[data-loc]').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.filter-btn[data-loc]').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      activeLoc = btn.dataset.loc;
      render();
    });
  });

  // ── Helpers ────────────────────────────────────────────────
  function escHtml(s) {
    const el = document.createElement('span');
    el.textContent = s;
    return el.innerHTML;
  }

  function escAttr(s) {
    return s.replace(/&/g,'&amp;').replace(/"/g,'&quot;').replace(/</g,'&lt;');
  }

  function hashStr(s) {
    let h = 0;
    for (let i = 0; i < s.length; i++) {
      h = ((h << 5) - h + s.charCodeAt(i)) | 0;
    }
    return Math.abs(h).toString(36);
  }

  // ── Init ───────────────────────────────────────────────────
  loadData();
})();
