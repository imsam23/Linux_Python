class Subject:
    def __init__(self):
        self._observers = []

    def attach(self, observer):
        self._observers.append(observer)

    def detach(self, observer):
        self._observers.remove(observer)

    def notify(self, *args, **kwargs):
        for observer in self._observers:
            observer.update(*args, **kwargs)

class Observer:
    def update(self, *args, **kwargs):
        pass  # Implement specific update logic here


class NewsFeed(Subject):
    def __init__(self):
        super().__init__()
        self._latest_news = None

    def update_news(self, news):
        self._latest_news = news
        self.notify(news)

class EmailSubscriber(Observer):
    def update(self, news):
        print(f"Sending email notification: {news}")

class SMSSubscriber(Observer):
    def update(self, news):
        print(f"Sending SMS notification: {news}")

# Create the news feed and subscribers
news_feed = NewsFeed()
email_subscriber = EmailSubscriber()
sms_subscriber = SMSSubscriber()

# Subscribe to the news feed
news_feed.attach(email_subscriber)
news_feed.attach(sms_subscriber)

# Publish news
news_feed.update_news("Breaking news: New product released!")

