"""Quick test of VADER sentiment analysis"""
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

analyzer = SentimentIntensityAnalyzer()
print('VADER imported successfully\n')

test_tweets = [
    'AAPL to the moon! 🚀',
    'Great, AAPL down again 😂',
    'Tesla stock looks neutral today',
    'TSLA crashing hard today 💀',
    'Love this NVDA rally!'
]

for tweet in test_tweets:
    score = analyzer.polarity_scores(tweet)
    print(f'{tweet:45} -> compound: {score["compound"]:6.3f}  (pos:{score["pos"]:.2f} neg:{score["neg"]:.2f})')
