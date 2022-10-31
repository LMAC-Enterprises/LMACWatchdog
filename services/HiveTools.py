from services.HiveNetwork import HiveComment


class HivePostType:


    _postType: int

    def __init__(self, postType: int):
        self._postType = postType

    @property
    def postType(self) -> int:
        return self._postType


class HivePostIdentifier:
    UNKOWN_POST_TYPE: int = 0
    CONTEST_POST_TYPE: int = 1
    LIL_POST_TYPE: int = 2
    TUTORIAL_POST_TYPE: int = 3
    NO_LIL_TABLE_LIL_POST_TYPE: int = 4

    @staticmethod
    def getPostType(post: HiveComment) -> int:
        title = post.title.lower()
        body = post.body.lower()

        if 'tutorial' in title or 'lmacschool' in post.cachedTags:
            return HivePostIdentifier.TUTORIAL_POST_TYPE

        if title.startswith('lil:') and '<table class="lil">' not in post.body:
            return HivePostIdentifier.NO_LIL_TABLE_LIL_POST_TYPE

        if title.startswith('lil') and 'lil' in post.cachedTags and '<table class="lil">' not in post.body:
            return HivePostIdentifier.NO_LIL_TABLE_LIL_POST_TYPE

        if title.startswith('lil') and 'lil' in post.cachedTags and '<table class="lil">' in post.body:
            return HivePostIdentifier.LIL_POST_TYPE

        if 'let\'s make a collage' in body and 'round' in body and ('letsmakeacollage' in post.cachedTags or 'lmac' in post.cachedTags):
            return HivePostIdentifier.CONTEST_POST_TYPE

        if 'lmac' in title and 'lil' not in title and 'lil' not in post.cachedTags and 'letsmakeacollage' in post.cachedTags:
            return HivePostIdentifier.CONTEST_POST_TYPE

        if ('letsmakeacollage' in post.cachedTags or 'lmac' in post.cachedTags) and (
                'round' in title or 'contest' in title or 'collage' in title or 'rondo' in title or 'concurso' in title or 'lmac special' in title or 'prize pool' in title):
            return HivePostIdentifier.CONTEST_POST_TYPE

        if 'letsmakeacollage' in post.cachedTags and 'let\'s make a collage' in title:
            return HivePostIdentifier.CONTEST_POST_TYPE

        if 'to LMAC #' in title or 'let\'s make a collage round' in title:
            return HivePostIdentifier.CONTEST_POST_TYPE

        return HivePostIdentifier.UNKOWN_POST_TYPE
