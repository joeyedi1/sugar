def rolling_percentile(series, window=260):
    """Percentile rank of each point vs its trailing `window`. Assumes series is date-sorted."""
    def pct_of_last(w):
        return (w < w[-1]).mean() * 100
    return series.rolling(window).apply(pct_of_last, raw=True)

