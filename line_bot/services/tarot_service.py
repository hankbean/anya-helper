import random
import textwrap

def get_random_tarot_image_url(imgur_client):
    images = imgur_client.get_album_images("jAqXRhh")#client.get_album_images("l8aRa")
    index = random.randint(0, len(images) - 1)
    url = images[index].link
    return url

def roll_astro_dice():
    star_num = random.randint(0, 10)
    sign_num = random.randint(0, 11)
    palace_num = random.randint(0, 11)
    asc_degree = random.randint(0, 359)
    star_degree = random.randint(0, 359)
    STAR = [
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
        "北交點"
    ]
    SIGN = [
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
    PALACE = [
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
    asc_index =  (asc_degree // 30) % 12
    sign_index = (star_degree // 30) % 12
    angular_distance = (star_degree - asc_degree + 360) % 360
    palace_index = angular_distance // 30
    content = f"""
        {random.choice(STAR)}，{SIGN[sign_index]}，{PALACE[palace_index]}
        備註: 上升星座 (ASC) 為{SIGN[asc_index]}
        
        以下為測試資料不需要理會
        ASC度數={str(asc_degree)}
        星體度數={str(star_degree)}"""
    return textwrap.dedent(content).strip()

def roll_astro_dice_plus():
    ascNum = random.randint(0, 11)
    MoonNum = random.randint(0, 11)
    SunNum = random.randint(0, 11)
    qNum = random.randint(0, 2)
    wNum = random.randint(0, 4)
    eNum = random.randint(0, 11)
    rNum = random.randint(0, 11)
    tNum = random.randint(0, 11)
    yNum = random.randint(0, 11)
    uNum = random.randint(0, 11)
    iNum = random.randint(0, 11)
    jNum = random.randint(0, 11)
    SIGN = [
        "白羊",
        "金牛",
        "雙子",
        "巨蟹",
        "獅子",
        "處女",
        "天秤",
        "天蝎",
        "射手",
        "摩羯",
        "水瓶",
        "雙魚"
    ] 
    content = f"""
        占星卜卦盤    ASC:   {SIGN[ascNum]}
        月亮: {SIGN[(ascNum-1+MoonNum+1)%12]} {MoonNum+1}宮    太陽: {SIGN[ascNum-1+SunNum+1]} {SunNum+1}宮
        水星: {SIGN[(ascNum-1+SunNum+1+qNum-1)%12]} {SunNum+1+qNum-1}宮    金星: {SIGN[(ascNum-1+SunNum+1+wNum-2)%12]} {SunNum+1+wNum-2}宮
        火星: {SIGN[(ascNum-1+eNum+1)%12]} {eNum+1}宮    木星: {SIGN[(ascNum-1+rNum+1)%12]} {rNum+1}宮
        土星: {SIGN[(ascNum-1+tNum+1)%12]} {tNum+1}宮    天王星: {SIGN[(ascNum-1+yNum+1)%12]} {yNum+1}宮
        海王星: {SIGN[(ascNum-1+uNum+1)%12]} {uNum+1}宮    冥王星: {SIGN[(ascNum-1+iNum+1)%12]} {iNum+1}宮
        北交點: {SIGN[(ascNum-1+jNum+1)%12]} {jNum+1}宮    南交點: {SIGN[(ascNum-1+(jNum+1+6)%12)%12]} {(jNum+1+6)%12}宮"""
    return textwrap.dedent(content).strip()#加上星座

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