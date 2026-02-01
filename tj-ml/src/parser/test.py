
# category_name = category_filename.removesuffix('.xml').removeprefix('sitemap-flow-').removeprefix('sitemap-')
# print(category_name)
# print(category_filename)

from article_parser import parse_category, prepare_chunks_from_category

category_filename = "sitemap-flow-charity.xml"
# category_name = category_filename.removesuffix('.xml').removeprefix('sitemap-flow-').removeprefix('sitemap-')
#
# data = get_category_urls_with_lastmod(category_filename)[1]
# url = data['url']
# last_mod = data['last_mod']
# print(parse_article(url, last_mod, category_name))

result = prepare_chunks_from_category(category_filename, 1)
print(result)