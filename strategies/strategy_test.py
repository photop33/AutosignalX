
def strategy_test(df):
    if len(df) < 2:
        return 0, ["לא מספיק נרות"]
    return 1, ["אסטרטגיית בדיקה – תמיד BUY"]
