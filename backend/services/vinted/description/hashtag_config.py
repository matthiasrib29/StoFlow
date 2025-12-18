"""
Hashtag Configuration for Vinted Descriptions

Centralise toutes les constantes de hashtags pour Vinted.

Author: Claude
Date: 2025-12-11
"""


class HashtagConfig:
    """Configuration centralisée des hashtags pour les descriptions Vinted."""

    # Nombre maximum de hashtags
    MAX_HASHTAGS = 40

    # Hashtags fixes (toujours présents)
    FIXED = [
        '#vintagestyle',
        '#secondemain',
        '#friperie',
        '#modeethique',
        '#vintagestore'
    ]

    # Hashtags tendance (mode, lifestyle, shopping)
    TRENDING = [
        '#tendance2024',
        '#ootd',
        '#fashion',
        '#style',
        '#vintage',
        '#retro',
        '#lookbook',
        '#instafashion',
        '#fashionista',
        '#vintagefinds',
        '#thrifted',
        '#sustainable',
        '#ecofriendly',
        '#slowfashion',
        '#preloved'
    ]

    # Mapping catégories → hashtags spécifiques
    BY_CATEGORY = {
        'Jeans': ['#jeans', '#denim', '#denimstyle', '#jeansaddict', '#denimhead', '#rawdenim'],
        'Jacket': ['#jacket', '#veste', '#outerwear', '#jacketstyle', '#layering'],
        'Coat': ['#coat', '#manteau', '#wintercoat', '#outerwear', '#cozy'],
        'Shirt': ['#shirt', '#chemise', '#workshirt', '#shirtstyle', '#casualshirt'],
        'T-shirt': ['#tshirt', '#tee', '#casualwear', '#basics', '#streetwear'],
        'Sweatshirt': ['#sweatshirt', '#sweat', '#hoodie', '#comfy', '#casualstyle'],
        'Pants': ['#pants', '#trousers', '#pantalon', '#chino', '#workwear'],
        'Shorts': ['#shorts', '#summerstyle', '#casualshorts', '#beachwear'],
        'Skirt': ['#skirt', '#jupe', '#femininestyle', '#vintage skirt'],
        'Dress': ['#dress', '#robe', '#dressup', '#summerdress', '#partydress'],
        'Sweater': ['#sweater', '#pull', '#knitwear', '#cozy', '#fallstyle'],
        'Blazer': ['#blazer', '#formal', '#workwear', '#professional', '#tailored'],
        'Suit': ['#suit', '#costume', '#formal', '#business', '#elegant'],
        'Accessories': ['#accessories', '#accessoires', '#details', '#finishing touches'],
        'Shoes': ['#shoes', '#chaussures', '#footwear', '#sneakers', '#boots'],
        'Bag': ['#bag', '#sac', '#handbag', '#leather', '#accessories'],
        'Sunglasses': ['#sunglasses', '#lunettes', '#eyewear', '#shades', '#retrosunglasses'],
    }

    # Mapping fit/coupe → hashtags
    BY_FIT = {
        'Slim': ['#slim', '#slimfit', '#fitted', '#modern'],
        'Regular': ['#regular', '#regularfit', '#classic', '#standard'],
        'Relaxed': ['#relaxed', '#relaxedfit', '#comfortable', '#loose'],
        'Oversized': ['#oversized', '#oversizedfit', '#streetwear', '#baggy'],
        'Skinny': ['#skinny', '#skinnyfit', '#tight', '#modern'],
        'Straight': ['#straight', '#straightfit', '#classic', '#timeless'],
        'Flare': ['#flare', '#flarefit', '#70s', '#retro'],
        'Bootcut': ['#bootcut', '#bootcutfit', '#flared', '#vintage'],
        'Wide Leg': ['#wideleg', '#widelegfit', '#palazzo', '#70sstyle'],
        'Tapered': ['#tapered', '#taperedfit', '#modern', '#slim'],
    }

    # Mapping décennies → hashtags
    BY_DECADE = {
        '1950s': ['#50s', '#1950s', '#vintage50s', '#rockabilly', '#pinup'],
        '50s': ['#50s', '#1950s', '#vintage50s', '#rockabilly', '#pinup'],
        '1960s': ['#60s', '#1960s', '#vintage60s', '#mod', '#retro60s'],
        '60s': ['#60s', '#1960s', '#vintage60s', '#mod', '#retro60s'],
        '1970s': ['#70s', '#1970s', '#vintage70s', '#disco', '#hippie', '#boho'],
        '70s': ['#70s', '#1970s', '#vintage70s', '#disco', '#hippie', '#boho'],
        '1980s': ['#80s', '#1980s', '#vintage80s', '#retro80s', '#nostalgia'],
        '80s': ['#80s', '#1980s', '#vintage80s', '#retro80s', '#nostalgia'],
        '1990s': ['#90s', '#1990s', '#vintage90s', '#90sfashion', '#grunge', '#y2k'],
        '90s': ['#90s', '#1990s', '#vintage90s', '#90sfashion', '#grunge', '#y2k'],
        '2000s': ['#00s', '#2000s', '#y2k', '#2000sfashion', '#early2000s'],
        '00s': ['#00s', '#2000s', '#y2k', '#2000sfashion', '#early2000s'],
    }

    # Mapping matières → hashtags
    BY_MATERIAL = {
        'Cotton': ['#cotton', '#coton', '#natural', '#breathable', '#comfortable'],
        'Denim': ['#denim', '#jeans', '#denimstyle', '#rawdenim', '#selvedge'],
        'Leather': ['#leather', '#cuir', '#genuine leather', '#leathergoods', '#quality'],
        'Wool': ['#wool', '#laine', '#warm', '#winter', '#cozy'],
        'Cashmere': ['#cashmere', '#luxury', '#soft', '#premium', '#elegant'],
        'Silk': ['#silk', '#soie', '#luxury', '#elegant', '#smooth'],
        'Linen': ['#linen', '#lin', '#summer', '#breathable', '#natural'],
        'Polyester': ['#polyester', '#synthetic', '#durable', '#easy care'],
        'Nylon': ['#nylon', '#synthetic', '#lightweight', '#durable'],
        'Suede': ['#suede', '#daim', '#soft', '#texture', '#premium'],
        'Corduroy': ['#corduroy', '#velours', '#texture', '#70s', '#retro'],
        'Velvet': ['#velvet', '#velours', '#luxury', '#soft', '#elegant'],
    }

    # Mapping marques → hashtags spécifiques
    BY_BRAND = {
        "Levi's": ['#levis', '#levisjeans', '#levisvintage', '#501', '#denimhead'],
        'Wrangler': ['#wrangler', '#wranglerjeans', '#westernstyle', '#americana'],
        'Lee': ['#lee', '#leejeans', '#vintagejeans', '#denim'],
        'Carhartt': ['#carhartt', '#workwear', '#carharttwip', '#streetwear', '#durability'],
        'Dickies': ['#dickies', '#workwear', '#streetwear', '#skater', '#durable'],
        'Ralph Lauren': ['#ralphlauren', '#polo', '#preppy', '#classic', '#american'],
        'Tommy Hilfiger': ['#tommyhilfiger', '#tommy', '#90s', '#preppy', '#classic'],
        'Nike': ['#nike', '#swoosh', '#sportswear', '#athletic', '#streetwear'],
        'Adidas': ['#adidas', '#3stripes', '#sportswear', '#streetwear', '#classic'],
        'Patagonia': ['#patagonia', '#outdoor', '#fleece', '#sustainable', '#quality'],
        'The North Face': ['#thenorthface', '#tnf', '#outdoor', '#adventure', '#technical'],
        'Champion': ['#champion', '#reverse weave', '#sportswear', '#vintage', '#streetwear'],
        'Lacoste': ['#lacoste', '#crocodile', '#preppy', '#tennis', '#french'],
        'Burberry': ['#burberry', '#luxury', '#british', '#tartan', '#classic'],
        'Gucci': ['#gucci', '#luxury', '#designer', '#italian', '#highfashion'],
    }

    # Mapping saisons → hashtags
    BY_SEASON = {
        'Spring': ['#spring', '#printemps', '#springstyle', '#newseason', '#fresh'],
        'Summer': ['#summer', '#ete', '#summerstyle', '#sunny', '#vacation'],
        'Autumn': ['#autumn', '#fall', '#automne', '#fallstyle', '#cozy'],
        'Winter': ['#winter', '#hiver', '#winterstyle', '#cold', '#warm'],
        'All Season': ['#allseason', '#versatile', '#yearround', '#timeless'],
    }

    # Mapping occasions → hashtags
    BY_OCCASION = {
        'Casual': ['#casual', '#everyday', '#comfortable', '#relaxed'],
        'Formal': ['#formal', '#business', '#professional', '#elegant'],
        'Party': ['#party', '#festive', '#celebration', '#special'],
        'Sport': ['#sport', '#athletic', '#active', '#fitness'],
        'Work': ['#work', '#office', '#professional', '#workwear'],
        'Outdoor': ['#outdoor', '#adventure', '#nature', '#hiking'],
    }


__all__ = ["HashtagConfig"]
