#!/usr/bin/env python3
"""
Article Creation Utility
Creates new articles as JSON files in the articles directory
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Optional
import argparse
import re


class ArticleCreator:
    """Creates and manages article JSON files"""

    def __init__(self, base_dir: Path):
        """
        Initialize ArticleCreator

        Args:
            base_dir: Base directory for the blog
        """
        self.base_dir = base_dir
        self.articles_dir = base_dir / 'articles'
        self.images_dir = base_dir / 'images'

        # Create directories if they don't exist
        self.articles_dir.mkdir(parents=True, exist_ok=True)
        self.images_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def generate_article_id(title: str) -> str:
        """
        Generate article ID from title and date

        Args:
            title: Article title

        Returns:
            Article ID in format: YYYY-MM-DD-{slug}
        """
        date_str = datetime.now().strftime('%Y-%m-%d')
        # Convert title to slug
        slug = re.sub(r'[^\w\s-]', '', title.lower())
        slug = re.sub(r'[\s]+', '-', slug)
        slug = re.sub(r'-+', '-', slug)
        slug = slug.strip('-')[:50]  # Limit to 50 chars

        return f"{date_str}-{slug}"

    def create_article(
        self,
        title: str,
        content: str,
        excerpt: str,
        keywords: List[str],
        category: str,
        featured_image: Optional[str] = None,
        status: str = 'draft'
    ) -> Optional[str]:
        """
        Create a new article

        Args:
            title: Article title
            content: HTML content
            excerpt: Article summary
            keywords: List of keywords/tags
            category: Article category
            featured_image: Relative path to featured image (e.g., 'images/photo.png')
            status: Article status ('draft' or 'ready')

        Returns:
            Article file path, or None on failure
        """
        # Validate inputs
        if not title or not content:
            print("â Error: Title and content are required")
            return None

        if status not in ['draft', 'ready', 'published']:
            print(f"â Error: Invalid status '{status}'. Must be 'draft', 'ready', or 'published'")
            return None

        if featured_image and not featured_image.startswith('images/'):
            featured_image = f"images/{featured_image}"

        # Generate article ID
        article_id = self.generate_article_id(title)

        # Create article object
        article = {
            'id': article_id,
            'title': title,
            'content': content,
            'excerpt': excerpt if excerpt else content[:200],
            'keywords': keywords if keywords else [],
            'category': category if category else 'Uncategorized',
            'featured_image': featured_image,
            'status': status,
            'created_at': datetime.now().isoformat(),
            'published_at': None,
            'wp_post_id': None,
            'wp_post_url': None
        }

        # Save article
        article_path = self.articles_dir / f"{article_id}.json"

        # Check if article already exists
        if article_path.exists():
            print(f"â Error: Article already exists: {article_path.name}")
            return None

        try:
            with open(article_path, 'w', encoding='utf-8') as f:
                json.dump(article, f, ensure_ascii=False, indent=2)

            print(f"â Article created: {article_path.name}")
            print(f"   Title: {title}")
            print(f"   Status: {status}")
            print(f"   Path: {article_path}")

            return str(article_path)

        except Exception as e:
            print(f"â Error saving article: {e}")
            return None

    def list_articles(self) -> None:
        """List all articles by status"""
        if not self.articles_dir.exists():
            print("No articles directory found")
            return

        articles_by_status = {
            'draft': [],
            'ready': [],
            'published': []
        }

        for article_file in self.articles_dir.glob('*.json'):
            try:
                with open(article_file, 'r', encoding='utf-8') as f:
                    article = json.load(f)
                    status = article.get('status', 'unknown')
                    if status in articles_by_status:
                        articles_by_status[status].append(article)
            except Exception as e:
                print(f"â ï¸  Warning: Error reading {article_file}: {e}")

        # Print articles by status
        for status in ['draft', 'ready', 'published']:
            articles = articles_by_status[status]
            if articles:
                print(f"\n{status.upper()} ({len(articles)})")
                print("-" * 70)
                for article in articles:
                    print(f"  â¢ {article['id']}")
                    print(f"    Title: {article['title']}")
                    if article.get('wp_post_id'):
                        print(f"    WordPress ID: {article['wp_post_id']}")


def main():
    """Main entry point"""

    parser = argparse.ArgumentParser(
        description='WordPress Article Manager',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Create a draft article
  %(prog)s create --title "My Article" --content "<p>Content</p>" \\
    --excerpt "Summary" --category "Technology"

  # Create an article ready for publishing
  %(prog)s create --title "Post Now" --content "<p>Content</p>" \\
    --status ready --featured-image "photo.png"

  # List all articles
  %(prog)s list
        """
    )

    parser.add_argument(
        'command',
        choices=['create', 'list'],
        help='Command to execute'
    )

    parser.add_argument(
        '--title',
        help='Article title'
    )

    parser.add_argument(
        '--content',
        help='HTML content'
    )

    parser.add_argument(
        '--excerpt',
        default='',
        help='Article excerpt/summary'
    )

    parser.add_argument(
        '--keywords',
        default='',
        help='Keywords (comma-separated)'
    )

    parser.add_argument(
        '--category',
        default='Uncategorized',
        help='Article category'
    )

    parser.add_argument(
        '--featured-image',
        help='Featured image path (relative to images/ directory)'
    )

    parser.add_argument(
        '--status',
        choices=['draft', 'ready'],
        default='draft',
        help='Article status'
    )

    parser.add_argument(
        '--base-dir',
        type=Path,
        default=Path(__file__).parent.parent,
        help='Base directory for blog files'
    )

    args = parser.parse_args()

    creator = ArticleCreator(args.base_dir)

    if args.command == 'create':
        # Validate required arguments
        if not args.title or not args.content:
            print("â Error: --title and --content are required")
            parser.print_help()
            sys.exit(1)

        # Parse keywords
        keywords = [k.strip() for k in args.keywords.split(',') if k.strip()]

        # Create article
        result = creator.create_article(
            title=args.title,
            content=args.content,
            excerpt=args.excerpt,
            keywords=keywords,
            category=args.category,
            featured_image=args.featured_image,
            status=args.status
        )

        if not result:
            sys.exit(1)

    elif args.command == 'list':
        creator.list_articles()


if __name__ == '__main__':
    main()
