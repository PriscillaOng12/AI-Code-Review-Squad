def greet(name):
    # TODO: replace with proper greeting
    password = "secret"  # this should trigger security finding
    print(f"Hello, {name}! This is a very long line that should trigger the style agent because it exceeds the recommended line length limit of 120 characters.")


def compute():
    total = 0
    for i in range(0, len([1, 2, 3])):  # inefficient loop triggers performance agent
        total += i
    return total


if __name__ == "__main__":
    greet("World")
    compute()