def extract_price_data(data:dict) -> dict:
    '''
    API 요청결과에서 가격정보를 재가공해 반환한다
    '''
    price_data = {}
    for item in data["Items"]:
        price_data[item["Name"]] = {
            '최저가' : item["CurrentMinPrice"],
            '전일가' : item["YDayAvgPrice"],
            '최근가' : item["RecentPrice"]
        }
    return price_data