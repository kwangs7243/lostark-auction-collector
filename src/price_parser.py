def extract_price_data(data:dict) -> dict:
    '''
    API 요청결과에서 가격정보를 재가공해 반환한다
    '''
    price_data = {}
    for item in data["Items"]:
        price_data[item["Name"]] = {
            'min_price' : item["CurrentMinPrice"],
            'y_day_avg_price' : item["YDayAvgPrice"],
            'recent_price' : item["RecentPrice"]
        }
    return price_data