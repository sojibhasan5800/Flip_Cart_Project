from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from .models import Product


def get_similar_products(product_id, top_n=5):

    vectorizer = TfidfVectorizer(stop_words="english")
    product_description = Product.objects.all().values_list("description",flat=True)
    tfid_matrix = vectorizer.fit_transform(product_description)
    target_product = Product.objects.get(id=product_id)
    all_product = list(Product.objects.all())
    target_index = all_product.index(target_product)
    cosine_sim = cosine_similarity(tfid_matrix[target_index],tfid_matrix).flatten()
    similar_index =cosine_sim.argsort()[-top_n-1:-1][::-1]
    similar_index = [i for i in similar_index if i != target_index]
    similar_products=[]
    for idx in similar_index:
        similar_products.append(all_product[idx])
    
    return similar_products

   