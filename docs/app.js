(() => {
  const DATA_URL = './data.json';

  // Brand images: domain → real photo URL (Unsplash/Wikimedia free-to-use)
  const BRAND_IMAGES = {
    'apple.com':       'https://images.unsplash.com/photo-1517336714731-489689fd1ca8?w=600&h=320&fit=crop',
    'thsrc.com.tw':    'https://images.unsplash.com/photo-1540893830500-2b4117132950?w=600&h=320&fit=crop',
    'ntm.gov.tw':      'https://images.unsplash.com/photo-1566127444979-b3d2b654e3d7?w=600&h=320&fit=crop',
    'mocataipei.org':  'https://images.unsplash.com/photo-1518998053901-5348d3961a04?w=600&h=320&fit=crop',
    'tfam.museum':     'https://images.unsplash.com/photo-1554907984-15263bfd63bd?w=600&h=320&fit=crop',
    'fubonartmuseum':  'https://images.unsplash.com/photo-1536924940846-227afb31e2a5?w=600&h=320&fit=crop',
    'caesarmetro.com': 'https://images.unsplash.com/photo-1414235077428-338989a2e8c0?w=600&h=320&fit=crop',
    'sogo.com.tw':     'https://images.unsplash.com/photo-1555396273-367ea4eb4db5?w=600&h=320&fit=crop',
    'claude-world.com':'https://images.unsplash.com/photo-1461749280684-dccba630e2f6?w=600&h=320&fit=crop',
    'cloud.google.com':'https://images.unsplash.com/photo-1451187580459-43490279c0fa?w=600&h=320&fit=crop',
    'nycu.edu.tw':     'https://images.unsplash.com/photo-1562774053-701939374585?w=600&h=320&fit=crop',
    'arts.nycu.edu.tw':'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=600&h=320&fit=crop',
    'easycard.com.tw': 'https://images.unsplash.com/photo-1570125909232-eb263c188f7e?w=600&h=320&fit=crop',
    'tripadvisor':     'https://images.unsplash.com/photo-1544025162-d76694265947?w=600&h=320&fit=crop',
    'jhujian.com.tw':  'https://images.unsplash.com/photo-1555939594-58d7cb561ad1?w=600&h=320&fit=crop',
  };

  // Category images (fallback)
  const CAT_IMAGES = {
    '展覽': 'https://images.unsplash.com/photo-1518998053901-5348d3961a04?w=600&h=320&fit=crop',
    '軟體': 'https://images.unsplash.com/photo-1461749280684-dccba630e2f6?w=600&h=320&fit=crop',
    '交通': 'https://images.unsplash.com/photo-1540893830500-2b4117132950?w=600&h=320&fit=crop',
    '餐廳': 'https://images.unsplash.com/photo-1414235077428-338989a2e8c0?w=600&h=320&fit=crop',
    '商店': 'https://images.unsplash.com/photo-1441986300917-64674bd600d8?w=600&h=320&fit=crop',
  };

  let allItems = [];
  let activeCat = 'all';
  let activeLoc = 'all';

  async function loadData() {
    try {
      const resp = await fetch(DATA_URL);
      if (!resp.ok) throw new Error(resp.status);
      const data = await resp.json();

      const today = new Date().toISOString().slice(0, 10);
      allItems = (data.items || []).filter(item => {
        if (item.end_date && item.end_date < today) return false;
        if (item.final_result === '不可用') return false;
        return true;
      });

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

  function render() {
    const container = document.getElementById('benefits-list');

    const filtered = allItems.filter(item => {
      if (activeCat === 'NYCU') {
        if (!item.is_nycu_official) return false;
      } else if (activeCat !== 'all' && item.category !== activeCat) {
        return false;
      }
      if (activeLoc !== 'all' && item.location_scope !== activeLoc) return false;
      return true;
    });

    if (filtered.length === 0) {
      container.innerHTML = '<div class="no-results">沒有符合條件的優惠</div>';
      return;
    }

    // Separate NYCU official items to top
    const nycu = filtered.filter(i => i.is_nycu_official);
    const others = filtered.filter(i => !i.is_nycu_official);

    let html = '';

    if (nycu.length > 0 && activeCat !== 'NYCU') {
      html += renderSection('NYCU 專屬優惠', nycu);
    }
    if (nycu.length > 0 && activeCat === 'NYCU') {
      html += renderSection('NYCU 專屬優惠', nycu);
    }
    if (others.length > 0) {
      // Group by category
      const cats = {};
      for (const item of others) {
        const cat = item.category || '其他';
        if (!cats[cat]) cats[cat] = [];
        cats[cat].push(item);
      }
      for (const [cat, items] of Object.entries(cats)) {
        html += renderSection(cat, items);
      }
    }

    container.innerHTML = html;
    bindToggle();
  }

  function renderSection(title, items) {
    const cards = items.map(renderCard).join('');
    return `
      <section class="section">
        <h2 class="section-title">${escHtml(title)}</h2>
        <div class="card-grid">${cards}</div>
      </section>`;
  }

  function getImageUrl(item) {
    const url = item.source_url || '';
    // Check brand images
    for (const [domain, img] of Object.entries(BRAND_IMAGES)) {
      if (url.includes(domain)) return img;
    }
    // Fallback to category
    return CAT_IMAGES[item.category] || null;
  }

  function getFaviconUrl(item) {
    const url = item.source_url || '';
    if (!url) return null;
    try {
      const domain = new URL(url).hostname;
      return `https://www.google.com/s2/favicons?domain=${domain}&sz=64`;
    } catch { return null; }
  }

  function renderCard(item) {
    const title = escHtml(item.title || '');
    const url = item.source_url || '';
    const titleHtml = url
      ? `<a href="${escAttr(url)}" target="_blank" rel="noopener">${title}</a>`
      : title;

    // Image
    const imgUrl = getImageUrl(item);
    const favicon = getFaviconUrl(item);
    let imgHtml;
    if (imgUrl) {
      imgHtml = `<img class="card-img" src="${escAttr(imgUrl)}" alt="${title}" loading="lazy" onerror="this.style.display='none'">`;
    } else {
      const brandName = escHtml(item.source_name || item.title || '');
      imgHtml = `<div class="card-img-placeholder">
        ${favicon ? `<img class="card-favicon" src="${escAttr(favicon)}" alt="" onerror="this.style.display='none'">` : ''}
        <span class="card-brand-text">${brandName}</span>
      </div>`;
    }

    // Tags
    let tagsHtml = '';
    if (item.is_nycu_official) {
      tagsHtml += '<span class="tag tag-nycu">NYCU</span>';
    }
    if (item.location_scope && item.location_scope !== '不明') {
      tagsHtml += `<span class="tag tag-loc">${escHtml(item.location_scope)}</span>`;
    }
    if (item.required_document && item.required_document !== '不明') {
      tagsHtml += `<span class="tag">${escHtml(item.required_document)}</span>`;
    }

    // Discount
    let discountHtml = '';
    const discount = item.discount || '';
    const mergedCount = item._merged_count || 1;

    if (mergedCount > 1 && discount.includes('\n')) {
      const lines = discount.split('\n');
      const header = lines[0];
      const products = lines.slice(1);
      discountHtml = `
        <div class="card-discount">
          <button class="products-toggle" data-id="${escAttr(item.title)}">
            ${escHtml(header)} ▾
          </button>
          <div class="products-list" id="pl-${hashStr(item.title)}">
            ${products.map(renderProductLine).join('')}
          </div>
        </div>`;
    } else if (discount) {
      discountHtml = `<div class="card-discount">${escHtml(discount)}</div>`;
    }

    // Date
    let dateHtml = '';
    if (item.end_date) {
      const dateStr = item.start_date
        ? `${item.start_date} ~ ${item.end_date}`
        : `截止 ${item.end_date}`;
      dateHtml = `<div class="card-date">${escHtml(dateStr)}</div>`;
    }

    return `
      <article class="card">
        ${imgHtml}
        <div class="card-body">
          <h3 class="card-title">${titleHtml}</h3>
          <div class="card-tags">${tagsHtml}</div>
          ${discountHtml}
          ${dateHtml}
        </div>
      </article>`;
  }

  function renderProductLine(line) {
    const clean = line.replace(/^\s*•\s*/, '');
    const idx = clean.indexOf('：');
    if (idx > 0) {
      const name = clean.slice(0, idx);
      const price = clean.slice(idx + 1);
      return `<div class="product-line">${escHtml(name)} <span class="product-price">${escHtml(price)}</span></div>`;
    }
    return `<div class="product-line">${escHtml(clean)}</div>`;
  }

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

  // Filter: category
  document.querySelectorAll('.filter-btn[data-cat]').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.filter-btn[data-cat]').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      activeCat = btn.dataset.cat;
      render();
    });
  });

  // Filter: location
  document.querySelectorAll('.filter-btn[data-loc]').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.filter-btn[data-loc]').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      activeLoc = btn.dataset.loc;
      render();
    });
  });

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

  loadData();
})();
