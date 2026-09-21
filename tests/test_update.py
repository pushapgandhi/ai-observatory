import datetime as dt
import json
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import update

class UpdateTests(unittest.TestCase):
    def test_rss_sanitizes_and_rejects_bad_dates_and_links(self):
        xml='''<rss><channel><item><title>Test model</title><link>https://openai.com/index/test/?utm_source=x</link><pubDate>Mon, 01 Jun 2026 12:00:00 GMT</pubDate><description>&lt;p&gt;Safe &amp;amp; readable&lt;/p&gt;</description></item><item><title>Future</title><link>https://openai.com/future</link><pubDate>Mon, 01 Jun 2099 12:00:00 GMT</pubDate></item><item><title>Bad</title><link>javascript:alert(1)</link><pubDate>Mon, 01 Jun 2026 12:00:00 GMT</pubDate></item></channel></rss>'''
        rows=update.parse_feed(xml,'OpenAI','News')
        self.assertEqual(len(rows),1);self.assertEqual(rows[0]['url'],'https://openai.com/index/test');self.assertNotIn('<p>',rows[0]['summary'])
    def test_atom_uses_publication_date_and_deduplicates_versions(self):
        xml='''<feed xmlns="http://www.w3.org/2005/Atom"><entry><title>Paper</title><published>2025-01-03T12:00:00Z</published><updated>2026-01-03T12:00:00Z</updated><id>http://arxiv.org/abs/2501.00001v2</id><summary>New results.</summary></entry></feed>'''
        row=update.parse_feed(xml,'arXiv','Research')[0]
        self.assertEqual(row['date'],'2025-01-03');self.assertEqual(row['url'],'https://arxiv.org/abs/2501.00001')
    def test_curated_records_survive_refresh_and_merge_is_idempotent(self):
        curated=dict(date='2022-11-30',url='https://openai.com/index/chatgpt/',title='Curated',automated=False)
        incoming=dict(curated,url=curated['url'].rstrip('/'),title='Feed title',automated=True)
        result=update.merge_entries([curated],[incoming])
        self.assertEqual(result,[curated]);self.assertEqual(update.merge_entries(result,[incoming]),result)
    def test_rejects_invalid_feed(self):
        with self.assertRaises(ValueError):update.parse_feed('<html/>','Publisher','News')
    def test_archive_integrity(self):
        data=json.loads(update.DATA.read_text('utf-8'));urls=set();years=set()
        for row in data['entries']:
            for field in ('date','type','publisher','title','summary','url'):self.assertTrue(row[field])
            date=dt.date.fromisoformat(row['date']);self.assertGreaterEqual(date,dt.date(2021,1,1));self.assertLessEqual(date,update.TODAY)
            key=row['url'].rstrip('/');self.assertNotIn(key,urls);urls.add(key);years.add(date.year)
            self.assertTrue(row['url'].startswith('https://'));self.assertIn(row['type'],('Research','Models','News'))
        self.assertTrue(set(range(2021,update.TODAY.year+1)).issubset(years))

if __name__=='__main__':unittest.main()
