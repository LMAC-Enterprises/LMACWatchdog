class Configuration:
    sourceBlacklistAgentRules: dict = {
        'blacklist': [
            r'^(?:http|https)\:\/\/stock\.adobe\.com\/.+',
            r'^(?:http|https)\:\/\/(?:\w*\.)?canva\.com\/\w.*$',
            r'^(?:http|https)\:\/\/(?:\w*\.)?istockphoto\.com\/\w.*$',
            r'^(?:http|https)\:\/\/(?:\w*\.)?vectorstock\.com\/\w.*$',
            r'^(?:http|https)\:\/\/(?:\w*\.)?dreamstime\.com\/\w.*$',
            r'^(?:http|https)\:\/\/(?:\w*\.)?bigstockphoto\.com\/\w.*$',
            r'^(?:http|https)\:\/\/(?:\w*\.)?stockunlimited\.com\/\w.*$',
            r'^(?:http|https)\:\/\/(?:\w*\.)?imagebank\.biz\/\w.*$',
            r'^(?:http|https)\:\/\/(?:\w*\.)?gettyimages\.com\/\w.*$',
            r'^(?:http|https)\:\/\/(?:\w*\.)?sciencephoto\.com\/\w.*$',
            r'^(?:http|https)\:\/\/(?:\w*\.)?alamy\.com\/\w.*$',
            r'^(?:http|https)\:\/\/(?:\w*\.)?peopleimages\.com\/\w.*$',
            r'^(?:http|https)\:\/\/(?:\w*\.)?stockvault\.net\/\w.*$',
            r'^(?:http|https)\:\/\/(?:\w*\.)?agefotostock\.com\/\w.*$',
            r'^(?:http|https)\:\/\/(?:\w*\.)?stockphotosecrets\.com\/\w.*$',
            r'^(?:http|https)\:\/\/(?:\w*\.)?shopify\.com\/\w.*$',
        ]
    }

    lmacBeneficiaryAgent: dict = {'minimumBenefication': 2000, 'requiredBeneficiary': 'lmac'}
    agentSupervisor: dict = {'hiveCommunityId': 'hive-174695', 'hiveCommunityTag': 'letsmakeacollage'}

    suspectHunterAgent: dict = {'downvoterIndicators': ['spaminator', 'theycallmedan', 'shaka', 'mballesteros', 'agmoore', 'quantumg']}