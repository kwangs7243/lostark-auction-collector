def extract_price_data(data: dict) -> dict:
    """API 응답에서 아이템 이름과 가격 정보만 골라 계산용 dict로 변환한다."""
    if "Items" not in data:
        raise ValueError("API 응답에 Items가 없습니다.")

    if not data["Items"]:
        raise ValueError("API 응답 Items가 비어 있습니다.")

    price_data = {}

    required_fields = [
        "Name",
        "CurrentMinPrice",
        "YDayAvgPrice",
        "RecentPrice",
    ]

    for item in data["Items"]:
        for field in required_fields:
            if field not in item:
                raise ValueError(f"가격 데이터에 {field} 필드가 없습니다.")

        price_data[item["Name"]] = {
            "최저가": item["CurrentMinPrice"],
            "전일가": item["YDayAvgPrice"],
            "최근가": item["RecentPrice"],
        }

    return price_data
