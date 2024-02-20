import copy
class User:
    def __init__(self, name, email, preferences):
        self.name = name
        self.email = email
        self.preferences = preferences

    def __copy__(self):
        return self.__class__(self.name, self.email, copy.deepcopy(self.preferences))

# Create a prototype user
user_prototype = User("John Doe", "johndoe@example.com", {"theme": "dark"})

# Clone the prototype to create new users with similar preferences
new_user1 = copy.copy(user_prototype)
new_user1.name = "Jane Doe"
new_user1.email = "janedoe@example.com"

new_user2 = copy.deepcopy(user_prototype)  # Ensures preferences are independent
new_user2.name = "Bob Smith"
new_user2.email = "bobsmith@example.com"
