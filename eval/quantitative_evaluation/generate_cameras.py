with open('cameras.txt', 'w') as file:
    for i in range(1, 151):
        line = f"{i} PINHOLE 1620 1080 2250.0 2250.0 810 540\n"
        file.write(line)

print("Done! Saved as cameras.txt")
