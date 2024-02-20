# Without DIP
class EmailNotifier:
    def send_notification(self, message):
        # Code to send an email notification
        pass

class SMSNotifier:
    def send_notification(self, message):
        # Code to send an SMS notification
        pass

class User:
    def __init__(self, name, email, phone):
        self.name = name
        self.email = email
        self.phone = phone

    def notify(self, notifier, message):
        notifier.send_notification(message)

# Example usage:
email_notifier = EmailNotifier()
sms_notifier = SMSNotifier()

user1 = User("Alice", "alice@example.com", "555-555-5555")
user2 = User("Bob", "bob@example.com", "555-555-5555")

user1.notify(email_notifier, "Hello from the Email Notifier!")
user2.notify(sms_notifier, "Hello from the SMS Notifier!")
##################################################################
# WITH DIP
class Notifier:
    def send_notification(self, message):
        pass

class EmailNotifier(Notifier):
    def send_notification(self, message):
        # Code to send an email notification
        pass

class SMSNotifier(Notifier):
    def send_notification(self, message):
        # Code to send an SMS notification
        pass

class User:
    def __init__(self, name, notifier):
        self.name = name
        self.notifier = notifier

    def notify(self, message):
        self.notifier.send_notification(message)

# Example usage:
email_notifier = EmailNotifier()
sms_notifier = SMSNotifier()

user1 = User("Alice", email_notifier)
user2 = User("Bob", sms_notifier)

user1.notify("Hello from the Email Notifier!")
user2.notify("Hello from the SMS Notifier!")

