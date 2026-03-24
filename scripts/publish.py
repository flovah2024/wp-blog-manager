#!/usr/bin/env python3
"""
WordPress Blog Auto-Publisher
Automatically publishes articles with images to WordPress.com via REST API
"""
import os, json, sys, requests
from pathlib import Path
from datetime import datetime

class WordPressPublisher:
    def __init__(self, site_url, api_base, token):
        self.api_base = api_base
        self.session = requests.Session()
        self.session.headers.update({'Authorization': f'Bearer {token}', 'User-Agent': 'WP-Blog-Manager/1.0'})

    def upload_image(self, path):
        if not path.exists(): return None
        mime = {'.jpg':'image/jpeg','.png':'image/png','.gif':'image/gif','.webp':'image/webp'}.get(path.suffix.lower(),'application/octet-stream')
        with open(path,'rb') as f:
            r = self.session.post(f"{self.api_base}/media", files={'file':(path.name,f,mime)})
        return r.json() if r.status_code in [200,201] else None

    def create_post(self, article):
        data = {'title':article.get('title',''),'content':article.get('content',''),'excerpt':article.get('excerpt',''),'status':'publish','comment_status':'open'}
        if article.get('featured_image_id'): data['featured_media']=article['featured_image_id']
        r = self.session.post(f"{self.api_base}/posts", json=data)
        return r.json() if r.status_code in [200,201] else None

class ArticleManager:
    def __init__(self, base_dir, config):
        self.base_dir, self.config = base_dir, config
        self.articles_dir = base_dir / 'articles'
        self.images_dir = base_dir / 'images'
        self.articles_dir.mkdir(parents=True, exist_ok=True)
        self.images_dir.mkdir(parents=True, exist_ok=True)

    def find_ready(self):
        result = []
        for f in self.articles_dir.glob('*.json'):
            try:
                with open(f,'r',encoding='utf-8') as fp:
                    if json.load(fp).get('status')=='ready': result.append(f)
            except: pass
        return sorted(result)

    def load(self, p):
        try:
            with open(p,'r',encoding='utf-8') as f: return json.load(f)
        except: return None

    def save(self, p, a):
        with open(p,'w',encoding='utf-8') as f: json.dump(a,f,ensure_ascii=False,indent=2)

    def update_published(self, p, a, wp):
        a.update({'status':'published','published_at':datetime.now().isoformat(),'wp_post_id':wp.get('id'),'wp_post_url':wp.get('link')})
        self.save(p, a)

def main():
    token = os.getenv('WP_ACCESS_TOKEN')
    if not token: print("Error: WP_ACCESS_TOKEN not set"); sys.exit(1)
    script_dir = Path(__file__).parent
    with open(script_dir.parent / 'config.json','r') as f: config = json.load(f)
    mgr = ArticleManager(script_dir.parent, config)
    wp = config.get('wordpress',{})
    pub = WordPressPublisher(wp.get('site'), wp.get('api_base'), token)
    ready = mgr.find_ready()
    if not ready: print("No articles ready"); return
    print(f"Found {len(ready)} article(s)")
    for ap in ready:
        a = mgr.load(ap)
        if not a: continue
        print(f"Publishing: {a.get('title')}")
        if a.get('featured_image'):
            m = pub.upload_image(mgr.images_dir / a['featured_image'])
            if m: a['featured_image_id'] = m.get('id')
        post = pub.create_post(a)
        if post: mgr.update_published(ap, a, post); print(f"Done: {post.get('id')}")
        else: print("Failed")

if __name__ == '__main__': main()
