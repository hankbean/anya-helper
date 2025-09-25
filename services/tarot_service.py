import random

def get_random_tarot_image_url(imgur_client):
    images = imgur_client.get_album_images("jAqXRhh")#client.get_album_images("l8aRa")
    index = random.randint(0, len(images) - 1)
    url = images[index].link
    return url

def roll_astro_dice():
    starNum = random.randint(0, 11)
    signNum = random.randint(0, 11)
    palaceNum = random.randint(0, 11)
    star = [
        "月亮",
        "水星",
        "金星",
        "太陽",
        "火星",
        "木星",
        "土星",
        "天王星",
        "海王星",
        "冥王星",
        "凱隆星",
        "北交點"
    ]
    sign = [
        "♈白羊",
        "♉金牛",
        "♊雙子",
        "♋巨蟹",
        "♌獅子",
        "♍處女",
        "♎天秤",
        "♏天蝎",
        "♐射手",
        "♑摩羯",
        "♒水瓶",
        "♓雙魚"
    ] 
    palace = [
        "1宮",
        "2宮",
        "3宮",
        "4宮",
        "5宮",
        "6宮",
        "7宮",
        "8宮",
        "9宮",
        "10宮",
        "11宮",
        "12宮"
    ] 
    return star[starNum] + "，" + sign[signNum] + "，" + palace[palaceNum]

def perform_tarot_drawing_logic():
    turn = [
        "正位",
        "逆位"
    ]
    majorArcana = [
        "愚人",
        "魔術師",
        "女教皇",
        "皇后",
        "皇帝",
        "教皇",
        "戀人",
        "戰車",
        "力量",
        "隱者",
        "命運之輪",
        "正義",
        "吊人",
        "死神",
        "節制",
        "惡魔",
        "塔",
        "星星",
        "月亮",
        "太陽",
        "審判",
        "世界"
    ]
    minorArcanaName = [
        "劍",
        "杖",
        "杯",
        "幣"
    ]
    minorArcanaNum = [
        "1",
        "2",
        "3",
        "4",
        "5",
        "6",
        "7",
        "8",
        "9",
        "10",
        "侍從",
        "騎士",
        "皇后",
        "國王"
    ]
    cardList = []
    for item in range(0,8,1):
        ifNum = random.randint(0, 78-1)
        if (ifNum >= (1-1) and ifNum < (22-1)):
            card = turn[random.randint(0, len(turn)-1)] + majorArcana[random.randint(0, len(majorArcana)-1)]
        else:
            card = turn[random.randint(0, len(turn)-1)] + minorArcanaName[random.randint(0, len(minorArcanaName)-1)] +\
                minorArcanaNum[random.randint(0, len(minorArcanaNum)-1)]
        cardList.append(card)
    print("卡牌cardList: ", cardList)
    return cardList