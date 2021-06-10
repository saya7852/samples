import csv

# this program takes a txt file, cleans it up and changes it into .csv


# open txt file to read
with open('Misc5_tagged.txt', 'r') as f:

    # remove \n character (newline) and split at \t (tab)
    stripped = (line.strip("\n") for line in f)
    lines = (line.split("\t") for line in stripped if line)

    # write a new file, add a header, and store data from each line
    with open("corpusMisc5.csv", "w") as corpus:
        writer = csv.writer(corpus)
        writer.writerow(('element', 'tag', 'hElement'))
        writer.writerows(lines)
