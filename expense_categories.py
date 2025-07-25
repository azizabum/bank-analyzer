# -*- coding: utf-8 -*-
"""
نظام التصنيفات المحسن - تصنيف على مستويين (رئيسي وفرعي)
مع تحسينات في دقة التصنيف ومعالجة النصوص العربية
"""

import re
import unicodedata
from typing import Tuple, Optional, List, Dict, Set

# قاموس التصنيفات الموسع والشامل
EXPENSE_CATEGORIES = {
    "🔄 تحويلات مالية": {
        "تحويل داخلي/خارجي": [
            "حوالة فورية", "تحويل داخلي", "تحويل فوري", "تحويل الى الاهل والاصدقاء",
            "BEN ID: ﺗﺤﻮﻳﻞ ﺩﺍﺧﻠﻲ ﺻﺎﺩﺭ ﺗﺤﻮﻳﻞ ﺍﻟﻰ ﺍﻻﻫﻞ ﻭﺍﻻﺻﺪﻗﺎﺀ",
            "تحويل داخلي صادر", "تحويل إلى الأهل والأصدقاء",
            "حوالة", "transfer", "تحويل صادر", "تحويل وارد", "حوالة محلية", "BEN ID: ﺗﺤﻮﻳﻞ ﺩﺍﺧﻠﻲ ﺻﺎﺩﺭ",
            "تحويل لأفراد", "تحويل الى الاهل", "حوالة فورية محلية", "swift",
            "تحويل دولي", "western union", "ويسترن يونيون",
            "internal transfer", "outgoing transfer", "incoming transfer", "family transfer",
            "ﻣﺒﻠﻎ ﺍﻟﻤﺪﺭﺳﻪﺗﺤﻮﻳﻞ ﺩﺍﺧﻠﻲ ﺻﺎﺩﺭ ﺗﺤﻮﻳﻞ ﺍﻟﻰ ﺍﻻﻫﻞ ﻭﺍﻻﺻﺪﻗﺎﺀ",
            "instant transfer", "remittance", "wire transfer", "international transfer",
            "حوالة فورية محلية صادرة", "تحويل للأفراد", "BENBK:", "AL RAJHI BANK",
            "AL INMA BANK", "THE SAUDI NATIONAL BANK", "SANCBKNCBK",
            "الأسرة أو الأصدقا", "تحويل لأفراد", "حوالة فورية صادرة",
            "SAUDI ARABIA", "محمد بن سلطان", "شركة وهج العمارة", 
            "أحلام بلال دباب", "ايمن ابوملحه", "MOHSEN MOHAMED ALI",
            "BEN ID:", "internal outgoing", "family friends transfer", "الى الاهل والاصدقاء",
            "BEN ID تحويل داخلي صادر", "تحويل داخلي صادر BEN ID"
        ],
        "ﺳﺤﺐ ﻧﻘﺪﻱ": ["ﺳﺤﺐ ﻧﻘﺪﻱ"],
        "تحويل لمحافظ": [
            "STC Pay", "stc pay", "stcpay", "اس تي سي باي",
            "D360", "د360", "دي360",
            "Barq", "برق", "بارق",
            "Urpay", "يور باي", "اور باي",
            "Mada Pay", "مدى باي", "madapay",
            "wallet transfer", "محفظة إلكترونية", "digital wallet"
        ],
        "تمويل وسداد": [
            "تمويل", "قرض", "سداد", "تقسيط", "قسط", "loan", "mortgage",
            "تمويل عقاري", "تمويل شخصي", "تمويل سيارة", "سداد مديونية",
            "ﺧﺼﻢ ﻗﺴﻂ ﻗﺮﺽ ﻋﻘﺎﺭﻱ", "خصم قسط قرض عقاري", "خصم قسط تمويل تأجيري",
            "ﺧﺼﻢ ﻗﺴﻂ ﺗﻤﻮﻳﻞ ﺗﺄﺟﻴﺮﻱ", "قسط عقاري", "قسط تأجيري", "قرض عقاري", "قسط قرض",
            "TABBY", "تابي", "TAMARA", "تمارا", "TAMMARA",
            "installment", "financing", "payment plan", "credit", "debt payment",
            "بنك التسليف", "صندوق التنمية", "سكني", "sakani",
            "leasing finance", "real estate loan", "personal loan installment",
            "installment deduction", "mortgage installment", "سداد قسط",
            "مدفوعات سداد", "مدفوعات سداد مخالفات", "مخالفات مرورية", "سداد مرور",
            "ﻣﺪﻓﻮﻋﺎﺕ ﺳﺪﺍﺩ 002-ﺍﻟﺸﺮﻛﺔ ﺍﻟﺴﻌﻮﺩﻳﺔ ﻟﻠﻜﻬﺮﺑﺎﺀ-",
            "ﻣﺪﻓﻮﻋﺎﺕ ﺳﺪﺍﺩ 044-ﺯﻳﻦ-", "ﻣﺪﻓﻮﻋﺎﺕ ﺳﺪﺍﺩ 090-ﺧﺪﻣﺎﺕ ﺍﻟﻤﻘﻴﻤﻴﻦ-",
            "ﻣﺪﻓﻮﻋﺎﺕ ﺳﺪﺍﺩ 093-ﺍﻟﻤﺨﺎﻟﻔﺎﺕ ﺍﻟﻤﺮﻭﺭﻳﺔ-",
            "090-خدمات المقيمين", "سداد خدمات المقيمين", "خدمات المقيمين",
            "093-المخالفات المرورية", "002-الشركة السعودية للكهرباء", "044-زين",
            "مدفوعات سداد", "090-خدمات المقيمين", "مدفوعات سداد-090"
        ]
    },
    
"🍽️ مطاعم ومقاهي": {
        "وجبات سريعة": [
            # الماركات العالمية
            "ماكدونالدز", "mcdonalds", "mcdonald's", "مكدونالز",
            "برجر كنج", "burger king", "burgerking", "بيرجر كنج",
            "كنتاكي", "kfc", "kentucky", "كي اف سي",
            "هرفي", "herfy", "هيرفي",
            "البيك", "albaik", "al baik", "بيك",
            "كودو", "kudu", "كودة", "KR64", "كودو KR64",
            "صب واي", "subway", "سبواي",
            "دومينوز", "dominos", "domino's", "دومينو",
            "بيتزا هت", "pizza hut", "pizzahut", "بيتزا هات",
            "بابا جونز", "papa johns", "papa john's", "بابا جون",
            "هارديز", "hardees", "hardee's", "هارديس",
            "تكساس", "texas", "تكساس تشيكن",
            "شاورمر", "shawarmer", "شورمر",
            "بنكو", "bunco", "بانكو",
            "ليتل سيزر", "little caesar", "ليتل سيزار",
            "فايف جايز", "five guys", "فايف غايز",
            "شيك شاك", "shake shack", "شيك شاك",
            "الطازج", "al tazaj", "tazaj", "الدجاج الطازج",
            "مطعم فاخر", "fine dining", "luxury restaurant",
            "نوبو", "nobu", "nobu riyadh",
            "كازا باستا", "casa pasta",
            "ماربل", "marble steakhouse",
            "كورو", "kuuru", "kuuru seafood",
            "لانش روم", "lunch room",
            "أسيب", "aseeb", "aseeb najdi",
            "السنبوك", "al sanbouk", "sanbouk seafood",
            "لوسين", "lusin", "lusin armenian",
            "دارين", "darin", "darin seafood",
            "مطعم راقي", "upscale restaurant", "مطعم فخم"
            "كوبر شندني", "copper chandni", "copper shandni",
            "مطعم هندي", "indian restaurant", "hindi restaurant",
            "جامبو الصيني", "jumbo chinese", "jambo chinese",
            "مطعم صيني", "chinese restaurant", "chinese food",
            "البيت التايلندي", "thai house", "thai restaurant",
            "البيت الإيطالي", "italian house", "al bayt al itali",
            "مطعم إيطالي", "italian restaurant", "italian food",
            "السرايا التركي", "al saraya al turki", "saraya turki",
            "مطعم تركي", "turkish restaurant", "turkish food",
            "مطعم لبناني", "lebanese restaurant", "lebanese food",
            "مطعم شامي", "shami restaurant", "levantine food"
            "البيك", "albaik", "al baik", "بيك الدجاج",
            "الرومانسية", "al romansiah", "romansiah", "مطعم الرومانسية",
            "كودو", "kudu", "كودة", "الكودو",
            "الطازج", "al tazaj", "tazaj", "مطعم الطازج",
            "الناضج", "al nadhej", "nadhej", "مطعم الناضج",
            "الصاج الريفي", "al saj al rifi", "saj rifi", "صاج ريفي",
            "عمو حمزة", "amo hamza", "uncle hamza", "عمو حمزه",
            "المجلس الخليجي", "al majlis al khaleeji", "khaleeji majlis",
            "السرايا التركي", "al saraya al turki", "saraya turki",
            "اوشال", "oushal", "أوشال",
            "أزن قريل", "azn grill", "azn qrill",
            "برقر بوتيك", "burger boutique", "burger botique",
            "برغرايزر", "burgerizer", "برجرايزر",
            "ابل بيز", "apple bees", "applebees",
            "برقر فيول", "burger fuel", "burger fyul",
             "الرومانسية", "al romansiah", "romansiah",
            "الطازج", "al tazaj", "tazaj",
            "الناضج", "al nadhej", "nadhej",
            "الصاج الريفي", "al saj al rifi", "saj rifi",
            "المجلس الخليجي", "al majlis al khaleeji",
            "عمو حمزة", "amo hamza", "uncle hamza",
            "مطعم شعبي", "popular restaurant", "traditional restaurant",
            "كباب الملك", "kabab al malik", "king kabab",
            "بيت الكبسة", "kabsa house", "kabsa home",
            "مندي", "mandi", "مندي دجاج", "مندي لحم",
            "كبسة", "kabsa", "kabsah",
            "مظبي", "mazhbi", "مضغوط",
            "حنيذ", "hanith", "حنيذ مله",
            "مشاوي", "mashawi", "grilled meat",
            "ذبائح", "zabayeh", "fresh meat"
            "دارين", "darin", "darin seafood",
            "كورو", "kuuru", "kuuru seafood",
            "السنبوك", "al sanbouk", "sanbouk",
            "مطعم بحري", "seafood restaurant", "sea food",
            "أسماك", "fish", "فيش",
            "جمبري", "shrimp", "prawns",
            "سمك", "samak", "fish restaurant"
            "مطعم", "restaurant", "مشويات", "كباب", "مندي", "برياني",
            "مطبخ", "kitchen", "شعبي", "تراثي", "أصيل",
            "البيت التايلندي", "thai house", "Mtam Albyt Alta", "مطعم البيت التا",
            "بيتوتي", "baytoti", "بايتوتي",
            "شيز", "chefz", "تشيفز", "شيفز",
            "ماما نورة", "mama noura", "mama nora", "ماما نوره",
            "DURMA", "دورما", "دوريما",
            "kirk najma altr", "كرك نجمة الطريق", "نجمة الطريق",
            "elite food", "food and", "نخبة الغذاء", "food elite",
            "elite food and", "نخبة", "الايت فود",
            "مشويات السنديان", "alsendyan grillﻣﻄﻌﻢ ﻣﺸﻮﻳﺎﺕ ﺍﻟﺲ", "sendyan grill", "السنديان",
            "طيف الضيافه", "dyafah al teef", "al teef", "teef al dyafah",
            "سطل", "sattel", "sattel for fast", "ساتل",
            "كباب الملك", "kabab al malik", "king kabab",
            "ريدان", "redan", "ريدآن",
            "مطعم الصخر", "rock restaurant", "al sakhr",
            "قصر الأوراق", "leaves palace", "awraq palace",
            "بيت الكبسة", "kabsa house", "كبسة هاوس",
            "JAZEA", "جزيرة", "الجزيرة",
            "نوبو", "nobu", "nobu riyadh",
            "كازا باستا", "casa pasta", "casa basta",
            "ماربل", "marble", "marble restaurant",
            "كورو", "kuuru", "kuuru restaurant", 
            "لانش روم", "lunch room", "lunch room riyadh",
            "أسيب", "aseeb", "aseeb restaurant",
            "السنبوك", "al sanbouk", "sanbouk",
            "لوسين", "lusin", "lusin restaurant",
            "دارين", "darin", "darin seafood",
            "كوبر شندني", "copper chandni", "copper shandni",
            "جامبو الصيني", "jumbo chinese", "jambo chinese",
            "البيت الإيطالي", "italian house", "al bayt al itali",
            "فطور", "breakfast", "غداء", "lunch", "عشاء", "dinner",
            "بوفيه", "buffet", "بوفية", "bofyah khlyt al", "بوفية خلية الرا",
            "الماكولات", "food express", "express food",
            "بوابة مراق", "miraqe gateway", "gateway miraqe",
            "AYA MALL BINDAW", "bindaw mall aya", "aya mall bindaw", "mall bindaw",
            "AYA MALL BINDAWﺑﻦ ﺩﺍﻭﻭﺩ ﺁﻳﺎ ﻣﻮ", "بن داوود آيا مو",
            "pickup burger", "بك آب برجر", "pickup برجر",
            "jadt alghetha", "جادة الغذا", "جادة الغذاء", "جاده الغذاء",
            "شركة جادة الغذ", "jadt", "الغذا", "غذاء", "alghetha",
            "جادت الغذاء", "جادة", "jadah food", "جادة فود",
            "jadt food", "شركة جادة", "jadah alghetha",
            "jonandvinnys", "jon and vinnys", "جون اند فينيز", "jon vinnys",
            "jon & vinnys", "جون آند فينيز", "jon and vinny's", "jonvinnys",
            "جون وفينيز", "jon vinny", "vinnys", "فينيز", "جون فينيز",
            "jonandvinnysqlu", "jon&vinnys", "j&v", "جي اند في",
            "sultan delight", "سلطان ديلايت", "سلطان دي لايت", "sultan dlight",
            "سلطان ديلايت بر", "sultan delight burger", "سلطان برجر",
            "sultan burger", "ديلايت برجر", "delight burger", "سلطان دلايت",
            "sultandelight", "sultan d light", "سلطان دي لايت برجر",
            "corn of happine", "ذرة السعاد", "ذرة السعادة", "corn happiness",
            "كورن اوف", "corn of", "شركة ذرة", "ذره السعاده",
            "corn happy", "كورن هابينس", "ذرة", "corn", "السعادة",
            "cornofhappine", "ذرة هابي", "happy corn", "كورن السعادة",
            "alakl almufadha", "الاكل المفضل", "الأكل المفضل", "اكل مفضل",
            "almufadha", "المفضل", "alakl", "الاكل", "favorite food",
            "مطعم الأكل المفضل", "المأكولات المفضلة", "almufadhal",
            "alamwaj", "الامواج", "الأمواج", "امواج", "alamwaj 1237",
            "الامواج 1237", "waves restaurant", "مطعم الأمواج",
            "alamwaj seafood", "الأمواج للمأكولات", "amwaj",
            "brunch zone", "برانش زون", "برنش زون", "brunch",
            "zone", "زون", "برانش", "برنش", "breakfast zone",
            "مطعم برانش", "brunch restaurant", "brunchzone"
            



            

        ],
        
        "مقاهي": [
            "hot and cold dr", "مشروبات ساخنة", "ساخن بارد", "hot cold drinks",
            "hot & cold", "هوت اند كولد", "مشروبات باردة",
            "hot cold", "drinks", "مشروبات", "كافيه مشروبات",
            "hot and cold drinks", "ساخن وبارد", "هوت كولد"
            "كافيه", "كافي", "كوفي", "قهوة", "coffee", "cafe",
            "ستاربكس", "starbucks", "ستارباكس",
            "بارنز", "barn's", "barns", "بارنس",
            "دانكن", "dunkin", "دانكن دونتس",
            "كاريبو", "caribou", "كاريبو كوفي",
            "تيم هورتنز", "tim hortons", "تيم هورتون",
            "كوستا", "costa", "costa coffee", "كوستا كوفي",
            "ديوانية وتد", "dewaniat watad", "وتد ديوانية", "مقهى وتد", "watad cafe",
            "دوز", "dose", "دوز كافيه",
            "بلاك", "black", "بلاك كوفي",
            "وايت", "white", "فلات وايت", "flat white",
            "كرافت", "craft", "كرافت كوفي",
            "يو كافيه", "ucoffee", "u coffee", "يو كوفي",
            "ريف الكوفي", "reef cofi", "cofi reef", "reef coffee",
            "onza", "أونزا", "onza cafe", "أونزا كافية",
            "برو 92", "brew 92", "92 brew", "برو تسعين",
            "kaia", "كايا", "كايا كافيه",
            "الوسوم العربي", "al wusoom arabi", "wusoom al arabi",
            "barns jdh171", "barns 171", "171 بارنز",
            "شركة الوسوم الع", "wusoom", "الوسوم",
            "نصف مليون", "half million", "نص مليون",
            "مؤسسة الكوب الم", "الكوب المميز",
            "BRSK", "برسك", "بريسك",
            "مقهى كي", "ki cafe", "كي كافيه",
            "سبشل", "special", "سبيشال",
            "روستري", "roastery", "محمصة",
            "كوفي تو", "coffee 2", "كوفي تو جو",
            "تو جو", "2 go", "to go",
            "موكا", "mocha", "موكا كافيه",
            "كافيه باتيسري", "cafe patisserie", "باتيسري كافيه",
            "Coarse Grind", "ﻛﻮﺭﺱ ﺟﺮﺍﻳﻨﺪ", "كورس جرايند", "grind coarse",
            "توتي كافيه", "totti cafe", "totti",
            "وايت قاردن", "white garden", "white garden cafe",
            "أروما", "aroma", "aroma cafe", "كافيه أروما",
            "بلو أوشن", "blue ocean", "blue ocean cafe",
            "هيف وكيف", "heif wakief", "heef and keef",
            "كلتشر كافيه", "culture cafe", "culture",
            "النافورة", "al nafoura", "nafoura cafe",
            "زيتونة باي", "zeitouna bay", "zaytona bay",
            "سكلبتشر", "sculpture", "sculpture cafe",
            "لينور", "lenore", "lenore cafe", "لينور كافية",
            "بوغوتا", "bogota", "bogota cafe", "بوجوتا",
            "رورال", "rural", "rural cafe", "رورال كافيه",
            "منت", "mint", "mint cafe", "منت كافيه",
            "أروق", "arouq", "arouq cafe", "أروق كافيه",
            "لاستوريا", "lastoria", "la storia", "لا ستوريا",
            "كافيهات الحمراء", "hamra cafes", "حمراء مول كافيهات",
            "kiffa roaster", "كفة", "محامص كفة", "كفة روستر",
            "kiffa", "كفه", "محمصة كفة", "كفة للقهوة",
            "kiffa coffee", "قهوة كفة", "كافيه كفة", "kiffa cafe",
            "كيفا", "kifa", "روستر", "roaster", "محامص",
            "كفة روستري", "kiffa roastery", "كفا روستر",
            "floated artisan", "فلوتيد ارتسنال", "فلوتد", "artisan",
            "floated", "ارتسنال", "فلوتيد", "specialty coffee",
            "floated coffee", "ارتيزان", "artisan coffee", "فلوتد كوفي"
        ],
        
        "حلويات ومخبوزات": [
            "افران الحطب", "al hatab bakery", "hatab bakery", "أفران الحطب",
            "حلويات", "حلى", "كيك", "cake", "كيكة",
            "مخبز", "bakery", "بيكري", "مخابز",
            "سايفور", "savor", "سافور",
            "معمول", "كنافة", "بقلاوة", "قطايف",
            "دونات", "donut", "دوناتس", "دونتس",
            "كرواسون", "croissant", "كروسان",
            "باتيسري", "patisserie", "باتيسيري",
            "كرسبي كريم", "krispy kreme", "كريسبي كريم",
            "AL-MAAMEER BAKR", "مخابز المعامير", "مخابز المعاملر",
            "al maameer", "مخابز معامير", "bakr",
            "مو سويت", "mo sweet", "موسويت",
            "شوكولا", "chocolate", "شكولاته",
            "آيس كريم", "ice cream", "ايس كريم",
            "باسكن روبنز", "baskin robbins", "باسكن",
            "هوجن داز", "haagen dazs", "هاجن داز",
            "كولد ستون", "cold stone", "كولدستون",
            "ماكرون", "macaron", "مكرون",
            "كب كيك", "cupcake", "كب كيكس",
            "تشيز كيك", "cheesecake", "تشيس كيك",
            "حلواني", "halawani", "الحلواني",
            "بوظة", "ice cream", "جيلاتو", "gelato"
        ],

        "توصيل طعام": [
            "جاهز", "jahez", "جاهز للتوصيل",
            "هنقرستيشن", "hungerstation", "هانقر ستيشن",
            "مرسول", "marsool", "مارسول",
            "توصيل", "delivery", "ديليفري",
            "توصيل طلبات", "food delivery", "طعام توصيل",
            "كريم", "careem", "كريم فود",
            "اوبر ايتس", "uber eats", "ubereats",
            "تالابات", "talabat", "طلبات",
            "زوماتو", "zomato", "زوماتو",
            "ديليفرو", "deliveroo", "ديليفيرو"
        ],
        

           
    },

    "🛒 سوبرماركت وبقالة": {
        "سوبرماركت كبير": [
            # السلاسل الكبيرة الرئيسية
            "كارفور", "carrefour", "كارفور هايبر", "carrefour hypermarket",
            "بنده", "panda", "هايبر بنده", "hyper panda", "بندا",
            "الدانوب", "danube", "دانوب هايبر", "danube hypermarket",
            "العثيم", "othaim", "اوتيم", "عثيم مول", "أسواق العثيم",
            "التميمي", "tamimi", "تميمي", "أسواق التميمي", "tamimi markets",
            "لولو", "lulu", "لولو هايبر", "lulu hypermarket", "lulu express",
            "مانويل", "manuel", "مانويل مول", "manuel market", "manuel hypermarket",
            "aswaq norah", "اسواق نوره", "أسواق نورة", "نورة ماركت",
            "aswaq noura", "نوره", "اسواق", "norah market",
            "أسواق نوره", "نورة سوبرماركت", "noura market",
            "اسواق نورا", "nora market", "سوبر ماركت نورة"
            
            # سلاسل محلية شهيرة
            "السدحان", "al sadhan", "sadhan", "سدحان", "alsadhan",
            "الجزيرة", "aljazera", "al jazera", "jazera", "اسواق الجزيرة",
            "العريق", "al areq", "areq", "العريق سوبرماركت",
            "سعودي", "saudi", "saudi supermarket", "سعودي سوبرماركت",
            "فريش", "fresh", "fresh market", "فريش ماركت",
            "العزيزية بنده", "aziziah panda", "العزيزية",
            "بنده للتجزئة", "panda retail co", "co retail panda",
            "اسواق العثيم", "aswaq al othaim", "اسواق عثيم",
            "مول العرب", "arab mall", "العرب مول",
            "كارفور سيتي", "carrefour city", "سيتي كارفور",
            "اف كي", "fk", "fk supermarket",
            "نستو", "nesto", "nesto hypermarket", "نستو هايبر",
            "سبار", "spar", "spar supermarket",
            "اكسترا", "extra", "extra stores", "اكسترا ستورز",
            "ساكو", "saco", "saco store",
            "بن داوود", "bin dawood", "bindawood", "بن داود",
            "المركز", "al markaz", "markaz", "المركز التجاري",
            "هايبر وان", "hyper one", "hyperone",
            "سوبر ماركت المدينة", "al madina supermarket", "مدينة سوبرماركت",
            "ali maeedh", "علي معيض", "مؤسسة علي معيض", "maeedh",
            "معيض", "ali", "علي", "معيض للتموينات", "maeedh store",
            "بقالة علي معيض", "تموينات معيض", "ali maeedh algh"
        ],
        
        "تموينات وبقالة": [
            "تموينات", "بقالة", "grocery", "تموينات وبقالة",
            "تموينات يزن", "tamwenat yazn", "تموينات يزن مقي",
            "يزن مقي", "yazn", "يزن للتموينات",
            "تموينات الجزيرة", "tamwenat aljaze", "الجزيرة",
            "aljaze", "جزيرة تموينات",
            "دكان", "dukan", "1023 دكان", "dukan 1023",
            "سوبر ماركت", "supermarket", "سوبرماركت",
            "mini market", "ميني ماركت", "مني ماركت",
            "luxury", "شركة التموين ال", "التموين",
            "نوري", "nouri", "نوري تموينات", "tамwenat nouri",
            "اسواق البشية", "albashih market", "market albashih",
            "باسمح للتسويق", "khaled abdullah", "abdullah khaled",
            "باسمح", "khaled باسمح", "باسمح للتسوق",
            "KHALED ﺑﺎﺳﻤﺢ ﻟﻠﺘﺴﻮﻳﻖ", "ﺑﺎﺳﻤﺢ ﻟﻠﺘﺴﻮﻳﻖ",
            "مؤسسة مريم", "maryam issa", "issa maryam",
            "السوق المركزي", "central market", "market central",
            "سوق مركزي", "central", "السوق", "market",
            "تموينات", "باسمح للتسوق", "مقهى كي",
            "WORLD PRICE", "شركة عالم الاس", "عالم الاسعار",
            "MODAWER AL AZEZ", "مدور العزيزية", "مدور العزيز",
            "MHASEN SHARG", "محاسن الشرق لتق", "محاسن الشرق",
            "One Advantage C", "شركة ميزة واحدة", "ميزة واحدة",
            "BAAD JADID FOR", "شركة بعد جديد ل", "بعد جديد",
            "F.S.T. Co - A", "F. S. T. Co - A", "شركة امداد الأط", "امداد الاطعمة",
            "ﺷﺮﻛﺔ ﺍﻣﺪﺍﺩ ﺍﻷﻁ", "امداد الأطعمة",
            "تموينات العائلة", "family grocery", "عائلة تموينات",
            "الخير تموينات", "al khair grocery", "خير تموينات",
            "النخيل تموينات", "palm grocery", "نخيل تموينات",
            "الأمانة تموينات", "amanah grocery", "أمانة تموينات",
            "الشرق تموينات", "sharq grocery", "شرق تموينات",
            "الغرب تموينات", "gharb grocery", "غرب تموينات",
            "الربع الثالث", "al rubea al tha", "مؤسسة الربع الث",
            "الشمال تموينات", "shamal grocery", "شمال تموينات",
            "الجنوب تموينات", "janoub grocery", "جنوب تموينات",
            "شركة امداد الأطعمة", "f.s.t. co", "fst food", "إمداد الأغذية",
            "مدور العزيزية", "modawer al azizia", "modawer al azeez", "modawer", "مدور العزيز",
            
            # تموينات إضافية منتشرة
            "تموينات الجامع", "jameh grocery", "الجامع تموينات",
            "تموينات الحي", "neighbourhood grocery", "حي تموينات",
            "تموينات المسجد", "mosque grocery", "مسجد تموينات",
            "تموينات الركن", "corner grocery", "ركن تموينات",
            "تموينات السوق", "market grocery", "سوق تموينات",
            "تموينات الصحة", "health grocery", "صحة تموينات",
            "تموينات الورد", "ward grocery", "ورد تموينات",
            "تموينات الزهور", "flowers grocery", "زهور تموينات",
            "تموينات السعادة", "happiness grocery", "سعادة تموينات",
            "تموينات النجاح", "success grocery", "نجاح تموينات",
            "تموينات الأمل", "hope grocery", "أمل تموينات",
            "تموينات البركة", "baraka grocery", "بركة تموينات",
            "تموينات الرحمة", "mercy grocery", "رحمة تموينات",
            "تموينات الخليج", "gulf grocery", "خليج تموينات",
            "تموينات العرب", "arab grocery", "عرب تموينات",
            "تموينات الوطن", "homeland grocery", "وطن تموينات",
            "تموينات القمة", "summit grocery", "قمة تموينات",
            "تموينات النور", "light grocery", "نور تموينات",
            "تموينات الفجر", "dawn grocery", "فجر تموينات",
            "تموينات المستقبل", "future grocery", "مستقبل تموينات",
            "تموينات الأصدقاء", "friends grocery", "أصدقاء تموينات",
            "تموينات الإخوان", "brothers grocery", "إخوان تموينات",
            "تموينات الطيبين", "good people grocery", "طيبين تموينات",
            "تموينات الكرام", "generous grocery", "كرام تموينات",
            "تموينات السلام", "peace grocery", "سلام تموينات",
            "تموينات الهدى", "guidance grocery", "هدى تموينات",
            "تموينات التقوى", "piety grocery", "تقوى تموينات",
            "تموينات الإيمان", "faith grocery", "إيمان تموينات",
            "بقالة السعودية", "saudi grocery", "سعودية بقالة",
            "بقالة الحي", "neighbourhood store", "حي بقالة",
            "بقالة الركن", "corner store", "ركن بقالة",
            "بقالة السوق", "market store", "سوق بقالة",
            "بقالة المركز", "center store", "مركز بقالة",
            "بقالة نورة", "nora grocery", "نورة بقالة",
            "بقالة فاطمة", "fatima grocery", "فاطمة بقالة",
            "بقالة عائشة", "aisha grocery", "عائشة بقالة",
            "بقالة خديجة", "khadija grocery", "خديجة بقالة",
            "دكان عبدالعزيز", "abdulaziz store", "عبدالعزيز دكان",
            "دكان محمد", "mohammed store", "محمد دكان",
            "دكان أحمد", "ahmed store", "أحمد دكان",
            "دكان علي", "ali store", "علي دكان",
            "دكان عبدالله", "abdullah store", "عبدالله دكان",
            "مؤسسة الغذاء", "food establishment", "غذاء مؤسسة",
            "مؤسسة التموين", "supply establishment", "تموين مؤسسة",
            "شركة المواد الغذائية", "food materials company", "مواد غذائية شركة"
        ]
    },
    
    "🛍️ تسوق وملابس": {
        "متاجر إلكترونية": [
            "أمازون", "amazon", "امازون", "amazon sa", "أمازون السعودية",
            "نون", "noon", "نون كوم", "noon.com",
            "علي بابا", "alibaba", "علي بابا كوم", "alibaba.com",
            "علي اكسبرس", "aliexpress", "علي اكسبريس", "ali express",
            "ebay", "ايباي", "اي باي", "eBay",
            "شي ان", "shein", "شين", "she in",
            "نمشي", "namshi", "نامشي", "namshi.com",
            "سوق", "souq", "سوق كوم", "souq.com",
            "جرير", "jarir", "مكتبة جرير", "jarir bookstore",
            "اكسترا", "extra", "إكسترا", "extra stores",
            "مكتبة", "bookstore", "مكتبات", "book store",
            "ساكو", "saco", "ساكو هاردوير", "saco hardware",
            "ايكيا", "ikea", "إيكيا", "ikea saudi",
            "هوم سنتر", "home center", "هوم سنتر السعودية", "homecentre",
            "ماكس", "max", "ماكس للأزياء", "max fashion",
            "الفردان", "al fardan", "فردان", "fardan",
            "العقيل", "al aqeel", "عقيل", "aqeel",
            "NiceOne", "نايس ون", "nice one",
            
            # متاجر إلكترونية محلية وعالمية إضافية
            "أوناس", "ounass", "اوناس", "ounass saudi", "أُناس",
            "فاشن", "fashion", "fashion.sa", "فاشن السعودية",
            "سلة", "salla", "منصة سلة", "salla platform",
            "سيفي", "sivvi", "سيفى", "sivvi.com",
            "زين ستور", "zain store", "زين", "zain shop",
            "موبايلي شوب", "mobily shop", "موبايلي", "mobily store",
            "stc store", "اس تي سي", "متجر اس تي سي", "stc shop",
            "اورانج", "orange", "متجر اورانج", "orange store",
            "برايسنا", "pricena", "مقارنة الأسعار", "price comparison",
            "أسناس", "asnas", "متجر أسناس", "asnas store",
            "دور الأناقة", "fashion house", "fashionhouse-sa",
            "بوينت", "point", "point shopping", "بوينت شوبنغ",
            "تطبيق حراج", "haraj", "حراج", "haraj app",
            "مستعمل", "mustaamil", "مستعمل.كوم", "used items",
            "تبي", "taby", "تبي تطبيق", "taby app"
        ],
        
        "ملابس وأزياء": [
            "زارا", "zara", "زاره", "zara saudi",
            "اتش اند ام", "h&m", "h and m", "اتش آند ام",
            "مانجو", "mango", "مانجو للأزياء", "mango fashion",
            "سنتربوينت", "centerpoint", "سنتر بوينت", "centrepoint",
            "ماكس", "max", "ماكس فاشون", "max fashion",
            "بولو", "polo", "بولو رالف لورين", "polo ralph lauren",
            "قاب", "gap", "جاب", "gap saudi",
            "فوريفر", "forever", "فوريفر 21", "forever 21",
            "بيرشكا", "bershka", "برشكا", "bershka saudi",
            "بول اند بير", "pull and bear", "بول آند بير", "pull & bear",
            "ماسيمو", "massimo", "ماسيمو دوتي", "massimo dutti",
            "لاكوست", "lacoste", "لكوست", "lacoste saudi",
            "نايك", "nike", "نايكي", "nike saudi",
            "اديداس", "adidas", "أديداس", "adidas saudi",
            "بوما", "puma", "بوما سبورت", "puma sport",
            "أديداس العربية", "adidas arabia", "arabia adidas",
            "لورو بيانا", "loro piana", "piana loro",
            "red sea zara", "زارا رد سي", "zara ma sea red",
            "zara red sea", "لورو بيانا",
            "فاشونيستا", "fashionista", "فاشونيستا للأزياء",
            "رد تاغ", "red tag", "ريد تاغ", "redtag",
            "بلو مود", "blue mood", "بلو موود", "blue mood fashion",
            "ناسك", "nask", "ناسك للأزياء", "nask fashion",
            "بودي شوب", "body shop", "بودي شوب العربية", "the body shop",
            "باث اند بودي", "bath and body", "باث آند بودي", "bath & body works",
            "فيكتوريا سيكريت", "victoria's secret", "فيكتوريا سيكرت", "victoria secret",
            "كالفن كلين", "calvin klein", "كالفن كلاين", "ck",
            "تومي هيلفيغر", "tommy hilfiger", "تومي هيلفيجر", "tommy",
            "ديزل", "diesel", "ديزل جينز", "diesel jeans",
            "ليفايز", "levi's", "ليفايس", "levis",
            
            # ماركات إضافية شهيرة
            "نكست", "next", "نكست السعودية", "next saudi",
            "مذركير", "mothercare", "مذر كير", "mother care",
            "تشيلدرن بليس", "children's place", "children place",
            "اوشكوش", "oshkosh", "اوش كوش", "osh kosh",
            "كارترز", "carter's", "كارترز للأطفال", "carters",
            "جيمبوري", "gymboree", "جيمبورى", "gymboree kids",
            "ذا تشيلدرن", "the children", "ذا شيلدرن", "children store",
            "مومزورلد", "moms world", "مومز ورلد", "momsworld",
            "جونيورز", "juniors", "جونيرز", "juniors store",
            "سبورتس دايركت", "sports direct", "سبورتس داركت", "sportsdirect",
            "فوت لوكر", "foot locker", "فوت لوكير", "footlocker",
            "اثليتكو", "athletico", "اثليتيكو", "athletico sports",
            "سن اند ساند", "sun and sand", "سن آند ساند", "sun & sand sports",
            "لايف ستايل", "lifestyle", "لايف ستايل", "lifestyle stores",
            "هوم بوكس", "home box", "هوم بوكس", "homebox",
            "ذات", "that", "ذات للأزياء", "that fashion",
            "مودا", "moda", "مودا للأزياء", "moda fashion",
            "إلگنت", "elegant", "ايليگنت", "elegant fashion",
            "شيك", "chic", "شيك فاشن", "chic fashion",
            "كلاسيك", "classic", "كلاسك فاشن", "classic fashion",
            "ترند", "trend", "ترند فاشن", "trend fashion"
        ],
        
        "اكسسوارات ومجوهرات": [
            "اكسسوارات", "accessories", "إكسسوارات", "accessory",
            "مجوهرات", "jewelry", "مجوهرات ذهب", "jewellery",
            "ذهب", "gold", "ذهب وفضة", "gold jewelry",
            "فضة", "silver", "فضة وذهب", "silver jewelry",
            "ساعات", "watches", "ساعة", "watch",
            "نظارات", "glasses", "نظارة", "sunglasses",
            "حقائب", "bags", "حقيبة", "handbags",
            "أحذية", "shoes", "حذاء", "footwear",
            "عطور", "perfumes", "عطر", "fragrance",
            "مكياج", "makeup", "ميك اب", "cosmetics",
            "كريمات", "creams", "كريم", "skincare",
            "لازوردي", "lazurde", "لازوردي للمجوهرات", "l'azurde",
            "داماس", "damas", "داماس للمجوهرات", "damas jewelry",
            "الفردان", "al fardan", "فردان للمجوهرات", "fardan jewelry",
            "سفورا", "sephora", "سيفورا", "sephora saudi",
            "ماك", "mac", "ماك كوزمتكس", "mac cosmetics",
            "لوريال", "loreal", "لوريال باريس", "l'oreal paris",
            
            # ماركات إضافية للاكسسوارات
            "مايكل كورس", "michael kors", "مايكل كورز", "mk",
            "كوتش", "coach", "كوتش باقز", "coach bags",
            "برادا", "prada", "برادا باقز", "prada bags",
            "قوتشي", "gucci", "جوتشي", "gucci bags",
            "لوي فيتون", "louis vuitton", "لويس فيتون", "lv",
            "شانيل", "chanel", "شانل", "chanel bags",
            "هيرمس", "hermes", "هيرميس", "hermes bags",
            "روليكس", "rolex", "رولكس", "rolex watches",
            "اوميغا", "omega", "اوميجا", "omega watches",
            "كارتير", "cartier", "كارتيير", "cartier watches",
            "تاغ هوير", "tag heuer", "تاق هوير", "tag heuer watches",
            "سيتيزن", "citizen", "سيتزن", "citizen watches",
            "كاسيو", "casio", "كاسيو", "casio watches",
            "ريبان", "ray ban", "راي بان", "rayban",
            "اوكلي", "oakley", "اوكلى", "oakley sunglasses",
            "فيرساتشي", "versace", "فيرساتشى", "versace perfume",
            "كلينيك", "clinique", "كلينيك", "clinique cosmetics",
            "لانكوم", "lancome", "لانكوم", "lancome makeup",
            "ايستي لودر", "estee lauder", "ايستى لودر", "estee lauder",
            "ديور", "dior", "ديور", "dior makeup",
            "شو", "shoe", "شوز", "shoes store",
            "بوتس", "boots", "بوتز", "boots store"
        ],
        
        "متاجر عامة": [
            "ساكو", "saco", "ساكو هاردوير", "saco hardware",
            "ايكيا", "ikea", "إيكيا", "ikea saudi",
            "sattel", "سطل", "ساتل", "sattel store",
            "هوم سنتر", "home center", "هوم سنتر", "homecentre",
            "مفروشات", "furniture", "أثاث", "home furniture",
            "ديكور", "decor", "ديكورات", "home decor",
            "أدوات منزلية", "home tools", "أدوات البيت", "house tools",
            "شركة السندي", "AL-Sanidi Company", "السندي", "al sanidi",
            "كهربائيات", "electronics", "أجهزة كهربائية", "electrical appliances",
            "fares albalushi", "فارس البلوشي", "فارس بلوشي", "albalushi",
            "البلوشي", "fares", "فارس", "balushi store", "متجر البلوشي",
            "فارس البلوشي للتجارة", "albalushi trading", "بلوشي",
            
            # متاجر عامة إضافية
            "هوم بوكس", "home box", "هوم بوكس", "homebox",
            "ايجبت بوكس", "egypt box", "إيجبت بوكس", "egyptbox",
            "بان ايميرتس", "pan emirates", "بان إمارتس", "pan emirates furniture",
            "ورلد اوف وندر", "world of wonder", "عالم العجائب", "wow store",
            "توي ار اس", "toys r us", "تويز ار اس", "toysrus",
            "هاملي", "hamleys", "هاملى", "hamleys toys",
            "ليجو", "lego", "ليجو", "lego store",
            "عروس دبي", "aroos dubai", "عروس دبى", "bride dubai",
            "اسس", "ace", "إيس", "ace hardware",
            "هوم اند ليفينغ", "home and living", "هوم آند ليفنغ", "home & living",
            "ليفينغ سبيس", "living spaces", "ليفنغ سبيسز", "living space",
            "اوتليت مول", "outlet mall", "اوتلت مول", "outlets",
            "بازار", "bazaar", "بازار ستور", "bazaar store",
            "مارت", "mart", "سوبرمارت", "supermart",
            "ستور", "store", "المتجر", "the store",
            "شوب", "shop", "المحل", "the shop",
            "مركز", "center", "سنتر", "centre",
            "بلازا", "plaza", "بلازا مول", "plaza mall",
            "darb al kamal", "درب الكمال", "مؤسسة درب الكمال", "darb",
            "الكمال", "kamal", "درب", "darb alkamal", "دروب الكمال",
            "darb trading", "درب للتجارة", "alkamal store"
        ]
    },
    
    "🚗 خدمات السيارات": {
        "صيانة السيارة": [
            "haji husein ali", "الحاج حسين علي", "حاج حسين", "علي رضا",
            "صيانة", "قطع غيار", "spare parts", "قطع سيارات",
            "ميكانيكي", "mechanic", "ميكانيك",
            "زيت", "oil", "زيت محرك",
            "فلتر", "filter", "فلاتر",
            "بطارية", "battery", "بطاريات",
            "إطار", "tire", "تاير", "إطارات",
            "ورشة", "workshop", "ورش",
            "كراج", "garage", "كراجات",
            "فحص", "inspection", "فحص دوري",
            "تصليح", "repair", "اصلاح",
            "خدمة سريعة", "quick service", "خدمات سريعة",
            "كاوتش", "تغيير زيت", "oil change",
            "بريك", "brake", "فرامل",
            "تكييف سيارة", "car ac", "تكييف المركبة",
            
            # مراكز صيانة محلية ومشهورة
            "مسمار", "mismar", "تطبيق مسمار", "mismar app",
            "ماي كار", "my car", "مركز ماي كار", "mycar center",
            "مايز", "mize", "مراكز مايز", "mize centers",
            "فيكس اوتو", "fix auto", "فيكس نيتورك", "fix network",
            "التميز الشامل", "excellence comprehensive", "الشامل لصيانة",
            "أركان", "arkan", "أركان كار", "arkan car",
            "ورشة متنقلة", "mobile workshop", "صيانة متنقلة",
            "مركز صيانة", "maintenance center", "service center",
            "صيانة دورية", "periodic maintenance", "regular service",
            "توضيب محرك", "engine overhaul", "توضيب مكينة",
            "برمجة سيارة", "car programming", "برمجة كمبيوتر",
            "فحص كمبيوتر", "computer diagnosis", "تشخيص إلكتروني",
            "كهرباء سيارة", "car electrical", "كهربائي سيارات",
            "سمكرة", "bodywork", "سمكرة ودهان",
            "دهان سيارة", "car painting", "بوية سيارة",
            "عفشة", "suspension", "صيانة عفشة",
            "جيربوكس", "gearbox", "صيانة جيربوكس",
            "تبديل قطع", "parts replacement", "استبدال قطع",
            "ضمان صيانة", "maintenance warranty", "ضمان ذهبي",
            "سحب سيارة", "car towing", "سطحة سيارة",
            "خدمة طوارئ", "emergency service", "خدمة 24 ساعة"
        ],
        
        "وقود": [
            "بنزين", "بترول", "petrol", "gasoline",
            "وقود", "fuel", "فيول",
            "محطة", "station", "محطات",
            "أرامكو", "aramco", "ارامكو", "aramco saudi",
            "ساسكو", "sasco", "ساسكو محطة", "saudi automotive services",
            "الدريس", "aldrees", "الدريس محطة", "al drees",
            "بترومين", "petromin", "بترومين محطة", "petromin station",
            "شل", "shell", "شل محطة", "shell station",
            "موبيل", "mobil", "موبيل محطة", "mobil station",
            "co petroly", "بترولي", "mall bindaw",
            "أومكو", "oomco", "اومكو محطة", "oomco station",
            "بترو لكس", "petrolex", "بتروليكس", "petrolex station",
            "نخلة ساسكو", "sasco palm", "palm sasco",
            "naft services", "خدمات نفط", "شركة خدمات النف",
            "اومكو", "هاوند", "hawand", "naft",
            "خدمات النفط", "oil services",
            "أدنوك", "adnoc", "ادنوك محطة", "adnoc station",
            "انوك", "enoc", "ايناك محطة", "enoc station",
            "ايموك", "emoc", "ايموك محطة", "emoc station",
            
            # محطات وقود إضافية حسب البحث
            "إينوك", "enoc international", "ينوك الدولية",
            "نفط", "naft", "خدمات النفط المحدودة",
            "التسهيلات للتسويق", "facilitating marketing", "تسهيلات التسويق",
            "النفط العمانية", "omani oil marketing", "عمانية للتسويق",
            "أورنج", "orange", "تطوير محطات الوقود", "orange fuel",
            "خدمة الوقود", "fuel service", "خدمة المحدودة",
            "فيول واي", "fuel way", "الوقود المتكاملة",
            "7plus", "سيفن بلاس", "التميز المتحدة",
            "الخنيني", "alkhenini", "الخنيني البترولية",
            "بترولات", "petrolat", "شركة بترولات",
            "الأتوز", "alatos", "الأتوز البترولية",
            "وافي", "wafi", "وافي للطاقة", "wafi energy",
            "لتر", "liter", "لتر للتجارة", "liter trading",
            "بترولي", "petroly", "بترولي للخدمات", "petroly services",
            "ريبن", "ribbon", "ريبن للخدمات", "ribbon services",
            "هلا", "hala", "هلا التجارية", "hala trading",
            "قلف", "gulf", "محطة قلف", "gulf station",
            "ويل", "well", "محطة ويل", "well station",
            "توتال", "total", "توتال انرجيز", "total energies",
            "فاي", "fy", "مقهى فاي", "fy cafe"
        ],
        
        "مغسلة سيارات": [
            "مغسلة", "غسيل", "car wash", "كار واش",
            "تلميع", "polish", "بوليش",
            "تنظيف", "cleaning", "wash", "واش",
            "مؤسسة موتور واي", "motor way", "موتور واي",
            "غسيل بخار", "steam wash", "غسيل تفصيلي",
            "detail wash", "تفصيلي", "تنظيف شامل",
            "مغسلة أوتوماتيكية", "automatic wash", "مغسلة آلية",
            
            # أنواع مغاسل السيارات الإضافية
            "غسيل يدوي", "hand wash", "غسيل باليد",
            "تنظيف داخلي", "interior cleaning", "تنظيف من الداخل",
            "تنظيف خارجي", "exterior cleaning", "تنظيف من الخارج",
            "شمع السيارة", "car wax", "تشميع السيارة",
            "تلميع مصابيح", "headlight polishing", "تلميع الأنوار",
            "تنظيف المحرك", "engine cleaning", "غسيل المحرك",
            "تنظيف الجنوط", "rim cleaning", "غسيل الجنوط",
            "تنظيف السجاد", "carpet cleaning", "غسيل الفرش",
            "إزالة البقع", "stain removal", "تنظيف البقع",
            "تطهير السيارة", "car sanitizing", "تعقيم السيارة",
            "تنظيف الزجاج", "glass cleaning", "غسيل الزجاج",
            "مغسلة سريعة", "quick wash", "غسيل سريع",
            "مغسلة متنقلة", "mobile car wash", "غسيل متنقل",
            "خدمة منزلية", "home service", "غسيل بالمنزل"
        ],
        
        "تأجير سيارات": [
            "تأجير سيارات", "car rental", "إيجار سيارة",
            "بدجت", "budget", "بدجت كار", "budget car rental",
            "هيرتز", "hertz", "هيرتس", "hertz car rental",
            "افيس", "avis", "أفيس", "avis car rental",
            "يوروب كار", "europcar", "يوروب", "europcar rental",
            "ثريفتي", "thrifty", "ثريفتي كار", "thrifty car rental",
            "سيكست", "sixt", "سيكست كار", "sixt rent a car",
            "اوتولوكس", "autolux", "أوتولوكس", "autolux rental",
            "لوكس", "lux", "لكس كار", "lux car rental",
            
            # شركات تأجير سيارات إضافية
            "انتربرايز", "enterprise", "enterprise car rental",
            "الاميريا", "alameria", "الاميريا للتأجير",
            "يلو", "yellow", "يلو كار", "yellow car rental",
            "فاست", "fast", "فاست رنت", "fast rent",
            "نشنال", "national", "نشنال كار", "national car rental",
            "الاميال", "al amyal", "الأميال للتأجير",
            "درايف", "drive", "درايف ريتال", "drive rental",
            "كار جت", "car jet", "كار جيت", "carjet",
            "رنت كار", "rent car", "ريت اكار", "rentacar",
            "تيمو", "temo", "تيمو كار", "temo car",
            "ريدي", "ready", "ريدي ريت", "ready rent",
            "فليكس", "flex", "فليكس كار", "flex car",
            "إيزي", "easy", "إيزي ريت", "easy rent",
            "سمارت", "smart", "سمارت ريت", "smart rent",
            "ايكار", "ekar", "إي كار", "ekar app",
            "اوبر كار", "uber car", "كريم كار", "careem car"
        ],
        
        "مواقف سيارات": [
            "LE MASCHOU", "مواقف لوماشو", "le maschou parking",
            "مواقف سيارات", "parking", "موقف سيارة",
            "باركنغ", "car parking", "موقف عام",
            "ساحة انتظار", "parking lot", "ساحات الانتظار",
            "موقف مجاني", "free parking", "باركنغ مجاني",
            "موقف مدفوع", "paid parking", "باركنغ مدفوع",
            "موقف مغطى", "covered parking", "باركنغ مسقوف",
            "موقف مكشوف", "open parking", "باركنغ مكشوف",
            "موقف تحت الأرض", "underground parking", "باركنغ سفلي",
            "موقف متعدد الطوابق", "multi-story parking", "باركنغ متعدد",
            "موقف فاليت", "valet parking", "خدمة فاليت",
            "موقف ذكي", "smart parking", "باركنغ ذكي",
            "تطبيق مواقف", "parking app", "ابلكيشن باركنغ",
            "حجز موقف", "parking reservation", "حجز باركنغ",
            "دفع إلكتروني", "electronic payment", "دفع رقمي",
            "موقف طويل الأمد", "long term parking", "باركنغ طويل",
            "موقف قصير الأمد", "short term parking", "باركنغ قصير",
            "موقف مطار", "airport parking", "باركنغ مطار",
            "موقف مول", "mall parking", "باركنغ مول",
            "موقف مستشفى", "hospital parking", "باركنغ مستشفى",
            "موقف جامعة", "university parking", "باركنغ جامعة"
        ]
    },
    
    "💇‍♂️ خدمات شخصية": {
        "حلاقة وصالونات": [
            "حلاق", "حلاقة", "barber", "باربر",
            "صالون", "salon", "صالونات",
            "كوافير", "شعر", "hair", "هير",
            "قص", "cut", "صبغة", "color",
            "حلاق شبح", "shabah", "شبح باربر",
            "امواس", "amwas", "أمواس باربر",
            "نايس باربر", "nice barber",
            "ستايل", "style", "ستايل باربر",
            "barbers 5", "باربرز", "هشام هزاع",
            "athra barbers", "barbers athra", "مؤسسة هشام",
            "حلاق الملك", "king barber", "باربر الملك",
            "حلاق VIP", "vip barber", "في آي بي",
            "براند باربر", "brand barber", "حلاق براند",
            
            # صالونات حلاقة شهيرة إضافية
            "30 درجة", "30 degrees", "ثيرتي ديجريز", "30degrees",
            "هوليود", "hollywood", "هوليوود باربر", "hollywood barber",
            "انترناشيونال باربر", "international barber", "international barbershop",
            "الشيخ زايد", "sheikh zayed", "الشيخ زايد للحلاقة", "zayed barber",
            "باربر شوب الأمير", "prince barber shop", "الأمير باربر",
            "صالون النخبة", "elite salon", "النخبة للرجال", "elite men salon",
            "زمزم للرجال", "zamzam men", "مركز زمزم", "zamzam center",
            "باربريا", "barberia", "باربيريا", "barberia salon",
            "الخليج للرجال", "gulf men", "مركز الخليج", "gulf center",
            "روزنامة", "roznamah", "روزنامة للرجال", "roznamah men",
            "تونسون", "tunsun", "تونسون للرجال", "tunsun men",
            "كلاسيك باربر", "classic barber", "كلاسك باربر", "classic barbershop",
            "مودرن باربر", "modern barber", "مودن باربر", "modern barbershop",
            "جنتلمان", "gentleman", "جنتلمان باربر", "gentleman barber",
            "رويال باربر", "royal barber", "الملكي باربر", "royal barbershop",
            "لندن باربر", "london barber", "لندن شوب", "london barbershop",
            "تركيش باربر", "turkish barber", "تركي باربر", "turkish barbershop",
            "عربي باربر", "arabic barber", "عربي شوب", "arabic barbershop",
            "سعودي باربر", "saudi barber", "سعودي شوب", "saudi barbershop",
            "خليجي باربر", "gulf barber", "خليجي شوب", "gulf barbershop",
            "الأصيل باربر", "authentic barber", "الأصيل شوب", "aseel barber",
            "التراث باربر", "heritage barber", "التراث شوب", "turath barber",
            "العصري باربر", "contemporary barber", "عصري شوب", "asri barber",
            "فاخر باربر", "luxury barber", "فاخر شوب", "fakher barber",
            "راقي باربر", "elegant barber", "راقي شوب", "raqi barber"
        ],
        
        "مغسلة ملابس": [
            "مغسلة", "غسيل", "كوي", "كي",
            "laundry", "لاندري", "لوندري",
            "dry clean", "دراي كلين", "تنظيف جاف",
            "لمسة الغد", "ghade", "نظافة",
            "مغسلة سريعة", "quick laundry", "غسيل سريع",
            "مغسلة وكوي", "wash and iron", "غسيل وكوي",
            "تنظيف بالبخار", "steam cleaning", "بخار",
            "مغسلة راقية", "premium laundry", "غسيل راقي",
            "مغسلة إيمان", "Iman laundry", "Iman bin", "ﻣﻐﺴﻠﺔ ﺍﻳﻤﺎﻥ",
            
            # مغاسل شهيرة إضافية
            "مغسلة الجبر", "aljabr laundry", "الجبر", "jabr laundry",
            "مغاسل الرهدن", "alrahden laundry", "الرهدن", "rahden laundry",
            "مغسلة مسار", "masar laundry", "مسار", "masar",
            "مغسلة هدوومي", "hudoomie laundry", "هدوومي", "hudoomie",
            "دي لاندري", "de laundry", "دى لاندري", "de laundry chain",
            "تطبيق مغاسل", "maghasel app", "مغاسل", "maghasel",
            "مغسلة النظافة", "cleanliness laundry", "النظافة", "nazafah laundry",
            "مغسلة الجودة", "quality laundry", "الجودة", "jawdah laundry",
            "مغسلة السرعة", "speed laundry", "السرعة", "sur'ah laundry",
            "مغسلة الخدمة", "service laundry", "الخدمة", "khidmah laundry",
            "مغسلة الأمانة", "trust laundry", "الأمانة", "amanah laundry",
            "مغسلة الدقة", "precision laundry", "الدقة", "diqqah laundry",
            "مغسلة الإتقان", "perfection laundry", "الإتقان", "itqan laundry",
            "مغسلة الفخامة", "luxury laundry", "الفخامة", "fakhamah laundry",
            "مغسلة الراحة", "comfort laundry", "الراحة", "rahah laundry",
            "مغسلة التميز", "excellence laundry", "التميز", "tamayuz laundry",
            "مغسلة الكمال", "perfection laundry", "الكمال", "kamal laundry",
            "مغسلة النجاح", "success laundry", "النجاح", "najah laundry",
            "مغسلة الذهبية", "golden laundry", "الذهبية", "dhahabiyah laundry",
            "مغسلة الملكية", "royal laundry", "الملكية", "malakiyah laundry",
            "مغسلة الأولى", "first laundry", "الأولى", "oola laundry",
            "مغسلة الحديثة", "modern laundry", "الحديثة", "hadithah laundry",
            "مغسلة العصرية", "contemporary laundry", "العصرية", "asriyah laundry",
            "مغسلة الطاهرة", "pure laundry", "الطاهرة", "tahirah laundry",
            "مغسلة الصافية", "clear laundry", "الصافية", "safiyah laundry"
        ],
        
        "عناية شخصية": [
            "سبا", "spa", "سبا وعناية",
            "مساج", "massage", "مساج علاجي",
            "عناية", "care", "عناية شخصية",
            "بشرة", "skin", "عناية بشرة",
            "أظافر", "nails", "مانيكير",
            "manicure", "باديكير", "pedicure",
            "صالون نسائي", "ladies salon", "صالون للسيدات",
            "مركز تجميل", "beauty center", "مركز الجمال",
            "عيادة تجميل", "beauty clinic", "كلينيك تجميل",
            
            # مراكز عناية شخصية إضافية
            "مركز هدوء الشرق", "hudoo alsharq center", "هدوء الشرق",
            "سبا راديسون", "radisson spa", "راديسون سبا",
            "سبا بريرا", "brera spa", "بريرا سبا",
            "مركز العناية الفاخرة", "luxury care center", "عناية فاخرة",
            "سبا الجمال", "beauty spa", "سبا التجميل",
            "مركز اللؤلؤة", "pearl center", "اللؤلؤة للعناية",
            "سبا الياسمين", "jasmine spa", "الياسمين سبا",
            "مركز الورد", "rose center", "الورد للعناية",
            "سبا الأناقة", "elegance spa", "الأناقة سبا",
            "مركز الجوهرة", "jewel center", "الجوهرة للعناية",
            "سبا الفخامة", "luxury spa", "الفخامة سبا",
            "مركز الملكة", "queen center", "الملكة للعناية",
            "سبا الأميرة", "princess spa", "الأميرة سبا",
            "مركز النعيم", "bliss center", "النعيم للعناية",
            "سبا الهدوء", "serenity spa", "الهدوء سبا",
            "مركز السكينة", "tranquility center", "السكينة للعناية",
            "سبا الراحة", "comfort spa", "الراحة سبا",
            "مركز الصحة", "health center", "الصحة والعناية",
            "سبا العافية", "wellness spa", "العافية سبا",
            "مركز النشاط", "vitality center", "النشاط والعناية",
            "سبا التجديد", "renewal spa", "التجديد سبا",
            "مركز الإشراق", "radiance center", "الإشراق للعناية",
            "سبا النضارة", "freshness spa", "النضارة سبا",
            "مركز الحيوية", "vitality center", "الحيوية للعناية",
            "سالون ڤينوس", "venus salon", "فينوس سالون",
            "صالون أفروديت", "aphrodite salon", "افروديت سالون",
            "مركز كليوباترا", "cleopatra center", "كليوباترا",
            "سبا شهرزاد", "shahrazad spa", "شهرزاد سبا"
        ],
        "خياطة":[
            "kyat ryf", "خياط ريوف", "خياط رياف", "خياط ملابس",
            "kyat", "خياط", "ريوف", "ryf", "riyouf tailor",
            "خياطة ريوف", "ريوف للخياطة", "kyat riyouf",
            "tailoring", "خياطة", "تفصيل", "خياط رجالي"
        ],

        
    },
    
        "🎬 ترفيه": {
        "سينما": [
            "سينما", "cinema", "سينمات",
            "موفي", "movie", "فيلم",
            "vox", "فوكس", "فوكس سينما", "ڤوكس سينما",
            "amc", "اي ام سي", "amc سينما", "AMC Cinemas",
            "muvi", "موفي سينما", "movie cinemas", "موڤي سينما",
            "imax", "ايماكس", "آي ماكس", "IMAX",
            "سينما مول", "mall cinema", "سينما المول",
            "كنكورد", "concord", "كونكورد سينما", "concord cinema",
            "موفي تايم", "movie time", "تايم سينما", "time cinema",
            
            # سلاسل سينما إضافية
            "ريل سينما", "reel cinema", "ريل", "reel cinemas",
            "نيو ميترو", "new metro", "ميترو سينما", "metro cinema",
            "جراند سينما", "grand cinema", "جراند", "grand cinemas",
            "امباير سينما", "empire cinema", "إمباير", "empire cinemas",
            "سينما البوليفارد", "boulevard cinema", "بوليفارد سينما",
            "سينما عبر", "via cinema", "عبر سينما", "via cinemas",
            "سينما الأندلس", "andalus cinema", "الأندلس سينما",
            "سينما اليسر", "alysr cinema", "اليسر سينما",
            "سينما مكة", "makkah cinema", "مكة سينما",
            "سينما المدينة", "madinah cinema", "المدينة سينما",
            "سينما النور", "alnoor cinema", "النور سينما",
            "4DX", "رباعية الأبعاد", "4D cinema", "فور دي اكس",
            "Xperience", "اكسبيرينس", "تجربة مميزة", "experience cinema",
            "سويتس", "suites", "سينما فاخرة", "luxury cinema",
            "DOLBY", "دولبي", "دولبي اتموس", "dolby atmos",
            "سينما كيدز", "kids cinema", "سينما الأطفال", "children cinema"
        ],
        
        "فعاليات وألعاب": [
            "هابي لاند", "happy land", "هابي لاند العاب", "happy land entertainment",
            "سباركيز", "sparky's", "سباركيز العاب", "sparkys games",
            "بولينج", "bowling", "بولينج سنتر", "bowling center",
            "بلياردو", "billiard", "بلياردو هول", "billiards hall",
            "ملعب", "playground", "ملاعب", "playgrounds",
            "نادي", "club", "نادي رياضي", "sports club",
            "جيم", "gym", "جيم سبورت", "gym sport",
            "نادي رياضي", "fitness", "فتنس سنتر", "fitness center",
            "العاب ترفيهية", "entertainment games", "ترفيه", "entertainment",
            "مدينة العاب", "theme park", "مدينة ترفيهية", "amusement park",
            "اكوا بارك", "aqua park", "مدينة مائية", "water city",
            "ووتر بارك", "water park", "العاب مائية", "water games",
            "HALA YALLA", "هلا يلا", "هالا يالا",
            "وناسه", "wanasa", "مركز لعب وناسه", "مركز وناسه", "wanasa play", "playgrou", "playground",
            "BRIGHT STAGEﻣﺆﺳﺴﺔ ﺍﻟﻤﻨﺼﺔ ﺍﻝ", "bright stage", "المنصة", "منصة مشرقة",
            
            # مراكز ترفيهية إضافية شهيرة
            "عطا الله هابي لاند", "atallah happy land", "عطا الله", "atallah entertainment",
            "فانكي لاند", "funky land", "فانكي", "funky entertainment",
            "آيس لاند", "ice land", "ايس لاند", "ice entertainment",
            "الكوبرا", "cobra", "ملاهي الكوبرا", "cobra entertainment",
            "الحكير", "al hokair", "مجموعة الحكير", "hokair group",
            "عالم الثلج", "snow world", "world of snow", "ثلج ورلد",
            "عالم المغامرات", "adventure world", "مغامرات ورلد", "adventures land",
            "عالم الجاذبية", "gravity world", "جرافيتي ورلد", "gravity zone",
            "جوكو للترفيه", "jokko entertainment", "جوكو", "jokko fun",
            "9 كلاود", "9 cloud", "تسعة كلاود", "nine cloud",
            "كريستال", "crystal", "كريستال أماكن", "crystal places",
            "دووس كارتنج", "doos karting", "دوس كارتنج", "doos racing",
            "كارتنج", "karting", "go kart", "جو كارت",
            "ليزر تاغ", "laser tag", "ليزر جيم", "laser game",
            "اسكيب روم", "escape room", "غرف الهروب", "escape games",
            "باينت بول", "paint ball", "بينت بول", "paintball",
            "ترامبولين", "trampoline", "نط", "jumping",
            "تسلق", "climbing", "جدار تسلق", "climbing wall",
            "محاكيات", "simulators", "واقع افتراضي", "virtual reality",
            "VR", "في آر", "ڤي آر", "virtual games",
            "AR", "واقع معزز", "augmented reality", "اي آر",
            "أركيد", "arcade", "العاب أركيد", "arcade games",
            "سباق سيارات", "car racing", "سباقات", "racing games",
            "طائرات درون", "drone racing", "درون", "drones",
            "روبوتات", "robots", "روبوت", "robotics"
        ],
        
        "تذاكر وحجوزات": [
            "تذكرة", "ticket", "تذاكر", "tickets",
            "حجز", "booking", "حجوزات", "bookings",
            "فعالية", "event", "فعاليات", "events",
            "حفلة", "concert", "حفلات", "concerts",
            "مباراة", "match", "مباريات", "matches",
            "game", "جيم", "لعبة", "games",
            "مؤتمر", "conference", "مؤتمرات", "conferences",
            "معرض", "exhibition", "معارض", "exhibitions",
            "ورشة عمل", "workshop", "ورش العمل", "workshops",
            
            # منصات تذاكر وحجوزات
            "ويجو", "wego", "ويغو تذاكر", "wego tickets",
            "تطبيق تذاكر", "tickets app", "تذاكري", "tazkirati",
            "بوك ماي شو", "book my show", "بوك مي شو", "bookmyshow",
            "إيفينت برايت", "eventbrite", "ايفنت برايت", "event bright",
            "تيكت ماستر", "ticketmaster", "تكت ماستر", "ticket master",
            "حجز مباشر", "direct booking", "حجز فوري", "instant booking",
            "تذاكر أونلاين", "online tickets", "تذاكر الكترونية", "e-tickets",
            "حجز الكتروني", "online booking", "حجز رقمي", "digital booking",
            "دفع الكتروني", "online payment", "دفع رقمي", "digital payment",
            "رمز QR", "QR code", "كيو آر", "qr ticket",
            "باركود", "barcode", "رمز شريطي", "bar code",
            "تذكرة مطبوعة", "printed ticket", "تذكرة ورقية", "paper ticket",
            "تذكرة رقمية", "digital ticket", "تذكرة الكترونية", "electronic ticket",
            "دخول VIP", "vip entry", "في آي بي", "vip access",
            "مقاعد مميزة", "premium seats", "مقاعد فاخرة", "luxury seats",
            "باكج عائلي", "family package", "عرض عائلي", "family deal",
            "باكج مجموعات", "group package", "حجز جماعي", "group booking",
            "خصم طلاب", "student discount", "خصم الطلبة", "students offer",
            "خصم كبار السن", "senior discount", "كبار السن", "elderly discount",
            "خصم الأطفال", "children discount", "خصم أطفال", "kids discount"
        ]
    },

    
    "🎧 اشتراكات تلقائية": {
        "ترفيه رقمي": [
            "netflix", "نتفليكس", "نيتفليكس",
            "شاهد", "shahid", "شاهد نت",
            "osn", "او اس ان", "اوه اس ان",
            "youtube", "يوتيوب", "يوتيوب بريميوم",
            "spotify", "سبوتيفاي", "سبوتي فاي",
            "apple tv", "ابل تي في", "apple tv+",
            "disney", "ديزني", "ديزني بلس",
            "amazon prime", "امازون برايم", "prime video",
            "hbo", "اتش بي او", "hbo max",
            "hulu", "هولو", "هولو",
            "starzplay", "ستارز بلاي", "starz play",
            "anghami", "انغامي", "انغامي بلس",
            "tidal", "تايدال", "tidal music",
        ],
        
        "خدمات آبل": [
            "apple.com/bill", "itunes.com", "apple bill",
            "icloud", "آي كلود", "icloud storage",
            "app store", "اب ستور", "متجر التطبيقات",
            "apple music", "ابل ميوزيك", "موسيقى ابل",
            "apple arcade", "ابل اركيد", "العاب ابل",
            "apple news", "ابل نيوز", "اخبار ابل",
            "apple fitness", "ابل فتنس", "لياقة ابل",
            "apple one", "ابل ون", "خدمات ابل",
            "STC Pay CITY: 0000682016SAM MCC- 6540ﻋﻤﻠﻴﺔ ﺷﺮﺍﺀ ﻋﺒﺮ ﺍﻹﻧﺘﺮﻧﺖ",
            "apple pay دولية", "apple pay - دولية", "apple", "آبل",
            "apple pay ون ديولانوما", "DEWANLAMASHSHAKIRA1 MADA",
            "WIATRO CITY", "apple pay عملية دولية", "CITY: 0000682016SAM",
            "Riyadh MADA ***1502 عملية شراء عبر الإنترنت", "MCC- 6540"
        ],
        
        "برامج وتطبيقات": [
            "canva", "كانفا", "كانفا برو",
            "adobe", "أدوبي", "ادوبي",
            "microsoft", "مايكروسوفت", "مايكروسوفت 365",
            "office", "اوفيس", "اوفس 365",
            "zoom", "زووم", "زوم برو",
            "dropbox", "دروب بوكس", "دروبوكس",
            "google", "جوجل", "google one",
            "manus ai", "ai manus", "مانوس اي آي",
            "7lle", "سلة", "7le",
            "mecca", "مكة", "مكة اب",
            "ibr", "آي بي آر", "ibr app",
            "uscb", "يو اس سي بي", "uscb app",
            "chatgpt", "تشات جي بي تي", "openai",
            "claude", "كلود", "anthropic",
            "notion", "نوشن", "notion pro"
        ]
    },
    
    "🎧 اشتراكات تلقائية": {
        "ترفيه رقمي": [
            "netflix", "نتفليكس", "نيتفليكس", "نتفلكس",
            "شاهد", "shahid", "شاهد نت", "shahid net", "شاهد VIP",
            "osn", "او اس ان", "اوه اس ان", "OSN+", "أو إس إن",
            "youtube", "يوتيوب", "يوتيوب بريميوم", "youtube premium",
            "spotify", "سبوتيفاي", "سبوتي فاي", "spotify premium",
            "apple tv", "ابل تي في", "apple tv+", "آبل تي في",
            "disney", "ديزني", "ديزني بلس", "disney plus", "disney+",
            "amazon prime", "امازون برايم", "prime video", "أمازون برايم",
            "hbo", "اتش بي او", "hbo max", "HBO Max",
            "hulu", "هولو", "هولو", "hulu plus",
            "starzplay", "ستارز بلاي", "starz play", "ستارز",
            "anghami", "انغامي", "انغامي بلس", "anghami plus",
            "tidal", "تايدال", "tidal music", "تايدل",
            
            # منصات إضافية شهيرة
            "كاسبر فلكس", "casper flix", "casperflix", "كسبر فلكس",
            "أروما تي في", "aroma tv", "aromaTV", "اروما",
            "واتش اي تي", "watch it", "watchit", "واتش ات",
            "ستارز", "starz", "starzplay arabia", "ستارز عربية",
            "پیکابو", "peekaboo", "بيكابو", "peek a boo",
            "توباك", "toopack", "توو باك", "2pack",
            "فيو", "view", "view tv", "ڤيو",
            "سكاي", "sky", "sky tv", "سكاي تي في",
            "بين سبورت", "bein sport", "بي ان سبورت", "bein sports",
            "يوتيوب ميوزيك", "youtube music", "youtube music premium",
            "ديزر", "deezer", "deezer premium", "ديزير",
            "ساوند كلاود", "soundcloud", "sound cloud", "ساند كلاود",
            "أبل ميوزيك", "apple music", "ابل موسيقى", "موسيقى ابل"
        ],
        
        "خدمات آبل": [
            "apple.com/bill", "itunes.com", "apple bill", "فاتورة ابل",
            "icloud", "آي كلود", "icloud storage", "تخزين اي كلاود",
            "app store", "اب ستور", "متجر التطبيقات", "أب ستور",
            "apple music", "ابل ميوزيك", "موسيقى ابل", "أبل ميوزيك",
            "apple arcade", "ابل اركيد", "العاب ابل", "أبل أركيد",
            "apple news", "ابل نيوز", "اخبار ابل", "أبل نيوز",
            "apple fitness", "ابل فتنس", "لياقة ابل", "أبل فتنس",
            "apple one", "ابل ون", "خدمات ابل", "أبل ون",
            "STC Pay CITY: 0000682016SAM MCC- 6540ﻋﻤﻠﻴﺔ ﺷﺮﺍﺀ ﻋﺒﺮ ﺍﻹﻧﺘﺮﻧﺖ",
            "apple pay دولية", "apple pay - دولية", "apple", "آبل",
            "apple pay ون ديولانوما", "DEWANLAMASHSHAKIRA1 MADA",
            "WIATRO CITY", "apple pay عملية دولية", "CITY: 0000682016SAM",
            "Riyadh MADA ***1502 عملية شراء عبر الإنترنت", "MCC- 6540",
            "itunes", "ايتونز", "آي تونز", "iTunes Store",
            "apple tv+", "ابل تي في بلس", "آبل تي في+", "أبل تي في+",
            "apple books", "ابل بوكس", "كتب ابل", "أبل بوكس",
            "apple podcasts", "ابل بودكاست", "بودكاست ابل", "أبل بودكاست"
        ],
        
        "برامج وتطبيقات": [
            "canva", "كانفا", "كانفا برو", "canva pro",
            "adobe", "أدوبي", "ادوبي", "أدوبي كريتيف كلاود",
            "microsoft", "مايكروسوفت", "مايكروسوفت 365", "microsoft 365",
            "office", "اوفيس", "اوفس 365", "office 365",
            "zoom", "زووم", "زوم برو", "zoom pro",
            "dropbox", "دروب بوكس", "دروبوكس", "dropbox plus",
            "google", "جوجل", "google one", "جوجل ون",
            "manus ai", "ai manus", "مانوس اي آي", "مانس اي اي",
            "7lle", "سلة", "7le", "سله",
            "mecca", "مكة", "مكة اب", "makkah app",
            "ibr", "آي بي آر", "ibr app", "ابر",
            "uscb", "يو اس سي بي", "uscb app", "يوسب",
            "chatgpt", "تشات جي بي تي", "openai", "شات جي بي تي",
            "claude", "كلود", "anthropic", "كلاود",
            "notion", "نوشن", "notion pro", "نوشين",
            
            # برامج إضافية شهيرة
            "photoshop", "فوتوشوب", "adobe photoshop", "أدوبي فوتوشوب",
            "illustrator", "اليستريتر", "adobe illustrator", "أدوبي اليستريتر",
            "premiere", "بريمير", "adobe premiere", "أدوبي بريمير",
            "after effects", "افتر افكتس", "adobe after effects", "أدوبي افتر",
            "lightroom", "لايت روم", "adobe lightroom", "أدوبي لايتروم",
            "indesign", "ان ديزاين", "adobe indesign", "أدوبي ان ديزاين",
            "acrobat", "اكروبات", "adobe acrobat", "أدوبي اكروبات",
            "windows", "ويندوز", "windows 10", "ويندوز 11",
            "teams", "تيمز", "microsoft teams", "مايكروسوفت تيمز",
            "outlook", "اوتلوك", "microsoft outlook", "مايكروسوفت اوتلوك",
            "onedrive", "ون درايف", "microsoft onedrive", "مايكروسوفت ون درايف",
            "word", "وورد", "microsoft word", "مايكروسوفت وورد",
            "excel", "اكسل", "microsoft excel", "مايكروسوفت اكسل",
            "powerpoint", "باوربوينت", "microsoft powerpoint", "مايكروسوفت باوربوينت",
            "skype", "سكايب", "microsoft skype", "مايكروسوفت سكايب",
            "github", "جيت هاب", "github copilot", "جيتهاب",
            "figma", "فيجما", "figma pro", "فجما",
            "slack", "سلاك", "slack premium", "سلاك بريميوم",
            "trello", "تريلو", "trello premium", "تريلو بريميوم",
            "evernote", "ايفرنوت", "evernote premium", "ايفر نوت",
            "grammarly", "جرامرلي", "grammarly premium", "جرامارلي",
            "lastpass", "لاست باس", "lastpass premium", "لاستباس",
            "1password", "ون باسوورد", "1password premium", "وان باسوورد",
            "vpn", "في بي ان", "vpn premium", "ڤي بي ان",
            "nordvpn", "نورد في بي ان", "nord vpn", "نورد ڤي بي ان",
            "expressvpn", "اكسبرس في بي ان", "express vpn", "إكسبرس ڤي بي ان"
        ],
        
        "متاجر اشتراكات رقمية": [
            # متاجر محلية سعودية
            "متجر اشتراكاتي", "eshtrakati", "اشتراكاتي", "eshtrakati.com",
            "متجر الاستثناء", "asthanio", "الاستثناء", "asthanio.com",
            "ميتا ديجيتال", "meta digital", "metadigital369", "ميتا رقمي",
            "متجر الكود الرقمي", "coderaqami", "الكود الرقمي", "coderaqami.com",
            "متجر مفتاح", "mftaah", "مفتاح", "mftaah.com",
            "متجر اللورد", "lordstr", "اللورد", "lordstr.com",
            "تركس ستور", "trx store", "s-trx", "متجر تركس",
            "سكاي فليكس", "sky flix", "skyflixes", "سكاى فلكس",
            "آر ام زيد", "rmz", "rmz.gg", "ار ام زد",
            
            # مصطلحات عامة للمتاجر
            "متجر رقمي", "digital store", "منتجات رقمية", "digital products",
            "اشتراكات رقمية", "digital subscriptions", "خدمات رقمية", "digital services",
            "تراخيص برامج", "software licenses", "مفاتيح تنشيط", "activation keys",
            "كوبونات رقمية", "digital coupons", "بطاقات رقمية", "digital cards",
            "حسابات مشتركة", "shared accounts", "حسابات مميزة", "premium accounts",
            "اشتراك مدى الحياة", "lifetime subscription", "اشتراك سنوي", "annual subscription",
            "اشتراك شهري", "monthly subscription", "اشتراك تعليمي", "educational subscription",
            "حساب تعليمي", "educational account", "حساب مجاني", "free account",
            "ترقية حساب", "account upgrade", "تجديد اشتراك", "subscription renewal"
        ]
    },
    
"🏛️ خدمات حكومية": {
        "فواتير حكومية": [
            "وزارة", "ministry", "بلدية", "municipality",
            "جوازات", "passport", "مرور", "traffic",
            "أحوال مدنية", "civil affairs", "عدل", "justice"
        ],
        "رسوم حكومية": [
            "رسوم حكومية", "government fees", "رسوم وزارة",
            "رسوم جوازات", "رسوم مرور", "رسوم بلدية",
            "رسوم تصديق", "authentication fees", "رسوم استخراج"
        ]
    },

    
    "💳 رسوم بنكية": {
        "رسوم خدمات بنكية": [
            "رسوم", "fees", "رسم خدمة",
            "رسوم تحويل", "transfer fees", "رسوم معاملة",
            "رسوم صيانة", "maintenance fees", "رسوم شهرية",
            "رسوم سحب", "withdrawal fees", "رسوم صراف",
            "رسوم بطاقة", "card fees", "رسوم سنوية",
            "عمولة", "commission", "عمولات",
            "رسوم تحويل", "رسوم تحويل بنكي", "bank transfer fees",
            "رسوم خارجية", "foreign fees", "رسوم تحويل دولي",
            "CITY: Digital Channel ﺭﺳﻮﻡ ﺗﺤﻮﻳﻞ",
            "ﺗﺤﻮﻳﻞ ﺩﺍﺧﻠﻲ ﺻﺎﺩﺭ NCBK82824148ALPO / ﺭﺳﻮﻡ ﺣﻮﺍﻟﺔ",
            "رسوم ديجيتال", "CITY: Digital Channel", "رسوم digital",
            "digital channel رسوم", "ضريبة القيمة المضافة",
             "ضريبة", 
        ],
        
        "بطاقة ائتمانية": [
            "مدفوعات بطاقة إئتمانية", "CARD: 430259 PAYMENT", "بطاقة ائتمان",
            "credit card payment", "سداد بطاقة ائتمانية", "payment credit card",
            "مدفوعات بطاقة", "card payment", "سداد فيزا", "visa payment",
            "سداد ماستركارد", "mastercard payment", "بطاقة ائتمانية",
            "credit card", "card 430259", "CARD:", "PAYMENT",
            "ﻣﺪﻓﻮﻋﺎﺕ ﺑﻄﺎﻗﺔ ﺇﺋﺘﻤﺎﻧﻴﺔ"
        ],
        
        "ضريبة القيمة المضافة": [
            "ضريبة القيمة المضافة",
            "ضريبة",  "ضرائب",
            "القيمة المضافة", "value added tax", "ضريبة 15%",
            "ضريبة مضافة", "added tax", "ضريبة قيمة",
            "CITY: Digital Channel ﺿﺮﻳﺒﺔ ﺍﻟﻘﻴﻤﺔ ﺍﻟﻤﻀﺎﻓﺔ"
        ]
    },
    
    "💊 صحة وأدوية": {
    "صيدليات": [
        # صيدليات كبيرة
        "صيدلية", "pharmacy", "صيدليات", "pharmacies",
        "النهدي", "nahdi", "صيدليات النهدي", "al nahdi",
        "الدواء", "dawaa", "صيدليات الدواء", "aldawaa",
        "يونايتد", "united", "صيدليات المتحدة", "united pharmacies",
        "بوتس", "boots", "بوتس صيدلية", "boots pharmacy",
        "دواء", "medicine", "أدوية", "medications",
        "علاج", "drug", "عقاقير", "treatment",
        "صيدليات المتحدة", "united pharmaci", "المتحده صيدليات",
        "صيدلية النهدي", "al nahdi pharma", "nahdi al pharma",
        "توازن الصحة", "health balance", "balance health",
        
        # صيدليات أخرى
        "صيدلية الحياة", "life pharmacy", "حياة صيدلية",
        "صيدلية الشفاء", "shifa pharmacy", "شفاء صيدلية",
        "صيدلية الأمل", "amal pharmacy", "أمل صيدلية",
        "صيدلية المدينة", "city pharmacy", "مدينة صيدلية",
        "صيدلية الصحة", "health pharmacy", "صحة صيدلية",
        "صيدلية الأطباء", "doctors pharmacy", "أطباء صيدلية",
        "صيدلية الإيمان", "iman pharmacy", "إيمان صيدلية",
        "صيدلية الرحمة", "rahma pharmacy", "رحمة صيدلية",
        "صيدلية الخير", "kheir pharmacy", "خير صيدلية",
        "صيدلية الحي", "neighborhood pharmacy", "حي صيدلية",
        "صيدلية 24", "24 hour pharmacy", "صيدلية ٢٤ ساعة",
        "صيدلية ليلية", "night pharmacy", "ليلية صيدلية",
        "وصفة طبية", "prescription", "روشتة",
        "أدوية بدون وصفة", "otc", "over the counter",
        "مكملات غذائية", "supplements", "فيتامينات",
        "كريمات", "creams", "مراهم",
        "قطرات", "drops", "شراب دواء"
    ],
    
    "عيادات ومستشفيات": [
        # مستشفيات حكومية
        "عيادة", "clinic", "عيادات", "clinics",
        "مستشفى", "hospital", "مستشفيات", "hospitals",
        "طبيب", "doctor", "دكتور", "dr",
        "مركز طبي", "medical center", "مراكز طبية",
        "مستوصف", "dispensary", "مستوصفات",
        "تحليل", "lab", "مختبر", "laboratory",
        "أشعة", "xray", "تصوير طبي",
        "سونار", "ultrasound", "الترا ساوند",
        "رنين مغناطيسي", "mri", "أشعة مقطعية",
        "ct scan", "تصوير بالرنين", "أشعة تشخيصية",
        
        # مستشفيات خاصة
        "مستشفى الملك فيصل", "king faisal hospital", "فيصل التخصصي",
        "مستشفى سليمان فقيه", "dr soliman fakeeh", "فقيه للرعاية",
        "مستشفى الحبيب", "al habib hospital", "الحبيب الطبي",
        "مستشفى السعودي الألماني", "saudi german hospital", "السعودي الألماني",
        "مستشفى دله", "dallah hospital", "دله الصحية",
        "مستشفى الأهلي", "al ahli hospital", "الأهلي للطب",
        "مستشفى بقشان", "bagshan hospital", "بقشان الطبي",
        "مستشفى المركز الطبي", "medical center hospital", "المركز الطبي",
        "مستشفى الاتحاد", "al ettihad hospital", "الاتحاد الطبي",
        "مستشفى النور", "al noor hospital", "النور التخصصي",
        
        # عيادات متخصصة
        "مركز أسنان", "dental center", "عيادة أسنان",
        "عيادة جلدية", "dermatology clinic", "طب جلدي",
        "عيادة عيون", "eye clinic", "طب عيون",
        "عيادة أطفال", "pediatric clinic", "طب أطفال",
        "عيادة نساء", "gynecology clinic", "طب نساء وولادة",
        "عيادة باطنية", "internal medicine", "طب باطني",
        "عيادة عظام", "orthopedic clinic", "طب عظام",
        "عيادة قلب", "cardiology clinic", "طب قلب",
        "عيادة أنف وأذن", "ent clinic", "أذن أنف حنجرة",
        "عيادة تجميل", "cosmetic clinic", "جراحة تجميل",
        "عيادة نفسية", "psychiatry clinic", "طب نفسي",
        "عيادة تغذية", "nutrition clinic", "تغذية علاجية",
        "عيادة علاج طبيعي", "physiotherapy", "العلاج الطبيعي",
        
        # مختبرات ومراكز تشخيص
        "مختبر البرج", "al borg lab", "برج المختبرات",
        "مختبر المدار", "al madar lab", "المدار للتحاليل",
        "مختبر الرازي", "al razi lab", "الرازي للتحاليل",
        "مختبر دلة", "dallah lab", "دلة للتحاليل",
        "مختبر ابن سينا", "ibn sina lab", "ابن سينا للتحاليل",
        "تحليل دم", "blood test", "فحص دم",
        "تحليل بول", "urine test", "فحص بول",
        "تحليل سكر", "glucose test", "فحص سكري",
        "تحليل كوليسترول", "cholesterol test", "فحص دهون",
        "تحليل وظائف كلى", "kidney function", "فحص كلى",
        "تحليل وظائف كبد", "liver function", "فحص كبد",
        "تحليل هرمونات", "hormone test", "فحص هرموني",
        "تحليل حمل", "pregnancy test", "فحص حمل",
        "تحليل فيتامينات", "vitamin test", "فحص فيتامين",
        "تحليل كورونا", "covid test", "فحص كوفيد",
        "pcr test", "مسحة كورونا", "اختبار مستضد",
        
        # خدمات طبية أخرى
        "طوارئ", "emergency", "قسم طوارئ",
        "إسعاف", "ambulance", "سيارة إسعاف",
        "عملية جراحية", "surgery", "جراحة",
        "منظار", "endoscopy", "تنظير",
        "قسطرة", "catheter", "قسطرة قلبية",
        "غسيل كلى", "dialysis", "ديال",
        "علاج كيماوي", "chemotherapy", "كيماوي",
        "علاج إشعاعي", "radiotherapy", "إشعاعي",
        "زراعة أعضاء", "transplant", "زراعة",
        "تأهيل طبي", "rehabilitation", "إعادة تأهيل",
        "رعاية مركزة", "icu", "عناية مركزة",
        "حضانة أطفال", "nicu", "عناية أطفال",
        "ولادة", "delivery", "قسم ولادة",
        "عيادة تطعيمات", "vaccination", "لقاحات"
    ]
},
    
    "🚚 شحن وتوصيل": {
        "شركات شحن": [
            # شركات محلية
            "أرامكس", "aramex", "ارامكس السعودية",
            "smsa", "اس ام اس اي", "smsa express",
            "زاجل", "zajil", "زاجل اكسبرس",
            "البريد السعودي", "saudi post", "بريد السعودية",
            "سبل", "spl", "سبل اكسبرس",
            
            # شركات عالمية
            "dhl", "دي اتش ال", "dhl express",
            "فيديكس", "fedex", "فيدكس اكسبرس",
            "ups", "يو بي اس", "ups express",
            "tnt", "تي ان تي", "tnt express",
            
            # شركات اخرى
            "نقل", "cargo", "شحن سريع",
            "express shipping", "توصيل سريع", "fast delivery"
        ]
    },
    
    "🏠 سكن وفواتير": {
        "إيجار": [
            "إيجار", "rent", "أجار", "إيجار شقة",
            "شقة", "apartment", "فيلا", "villa",
            "سكن", "housing", "عقار", "real estate",
            "استئجار", "rental", "تأجير عقار",
            "دور", "floor", "منزل", "house",
            "غرفة", "room", "استوديو", "studio"
        ],
        
        "مرافق": [
            # الكهرباء
            "كهرباء", "electricity", "الشركة السعودية للكهرباء",
            "sec", "سيك", "فاتورة كهرباء",
            
            # الماء
            "ماء", "water", "مياه", "مياه وطنية",
            "صرف صحي", "sewage", "شركة المياه",
            
            # الغاز
            "غاز", "gas", "غاز طبيعي",
            "أسطوانة غاز", "gas cylinder", "سامغاز",
            
            # الاتصالات
            "موبايلي الألياف", "mobily fiber", "stc fiber",
            "زين فايبر", "zain fiber", "انترنت منزلي"
        ]
    },
    
    "🎓 تعليم وكتب": {
        "دورات تعليمية": [
            # منصات عالمية
            "udemy", "يوديمي", "يودمي",
            "coursera", "كورسيرا", "كورسرا",
            "edx", "ادكس", "اي دي اكس",
            "دورة", "course", "كورس",
            "تدريب", "training", "تريننغ",
            "معهد", "institute", "أكاديمية",
            "academy", "اكاديمية", "اكادمية",
            
            # منصات محلية
            "طريق", "tariiq", "أريد",
            "uread", "معارف", "maaref",
            "ادراك", "edraak", "رواق",
            "rwaq", "نون اكادمي", "noon academy"
        ],
        
        "كتب ومستلزمات": [
            "كتاب", "book", "كتب",
            "قرطاسية", "stationery", "ستيشنري",
            "أدوات مدرسية", "school supplies", "مستلزمات مدرسية",
            "جامعة", "university", "مدرسة",
            "school", "مكتبة جرير", "jarir bookstore",
            "أقلام", "pens", "دفاتر",
            "notebooks", "حقيبة مدرسية", "school bag",
            "آلة حاسبة", "calculator", "مسطرة",
            "ruler", "مبراة", "sharpener"
        ]
    },
    
    "🏦 معاملات بنكية": {
        "سحب نقدي": [
            "سحب نقدي", "atm", "صراف", "صراف آلي",
            "withdrawal", "cash", "نقد", "كاش",
            "سحب نقدي بالريال", "cash withdrawal", "سحب نقود",
            "صراف بنكي", "bank atm", "سحب فوري"
        ],
        
        "إيداع": [
            "إيداع نقدي", "إيداع", "deposit", "إيداع نقود",
            "cash deposit", "إيداع راتب", "salary deposit",
            "مكافأة طلاب", "students rewards", "مكافأة",
            "uni rewards", "rewards students", "reward",
            "حوالة واردة", "incoming transfer", "تحويل وارد",
            "إيداع شيك", "check deposit", "إيداع تحويل"
        ]
    },
    
    "🎁 هدايا ومناسبات": {
        "هدايا": [
            "هدية", "gift", "هدايا", "gifts",
            "تغليف", "wrapping", "تغليف هدايا",
            "بطاقة هدايا", "gift card", "قفت كارد",
            "ورد", "flowers", "ورود", "زهور",
            "باقة", "bouquet", "بوكيه",
            "متجر هدايا", "gift shop", "هدايا وتحف",
            "تحف", "souvenirs", "تذكارات",
            "azahar al ajaz", "ازهار الاعجاز", "أزهار الإعجاز", "ازهار الاجاز",
            "azahar", "أزهار", "زهور", "الاعجاز", "ajaz flowers",
            "مؤسسة ازهار", "azhar", "زهور الإعجاز", "flowers ajaz",
            "ورود", "باقات", "هدايا الأزهار", "azahar gifts"
        ],
        
        "مناسبات": [
            "مناسبة", "occasion", "مناسبات",
            "عيد", "eid", "عيد الفطر",
            "عيد الأضحى", "زواج", "wedding",
            "عرس", "marriage", "ميلاد",
            "birthday", "تخرج", "graduation",
            "خطوبة", "engagement", "احتفال",
            "celebration", "حفلة", "party"
        ]
    },
    
    "💼 عمل ومشاريع": {
        "إعلانات وتسويق": [
            "إعلان", "ads", "advertisement", "اعلانات",
            "تسويق", "marketing", "تسويق رقمي",
            "فيسبوك", "facebook", "فيس بوك",
            "انستجرام", "instagram", "انستا",
            "تويتر", "twitter", "تويتر اعلانات",
            "جوجل ادز", "google ads", "جوجل اعلانات",
            "سناب", "snapchat", "سناب اعلانات",
            "تيك توك", "tiktok", "تيك توك اعلانات",
            "يوتيوب اعلانات", "youtube ads", "اعلانات يوتيوب"
        ],
        
        "خدمات رقمية": [
            "دومين", "domain", "نطاق",
            "استضافة", "hosting", "هوستنج",
            "vps", "في بي اس", "سيرفر",
            "server", "خادم", "godaddy",
            "namecheap", "cloudflare", "كلاود فلير",
            "aws", "amazon web services", "امازون ويب",
            "microsoft azure", "مايكروسوفت ازور", "ازور",
            "google cloud", "جوجل كلاود", "كلاود جوجل"
        ]
    },
    
    "🕌 تبرعات وخيرية": {
        "جمعيات خيرية": [
            "إحسان", "ehsan", "احسان",
            "تبرع", "donation", "تبرعات",
            "صدقة", "charity", "صدقات",
            "زكاة", "zakat", "زكاة مال",
            "جمعية", "association", "جمعيات",
            "خيرية", "charitable", "جمعية خيرية",
            "وقف", "endowment", "اوقاف",
            "كافل", "kafil", "كفالة",
            "سقيا", "saqia", "سقيا الماء",
            "الوليد الخيرية", "alwaleed philanthropies", "مؤسسة الوليد",
            "مؤسسة محمد", "mohammed foundation", "الملك عبدالعزيز الخيرية"
        ]
    },
    
    "🛫 سفر وتنقل": {
        "طيران وفنادق": [
            # طيران محلي
            "طيران", "airlines", "الخطوط السعودية",
            "saudia", "السعودية", "ناس", "flynas",
            "فلاي ناس", "flynas airlines", "طيران ناس",
            
            # طيران اقليمي وعالمي
            "فلاي دبي", "flydubai", "طيران دبي",
            "العربية", "air arabia", "طيران العربية",
            "الامارات", "emirates", "طيران الامارات",
            "القطرية", "qatar airways", "طيران قطر",
            "الكويتية", "kuwait airways", "طيران الكويت",
            "المصرية", "egyptair", "طيران مصر",
            
            # حجز فنادق
            "فندق", "hotel", "فنادق",
            "حجز", "booking", "booking.com",
            "agoda", "اجودا", "اغودا",
            "trivago", "تريفاجو", "expedia",
            "اكسبيديا", "hotels.com", "هوتيلز"
        ],
        
        "مواصلات": [
            # تطبيقات المواصلات
            "أوبر", "uber", "اوبر",
            "كريم", "careem", "كريم تاكسي",
            "تاكسي", "taxi", "كابتن",
            "captain", "ليموزين", "limousine",
            
            # مواصلات عامة
            "باص", "bus", "حافلة",
            "مترو", "metro", "قطار",
            "train", "الحرمين", "haramain",
            "قطار الحرمين", "haramain train", "سكة حديد",
            
            # تأجير مركبات
            "تأجير دراجة", "bike rental", "سكوتر",
            "scooter", "دراجة كهربائية", "electric bike"
        ]
    },
    
    "🛠️ خدمات منزلية وصيانة": {
        "خدمات منزلية": [
            "سباك", "plumber", "سباكة",
            "كهربائي", "electrician", "كهرباء منزلية",
            "تكييف", "ac", "air condition",
            "صيانة تكييف", "ac maintenance", "تكييف مركزي",
            "نجار", "carpenter", "نجارة",
            "دهان", "painter", "دهانات",
            "صيانة", "maintenance", "صيانة منزلية",
            "إصلاح", "repair", "تصليح",
            "fix", "فكس", "تركيب",
            "installation", "تركيبات", "فني صيانة",
            # من المعاملات
            "Musaned Contrac", "مساند للمقاولات", "مساند كونتراكت",
            "ﻋﻤﻠﻴﺔ ﺷﺮﺍﺀ ﻋﺒﺮ ﺍﻹﻧﺘﺮﻧﺖ", "musaned"
        ],
        
        "تنظيف منزلي": [
            "تنظيف", "cleaning", "تنظيف منزلي",
            "عاملة تنظيف", "house cleaner", "خادمة",
            "maid", "مايد", "شغالة",
            "تنظيف عميق", "deep cleaning", "تنظيف شامل",
            "شركة تنظيف", "cleaning company", "تنظيف مكاتب",
            "تنظيف سجاد", "carpet cleaning", "تنظيف موكيت"
        ]
    },
    
    "📈 استثمارات": {
        "تداول": [
            # منصات تداول عالمية
            "binance", "بينانس", "بايننس",
            "تداول", "trading", "الراجحي كابيتال",
            "alrajhi capital", "الأهلي كابيتال", "snb capital",
            "عملات رقمية", "crypto", "كريبتو",
            "bitcoin", "بيتكوين", "btc",
            
            # منصات محلية
            "تداول السعودية", "tadawul", "تداول",
            "سوق الأسهم", "stock market", "الأسهم السعودية",
            "أسهم", "stocks", "الأسهم",
            "صناديق", "funds", "صندوق استثمار",
            "mutual funds", "etf", "ريت"
        ]
    },
    
    "⚽ رياضة ولياقة": {
        "أندية رياضية": [
            "نادي", "club", "نادي رياضي",
            "جيم", "gym", "فتنس",
            "fitness", "نادي لياقة", "fitness center",
            "جولد جيم", "gold's gym", "فتنس تايم",
            "fitness time", "بودي ماسترز", "body masters",
            "فتنس فرست", "fitness first", "انيرجي",
            "energy fitness", "باور هاوس", "power house"
        ],
        
        "معدات رياضية": [
            "معدات رياضية", "sports equipment", "أدوات رياضة",
            "ديكاثلون", "decathlon", "سن اند ساند",
            "sun and sand", "نايك", "nike",
            "اديداس", "adidas", "بوما", "puma",
            "اندر ارمور", "under armour", "ريبوك", "reebok"
        ]
    },
    
    "🔧 أدوات وهاردوير": {
        "أدوات ومعدات": [
            "أدوات", "tools", "هاردوير",
            "hardware", "معدات", "equipment",
            "ساكو", "saco", "ace", "ايس",
            "هوم سنتر", "home center", "بناء",
            "construction", "مسامير", "screws",
            "مفاتيح", "keys", "أقفال", "locks"
        ]
    }
}

# قائمة وسائل الدفع الموسعة
PAYMENT_METHODS = [
    # بطاقات ووسائل الدفع
    "mada", "مدى", "مدي", "visa", "فيزا", "ڤيزا",
    "mastercard", "ماستركارد", "ماستر كارد", "master card",
    "apple pay", "apple cash", "ابل باي", "ابل كاش",
    "google pay", "جوجل باي", "google wallet", "جوجل محفظة",
    "samsung pay", "سامسونج باي", "samsung wallet",
    "stc pay", "stcpay", "اس تي سي باي", "stc wallet",
    "urpay", "يور باي", "اور باي", "mada pay", "مدى باي",
    "paypal", "بايبال", "باي بال",
    "tabby", "تابي", "tamara", "تمارا", "tammara",
    
    # أرقام البطاقات المخفية
    r"\*{3,}\d{4}", r"\d{4}\s*\*{3,}", r"xxxx\d{4}",
    r"\*{4,}", r"x{4,}", r"\d{4}x{4,}",
    
    # رموز القنوات وطرق الدفع
    "digital channel", "pos", "atm", "online", "contactless",
    "عدم اللمس", "بدون لمس", "tap", "تاب", "wave", "ويف",
    "chip", "تشيب", "شريحة", "magnetic", "مغناطيسي",
    "swipe", "سوايب", "magnetic stripe", "الشريط المغناطيسي"
]

# كلمات يجب تجاهلها عند التصنيف (موسعة)
IGNORE_WORDS = [
    # ضرائب ورسوم
    "vat", "chrg", "charges", "fee", "tax", "fees",
    "رسوم", "ضريبة", "ضرائب", "عمولة", "رسم",
    
    # مدن ومناطق
    "city", "jeddah", "jed", "riyadh", "ryd", "mecca", "makkah",
    "dammam", "dmm", "khobar", "khb", "taif", "taf",
    "medina", "mad", "abha", "ahb", "tabuk", "tbk",
    "hail", "hil", "qassim", "qas", "jazan", "jzn",
    "najran", "egr", "baha", "bha", "jouf", "jof",
    
    # دول ومناطق
    "sa", "sau", "saudi", "arabia", "ksa", "السعودية",
    "gcc", "gulf", "uae", "kuwait", "qatar", "bahrain",
    "oman", "egypt", "jordan", "lebanon", "syria",
    
    # مصطلحات الدفع
    "payment", "purchase", "debit", "credit", "transaction",
    "عملية", "شراء", "دفع", "معاملة", "خصم", "ائتمان",
    
    # تواريخ وأوقات
    "am", "pm", "date", "time", "تاريخ", "وقت",
    
    # معرفات تقنية
    "id", "ref", "trn", "mcc", "terminal", "merchant",
    "معرف", "مرجع", "تاجر", "طرفية"
]


def normalize_arabic_text(text: str) -> str:
    """
    تطبيع النص العربي ومعالجة المشاكل الشائعة
    """
    if not text:
        return ""
    
    # تطبيع Unicode
    text = unicodedata.normalize('NFKC', text)
    
    # إزالة علامات التحكم غير المرئية
    text = ''.join(char for char in text if unicodedata.category(char)[0] != 'C')
    
    # إزالة علامات الاتجاه
    text = text.replace('\u200f', '').replace('\u200e', '')
    text = text.replace('\u202a', '').replace('\u202b', '').replace('\u202c', '')
    
    # تحويل الأرقام العربية إلى إنجليزية للتوحيد
    arabic_numerals = '٠١٢٣٤٥٦٧٨٩'
    english_numerals = '0123456789'
    trans_table = str.maketrans(arabic_numerals, english_numerals)
    text = text.translate(trans_table)
    
    # توحيد الحروف العربية المتشابهة
    replacements = {
        'أ': 'ا', 'إ': 'ا', 'آ': 'ا',
        'ة': 'ه',
        'ى': 'ي',
        'ؤ': 'و',
        'ئ': 'ي'
    }
    
    for old, new in replacements.items():
        text = text.replace(old, new)
    
    return text


def get_all_keywords() -> Set[str]:
    """
    استخراج جميع الكلمات المفتاحية من قاموس التصنيفات
    """
    all_keywords = set()
    
    for main_category, subcategories in EXPENSE_CATEGORIES.items():
        for sub_category, keywords in subcategories.items():
            for keyword in keywords:
                all_keywords.add(keyword.lower())
                # إضافة النسخة المطبعة أيضاً
                normalized = normalize_arabic_text(keyword.lower())
                if normalized != keyword.lower():
                    all_keywords.add(normalized)
    
    return all_keywords


def extract_payment_method(description: str) -> Optional[str]:
    """
    استخراج وسيلة الدفع من الوصف بدقة أكبر
    """
    if not description:
        return None
    
    desc_lower = description.lower()
    desc_normalized = normalize_arabic_text(desc_lower)
    
    # ترتيب أولوية البحث (الأكثر تحديداً أولاً)
    priority_methods = [
        ("apple pay", "Apple Pay"),
        ("google pay", "Google Pay"),
        ("samsung pay", "Samsung Pay"),
        ("stc pay", "STC Pay"),
        ("stcpay", "STC Pay"),
        ("اس تي سي باي", "STC Pay"),
        ("urpay", "UrPay"),
        ("يور باي", "UrPay"),
        ("mada pay", "Mada Pay"),
        ("مدى باي", "Mada Pay"),
        ("paypal", "PayPal"),
        ("بايبال", "PayPal"),
        ("tabby", "Tabby"),
        ("تابي", "Tabby"),
        ("tamara", "Tamara"),
        ("تمارا", "Tamara"),
        ("mastercard", "Mastercard"),
        ("ماستركارد", "Mastercard"),
        ("visa", "Visa"),
        ("فيزا", "Visa"),
        ("mada", "Mada"),
        ("مدى", "Mada"),
        ("contactless", "بدون لمس"),
        ("عدم اللمس", "بدون لمس"),
        ("pos", "نقطة البيع"),
        ("atm", "صراف آلي")
    ]
    
    for method_key, method_name in priority_methods:
        if method_key in desc_lower or method_key in desc_normalized:
            return method_name
    
    # البحث عن أنماط أرقام البطاقات
    card_patterns = [
        r"\*{3,}\d{4}",
        r"\d{4}\s*\*{3,}",
        r"xxxx\d{4}",
        r"\*{4,}",
        r"x{4,}"
    ]
    
    for pattern in card_patterns:
        if re.search(pattern, desc_lower):
            return "بطاقة بنكية"
    
    return None


def clean_for_classification(description: str, preserve_keywords: bool = True) -> str:
    """
    تنظيف الوصف للتصنيف مع خيار الحفاظ على الكلمات المفتاحية
    """
    if not description:
        return description
    
    # تطبيع النص أولاً
    clean_desc = normalize_arabic_text(description)
    
    # الحصول على جميع الكلمات المفتاحية إذا كنا نريد الحفاظ عليها
    all_keywords = get_all_keywords() if preserve_keywords else set()
    
    # حفظ الكلمات المفتاحية الموجودة في النص
    preserved_keywords = []
    if preserve_keywords:
        desc_lower = clean_desc.lower()
        for keyword in all_keywords:
            if keyword in desc_lower:
                # البحث عن موقع الكلمة المفتاحية وحفظها
                pattern = re.compile(re.escape(keyword), re.IGNORECASE)
                matches = pattern.finditer(clean_desc)
                for match in matches:
                    preserved_keywords.append((match.start(), match.end(), match.group()))
    
    # إزالة وسائل الدفع فقط إذا لم تكن من الكلمات المفتاحية
    for method in PAYMENT_METHODS:
        if isinstance(method, str):
            method_lower = method.lower()
            if method_lower not in all_keywords:
                pattern = re.compile(re.escape(method), re.IGNORECASE)
                clean_desc = pattern.sub('', clean_desc)
        else:  # regex pattern
            clean_desc = re.sub(method, '', clean_desc, flags=re.IGNORECASE)
    
    # إزالة الكلمات غير المهمة فقط إذا لم تكن من الكلمات المفتاحية
    for word in IGNORE_WORDS:
        word_lower = word.lower()
        if word_lower not in all_keywords:
            pattern = re.compile(r'\b' + re.escape(word) + r'\b', re.IGNORECASE)
            clean_desc = pattern.sub('', clean_desc)
    
    # إزالة الأجزاء غير المهمة (أنماط أكثر شمولية)
    patterns_to_remove = [
        # معرفات المدن والمناطق (فقط إذا لم تكن جزء من كلمة مفتاحية)
        r'[A-Z]{3}\d+[A-Z]{2}\s*[A-Z]+',
        r'JEDHAH?\s+MADA',
        r'JEDDAH\s+MADA',
        r'[A-Z]{3}\s+SA\b',
        
        # أرقام البطاقات والمراجع
        r'\*{3,}\d{4}',
        r'\d{4}\*{3,}',
        r'xxxx\d{4}',
        r'\*{4,}',
        r'x{4,}',
        
        # معلومات تقنية
        r'MCC[:\-]?\s*\d+',
        r'ID:\s*\d+',
        r'REF:\s*\w+',
        r'TRN:\s*\w+',
        r'TERMINAL:\s*\w+',
        r'MERCHANT:\s*\w+',
        
        # أرقام مرجعية طويلة
        r'SANBCBNK\d+',
        r'\b\d{10,}\b',
        
        # عبارات الدفع (مع التحقق من الكلمات المفتاحية)
        r'ﺷﺮﺍﺀ ﻋﺒﺮ ﻧﻘﺎﻁ ﺑﻴﻊ',
        r'ﻋﻤﻠﻴﺔ ﺷﺮﺍﺀ ﻋﺒﺮ ﺍﻹﻧﺘﺮﻧﺖ',
        r'VAT CHRG:\s*[\d.]+\s*[\d.]+'
    ]
    
    # تطبيق أنماط الإزالة مع الحذر
    for pattern in patterns_to_remove:
        # تحقق من أن النمط لا يحذف كلمة مفتاحية
        temp_desc = re.sub(pattern, ' ', clean_desc, flags=re.IGNORECASE)
        
        # إذا لم نحذف أي كلمة مفتاحية، نطبق التغيير
        if preserve_keywords:
            temp_lower = temp_desc.lower()
            keywords_intact = all(any(keyword in temp_lower for keyword in all_keywords 
                                    if keyword in clean_desc.lower()) 
                                for keyword in all_keywords 
                                if keyword in clean_desc.lower())
            if keywords_intact:
                clean_desc = temp_desc
        else:
            clean_desc = temp_desc
    
    # تنظيف المسافات الزائدة والرموز
    clean_desc = re.sub(r'[^\w\s\u0600-\u06FF\-]', ' ', clean_desc)
    clean_desc = re.sub(r'\s+', ' ', clean_desc).strip()
    
    return clean_desc


def classify_transaction(description: str, debug: bool = False) -> Tuple[str, str]:
    """
    تصنيف المعاملة إلى تصنيف رئيسي وفرعي مع تحسينات
    """
    if not description:
        return "❓ غير مصنف", "غير محدد"
    
    # تطبيع النص أولاً
    desc_normalized = normalize_arabic_text(description)
    
    # تنظيف الوصف مع الحفاظ على الكلمات المفتاحية
    desc_clean = clean_for_classification(desc_normalized, preserve_keywords=True)
    
    # إذا لم يبقَ شيء بعد التنظيف، استخدم النص المطبع
    if not desc_clean.strip():
        desc_clean = desc_normalized
    
    desc_lower = desc_clean.lower()
    desc_no_spaces = desc_lower.replace(" ", "")  # للبحث عن الكلمات الملتصقة
    
    if debug:
        print(f"DEBUG: الوصف الأصلي: {description}")
        print(f"DEBUG: بعد التطبيع: {desc_normalized}")
        print(f"DEBUG: بعد التنظيف: {desc_clean}")
        print(f"DEBUG: بدون مسافات: {desc_no_spaces}")
    
    # قائمة الأولويات الخاصة (يتم فحصها أولاً)
    priority_checks = [
        # بطاقة ائتمانية
        {
            "keywords": ["مدفوعات بطاقة إئتمانية", "card: 430259 payment", "ﻣﺪﻓﻮﻋﺎﺕ ﺑﻄﺎﻗﺔ ﺇﺋﺘﻤﺎﻧﻴﺔ"],
            "category": "💳 رسوم بنكية",
            "subcategory": "بطاقة ائتمانية"
        },
        # تحويلات بنكية
        {
            "keywords": ["ben id", "benbk", "تحويل الى الاهل والاصدقاء", "حوالة فورية محلية صادرة",
                        "تحويل لأفراد", "تحويل داخلي صادر", "الأسرة أو الأصدقا"],
            "category": "🔄 تحويلات مالية",
            "subcategory": "تحويل داخلي/خارجي"
        },
        # قروض وأقساط
        {
            "keywords": ["خصم قسط قرض", "خصم قسط تمويل", "قسط عقاري", "قسط تأجيري"],
            "category": "🔄 تحويلات مالية",
            "subcategory": "تمويل وسداد"
        },
        # خدمات سداد
        {
            "keywords": ["مدفوعات سداد", "093-المخالفات المرورية", "090-خدمات المقيمين",
                        "002-الشركة السعودية للكهرباء", "044-زين"],
            "category": "🔄 تحويلات مالية",
            "subcategory": "تمويل وسداد"
        },
        # رسوم بنكية
        {
            "keywords": ["city: digital channel", "رسوم تحويل", "ضريبة القيمة المضافة"],
            "condition": lambda desc: ("رسوم" in desc or "ضريبة" in desc) and "digital channel" in desc,
            "category": "💳 رسوم بنكية",
            "subcategory": "رسوم خدمات بنكية"
        },
        # خدمات آبل
        {
            "keywords": ["apple pay - دولية", "apple pay ون ديولانوما", "wiatro city",
                        "dewanlamashshakira1", "apple pay عملية دولية", "mcc- 6540"],
            "category": "🎧 اشتراكات تلقائية",
            "subcategory": "خدمات آبل"
        }
    ]
    
    # فحص الأولويات الخاصة
    for check in priority_checks:
        if "condition" in check:
            if check["condition"](desc_lower):
                if debug:
                    print(f"DEBUG: تطابق مع شرط خاص: {check['category']} - {check['subcategory']}")
                return check["category"], check["subcategory"]
        else:
            for keyword in check["keywords"]:
                keyword_lower = keyword.lower()
                keyword_normalized = normalize_arabic_text(keyword_lower)
                
                if (keyword_lower in desc_lower or 
                    keyword_lower in desc_no_spaces or
                    keyword_normalized in desc_lower or
                    keyword_normalized in desc_no_spaces):
                    if debug:
                        print(f"DEBUG: تطابق أولوية مع: {keyword}")
                    return check["category"], check["subcategory"]
    
    # البحث في جميع التصنيفات مع نظام نقاط محسن
    best_match = None
    best_score = 0
    best_keyword = ""
    all_matches = []  # لحفظ جميع التطابقات للـ debug
    
    for main_category, subcategories in EXPENSE_CATEGORIES.items():
        for sub_category, keywords in subcategories.items():
            for keyword in keywords:
                keyword_lower = keyword.lower()
                keyword_normalized = normalize_arabic_text(keyword_lower)
                keyword_no_spaces = keyword_lower.replace(" ", "")
                
                # تخطي إذا كانت الكلمة قصيرة جداً
                if len(keyword_lower) < 3:
                    continue
                
                # حساب نقاط التطابق بنظام محسن
                score = 0
                match_type = ""
                
                # التحقق من التطابقات المختلفة
                checks = [
                    (keyword_lower == desc_lower, 100, "تطابق كامل"),
                    (keyword_normalized == desc_lower, 98, "تطابق كامل (مطبع)"),
                    (desc_lower.startswith(keyword_lower + ' ') or desc_lower.startswith(keyword_lower), 95, "بداية النص"),
                    (desc_lower.endswith(' ' + keyword_lower) or desc_lower.endswith(keyword_lower), 90, "نهاية النص"),
                    (re.search(r'\b' + re.escape(keyword_lower) + r'\b', desc_lower), 85, "كلمة كاملة"),
                    (re.search(r'\b' + re.escape(keyword_normalized) + r'\b', desc_lower), 83, "كلمة كاملة (مطبعة)"),
                    (keyword_lower in desc_lower, 75, "جزء من النص"),
                    (keyword_normalized in desc_lower, 73, "جزء من النص (مطبع)"),
                    (keyword_no_spaces in desc_no_spaces, 70, "ملتصق")
                ]
                
                for condition, points, match_desc in checks:
                    if condition:
                        score = points
                        match_type = match_desc
                        break
                
                # إضافة نقاط إضافية للكلمات المحددة
                specific_keywords = [
                    "khaled ﺑﺎﺳﻤﺢ", "f. s. t. co", "musaned", "coarse grind", 
                    "aya mall bindaw", "bright stage", "digital channel", "ben id",
                    "apple pay - دولية", "خدمات المقيمين", "رسوم ديجيتال",
                    "مدفوعات بطاقة إئتمانية", "card: 430259"
                ]
                
                if keyword_lower in specific_keywords:
                    score += 20
                    match_type += " (كلمة خاصة)"
                
                # إضافة نقاط للكلمات الطويلة
                if len(keyword_lower) >= 10:
                    score += 10
                elif len(keyword_lower) >= 6:
                    score += 5
                
                # حفظ التطابق إذا كان له نقاط
                if score > 0:
                    all_matches.append({
                        'keyword': keyword,
                        'category': main_category,
                        'subcategory': sub_category,
                        'score': score,
                        'type': match_type
                    })
                
                # تحديث أفضل تطابق
                if score > best_score:
                    best_score = score
                    best_match = (main_category, sub_category)
                    best_keyword = keyword
    
    if debug and all_matches:
        print(f"\nDEBUG: جميع التطابقات:")
        sorted_matches = sorted(all_matches, key=lambda x: x['score'], reverse=True)
        for match in sorted_matches[:5]:  # أعلى 5 تطابقات
            print(f"  - {match['keyword']} ({match['category']} - {match['subcategory']})")
            print(f"    النقاط: {match['score']}, النوع: {match['type']}")
    
    # إذا تم العثور على تصنيف بنقاط كافية
    if best_match and best_score >= 50:  # خفضنا الحد الأدنى
        if debug:
            print(f"\nDEBUG: أفضل تطابق: {best_keyword} ({best_score} نقطة)")
        return best_match
    
    # محاولة أخيرة: البحث عن كلمات مفتاحية عامة
    general_patterns = {
        "🍽️ مطاعم ومقاهي": {
            "patterns": ["restaurant", "cafe", "food", "eat", "coffee", "مطعم", "كافيه", "طعام", "قهوة"],
            "subcategory": "وجبات سريعة"
        },
        "🛒 سوبرماركت وبقالة": {
            "patterns": ["store", "shop", "market", "grocery", "سوق", "متجر", "بقالة", "تموينات"],
            "subcategory": "تموينات وبقالة"
        },
        "🚗 خدمات السيارات": {
            "patterns": ["gas", "fuel", "car", "petrol", "بنزين", "وقود", "سيارة", "محطة"],
            "subcategory": "وقود"
        },
        "💊 صحة وأدوية": {
            "patterns": ["pharma", "medical", "health", "clinic", "صيدلية", "طبي", "صحة", "عيادة"],
            "subcategory": "صيدليات"
        }
    }
    
    for category, data in general_patterns.items():
        for pattern in data["patterns"]:
            if pattern in desc_lower:
                if debug:
                    print(f"DEBUG: تطابق عام مع: {pattern}")
                return category, data["subcategory"]
    
    if debug:
        print(f"DEBUG: لم يتم العثور على تصنيف مناسب")
    
    # إذا لم يتم العثور على أي تصنيف
    return "❓ غير مصنف", "غير محدد"


def clean_description(description: str) -> str:
    """
    تنظيف وصف المعاملة بطريقة شاملة
    """
    if not description:
        return ""
    
    # تحويل إلى نص وتطبيع
    desc = str(description)
    desc = normalize_arabic_text(desc)
    
    # إزالة الأرقام الطويلة والمراجع التقنية
    desc = re.sub(r'\b\d{10,}\b', '', desc)
    desc = re.sub(r'SANBCBNK\d+', '', desc, flags=re.IGNORECASE)
    desc = re.sub(r'\*{4,}\d{4}', '', desc)
    desc = re.sub(r'\d{4}\*{4,}', '', desc)
    
    # إزالة معلومات البنوك والتحويلات التقنية
    technical_patterns = [
        r'REMBK:.*?(?=\s|$)',
        r'SWIFT:.*?(?=\s|$)',
        r'IBAN:.*?(?=\s|$)',
        r'BIC:.*?(?=\s|$)',
        r'REF:.*?(?=\s|$)',
        r'TRN:.*?(?=\s|$)',
        r'ID:\s*\d+',
        r'TERMINAL:\s*\d+',
        r'MERCHANT:\s*\d+',
        r'BATCH:\s*\d+',
        r'TRACE:\s*\d+',
        r'AUTH:\s*\d+',
        r'RRN:\s*\d+'
    ]
    
    for pattern in technical_patterns:
        desc = re.sub(pattern, '', desc, flags=re.IGNORECASE)
    
    # تنظيف المسافات الزائدة
    desc = re.sub(r'\s+', ' ', desc)
    desc = desc.strip()
    
    return desc


# للتوافق مع النظام القديم
KEYWORD_CATEGORIES = EXPENSE_CATEGORIES


if __name__ == "__main__":
    # اختبار التصنيف المحسن
    test_descriptions = [
        "KHALED ﺑﺎﺳﻤﺢ ﻟﻠﺘﺴﻮﻳﻖ Apple Pay - ﺷﺮﺍﺀ ﻋﺒﺮ ﻧﻘﺎﻁ ﺑﻴﻊABDULLAH CITY: JEDH682016JED JEDDAH MADA***8768 VAT CHRG: 0. 00 0. 00",
        "BEN ID: ﺗﺤﻮﻳﻞ ﺩﺍﺧﻠﻲ ﺻﺎﺩﺭ ﺗﺤﻮﻳﻞ ﺍﻟﻰ ﺍﻻﻫﻞ ﻭﺍﻻﺻﺪﻗﺎﺀ",
        "ﺧﺼﻢ ﻗﺴﻂ ﺗﻤﻮﻳﻞ ﺗﺄﺟﻴﺮﻱ",
        "STC Pay CITY: 0000682016SAM MCC- 6540ﻋﻤﻠﻴﺔ ﺷﺮﺍﺀ ﻋﺒﺮ ﺍﻹﻧﺘﺮﻧﺖ Riyadh MADA ***1502 VAT CHRG: 0. 00 0. 00",
        "ﻣﺪﻓﻮﻋﺎﺕ ﺳﺪﺍﺩ 002-ﺍﻟﺸﺮﻛﺔ ﺍﻟﺴﻌﻮﺩﻳﺔ ﻟﻠﻜﻬﺮﺑﺎﺀ-",
        "ﻣﺪﻓﻮﻋﺎﺕ ﺳﺪﺍﺩ 093-ﺍﻟﻤﺨﺎﻟﻔﺎﺕ ﺍﻟﻤﺮﻭﺭﻳﺔ-",
        "F. S. T. Co - Aﺷﺮﻛﺔ ﺍﻣﺪﺍﺩ ﺍﻷﻁ Apple Pay - ﺷﺮﺍﺀ ﻋﺒﺮ ﻧﻘﺎﻁ ﺑﻴﻊCITY: 0000682016SAM RAS TANOURAH MADA***1502 VAT CHRG: 0. 00 0. 00",
        "ﺗﺤﻮﻳﻞ ﺩﺍﺧﻠﻲ ﺻﺎﺩﺭ NCBK82824148ALPO / ﺭﺳﻮﻡ ﺣﻮﺍﻟﺔ",
        "BRIGHT STAGEﻣﺆﺳﺴﺔ ﺍﻟﻤﻨﺼﺔ ﺍﻝ Apple Pay - ﺷﺮﺍﺀ ﻋﺒﺮ ﻧﻘﺎﻁ ﺑﻴﻊEV CITY: 0000682016SAM KHOBAR MADA***1502 VAT CHRG: 0. 00 0. 00",
        "CITY: Digital Channel ﺭﺳﻮﻡ ﺗﺤﻮﻳﻞ",
        "CITY: Digital Channel ﺿﺮﻳﺒﺔ ﺍﻟﻘﻴﻤﺔ ﺍﻟﻤﻀﺎﻓﺔ",
        "CARD: 430259 PAYMENT ﻣﺪﻓﻮﻋﺎﺕ ﺑﻄﺎﻗﺔ ﺇﺋﺘﻤﺎﻧﻴﺔ",
        "Musaned Contrac ﻋﻤﻠﻴﺔ ﺷﺮﺍﺀ ﻋﺒﺮ ﺍﻹﻧﺘﺮﻧﺖCITY: 0000682016SAM Riyadh MADA ***1502VAT CHRG: 0. 00 0. 00",
        "Coarse Grind ﺷﺮﺍﺀ ﻋﺒﺮ ﻧﻘﺎﻁ ﺑﻴﻊ - ﻣﺪﻯ ﺃﺛﻴﺮ ﻛﻮﺭﺱ ﺟﺮﺍﻳﻨﺪCITY: 0000682016SAM JEDDAH MADA ***8768VAT CHRG: 0. 00 0. 00",
        "AYA MALL BINDAWﺑﻦ ﺩﺍﻭﻭﺩ ﺁﻳﺎ ﻣﻮ Apple Pay - ﺷﺮﺍﺀ ﻋﺒﺮ ﻧﻘﺎﻁ ﺑﻴﻊCITY: 0000682016SAM JEDDAH MADA ***8768VAT CHRG: 0. 00 0. 00"
    ]
    
    print("اختبار نظام التصنيف المحسن:")
    print("=" * 80)
    
    success_count = 0
    total_tests = len(test_descriptions)
    
    for i, desc in enumerate(test_descriptions, 1):
        print(f"\n{'=' * 80}")
        print(f"الاختبار رقم {i}")
        print(f"{'=' * 80}")
        
        # تصنيف مع debug
        main_cat, sub_cat = classify_transaction(desc, debug=True)
        payment = extract_payment_method(desc)
        
        print(f"\n📌 النتيجة النهائية:")
        print(f"   التصنيف الرئيسي: {main_cat}")
        print(f"   التصنيف الفرعي: {sub_cat}")
        if payment:
            print(f"   وسيلة الدفع: {payment}")
        
        # تحديد نجاح التصنيف
        if main_cat != "❓ غير مصنف":
            success_count += 1
            print(f"   ✅ تم التصنيف بنجاح")
        else:
            print(f"   ❌ فشل التصنيف")
    
    print(f"\n{'=' * 80}")
    print(f"📊 ملخص النتائج:")
    print(f"✅ نجح في تصنيف: {success_count}/{total_tests} ({success_count/total_tests*100:.1f}%)")
    print(f"❌ فشل في تصنيف: {total_tests-success_count}/{total_tests}")
    print(f"{'=' * 80}")

def get_category_statistics(expense_details):
    """
    حساب إحصائيات التصنيفات بالنظام الجديد
    """
    statistics = {}
    
    # تجميع البيانات حسب التصنيف الرئيسي والفرعي
    for category, transactions in expense_details.items():
        # استخراج التصنيف الرئيسي والفرعي إذا كان بالنظام الجديد
        if " - " in category:
            main_cat, sub_cat = category.split(" - ", 1)
        else:
            # للتوافق مع النظام القديم
            main_cat = category
            sub_cat = "غير محدد"
        
        # تهيئة التصنيف الرئيسي إذا لم يكن موجوداً
        if main_cat not in statistics:
            statistics[main_cat] = {
                'total_amount': 0,
                'transaction_count': 0,
                'subcategories': {}
            }
        
        # تهيئة التصنيف الفرعي
        if sub_cat not in statistics[main_cat]['subcategories']:
            statistics[main_cat]['subcategories'][sub_cat] = {
                'amount': 0,
                'count': 0,
                'transactions': []
            }
        
        # إضافة البيانات
        for trans in transactions:
            amount = trans['amount']
            statistics[main_cat]['total_amount'] += amount
            statistics[main_cat]['transaction_count'] += 1
            statistics[main_cat]['subcategories'][sub_cat]['amount'] += amount
            statistics[main_cat]['subcategories'][sub_cat]['count'] += 1
            statistics[main_cat]['subcategories'][sub_cat]['transactions'].append(trans)
    
    return statistics


def format_category_report(category_stats):
    """
    تنسيق تقرير التصنيفات
    """
    report_lines = []
    
    # ترتيب التصنيفات الرئيسية حسب المبلغ
    sorted_main = sorted(
        category_stats.items(),
        key=lambda x: x[1]['total_amount'],
        reverse=True
    )
    
    for main_category, data in sorted_main:
        # عنوان التصنيف الرئيسي
        report_lines.append(f"\n{main_category}")
        report_lines.append(f"إجمالي: {data['total_amount']:,.2f} ريال ({data['transaction_count']} عملية)")
        report_lines.append("-" * 50)
        
        # ترتيب التصنيفات الفرعية
        sorted_subs = sorted(
            data['subcategories'].items(),
            key=lambda x: x[1]['amount'],
            reverse=True
        )
        
        for sub_name, sub_data in sorted_subs:
            percentage = (sub_data['amount'] / data['total_amount'] * 100)
            report_lines.append(
                f"  • {sub_name}: {sub_data['amount']:,.2f} ريال "
                f"({sub_data['count']} عملية) - {percentage:.1f}%"
            )
    
    return "\n".join(report_lines)


# ==================== التحسينات الجديدة - نظام التصنيف المتقدم ====================
# يمكن إضافة هذا الكود في نهاية الملف الأساسي

import json
from datetime import datetime
from difflib import SequenceMatcher
import os

# ==================== 1. نظام التعلم ====================

class ClassificationLearner:
    """نظام تعلم بسيط لتحسين التصنيف"""
    
    def __init__(self, filename='classification_patterns.json'):
        self.filename = filename
        self.patterns = self.load_patterns()
    
    def load_patterns(self):
        try:
            with open(self.filename, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {"patterns": {}, "merchants": {}, "statistics": {}}
    
    def save_patterns(self):
        try:
            with open(self.filename, 'w', encoding='utf-8') as f:
                json.dump(self.patterns, f, ensure_ascii=False, indent=2)
        except:
            pass
    
    def learn_pattern(self, description, category, subcategory):
        """تعلم نمط جديد"""
        key = description.lower().strip()
        
        if key not in self.patterns["patterns"]:
            self.patterns["patterns"][key] = {
                "category": category,
                "subcategory": subcategory,
                "count": 0,
                "first_seen": datetime.now().isoformat(),
                "last_seen": datetime.now().isoformat()
            }
        
        self.patterns["patterns"][key]["count"] += 1
        self.patterns["patterns"][key]["last_seen"] = datetime.now().isoformat()
        
        # حفظ اسم التاجر
        merchant_name = self.extract_merchant_name(description)
        if merchant_name:
            self.patterns["merchants"][merchant_name] = {
                "category": category,
                "subcategory": subcategory
            }
        
        self.save_patterns()
    
    def extract_merchant_name(self, description):
        """استخراج اسم التاجر"""
        cleaned = re.sub(r'\b\d+\b', '', description)
        cleaned = re.sub(r'[^\w\s]', ' ', cleaned)
        words = cleaned.split()
        
        if len(words) >= 2:
            return ' '.join(words[:2])
        return None
    
    def get_learned_classification(self, description):
        """الحصول على تصنيف متعلم"""
        key = description.lower().strip()
        
        if key in self.patterns["patterns"]:
            pattern = self.patterns["patterns"][key]
            if pattern["count"] >= 3:
                return (pattern["category"], pattern["subcategory"])
        
        for merchant, info in self.patterns["merchants"].items():
            if merchant.lower() in key:
                return (info["category"], info["subcategory"])
        
        return None

# ==================== 2. معالج اللغة الطبيعية ====================

class NLPProcessor:
    """معالج بسيط للغة الطبيعية"""
    
    def __init__(self):
        self.stop_words = {
            'في', 'من', 'إلى', 'على', 'عند', 'مع', 'هذا', 'هذه',
            'the', 'in', 'at', 'on', 'from', 'to', 'with', 'for'
        }
        
        self.important_words = {
            'مطعم', 'كافيه', 'صيدلية', 'سوبرماركت', 'محطة', 'تحويل',
            'restaurant', 'cafe', 'pharmacy', 'supermarket', 'station', 'transfer'
        }
    
    def extract_keywords(self, text):
        """استخراج الكلمات المفتاحية"""
        words = text.lower().split()
        keywords = []
        
        for word in words:
            if len(word) < 3 or word.isdigit():
                continue
            
            if word in self.stop_words:
                continue
            
            if word in self.important_words:
                keywords.insert(0, word)
            else:
                keywords.append(word)
        
        return keywords[:5]
    
    def calculate_similarity(self, text1, text2):
        """حساب التشابه بين نصين"""
        keywords1 = set(self.extract_keywords(text1))
        keywords2 = set(self.extract_keywords(text2))
        
        if not keywords1 or not keywords2:
            return 0
        
        intersection = keywords1 & keywords2
        union = keywords1 | keywords2
        
        return len(intersection) / len(union)

# ==================== 3. قاعدة بيانات التجار الموسعة ====================

MERCHANT_DATABASE = {
    # مطاعم
    "THE CHEFZ": ("🍽️ مطاعم ومقاهي", "وجبات سريعة"),
    "شيفز": ("🍽️ مطاعم ومقاهي", "وجبات سريعة"),
    "CHEFZ": ("🍽️ مطاعم ومقاهي", "وجبات سريعة"),
    "MCDONALDS": ("🍽️ مطاعم ومقاهي", "وجبات سريعة"),
    "ماكدونالدز": ("🍽️ مطاعم ومقاهي", "وجبات سريعة"),
    "BURGER KING": ("🍽️ مطاعم ومقاهي", "وجبات سريعة"),
    "برجر كنج": ("🍽️ مطاعم ومقاهي", "وجبات سريعة"),
    "KFC": ("🍽️ مطاعم ومقاهي", "وجبات سريعة"),
    "كنتاكي": ("🍽️ مطاعم ومقاهي", "وجبات سريعة"),
    "ALBAIK": ("🍽️ مطاعم ومقاهي", "وجبات سريعة"),
    "البيك": ("🍽️ مطاعم ومقاهي", "وجبات سريعة"),
    "KUDU": ("🍽️ مطاعم ومقاهي", "وجبات سريعة"),
    "كودو": ("🍽️ مطاعم ومقاهي", "وجبات سريعة"),
    
    # كافيهات
    "STARBUCKS": ("🍽️ مطاعم ومقاهي", "مقاهي"),
    "ستاربكس": ("🍽️ مطاعم ومقاهي", "مقاهي"),
    "BARNS": ("🍽️ مطاعم ومقاهي", "مقاهي"),
    "بارنز": ("🍽️ مطاعم ومقاهي", "مقاهي"),
    "DUNKIN": ("🍽️ مطاعم ومقاهي", "مقاهي"),
    "دانكن": ("🍽️ مطاعم ومقاهي", "مقاهي"),
    
    # سوبرماركت
    "CARREFOUR": ("🛒 سوبرماركت وبقالة", "سوبرماركت كبير"),
    "كارفور": ("🛒 سوبرماركت وبقالة", "سوبرماركت كبير"),
    "PANDA": ("🛒 سوبرماركت وبقالة", "سوبرماركت كبير"),
    "بنده": ("🛒 سوبرماركت وبقالة", "سوبرماركت كبير"),
    "DANUBE": ("🛒 سوبرماركت وبقالة", "سوبرماركت كبير"),
    "الدانوب": ("🛒 سوبرماركت وبقالة", "سوبرماركت كبير"),
    
    # صيدليات
    "NAHDI": ("💊 صحة وأدوية", "صيدليات"),
    "النهدي": ("💊 صحة وأدوية", "صيدليات"),
    "DAWAA": ("💊 صحة وأدوية", "صيدليات"),
    "الدواء": ("💊 صحة وأدوية", "صيدليات"),
    
    # متاجر إلكترونية
    "AMAZON": ("🛍️ تسوق وملابس", "متاجر إلكترونية"),
    "امازون": ("🛍️ تسوق وملابس", "متاجر إلكترونية"),
    "NOON": ("🛍️ تسوق وملابس", "متاجر إلكترونية"),
    "نون": ("🛍️ تسوق وملابس", "متاجر إلكترونية"),
    
    # اشتراكات
    "NETFLIX": ("🎧 اشتراكات تلقائية", "ترفيه رقمي"),
    "نتفليكس": ("🎧 اشتراكات تلقائية", "ترفيه رقمي"),
    "SPOTIFY": ("🎧 اشتراكات تلقائية", "ترفيه رقمي"),
    "سبوتيفاي": ("🎧 اشتراكات تلقائية", "ترفيه رقمي"),
    "APPLE.COM/BILL": ("🎧 اشتراكات تلقائية", "خدمات آبل"),
    "ITUNES.COM": ("🎧 اشتراكات تلقائية", "خدمات آبل"),
}

# ==================== 4. إنشاء مثيلات عامة ====================

# إنشاء مثيلات من الأنظمة المساعدة
_learner = ClassificationLearner()
_nlp = NLPProcessor()

# ==================== 5. نسخة محسنة من دالة التصنيف ====================

# حفظ النسخة الأصلية
_original_classify_transaction = classify_transaction

def classify_transaction(description: str, amount: float = 0, date: str = "", debug: bool = False) -> Tuple[str, str]:
    """
    نسخة محسنة من دالة التصنيف بدقة عالية جداً
    """
    if not description:
        return "❓ غير مصنف", "غير محدد"
    
    # 1. تطبيع وتنظيف النص
    normalized_desc = normalize_arabic_text(description)
    clean_desc = clean_for_classification(normalized_desc, preserve_keywords=True)
    
    if debug:
        print(f"DEBUG: النص الأصلي: {description}")
        print(f"DEBUG: بعد التنظيف: {clean_desc}")
    
    # 2. التحقق من الأنماط المتعلمة
    learned = _learner.get_learned_classification(clean_desc)
    if learned:
        if debug:
            print(f"DEBUG: تصنيف متعلم: {learned}")
        return learned
    
    # 3. البحث في قاعدة بيانات التجار
    desc_upper = clean_desc.upper()
    for merchant, category in MERCHANT_DATABASE.items():
        if merchant in desc_upper or merchant in description.upper():
            if debug:
                print(f"DEBUG: تاجر معروف: {merchant} => {category}")
            # حفظ النمط للتعلم
            _learner.learn_pattern(description, category[0], category[1])
            return category
    
    # 4. استخدام دالة التصنيف الأصلية
    result = _original_classify_transaction(description, debug)
    
    # 5. إذا فشل التصنيف، نحاول مطابقة متقدمة
    if result[0] == "❓ غير مصنف":
        # استخراج الكلمات المفتاحية
        keywords = _nlp.extract_keywords(clean_desc)
        
        # البحث عن أفضل تطابق
        best_match = None
        best_score = 0
        
        for main_cat, subcats in EXPENSE_CATEGORIES.items():
            for sub_cat, category_keywords in subcats.items():
                for keyword in category_keywords:
                    # حساب التشابه
                    similarity = _nlp.calculate_similarity(clean_desc, keyword)
                    
                    # نقاط إضافية للكلمات المشتركة
                    keyword_words = set(keyword.lower().split())
                    desc_words = set(clean_desc.lower().split())
                    common_words = keyword_words & desc_words
                    
                    score = similarity * 50 + len(common_words) * 20
                    
                    if score > best_score and score > 30:
                        best_score = score
                        best_match = (main_cat, sub_cat)
        
        if best_match:
            if debug:
                print(f"DEBUG: مطابقة متقدمة: {best_match} (نقاط: {best_score})")
            result = best_match
    
    # 6. التعلم من النتيجة
    if result[0] != "❓ غير مصنف":
        _learner.learn_pattern(description, result[0], result[1])
    
    return result

# ==================== 6. واجهة محسنة للاستخدام (اختيارية) ====================

class TransactionClassifier:
    """واجهة موحدة لنظام التصنيف المتقدم"""
    
    def __init__(self):
        self.learner = _learner
        self.nlp = _nlp
        self.cache = {}
    
    def classify(self, description, amount=0, date=None):
        """تصنيف معاملة"""
        cache_key = f"{description}_{amount}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        result = classify_transaction(description, amount, date or "", False)
        self.cache[cache_key] = result
        return result
    
    def classify_batch(self, transactions):
        """تصنيف مجموعة معاملات"""
        results = []
        for trans in transactions:
            desc = trans.get("description", "")
            amount = trans.get("amount", 0)
            date = trans.get("date", "")
            
            classification = self.classify(desc, amount, date)
            results.append({
                "original": trans,
                "classification": classification
            })
        
        return results

# ==================== النهاية ====================

# اختبار سريع للتأكد من عمل النظام
if __name__ == "__main__":
    print("اختبار نظام التصنيف المحسن...")
    test_cases = [
        "THE CHEFZ RIYADH",
        "CARREFOUR HYPERMARKET",
        "تحويل الى محمد احمد",
        "APPLE.COM/BILL",
        "صيدلية النهدي"
    ]
    
    for desc in test_cases:
        result = classify_transaction(desc, debug=True)
        print(f"{desc} => {result[0]} - {result[1]}")
        print("-" * 50)

def classify_alrajhi_transaction(description: str) -> Tuple[str, str]:
    """
    تصنيف خاص لمعاملات بنك الراجحي
    """
    desc_lower = description.lower()
    
    # فحوصات خاصة لمعاملات الراجحي
    if "apple pay" in desc_lower:
        if "شراء عبر نقاط البيع" in description or "online purchase" in desc_lower:
            return "🎧 اشتراكات تلقائية", "خدمات آبل"
    
    if "حوالة فورية" in description or "payment capital" in desc_lower:
        return "🔄 تحويلات مالية", "تحويل داخلي/خارجي"
    
    if "رسوم" in description:
        return "💳 رسوم بنكية", "رسوم خدمات بنكية"
    
    if "سحب نقدي" in description or "atm withdrawal" in desc_lower:
        return "🏦 معاملات بنكية", "سحب نقدي"
    
    # إذا لم يتم العثور على تصنيف خاص، استخدم التصنيف العام
    return classify_transaction(description)
