class LazyLayoutNavigator:

    def __init__(self, content, layout, exclude=[], threshold=0.0):
        self._content = content
        self._layout = layout
        self.exclude = exclude
        self.threshold = threshold

    def content(self, separator=''):
        content = []
        for b in self._content:
            if b['type'] == 'google' and b['type'] not in self.exclude:
                content.append(b['text'])
        return separator.join(content)

    def get(self, name: str):
        parents = [p for p in self._layout if p['type'] == name]
        navigators = []
        for p in parents:
            ll = [l for l in self._layout if l['bbox'].overlap(p['bbox'])]
            cc = [c for c in self._content if c['bbox'].overlap(p['bbox']) > .6]
            n = LazyLayoutNavigator(cc, ll, exclude=self.exclude)
            navigators.append(n)
        return navigators
