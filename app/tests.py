from django.test import TestCase
from django.urls import reverse

# Create your tests here.

class ProductNavigationTests(TestCase):
    def test_product_detail_route_available(self):
        response = self.client.get(reverse('product-detail'))
        self.assertEqual(response.status_code, 200)

    def test_category_page_includes_detail_destination(self):
        response = self.client.get(reverse('category-all'))
        self.assertContains(response, f'data-product-detail-url="{reverse("product-detail")}"')

    def test_category_page_uses_existing_static_asset_paths(self):
        response = self.client.get(reverse('category-all'))
        self.assertContains(response, 'href="/static/app/css/style.css"')
        self.assertContains(response, 'src="/static/app/js/main.js"')

    def test_brand_pages_available(self):
        list_response = self.client.get(reverse('brand-list'))
        self.assertEqual(list_response.status_code, 200)
        detail_response = self.client.get(reverse('brand-detail', kwargs={'slug': 'dior'}))
        self.assertEqual(detail_response.status_code, 200)

    def test_blog_pages_available(self):
        blog_response = self.client.get(reverse('blog-list'))
        self.assertEqual(blog_response.status_code, 200)
        article_response = self.client.get(
            reverse('article-detail', kwargs={'slug': 'chon-mui-huong-cho-moi-thoi-tiet'})
        )
        self.assertEqual(article_response.status_code, 200)

    def test_contact_and_cart_pages_available(self):
        contact_response = self.client.get(reverse('contact-page'))
        self.assertEqual(contact_response.status_code, 200)
        cart_response = self.client.get(reverse('cart-page'))
        self.assertEqual(cart_response.status_code, 200)