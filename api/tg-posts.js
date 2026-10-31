// Останні пости відкритого Telegram-каналу для сторінки «Група».
// Читає публічну сторінку t.me/s/<канал> і віддає номери свіжих постів.
// Відповідь кешується на Vercel на 10 хвилин — нові пости з'являються самі.
const CHANNEL = 'wot_boosted_news';
const LIMIT = 10;

module.exports = async (req, res) => {
  try {
    const r = await fetch('https://t.me/s/' + CHANNEL, {
      headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36',
        'Accept-Language': 'uk,en;q=0.8'
      }
    });
    if (!r.ok) throw new Error('telegram ' + r.status);
    const html = await r.text();
    const seen = new Set();
    const posts = [];
    for (const m of html.matchAll(/data-post="([A-Za-z0-9_]+)\/(\d+)"/g)) {
      if (m[1].toLowerCase() !== CHANNEL) continue;
      const key = m[1] + '/' + m[2];
      if (seen.has(key)) continue;
      seen.add(key);
      posts.push({ key, id: Number(m[2]) });
    }
    posts.sort((a, b) => b.id - a.id);
    res.setHeader('Cache-Control', 'public, s-maxage=600, stale-while-revalidate=3600');
    res.status(200).json({ channel: CHANNEL, posts: posts.slice(0, LIMIT).map(p => p.key) });
  } catch (e) {
    res.setHeader('Cache-Control', 'public, s-maxage=60');
    res.status(502).json({ channel: CHANNEL, posts: [], error: 'unavailable' });
  }
};
