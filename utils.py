import jwt

detail_base_url = {
    'bunjang': 'https://m.bunjang.co.kr/products/{{PID}}',
    'joongna': 'https://m.joongna.com/product-detail/{{PID}}',
    'hellomarket': 'https://www.hellomarket.com/item/{{PID}}'
}
    
    
def token_to_id(token, secret_key):
    '''유저 토큰과 비밀 키를 받아서 토큰을 아이디로 변환하는 함수 
    
    Args: 
        token (str): 유저 토큰 정보 
        secret_key (str): 비밀 키 값
    
    Returns: 
        str: 유저 아이디
    '''

    token = bytes(token[2:-1].encode('ascii'))
    payload= jwt.decode(token, secret_key, algorithms=['HS256'])
    return payload['ID']


def generate_mypage_response(user_favorites):
    '''유저 즐겨찾기 정보를 받아서 response로 변환하는 함수(deprecated)
    Args: 
        user_favorites (list): 데이터베이스에서 가져온 유저 즐겨찾기 정보 리스트

    Returns:
        dict: 마이페이지 정보가 담긴 dictionary
    '''
    response = {}
    items = []
    for item in user_favorites:
        item_dict = {}
        item_dict['title'] = item['title']
        item_dict['price'] = item['price']
        item_dict['imageUrl'] = item['image_url']
        item_dict['company'] = item['company']
        item_dict['productPageUrl'] = detail_base_url[item['company']].replace('{{PID}}', str(item['pid']))
        items.append(item_dict)
    response['result'] = 'success'
    response['counts'] = len(items)
    response['items'] = items
    return response
    

def generate_product_response(result_dict, user_favorites_pid):
    '''각 사이트별 API를 통해 얻은 결과를 response로 가공하는 함수 
    
    Args: 
        result_dict (dict): 각 사이트별 API를 통해 얻은 필터된 아이템들의 정보와 사이트별 평균가격이 담긴 dictionary
        user_favorites_pid (set): 현재 유저가 좋아요를 누른 상품에 대한 pid 값이 담긴 set
    
    Returns: 
        dict: 상품 정보 요청에 대한 리스폰스 정보가 담긴 dictionary
    '''
    response = {
        'status': 200, 
        'total_average': 0,
        'items': {
            'bunjang':{
                'average':0,
                'percentage':0,
                'counts': 0,
                'items':[{
                    'title': '',
                    'price': 0,
                    'imageUrl': '',
                    'productPageUrl': '',
                    'percentage': 0
                }],
            },
            'joongna':{
                'average':0,
                'percentage':0,
                'counts': 0,
                'items':[{
                    'title': '',
                    'price': 0,
                    'imageUrl': '',
                    'productPageUrl': '',
                    'percentage': 0
                }]
            },
            'hellomarket':{
                'average':0,
                'percentage':0,
                'counts': 0,
                'items':[{
                    'title': '',
                    'price': 0,
                    'imageUrl': '',
                    'productPageUrl': '',
                    'percentage': 0
                }]
            },
        }
    }
    total_average = 0 
    total_count = 0
    for company in result_dict:
        items_list, company_avg = result_dict[company]
        company_count = len(items_list)
        total_average += company_count * company_avg
        total_count += company_count
    total_average = total_average / total_count
    response['total_average'] = total_average

    for company in result_dict:
        items_list, company_avg = result_dict[company]
        company_count = len(items_list)
        response['items'][company]['average'] = company_avg
        response['items'][company]['counts'] = company_count
        company_items = []

        for item in items_list:
            an_item = {}
            an_item['title'] = item[1]
            an_item['imageUrl'] = item[2]
            an_item['price'] = item[0]
            an_item['productPageUrl'] = detail_base_url[company].replace('{{PID}}', str(item[3]))
            an_item['percentage'] = (item[0] - total_average) / total_average * 100 
            an_item['isFavorite'] = True if str(item[3]) in user_favorites_pid else False
            company_items.append(an_item)
        response['items'][company]['items'] = company_items 

        if response['items'][company]['counts'] != 0:
            response['items'][company]['percentage'] = (company_avg - total_average) / total_average * 100 
        else:
            response['items'][company]['percentage'] = 0
            
    return response
